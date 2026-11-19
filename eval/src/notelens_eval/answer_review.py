"""Read-only integrity checks; human declarations are not verified human authorship."""
import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

DIMENSIONS = {"source_support", "required_facts", "extra_facts", "uncertainty_and_context",
              "evidence_gaps", "scope_and_safety", "clarity_and_english"}
IDENTITY = ("review_id", "reviewer_alias", "case_id", "doc_id", "text_sha256",
            "response_id", "response_sha256", "mode", "extractor_or_answer_version", "prompt_version")


def inspect(record):
    """Return a state without filling or changing any submitted field."""
    if not isinstance(record, dict):
        raise ValueError("Review must be an object.")
    if record.get("rubric_version") != "d-answer-review-rubric-v1":
        raise ValueError("Unsupported rubric version.")
    scores = record.get("dimensions")
    if not isinstance(scores, dict) or set(scores) != DIMENSIONS:
        raise ValueError("Unexpected review dimensions.")
    if any(v is not None and v != "U" and (type(v) is not int or v not in (0, 1, 2)) for v in scores.values()):
        raise ValueError("Invalid dimension score.")
    for key in ("human_reviewed", "independent_review"):
        if type(record.get(key)) is not bool:
            raise ValueError("Review declarations must be boolean.")
    for key in ("critical_error", "needs_adjudication"):
        if record.get(key) is not None and type(record[key]) is not bool:
            raise ValueError("Invalid review flag.")
    for key in IDENTITY + ("rationale", "completed_at"):
        if record.get(key) is not None and (not isinstance(record[key], str) or not record[key].strip()):
            raise ValueError("Invalid review metadata.")
    for key in ("text_sha256", "response_sha256"):
        digest = record.get(key)
        if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid review digest.")
    if record.get("mode") not in (None, "mock", "live"):
        raise ValueError("Invalid review mode.")
    if record.get("response_action") not in (None, "answer", "partial_answer", "abstain", "unclear", "operational_error"):
        raise ValueError("Invalid response action.")
    if record.get("answerable_from_document") not in (None, "yes", "partly", "no", "unclear"):
        raise ValueError("Invalid answerability flag.")
    for key in ("issue_codes", "claim_source_notes"):
        if not isinstance(record.get(key), list):
            raise ValueError("Review notes must be arrays.")
    if record.get("completed_at"):
        try:
            stamp = datetime.fromisoformat(record["completed_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError()
        except ValueError:
            raise ValueError("Completion timestamp requires timezone.") from None
    if record.get("response_action") == "operational_error":
        if any(v is not None for v in scores.values()) or record["human_reviewed"]:
            raise ValueError("Operational failures cannot carry answer quality ratings.")
        return "operational_error"
    started = any(record.get(k) is not None for k in IDENTITY + ("rationale", "completed_at", "response_action")) or any(v is not None for v in scores.values()) or record["human_reviewed"]
    if not started:
        return "blank"
    complete = (all(record.get(k) is not None for k in IDENTITY)
                and record["human_reviewed"] and record["independent_review"]
                and all(v is not None for v in scores.values())
                and all(record.get(k) is not None for k in ("critical_error", "needs_adjudication", "answerable_from_document", "rationale", "completed_at", "response_action")))
    return "completed_declared_human_review" if complete else "incomplete"


def summarize(records):
    counts = Counter({k: 0 for k in ("blank", "incomplete", "operational_error", "completed_declared_human_review", "invalid")})
    dimensions = {k: {"rated": 0, "unable_to_judge": 0, "sum": 0, "score_counts": {"0": 0, "1": 0, "2": 0}} for k in sorted(DIMENSIONS)}
    seen = set()
    errors = []
    outcomes = Counter()
    critical_errors = adjudication_pending = 0
    for index, record in enumerate(records):
        try:
            state = inspect(record)
            identifier = record.get("review_id")
            if identifier is not None:
                if identifier in seen:
                    raise ValueError("Duplicate review ID.")
                seen.add(identifier)
            counts[state] += 1
            if state == "completed_declared_human_review":
                outcomes[record["response_action"]] += 1
                critical_errors += record["critical_error"]
                adjudication_pending += record["needs_adjudication"]
                for key, value in record["dimensions"].items():
                    if value == "U":
                        dimensions[key]["unable_to_judge"] += 1
                    else:
                        dimensions[key]["score_counts"][str(value)] += 1
                        dimensions[key]["rated"] += 1
                        dimensions[key]["sum"] += value
        except ValueError as exc:
            counts["invalid"] += 1
            errors.append({"record_index": index, "reason": str(exc)})
    for result in dimensions.values():
        result["mean"] = result.pop("sum") / result["rated"] if result["rated"] else None
        result.pop("sum", None)
    return {"rubric_status": "draft_uncalibrated", "counts": dict(counts), "dimensions": dimensions,
            "completed_outcomes": dict(outcomes), "critical_errors": critical_errors,
            "adjudication_pending": adjudication_pending,
            "errors": errors, "human_authorship_verified": False,
            "limitations": "Structural checks only; no clinical validation or reviewer approval is inferred."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    args = parser.parse_args()
    records = []
    for path in args.inputs:
        value = json.loads(path.read_text(encoding="utf-8"))
        records.extend(value if isinstance(value, list) else [value])
    report = summarize(records)
    print(json.dumps(report, indent=2))
    return 1 if report["counts"]["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
