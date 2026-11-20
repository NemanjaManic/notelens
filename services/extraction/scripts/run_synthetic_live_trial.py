"""Run D's approved two-request synthetic OpenAI smoke exactly once."""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_ROOT.parent.parent
sys.path.insert(0, str(SERVICE_ROOT / "src"))

from notelens_extraction.demo import request as demo_request
from notelens_extraction.errors import ServiceError
from notelens_extraction.openai_trial import DEMO_QUESTION, OpenAITrialProvider
from notelens_extraction.openai_transport import TrialBudget, request_sha256, trial_provider
from notelens_extraction.service import generation_instructions, run


APPROVAL_PATH = REPO_ROOT / "docs/extraction-eval/d-004-live-trial-2026-11-20.json"
RECEIPT_PATH = SERVICE_ROOT / ".trial-receipt-2026-11-20"
OUTPUT_LIMIT = 512


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("D-004 trial not started: OPENAI_API_KEY is not configured.", file=sys.stderr)
        return 2

    approval = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    if (approval["approval"]["status"] != "reported-approved"
            or approval["approval"]["max_provider_calls"] != 2
            or approval["request_limits"]["max_output_tokens_each"] != OUTPUT_LIMIT):
        print("D-004 trial not started: approval record does not match this runner.", file=sys.stderr)
        return 2

    bounds = approval["request_limits"]["requests"]
    preflight = OpenAITrialProvider(lambda _payload: {}, max_output_tokens=OUTPUT_LIMIT)
    operations = (
        ("extract", demo_request()),
        ("answer", demo_request(DEMO_QUESTION)),
    )
    approved_bounds = {}
    for operation, request in operations:
        instructions, _ = generation_instructions(operation)
        payload = preflight.prepare(operation, request, instructions)
        digest = request_sha256(payload)
        record = bounds[operation]
        if digest != record["request_sha256"]:
            print(f"D-004 trial not started: {operation} payload hash changed.", file=sys.stderr)
            return 2
        approved_bounds[digest] = record["approved_input_token_bound"]

    budget = TrialBudget(
        approved_bounds,
        input_usd_per_million=Decimal(approval["provider"]["input_usd_per_million_tokens"]),
        output_usd_per_million=Decimal(approval["provider"]["output_usd_per_million_tokens"]),
    )
    try:
        provider = trial_provider(
            api_key=api_key, budget=budget, receipt=RECEIPT_PATH,
            max_output_tokens=OUTPUT_LIMIT,
        )
        results = {}
        for operation, request in operations:
            results[operation] = run(request, operation, provider)[0]
    except ValueError:
        print(
            "D-004 trial not started: credential must be the raw printable ASCII API key, "
            "without spaces, quotes, or a 'Bearer ' prefix.",
            file=sys.stderr,
        )
        return 2
    except ServiceError as exc:
        print(f"D-004 trial ended safely: {exc.code}: {exc.message}", file=sys.stderr)
        return 1

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
