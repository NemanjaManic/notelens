import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from notelens_eval.run import produce
from notelens_eval.suite import evaluate_suite, validate_references

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/extraction-qa-synthetic-v1.json"


def references():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_has_balanced_unique_documents_and_traceable_references():
    refs = references()
    validate_references(refs)
    assert len(refs["cases"]) == 24
    assert sum(len(c["qa"]) for c in refs["cases"]) == 48
    assert len({c["group"] for c in refs["cases"]}) == 6
    assert all(sum(c["group"] == group for c in refs["cases"]) == 4
               for group in {c["group"] for c in refs["cases"]})


@pytest.mark.parametrize("corruption", ["hash", "span", "duplicate", "qa", "support", "gap"])
def test_bad_references_fail_before_generation(corruption):
    refs = references()
    case = refs["cases"][0]
    if corruption == "hash":
        case["request"]["document"]["text_sha256"] = "0" * 64
    elif corruption == "span":
        case["entities"][0]["mention"]["end"] += 1
    elif corruption == "duplicate":
        refs["cases"][1]["id"] = case["id"]
    elif corruption == "qa":
        case["qa"][1]["id"] = case["qa"][0]["id"]
    elif corruption == "gap":
        case["qa"][1].pop("expected_gaps")
    else:
        case["qa"][0]["expected_support"][0] = "Not in the document."
    with pytest.raises(ValueError):
        validate_references(refs)


def test_suite_reports_groups_misses_and_qa_failures_without_rewriting_references():
    refs = references()
    saved = copy.deepcopy(refs)
    predictions = produce(refs)
    report = evaluate_suite(refs, predictions)
    assert refs == saved
    assert report["counts"] == {"documents": 24, "qa": 48}
    assert sum(g["counts"]["documents"] for g in report["groups"].values()) == 24
    assert report["entities_exact"]["fn"] > 0
    assert any(f["category"] == "missing_entity" for f in report["failures"])
    assert any(f["category"] == "qa_state" for f in report["failures"])
    assert all(f["proposal"] and f["likely_cause"] for f in report["failures"])
    assert report["reference_sha256"]


def test_technical_failure_is_not_a_correct_rejection_and_metrics_are_withheld():
    refs = references()
    predictions = produce(refs)
    predictions["cases"][0]["result"] = None
    predictions["cases"][0]["qa"][1]["result"] = None
    report = evaluate_suite(refs, predictions)
    assert "unavailable" in report["entities_exact"]
    assert report["record_validation"]["technical_errors"] == 2
    assert any(f["category"] == "technical_error" for f in report["failures"])


def test_correct_state_with_wrong_supported_topic_is_flagged():
    refs = references()
    case = next(c for c in refs["cases"] if c["id"] == "complex-04")
    subset = {**refs, "cases": [case]}
    predictions = produce(subset)
    # A valid literal asthma response has the right state but does not answer chest pain.
    from notelens_extraction.service import run
    response, _ = run({**case["request"], "question": "What diagnoses or symptoms are mentioned?"}, "answer")
    response["claims"] = response["claims"][-1:]
    response["sources"] = response["sources"][-1:]
    response["text"] = response["claims"][0]["text"]
    predictions["cases"][0]["qa"][0]["result"] = response
    report = evaluate_suite(subset, predictions)
    assert any(f["category"] == "required_fact_missing" for f in report["failures"])


def test_gap_disclosure_is_checked_separately_from_correct_partial_state():
    refs = references()
    case = next(c for c in refs["cases"] if c["id"] == "limited-04")
    subset = {**refs, "cases": [case]}
    predictions = produce(subset)
    answer = predictions["cases"][0]["qa"][0]["result"]
    assert answer["evidence_state"] == "partial"
    answer["warnings"] = ["Deterministic synthetic response."]
    report = evaluate_suite(subset, predictions)
    assert any(f["category"] == "expected_gap_not_disclosed" for f in report["failures"])


def test_extra_source_claim_is_flagged_even_when_required_quote_is_present():
    refs = references()
    case = next(c for c in refs["cases"] if c["id"] == "complex-04")
    subset = {**refs, "cases": [case]}
    predictions = produce(subset)
    from notelens_extraction.service import run
    broad, _ = run({**case["request"], "question": "What diagnoses or symptoms are mentioned?"}, "answer")
    predictions["cases"][0]["qa"][0]["result"] = broad
    report = evaluate_suite(subset, predictions)
    assert any(f["category"] == "unexpected_answer_fact" for f in report["failures"])


def test_fixture_facts_and_gaps_are_evaluator_metadata_only():
    refs = references()
    case = refs["cases"][0]
    qa = case["qa"][0]
    assert len(qa["required_facts"]) == 1 and qa["expected_gaps"] == []
    assert refs["cases"][0]["qa"][1]["expected_gaps"] == ["age"]
    predictions = produce({**refs, "cases": [case]})
    assert "required_facts" not in json.dumps(predictions)
    assert "expected_gaps" not in json.dumps(predictions)


def test_cli_generates_and_rescores_the_same_results(tmp_path):
    first, second = tmp_path / "generated", tmp_path / "rescored"
    command = [sys.executable, "-m", "notelens_eval.run", "--profile", "synthetic-suite"]
    result = subprocess.run(command + ["--output", str(first)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(command + ["--predictions", str(first / "predictions.json"),
                                       "--output", str(second)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert (first / "results.json").read_bytes() == (second / "results.json").read_bytes()
    assert "Failure analysis" in (first / "report.md").read_text()


def test_provider_only_receives_requests_not_reference_labels(monkeypatch):
    import notelens_eval.run as runner
    original = runner.generate
    seen = []

    def capture(request, operation, **kwargs):
        assert set(request) <= {"schema_version", "document", "question"}
        assert "entities" not in request and "expected_support" not in request
        seen.append(operation)
        return original(request, operation, **kwargs)

    monkeypatch.setattr(runner, "generate", capture)
    produce(references())
    assert seen.count("extract") == 24 and seen.count("answer") == 48
