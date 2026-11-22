"""Read-only integrity checks; human declarations are not verified human authorship."""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

DIMENSIONS = {"source_support", "required_facts", "extra_facts", "uncertainty_and_context",
              "evidence_gaps", "scope_and_safety", "clarity_and_english"}
IDENTITY = ("review_id", "reviewer_alias", "case_id", "doc_id", "text_sha256",
            "response_id", "response_sha256", "mode", "extractor_or_answer_version", "prompt_version")
CURRENT_FORM_VERSION = "d-answer-review-form-v2"
OUTPUT_TYPES = {"document_answer", "summary", "literature_answer", "mixed_answer"}
COMPONENT_OUTCOMES = {"answer", "partial_answer", "abstain", "operational_error"}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _current_form_ready(record, scores):
    output = record.get("reviewed_output")
    if output is not None and (not isinstance(output, str) or output not in OUTPUT_TYPES):
        raise ValueError("Invalid reviewed output type.")
    exposure = [record.get(key) for key in ("prior_exposure", "self_authored_output")]
    if any(value is not None and type(value) is not bool for value in exposure):
        raise ValueError("Exposure declarations must be boolean.")
    if True in exposure:
        if record["independent_review"]:
            raise ValueError("An exposed or self-authored review cannot be independent.")
        if not _nonempty(record.get("exposure_note")):
            raise ValueError("Disclosed exposure requires a note.")

    explained = set()
    for note in record["claim_source_notes"]:
        if (not isinstance(note, dict) or not isinstance(note.get("dimension"), str)
                or note["dimension"] not in DIMENSIONS
                or not _nonempty(note.get("reason")) or not _nonempty(note.get("minimum_correction"))):
            raise ValueError("Each dimension note needs a dimension, reason and minimum correction.")
        if any(note.get(key) is not None and not _nonempty(note[key]) for key in ("claim_id", "source_id")):
            raise ValueError("Claim and source identifiers must be nonempty or null.")
        explained.add(note["dimension"])
    notes_ready = all(key in explained for key, score in scores.items() if score in (0, 1, "U"))

    components = record.get("component_outcomes")
    if not isinstance(components, list):
        raise ValueError("Component outcomes must be an array.")
    routes = {}
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("Each component outcome must be an object.")
        route, outcome = component.get("route"), component.get("outcome")
        if (route not in ("document", "literature") or route in routes
                or not isinstance(outcome, str) or outcome not in COMPONENT_OUTCOMES):
            raise ValueError("Expected a unique document or literature component and a valid outcome.")
        if outcome == "operational_error" and not all(
            _nonempty(component.get(key)) for key in ("error_code", "request_or_run_id")
        ):
            raise ValueError("A failed component requires its error code and request or run ID.")
        if outcome != "operational_error" and component.get("error_code") is not None:
            raise ValueError("A healthy component cannot carry an operational error code.")
        routes[route] = outcome
    if components and output != "mixed_answer":
        raise ValueError("Component outcomes apply to mixed answers.")
    if "operational_error" in routes.values() and len(routes) == 2:
        has_content = any(value in ("answer", "partial_answer") for value in routes.values())
        expected = "partial_answer" if has_content else "operational_error"
        if record.get("response_action") not in (None, expected):
            raise ValueError("Mixed response action conflicts with its failed component and surviving content.")
    components_ready = output != "mixed_answer" or set(routes) == {"document", "literature"}

    snapshot_id = record.get("source_snapshot_id")
    snapshot_digest = record.get("source_snapshot_sha256")
    if snapshot_id is not None and not _nonempty(snapshot_id):
        raise ValueError("Invalid evidence snapshot ID.")
    if snapshot_digest is not None and (not isinstance(snapshot_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", snapshot_digest)):
        raise ValueError("Invalid evidence snapshot digest.")
    snapshot_ready = output not in ("literature_answer", "mixed_answer") or bool(snapshot_id and snapshot_digest)
    return (output is not None and exposure == [False, False] and notes_ready
            and components_ready and snapshot_ready)


def inspect(record, *, require_current_form=False):
    """Return a state without filling or changing any submitted field."""
    if not isinstance(record, dict):
        raise ValueError("Review must be an object.")
    if record.get("rubric_version") != "d-answer-review-rubric-v1":
        raise ValueError("Unsupported rubric version.")
    version = record.get("review_form_version")
    if version not in (None, CURRENT_FORM_VERSION) or (require_current_form and version != CURRENT_FORM_VERSION):
        raise ValueError("Expected the current D-008 review form.")
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
    form_ready = version is None or _current_form_ready(record, scores)
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
    # A response can abstain before generating, with an explicit null prompt version.
    nullable_identity = {"prompt_version"}
    if version == CURRENT_FORM_VERSION and record.get("reviewed_output") == "literature_answer":
        nullable_identity.update(("doc_id", "text_sha256"))
    identity_present = "prompt_version" in record and all(
        record.get(key) is not None for key in IDENTITY if key not in nullable_identity
    )
    complete = (identity_present and form_ready
                and record["human_reviewed"] and record["independent_review"]
                and all(v is not None for v in scores.values())
                and all(record.get(k) is not None for k in ("critical_error", "needs_adjudication", "answerable_from_document", "rationale", "completed_at", "response_action")))
    return "completed_declared_human_review" if complete else "incomplete"


def compare_reviewers(groups):
    """Compare independent declarations about the same pinned output."""
    dimensions = {key: Counter(comparable=0, exact=0, major_disagreement=0, unable=0)
                  for key in sorted(DIMENSIONS)}
    adjudication = []
    pairs = 0
    for reviewers in groups.values():
        for left, right in combinations(sorted(reviewers.values(), key=lambda row: row["review_id"]), 2):
            pairs += 1
            disagreements = []
            for key, totals in dimensions.items():
                first, second = left["dimensions"][key], right["dimensions"][key]
                if "U" in (first, second):
                    totals["unable"] += 1
                    continue
                totals["comparable"] += 1
                totals["exact"] += int(first == second)
                totals["major_disagreement"] += int(abs(first - second) == 2)
                if first != second:
                    disagreements.append(key)
            flags = [key for key in ("response_action", "answerable_from_document", "critical_error")
                     if left[key] != right[key]]
            if disagreements or flags or left["needs_adjudication"] or right["needs_adjudication"]:
                adjudication.append({
                    "case_id": left["case_id"], "response_id": left["response_id"],
                    "review_ids": [left["review_id"], right["review_id"]],
                    "dimensions": disagreements, "flags": flags,
                })
    return {"matched_pairs": pairs, "by_dimension": dimensions, "adjudication_pairs": adjudication}


def summarize(records, *, require_current_form=False):
    counts = Counter({k: 0 for k in ("blank", "incomplete", "operational_error", "completed_declared_human_review", "invalid")})
    dimensions = {k: {"rated": 0, "unable_to_judge": 0, "sum": 0, "score_counts": {"0": 0, "1": 0, "2": 0}} for k in sorted(DIMENSIONS)}
    seen = set()
    errors = []
    outcomes = Counter()
    groups = defaultdict(dict)
    component_outcomes = defaultdict(Counter)
    component_failures = []
    critical_errors = adjudication_pending = 0
    for index, record in enumerate(records):
        try:
            state = inspect(record, require_current_form=require_current_form)
            identifier = record.get("review_id")
            if identifier is not None:
                if identifier in seen:
                    raise ValueError("Duplicate review ID.")
                seen.add(identifier)
            if state == "completed_declared_human_review":
                scope = ("document_answer", None, None)
                if record.get("review_form_version") == CURRENT_FORM_VERSION:
                    scope = (record["reviewed_output"], record.get("source_snapshot_id"), record.get("source_snapshot_sha256"))
                identity = tuple(record.get(key) for key in IDENTITY[2:]) + scope
                alias = record["reviewer_alias"].strip().casefold()
                if alias in groups[identity]:
                    raise ValueError("Duplicate reviewer for the same pinned output.")
                groups[identity][alias] = record
            counts[state] += 1
            if record.get("review_form_version") == CURRENT_FORM_VERSION and state in (
                "completed_declared_human_review", "operational_error",
            ):
                for component in record["component_outcomes"]:
                    route, outcome = component["route"], component["outcome"]
                    component_outcomes[route][outcome] += 1
                    if outcome == "operational_error":
                        component_failures.append({
                            "review_id": identifier, "case_id": record.get("case_id"), "route": route,
                            "error_code": component["error_code"], "request_or_run_id": component["request_or_run_id"],
                        })
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
            "component_outcomes": {route: dict(totals) for route, totals in component_outcomes.items()},
            "component_failures": component_failures,
            "adjudication_pending": adjudication_pending,
            "reviewer_agreement": compare_reviewers(groups),
            "errors": errors, "human_authorship_verified": False,
            "limitations": "Structural checks only; no clinical validation or reviewer approval is inferred."}


def verify_response_artifacts(records, artifact_directory, *, require_current_form=False):
    """Check declared response hashes against exact retained UTF-8 artifact bytes."""
    checked = 0
    root = artifact_directory.resolve()
    for record in records:
        state = inspect(record, require_current_form=require_current_form)
        if state != "completed_declared_human_review":
            continue
        response_id = record["response_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", response_id):
            raise ValueError("Response ID cannot safely identify an artifact.")
        path = (root / f"{response_id}.json").resolve()
        if path.parent != root:
            raise ValueError("Response artifact must stay within its directory.")
        raw = path.read_bytes()
        json.loads(raw.decode("utf-8"))
        if hashlib.sha256(raw).hexdigest() != record["response_sha256"]:
            raise ValueError("Reviewed response artifact digest mismatch.")
        checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--response-artifacts", type=Path)
    parser.add_argument("--require-current-form", action="store_true", help="Require form v2 for new submissions.")
    args = parser.parse_args()
    records = []
    for path in args.inputs:
        value = json.loads(path.read_text(encoding="utf-8"))
        records.extend(value if isinstance(value, list) else [value])
    report = summarize(records, require_current_form=args.require_current_form)
    report["verified_response_artifacts"] = None
    if args.response_artifacts:
        try:
            report["verified_response_artifacts"] = verify_response_artifacts(
                records, args.response_artifacts, require_current_form=args.require_current_form,
            )
        except (OSError, ValueError):
            parser.error("Response artifact verification failed.")

    print(json.dumps(report, indent=2))
    counts = report["counts"]
    pending = counts["blank"] + counts["incomplete"]
    return 1 if counts["invalid"] or (args.require_current_form and pending) else 0


if __name__ == "__main__":
    raise SystemExit(main())
