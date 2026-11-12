"""Inspectable synthetic development suite, never a clinical or held-out benchmark."""

import hashlib
import json

from notelens_extraction.contracts import validate_extraction, validate_generation, validate_schema
from notelens_extraction.evidence import validate_span, validate_text

from .metrics import match, prediction_mentions


def validate_references(references: dict) -> None:
    if references.get("kind") != "synthetic_reference_proposal" or references.get("human_reviewed") is not False:
        raise ValueError("Expected explicitly unreviewed synthetic references.")
    seen, docs = set(), set()
    for case in references["cases"]:
        document = case["request"]["document"]
        validate_schema(case["request"], "ExtractionRequest")
        validate_text(document["text"], document["text_sha256"])
        if case["id"] in seen or document["doc_id"] in docs:
            raise ValueError("Duplicate case or document identity.")
        seen.add(case["id"])
        docs.add(document["doc_id"])
        # Repeated text across cases is intentional: a question can exercise a different behavior.
        if not case.get("group") or not case.get("rationale"):
            raise ValueError("References require a group and rationale.")
        mentions = set()
        for entity in case["entities"]:
            validate_span(document["text"], entity["mention"])
            key = (entity["type"], entity["mention"]["start"], entity["mention"]["end"])
            if key in mentions or entity["type"] not in {"diagnosis", "symptom", "procedure"}:
                raise ValueError("Duplicate or invalid reference entity.")
            mentions.add(key)
            for attribute, allowed in {
                "assertion": {"confirmed", "suspected", "negated", None},
                "temporality": {"current", "historical", "unknown", None},
                "subject": {"patient", "family", "other", "unknown", None},
            }.items():
                if entity[attribute] not in allowed:
                    raise ValueError("Invalid reference attribute.")
        qa_ids = set()
        for qa in case["qa"]:
            if qa["id"] in qa_ids or not qa.get("rationale"):
                raise ValueError("Duplicate QA identity or missing rationale.")
            qa_ids.add(qa["id"])
            validate_schema({**case["request"], "question": qa["question"]}, "DocumentQuestionRequest")
            state, support = qa["expected_evidence_state"], qa["expected_support"]
            if state not in {"sufficient", "partial", "insufficient"} or type(qa["answerable"]) is not bool:
                raise ValueError("Invalid QA expectation.")
            if qa["answerable"] != bool(support) or (state == "insufficient") != (not support):
                raise ValueError("Inconsistent QA answerability and support.")
            if any(not isinstance(s, str) or not s or s not in document["text"] for s in support):
                raise ValueError("Expected support must occur verbatim in the source.")


def evaluate_suite(references: dict, predictions: dict) -> dict:
    from .run import evaluate

    validate_references(references)
    report = evaluate(references, predictions)
    report["reference_sha256"] = hashlib.sha256(
        json.dumps(references, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    report["groups"] = {}
    for group in sorted({c["group"] for c in references["cases"]}):
        cases = [c for c in references["cases"] if c["group"] == group]
        ids = {c["id"] for c in cases}
        grouped = evaluate({**references, "cases": cases},
                           {**predictions, "cases": [p for p in predictions["cases"] if p["id"] in ids]})
        report["groups"][group] = {k: grouped[k] for k in (
            "counts", "entities_exact", "entities_relaxed", "answerability", "record_validation")}
    failures, per_case = [], []
    by_id = {p["id"]: p for p in predictions["cases"]}
    support_correct = 0

    def fail(case, category, expected, actual, *, qa_id=None, technical=False):
        failures.append({"case_id": case["id"], "group": case["group"], "qa_id": qa_id,
                         "category": category, "expected": expected, "actual": actual,
                         "likely_cause": ("Unavailable or invalid service output; inspect diagnostics."
                                          if technical else "Limited literal mock catalog or a candidate behavior mismatch; inspect this case."),
                         "proposal": ("Investigate service/adapter validation before interpreting quality metrics."
                                      if technical else "Retain the regression case for the approved real provider; review reference semantics with the team.")})

    for case in references["cases"]:
        document, prediction = case["request"]["document"], by_id[case["id"]]
        first_failure = len(failures)
        try:
            if prediction["result"] is None:
                raise ValueError("Unavailable extraction.")
            validate_extraction(prediction["result"], document)
            predicted = prediction_mentions(document, prediction["result"]["items"])
            expected = [{**r, "doc_id": document["doc_id"]} for r in case["entities"]]
            pairs = match(predicted, expected)
            matched_p, matched_r = {p for p, _ in pairs}, {r for _, r in pairs}
            for index, entity in enumerate(expected):
                if index not in matched_r:
                    fail(case, "missing_entity", entity, None)
            for index, entity in enumerate(predicted):
                if index not in matched_p:
                    fail(case, "unexpected_entity", None, entity)
            for p, r in pairs:
                for attribute in ("assertion", "temporality", "subject"):
                    if expected[r][attribute] is not None and predicted[p][attribute] != expected[r][attribute]:
                        fail(case, "entity_" + attribute, expected[r], predicted[p])
        except ValueError as exc:
            fail(case, "technical_error" if prediction["result"] is None else "invalid_extraction",
                 "Valid extraction with resolvable evidence", str(exc), technical=True)
        answers = {q["id"]: q for q in prediction["qa"]}
        for qa in case["qa"]:
            answer = answers[qa["id"]]["result"]
            try:
                if answer is None:
                    raise ValueError("Unavailable answer.")
                validate_schema(answer, "AnswerResult")
                validate_generation(answer, document, answer=True)
            except ValueError as exc:
                fail(case, "technical_error" if answer is None else "invalid_answer", "Valid answer",
                     str(exc), qa_id=qa["id"], technical=True)
                continue
            if answer["evidence_state"] != qa["expected_evidence_state"]:
                fail(case, "qa_state", qa["expected_evidence_state"], answer["evidence_state"], qa_id=qa["id"])
            # Literal fixture support coverage is narrower than semantic answer correctness.
            linked = {source_id for claim in answer["claims"] for source_id in claim["source_ids"]}
            quotes = {s["evidence"]["quote"] for s in answer["sources"] if s["source_id"] in linked}
            missing = [s for s in qa["expected_support"] if s not in quotes]
            support_ok = not missing and (bool(answer["claims"]) == qa["answerable"])
            support_correct += int(support_ok and answer["evidence_state"] == qa["expected_evidence_state"])
            if not support_ok:
                fail(case, "qa_support", qa["expected_support"], sorted(quotes), qa_id=qa["id"])
        per_case.append({"case_id": case["id"], "group": case["group"],
                         "failure_count": len(failures) - first_failure,
                         "unresolved_reference_attributes": sum(e[a] is None for e in case["entities"]
                                                                 for a in ("assertion", "temporality", "subject"))})
    report.update(failures=failures, cases=per_case,
                  unique_texts=len({c["request"]["document"]["text_sha256"] for c in references["cases"]}),
                  qa_literal_support={"state_and_required_quotes_correct": support_correct,
                                      "evaluated": report["counts"]["qa"],
                                      "limitation": "Exact required source-quote coverage, not semantic or clinical correctness; extra relevant/irrelevant claims need review."})
    return report


def render_report(report: dict) -> str:
    lines = ["# Synthetic extraction and QA evaluation", "",
             "Agent-authored development fixtures; no human, clinical or live-model validation.", "",
             f"Documents: {report['counts']['documents']}; questions: {report['counts']['qa']}.", "",
             f"Reference version: `{report['reference_version']}`.",
             f"Reference normalized JSON SHA-256: `{report['reference_sha256']}`.", "",
             "| Group | Documents | Exact TP | FP | FN | QA states correct |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for group, result in report["groups"].items():
        score = result["entities_exact"]
        lines.append(f"| {group} | {result['counts']['documents']} | {score.get('tp', 'withheld')} | {score.get('fp', 'withheld')} | {score.get('fn', 'withheld')} | {result['answerability']['expected_state_correct']}/{result['counts']['qa']} |")
    lines += ["", f"Exact entity scores: `{json.dumps(report['entities_exact'], sort_keys=True)}`.", "",
              f"Record validation: `{json.dumps(report['record_validation'], sort_keys=True)}`.", "",
              f"Required literal support and expected state: {report['qa_literal_support']['state_and_required_quotes_correct']}/{report['counts']['qa']}.", "",
              "State matching and exact quote coverage do not establish semantic completeness or clinical accuracy.", "",
              "## Case outcomes", "", "| Case | Group | Failure records | Unresolved reference attributes |",
              "| --- | --- | ---: | ---: |"]
    for case in report["cases"]:
        lines.append(f"| {case['case_id']} | {case['group']} | {case['failure_count']} | {case['unresolved_reference_attributes']} |")
    lines += ["", "## Failure analysis", "",
              "Failure records can overlap: one answer may fail both state and required-support checks.", ""]
    for failure in report["failures"]:
        lines += [f"### {failure['case_id']} / {failure['qa_id'] or 'extraction'} / {failure['category']}", "",
                  f"Expected: `{json.dumps(failure['expected'], ensure_ascii=True)}`.", "",
                  f"Actual: `{json.dumps(failure['actual'], ensure_ascii=True)}`.", "",
                  f"Likely cause: {failure['likely_cause']}", "",
                  f"Proposed next action: {failure['proposal']}", ""]
    lines += ["## Limitations", ""]
    lines += [f"- {key}: {value}" for key, value in report["unavailable"].items()]
    return "\n".join(lines) + "\n"
