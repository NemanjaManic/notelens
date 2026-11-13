"""Synthetic validator exercises, never human review evidence."""
import copy
import json
from pathlib import Path
import pytest
from notelens_eval.answer_review import inspect, summarize


def blank():
    return json.loads((Path(__file__).parents[1] / "fixtures/answer-review-template-v1.json").read_text())


def completed():
    record = blank()
    record.update(review_id="synthetic-test", reviewer_alias="test-only", case_id="test", doc_id="test",
                  text_sha256="a" * 64, response_id="test", response_sha256="b" * 64, mode="mock", extractor_or_answer_version="test",
                  prompt_version="test", human_reviewed=True, answerable_from_document="yes",
                  response_action="answer", critical_error=False, needs_adjudication=False,
                  rationale="Synthetic unit test only.", completed_at="2026-11-13T12:00:00Z")
    record["dimensions"] = dict.fromkeys(record["dimensions"], 2)
    return record


def test_states_and_no_mutation():
    empty, partial, human, failure = blank(), blank(), completed(), blank()
    partial["review_id"] = "unfinished"
    human["dimensions"]["source_support"] = "U"
    failure["response_action"] = "operational_error"
    records = [empty, partial, human, failure]
    original = copy.deepcopy(records)
    result = summarize(records)
    assert records == original
    assert result["counts"] == dict(blank=1, incomplete=1, completed_declared_human_review=1, operational_error=1, invalid=0)
    assert result["dimensions"]["source_support"] == dict(rated=0, unable_to_judge=1, mean=None, score_counts={"0": 0, "1": 0, "2": 0})
    assert result["human_authorship_verified"] is False


@pytest.mark.parametrize("field,value", [("text_sha256", "bad"), ("completed_at", "2026-11-13"), ("human_reviewed", "true"), ("response_action", "made-up")])
def test_bad_metadata(field, value):
    record = completed()
    record[field] = value
    with pytest.raises(ValueError):
        inspect(record)


def test_duplicate_and_boolean_score_rejected():
    record = completed()
    assert summarize([record, record])["counts"]["invalid"] == 1
    record["dimensions"]["source_support"] = True
    with pytest.raises(ValueError):
        inspect(record)


def test_operational_error_not_quality_and_missing_declaration():
    record = completed()
    record["human_reviewed"] = False
    assert inspect(record) == "incomplete"
    record["response_action"] = "operational_error"
    with pytest.raises(ValueError):
        inspect(record)
