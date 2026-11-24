"""Structural final QA scoring without inventing extraction or semantic labels."""

import hashlib

from notelens_extraction.contracts import validate_schema
from notelens_extraction.evidence import EvidenceError, validate_span, validate_text
from .retrieval_metrics import indexed_cases


def evaluate_saved_qa(references, predictions):
    expected, actual = indexed_cases(references["cases"]), indexed_cases(predictions["cases"])
    if expected.keys() != actual.keys():
        raise ValueError("Final QA references and saved outputs require identical case IDs.")
    valid = grounded = errors = state_matches = route_matches = 0
    state_denominator = route_denominator = 0
    missing_context = []
    rows = []
    for case_id, case in expected.items():
        prediction = actual[case_id]
        if prediction.get("case_version") != case.get("case_version") or not case.get("case_version"):
            raise ValueError("Final QA case versions differ or are absent.")
        document = case.get("document")
        if document is not None:
            validate_schema(document, "PreparedDocument")
            validate_text(document["text"], document["text_sha256"])
        passages = {}
        for passage in case.get("passages", []):
            pid = passage["passage_id"]
            if pid in passages or hashlib.sha256(passage["text"].encode("utf-8")).hexdigest() != passage["text_sha256"]:
                raise ValueError("Final QA passage identity or digest is invalid.")
            passages[pid] = passage
        result = prediction.get("result")
        row = {"id": case_id, "case_version": case["case_version"], "schema_valid": False,
               "literal_evidence_valid": False, "error": None}
        if result is None:
            errors += 1
            row["error"] = "technical_error"
            rows.append(row)
            continue
        if not isinstance(result, dict):
            row["error"] = "schema_invalid"
            rows.append(row)
            continue
        if result.get("mode") != "live":
            raise ValueError("Final QA saved outputs must be explicitly live-mode, not mock.")
        try:
            validate_schema(result, "AnswerResult", document=document)
            valid += 1
            row["schema_valid"] = True
        except (EvidenceError, ValueError):
            row["error"] = "schema_invalid"
            rows.append(row)
            continue
        context_missing = False
        try:
            for source in result["sources"]:
                if source["kind"] == "document":
                    if document is None:
                        context_missing = True
                        continue
                    if (source["doc_id"], source["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
                        raise EvidenceError("Final QA source belongs to another document.")
                    validate_span(document["text"], source["evidence"])
                else:
                    passage = passages.get(source["passage_id"])
                    if passage is None:
                        context_missing = True
                        continue
                    if source["text"] not in passage["text"]:
                        raise EvidenceError("Final literature excerpt is absent from the pinned passage.")
            if context_missing:
                missing_context.append(case_id)
                row["error"] = "canonical_source_context_missing"
            else:
                grounded += 1
                row["literal_evidence_valid"] = True
        except (EvidenceError, ValueError):
            row["error"] = "literal_evidence_invalid"
        if case.get("expected_evidence_state") is not None:
            state_denominator += 1
            state_matches += int(result["evidence_state"] == case["expected_evidence_state"])
        if case.get("expected_answer_route") is not None:
            route_denominator += 1
            route_matches += int(result["route"] == case["expected_answer_route"])
        rows.append(row)
    total = len(expected)
    return {
        "label": "Frozen final QA structural and literal-source checks; not semantic correctness",
        "metric_scope": "Saved final QA AnswerResults only; extraction F1 and extraction-output structural validity are not measured by this component.",
        "counts": {"cases": total, "schema_valid": valid, "literal_evidence_valid": grounded,
                   "technical_errors": errors},
        "schema_validity": valid / total,
        "span_validity": None if missing_context else grounded / total,
        "source_context_missing_cases": missing_context,
        "state_matches": {"correct": state_matches, "evaluated": state_denominator},
        "route_matches": {"correct": route_matches, "evaluated": route_denominator},
        "semantic_answer_risk": None, "entity_exact_f1": None, "cases": rows,
        "limits": ["Document evidence uses exact code-point offsets and canonical digest.",
                   "Literature evidence checks literal excerpt membership in a separately pinned canonical passage; the AnswerResult contract has no literature offsets.",
                   "State/route agreement and literal citations do not establish semantic correctness or completeness."]}
