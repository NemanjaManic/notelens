"""Check the C-007 classifier contract over authenticated loopback on synthetic inputs."""

import argparse
from hashlib import sha256
import json
import os
import sys

from notelens_contracts.v1 import ContractValidationError, validate_record
from notelens_extraction.demo import request

from .mock_http import post_loopback


CASES = {
    "supported": ("Orthopedic consultation. Right knee pain and swelling after a sports injury.", "Orthopedic"),
    "uncertain": ("Follow-up visit. No other details are available.", None),
}


def synthetic_request(case: str) -> dict:
    text, _ = CASES[case]
    payload = request()
    payload["document"].update(doc_id=f"d-c007-{case}-v1", text=text,
                               text_sha256=sha256(text.encode("utf-8")).hexdigest())
    return payload


def check_response(record: dict, document: dict, *, mode: str, model_version: str | None, case: str) -> dict:
    if record.get("mode") != mode:
        raise ValueError("Classifier mode differs from the requested mock or fitted profile.")
    if mode == "live" and (not model_version or record.get("model_version") != model_version):
        raise ValueError("Classifier model version differs from the expected fitted version.")
    if (record.get("doc_id"), record.get("text_sha256")) != (document["doc_id"], document["text_sha256"]):
        raise ValueError("Classifier response differs from the prepared document identity.")
    try:
        validate_record("ClassificationResult", record, document=document)
    except ContractValidationError as exc:
        raise ValueError("Classifier response violates the frozen classification contract.") from exc
    _, expected_category = CASES[case]
    if mode == "mock" and case == "supported":
        expected_category = "Cardiovascular / Pulmonary"
    if record["status"] != case or record["category"] != expected_category:
        raise ValueError("Classifier status or category differs from the synthetic case expectation.")
    if mode == "live" and record["score_kind"] != "probability":
        raise ValueError("This fitted Logistic Regression check requires probability scores.")
    return {
        "input": "synthetic", "case": case, "mode": mode,
        "model_version": record["model_version"], "doc_id": record["doc_id"], "text_sha256": record["text_sha256"],
        "status": record["status"], "category": record["category"],
        "outcome": "abstained" if case == "uncertain" else "classified",
        "score_kind": record["score_kind"], "score_labels": [score["category"] for score in record["scores"]],
    }


def check_classifier(port: int, token: str, *, mode: str, model_version: str | None, case: str) -> dict:
    payload = synthetic_request(case)
    first = post_loopback(port, "/v1/classify", payload, token=token, require_no_store=True)
    report = check_response(first, payload["document"], mode=mode, model_version=model_version, case=case)
    second = post_loopback(port, "/v1/classify", payload, token=token, require_no_store=True)
    if second != first:
        raise ValueError("Repeated classifier results differed for the same synthetic input.")
    return {**report, "repeatable": True, "http_successes": 2}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--mode", choices=("mock", "live"), required=True,
                        help="Use live for explicitly started fitted local inference.")
    parser.add_argument("--model-version", help="Expected version for fitted local inference.")
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    args = parser.parse_args()
    token = os.getenv("NOTELENS_CLASSIFIER_SERVICE_TOKEN")
    if not token:
        parser.error("Set the local classifier service token before running the check.")
    if (args.mode == "live") != bool(args.model_version and args.model_version.strip()):
        parser.error("Provide --model-version for the fitted local profile only.")
    try:
        report = check_classifier(args.port, token, mode=args.mode, model_version=args.model_version, case=args.case)
    except ValueError as exc:
        print(f"Classifier check failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
