import copy
import hashlib
import json
from pathlib import Path

import pytest

from notelens_eval.annotations import merge, select, templates, SPECIALTIES
from notelens_eval.metrics import entity_scores, match
from notelens_eval.run import produce, evaluate

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_predictions_are_generated_then_scored_with_a_missed_entity():
    references = json.loads((FIXTURES / "smoke-references.json").read_text())
    predictions = produce(references)
    assert predictions["cases"][0]["result"]["items"] != references["cases"][0]["entities"]
    report = evaluate(references, predictions)
    assert report["entities_exact"]["tp"] == 4 and report["entities_exact"]["fn"] == 1
    assert report["answerability"]["correct_rejections"] == 1
    assert report["answerability"]["expected_state_correct"] == 3
    assert report["unavailable"]["semantic_support"]


def test_invalid_predictions_are_reported_not_counted_as_abstentions():
    references = json.loads((FIXTURES / "smoke-references.json").read_text())
    predictions = produce(references)
    predictions["cases"][0]["result"]["items"][0]["evidence"][0]["quote"] = "wrong"
    predictions["cases"][0]["qa"][1]["result"] = None
    report = evaluate(references, predictions)
    assert report["record_validation"]["evidence_or_relationship_invalid"] == 1
    assert report["record_validation"]["technical_errors"] == 1
    assert "unavailable" in report["entities_exact"]
    assert report["answerability"]["correct_rejections"] == 0


def entity(start, end, **fields):
    return {"doc_id": "d", "type": "symptom", "mention": {"start": start, "end": end},
            "assertion": "negated", "temporality": "unknown", "subject": "patient", **fields}


def test_one_to_one_matching_and_zero_denominators():
    reference = [entity(1, 5)]
    score = entity_scores([entity(1, 5), entity(1, 5)], reference)
    assert score["tp"] == 1 and score["fp"] == 1
    assert entity_scores([], [])["precision"] is None
    assert entity_scores([], [])["f1"] is None
    assert entity_scores([entity(1, 4)], reference)["tp"] == 0
    assert entity_scores([entity(1, 4)], reference, relaxed=True)["tp"] == 1


def test_relaxed_matching_is_maximum_cardinality_not_greedy():
    # Broad prediction can match either reference; narrow one can only match first.
    pairs = match([entity(0, 9), entity(0, 3)], [entity(0, 3), entity(5, 9)], relaxed=True)
    assert sorted(pairs) == [(0, 1), (1, 0)]


def test_matching_preserves_attribute_errors():
    result = entity_scores([entity(0, 3, subject="family")], [entity(0, 3)])
    assert result["subject"]["correct"] == 0 and result["assertion"]["correct"] == 1


def source40():
    docs = []
    for i in range(40):
        docs.append({"doc_id": f"fixture-{i:02}", "group_id": f"group-{i:02}",
                     "specialty": SPECIALTIES[i % 5], "split": "validation" if i < 20 else "test",
                     "permitted_for_annotation": True, "text_sha256": hashlib.sha256(f"fixture-{i}".encode()).hexdigest()})
    return {"kind": "synthetic", "source_version": "test-only", "documents": docs}


def test_40_assignment_algorithm_without_real_assignments():
    manifest = source40()
    result = select(manifest, count=40, reviews=10, seed=20261111)
    assert result == select(manifest, count=40, reviews=10, seed=20261111)
    assert all(sum(a["primary"] == member for a in result["assignments"]) == 10
               for member in ["member-a", "member-b", "member-c", "member-d"])
    assert sorted(result["specialty_counts"].values()) == [8] * 5
    assert sum(a["reviewer"] is not None for a in result["assignments"]) == 10
    for a in result["assignments"]:
        assert a["reviewer"] != a["primary"]
        if a["primary"] == "member-c" or a["reviewer"] == "member-c":
            assert a["portion"] == "development"
    assert all(t["entities"] is None and not t["human_reviewed"] for t in templates(result))


def test_selection_rejects_leakage_and_infeasible_inputs():
    manifest = source40()
    manifest["documents"][25]["group_id"] = manifest["documents"][0]["group_id"]
    with pytest.raises(ValueError, match="crosses"):
        select(manifest, count=40, reviews=10, seed=1)
    with pytest.raises(ValueError, match="Insufficient"):
        select({**source40(), "documents": source40()["documents"][:3]}, count=40, reviews=10, seed=1)


def test_merge_preserves_inputs_and_does_not_generate_human_review():
    text = "Synthetic sentence."
    document = {"doc_id": "test-doc", "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
    assignment = {"assignment_id": "a", "doc_id": document["doc_id"], "text_sha256": document["text_sha256"],
                  "primary": "member-a", "reviewer": "member-d"}
    submissions = [{"assignment_id": "a", "submission_id": "primary-fixture", "role": "primary", "annotator": "member-a",
                    "doc_id": document["doc_id"], "text_sha256": document["text_sha256"],
                    "complete_document_review": True, "entities": [], "human_reviewed": False}]
    submissions.append({**submissions[0], "submission_id": "review-fixture", "role": "secondary", "annotator": "member-d"})
    saved = copy.deepcopy(submissions)
    pending = merge(assignment, document, submissions, None, synthetic=True)
    assert pending["entities"] is None and pending["review_state"] == "pending_adjudication"
    decision = {"adjudicator": "synthetic-fixture-only", "rationale": "Test-only explicit decision.",
                "selected_submission_id": "primary-fixture"}
    resolved = merge(assignment, document, submissions, decision, synthetic=True)
    assert resolved["review_state"] == "synthetic_adjudication" and not resolved["human_reviewed"]
    assert saved == submissions
    with pytest.raises(ValueError, match="Human review"):
        merge(assignment, document, submissions, decision, synthetic=False)
