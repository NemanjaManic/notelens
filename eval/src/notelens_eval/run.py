"""Generate mock predictions separately, then score versioned reference files."""

import argparse
import hashlib
import json
from pathlib import Path

from notelens_extraction.contracts import SCHEMA_PATH, validate_extraction, validate_generation, validate_schema
from notelens_extraction.evidence import EvidenceError, validate_span, validate_text
from notelens_extraction.errors import ServiceError
from notelens_extraction.service import Diagnostics, run as generate
from .metrics import entity_scores, prediction_mentions

EVAL_ROOT = Path(__file__).resolve().parents[2]


def produce(cases: dict) -> dict:
    if cases.get("version") == "d-extraction-qa-synthetic-v1":
        from .suite import validate_references
        validate_references(cases)
    # Only the public/synthetic request is passed. References never enter providers.
    predictions = []
    for case in cases["cases"]:
        trace = Diagnostics()
        try:
            result, diagnostics = generate(case["request"], "extract", diagnostics=trace)
        except ServiceError as exc:
            result, diagnostics = None, vars(trace)
            diagnostics = {**diagnostics, "technical_error": exc.code}
        answers = []
        for qa in case["qa"]:
            request = {**case["request"], "question": qa["question"]}
            trace = Diagnostics()
            try:
                answer, stats = generate(request, "answer", diagnostics=trace)
            except ServiceError as exc:
                answer, stats = None, {**vars(trace), "technical_error": exc.code}
            answers.append({"id": qa["id"], "result": answer, "diagnostics": stats})
        predictions.append({"id": case["id"], "result": result, "diagnostics": diagnostics, "qa": answers})
    return {"kind": "synthetic_mock_predictions", "version": "d-mock-predictions-v1", "cases": predictions}


def evaluate(references: dict, predictions: dict) -> dict:
    expected_ids = [c["id"] for c in references["cases"]]
    actual_ids = [c["id"] for c in predictions["cases"]]
    if len(set(expected_ids)) != len(expected_ids) or len(set(actual_ids)) != len(actual_ids) or set(expected_ids) != set(actual_ids):
        raise ValueError("Missing, duplicate or unexpected evaluation case IDs.")
    by_id = {c["id"]: c for c in predictions["cases"]}
    predicted_entities, reference_entities = [], []
    extraction_valid = answer_valid = failures = repairs = attempts = 0
    schema_valid = invalid_schema = invalid_evidence = technical_errors = 0
    invalid_extractions = expected_state_correct = 0
    validation_issues = []
    answerable = answered = unanswerable = rejected = qa_count = 0
    cases_trace = []
    for case in references["cases"]:
        document = case["request"]["document"]
        validate_text(document["text"], document["text_sha256"])
        for reference in case["entities"]:
            validate_span(document["text"], reference["mention"])
        prediction = by_id[case["id"]]
        result = prediction["result"]
        if isinstance(result, dict) and result.get("mode") != "mock":
            raise ValueError("The synthetic smoke profile only scores explicit mock predictions.")
        try:
            if result is None:
                technical_errors += 1
                raise EvidenceError("Technical extraction failure.")
            validate_schema(result, "ExtractionResult")
            schema_valid += 1
            validate_extraction(result, document)
            extraction_valid += 1
            predicted_entities.extend(prediction_mentions(document, result["items"]))
        except (EvidenceError, ValueError):
            invalid_extractions += 1
            if result is not None:
                try:
                    validate_schema(result, "ExtractionResult")
                    invalid_evidence += 1
                except EvidenceError:
                    invalid_schema += 1
            validation_issues.append({"case_id": case["id"], "operation": "extract", "issue": "Invalid or unavailable extraction; entity metrics withheld."})
        reference_entities.extend({**r, "doc_id": document["doc_id"]} for r in case["entities"])
        stats = prediction["diagnostics"]
        failures += stats["raw_validation_failures"]
        attempts += stats["attempts"]
        repairs += stats["repairs"]
        qa_ids = [a["id"] for a in prediction["qa"]]
        if len(set(qa_ids)) != len(qa_ids) or set(qa_ids) != {q["id"] for q in case["qa"]}:
            raise ValueError("Missing, duplicate or unexpected QA IDs.")
        answers = {a["id"]: a for a in prediction["qa"]}
        for qa in case["qa"]:
            response = answers[qa["id"]]
            answer = response["result"]
            if isinstance(answer, dict) and answer.get("mode") != "mock":
                raise ValueError("The synthetic smoke profile only scores explicit mock answers.")
            valid_answer = False
            if answer is None:
                technical_errors += 1
            else:
                try:
                    validate_schema(answer, "AnswerResult")
                    schema_valid += 1
                    validate_generation(answer, document, answer=True)
                    answer_valid += 1
                    valid_answer = True
                except EvidenceError:
                    try:
                        validate_schema(answer, "AnswerResult")
                        invalid_evidence += 1
                    except EvidenceError:
                        invalid_schema += 1
            if not valid_answer:
                validation_issues.append({"case_id": case["id"], "qa_id": qa["id"], "issue": "Invalid or unavailable answer; not counted as a correct abstention."})
            qa_count += 1
            stats = response["diagnostics"]
            failures += stats["raw_validation_failures"]
            attempts += stats["attempts"]
            repairs += stats["repairs"]
            has_answer = valid_answer and bool(answer["claims"])
            expected_state_correct += int(valid_answer and answer["evidence_state"] == qa["expected_evidence_state"])
            if qa["answerable"]:
                answerable += 1
                answered += int(has_answer)
            else:
                unanswerable += 1
                rejected += int(valid_answer and not has_answer and answer["evidence_state"] == "insufficient")
        cases_trace.append({"case_id": case["id"], "doc_id": document["doc_id"],
                            "text_sha256": document["text_sha256"], "extractor_version": result.get("extractor_version") if isinstance(result, dict) else None,
                            "prompt_version": result.get("prompt_version") if isinstance(result, dict) else None,
                            "mode": result.get("mode") if isinstance(result, dict) else None})
    return {"label": "synthetic/mock structural and scoring demonstration; not real-model quality",
            "schema_sha256": hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(), "contract_status": "draft-provisional",
            "reference_version": references["version"], "prediction_version": predictions["version"],
            "human_reviewed": False, "trace": cases_trace,
            "counts": {"documents": len(expected_ids), "qa": qa_count},
            "generation": {"attempts": attempts, "raw_validation_failures": failures, "repaired_outputs": repairs},
            "record_validation": {"schema_valid": schema_valid, "schema_invalid": invalid_schema,
                                  "evidence_or_relationship_invalid": invalid_evidence, "technical_errors": technical_errors},
            "validation_issues": validation_issues,
            "valid_returned_records": {"extraction": extraction_valid, "answers": answer_valid},
            "en_declarations_on_valid_answers": answer_valid,
            "entities_exact": entity_scores(predicted_entities, reference_entities) if not invalid_extractions else {"unavailable": "At least one extraction is invalid or unavailable; no silent exclusion."},
            "entities_relaxed": entity_scores(predicted_entities, reference_entities, relaxed=True) if not invalid_extractions else {"unavailable": "At least one extraction is invalid or unavailable; no silent exclusion."},
            "answerability": {"answerable": answerable, "answered": answered,
                              "answer_rate": answered / answerable if answerable else None,
                              "unanswerable": unanswerable, "correct_rejections": rejected,
                              "rejection_rate": rejected / unanswerable if unanswerable else None,
                              "expected_state_correct": expected_state_correct, "evaluated": qa_count},
            "unavailable": {"semantic_support": "Requires independent human review or an approved calibrated judge.",
                            "english_output_quality": "The en declaration and English catalog do not prove language compliance.",
                            "unsupported_item_rate": "No independent support judgments are present.",
                            "risk_vs_coverage": "Needs independent correctness labels, not quote existence alone.",
                            "classification_and_retrieval": "Requires C outputs and A corpus/relevance handoffs.",
                            "real_model_performance": "No approved live provider/model or real reference set is available."}}


def main() -> int:
    parser = argparse.ArgumentParser(description="D's first synthetic/offline evaluation slice")
    parser.add_argument("--profile", choices=["smoke", "synthetic-suite"], default="smoke")
    parser.add_argument("--references", type=Path)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--output", type=Path, default=EVAL_ROOT / "reports/local")
    args = parser.parse_args()
    reference_path = args.references or EVAL_ROOT / "fixtures" / (
        "extraction-qa-synthetic-v1.json" if args.profile == "synthetic-suite" else "smoke-references.json")
    references = json.loads(reference_path.read_text(encoding="utf-8"))
    # Generation/writing is limited to public synthetic smoke data in this milestone.
    if references.get("kind") != "synthetic_reference_proposal":
        parser.error("This CLI profile currently accepts synthetic benchmark fixtures only.")
    if args.profile == "synthetic-suite":
        from .suite import evaluate_suite, render_report, validate_references
        validate_references(references)
    predictions = (json.loads(args.predictions.read_text(encoding="utf-8")) if args.predictions else produce(references))
    report = evaluate_suite(references, predictions) if args.profile == "synthetic-suite" else evaluate(references, predictions)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "predictions.json").write_text(json.dumps(predictions, indent=2) + "\n", encoding="utf-8")
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    text = ("# Synthetic/mock evaluation\n\nNot real-model, real-data or clinical performance. Human review is pending.\n\n"
            f"Documents: {report['counts']['documents']}; QA: {report['counts']['qa']}.\n\n"
            f"Exact entity counts: {report['entities_exact']}.\n\n"
            f"Raw failures/repairs: {report['generation']}.\n\n"
            "The fake intentionally misses the cough mention; returned validity is not model accuracy.\n\n"
            + "\n".join(f"- {key}: {value}" for key, value in report["unavailable"].items()) + "\n")
    if args.profile == "synthetic-suite":
        text = render_report(report)
    (args.output / "report.md").write_text(text, encoding="utf-8")
    print(json.dumps({"label": report["label"], "counts": report["counts"],
                      "entities_exact": report["entities_exact"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
