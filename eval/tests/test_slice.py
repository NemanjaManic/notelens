import copy
import hashlib
import json
from pathlib import Path

import pytest

from notelens_eval.annotations import lint_submission, merge, select, templates, SPECIALTIES
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
    assert any(a["reviewer"] == "member-c" for a in result["assignments"])
    for a in result["assignments"]:
        assert a["reviewer"] != a["primary"]
        if a["primary"] == "member-c" or a["reviewer"] == "member-c":
            assert a["portion"] == "development"
    assert all(t["entities"] is None and not t["human_reviewed"] for t in templates(result))


@pytest.mark.parametrize("reviews, warnings", [(10, ["member_c_development_review_unavailable"]), (0, [])])
def test_selection_reports_when_cannot_allocate_c_a_development_review(reviews, warnings):
    manifest = source40()
    for document in manifest["documents"][10:]:
        document["split"] = "test"

    result = select(manifest, count=40, reviews=reviews, seed=1)

    assert result["review_warnings"] == warnings
    assert result["status"] == "proposal_pending_team_review"
    assert sum(a["reviewer"] is not None for a in result["assignments"]) == reviews
    assert all(a["reviewer"] != "member-c" for a in result["assignments"])


def test_selection_rejects_leakage_and_infeasible_inputs():
    manifest = source40()
    manifest["documents"][25]["group_id"] = manifest["documents"][0]["group_id"]
    with pytest.raises(ValueError, match="crosses"):
        select(manifest, count=40, reviews=10, seed=1)
    with pytest.raises(ValueError, match="Insufficient"):
        select({**source40(), "documents": source40()["documents"][:3]}, count=40, reviews=10, seed=1)


@pytest.mark.parametrize("permission", [False, None, "false", "true", 1])
def test_selection_requires_explicit_boolean_permission(permission):
    manifest = source40()
    manifest["documents"][0]["permitted_for_annotation"] = permission

    with pytest.raises(ValueError, match="Source access/permission"):
        select(manifest, count=40, reviews=10, seed=1)


def test_selection_rejects_identical_text_in_distinct_groups_in_the_same_split():
    manifest = source40()
    manifest["documents"][5]["text_sha256"] = manifest["documents"][0]["text_sha256"]

    with pytest.raises(ValueError, match="identical canonical hash belongs to different duplicate groups"):
        select(manifest, count=40, reviews=10, seed=1)


def test_selection_uses_one_representative_for_identical_text_in_the_same_group():
    manifest = source40()
    expected = select(manifest, count=40, reviews=10, seed=1)
    manifest["documents"].append({**manifest["documents"][0], "doc_id": "fixture-copy"})

    assert select(manifest, count=40, reviews=10, seed=1) == expected


@pytest.mark.parametrize("field", ["type", "assertion", "temporality", "subject", "procedure_status"])
@pytest.mark.parametrize("invalid_value", [[], {}])
def test_annotation_lint_reports_malformed_entity_labels(field, invalid_value):
    bundle = json.loads((FIXTURES / "annotation-lint-synthetic-v1.json").read_text(encoding="utf-8"))
    entity = bundle["submission"]["entities"][0]
    if field == "procedure_status":
        entity["type"] = "procedure"
    entity[field] = invalid_value

    report = lint_submission(bundle["assignment"], bundle["document"], bundle["submission"])

    assert report["status"] == "needs_correction"
    assert report["errors"] == [f"entity_1_invalid_{field}"]


def test_synthetic_annotation_workflow_keeps_submissions_independent():
    source = json.loads((FIXTURES / "annotation-source-synthetic.json").read_bytes())
    proposal = select(source, count=20, reviews=10, seed=20261111)
    assignment = next(row for row in proposal["assignments"] if row["reviewer"] == "member-c")
    source_doc = next(row for row in source["documents"] if row["doc_id"] == assignment["doc_id"])
    document = {"doc_id": assignment["doc_id"], "text_sha256": assignment["text_sha256"],
                "text": source_doc["canonical_text"]}
    primary, review = [row for row in templates(proposal) if row["assignment_id"] == assignment["assignment_id"]]
    assert primary["role"] == "primary" and review["role"] == "secondary"
    assert review["annotator"] == "member-c" and review["portion"] == "development"
    assert primary["annotator"] != review["annotator"]
    assert primary["unresolved_questions"] == review["unresolved_questions"] == []
    for submission in (primary, review):
        assert submission["doc_id"] == document["doc_id"] and submission["text_sha256"] == document["text_sha256"]
        submission.update(submission_id=f"synthetic-{submission['role']}", complete_document_review=True, entities=[])
        assert lint_submission(assignment, document, submission)["status"] == "ready_for_independent_review"

    saved = copy.deepcopy([primary, review])
    pending = merge(assignment, document, [primary, review], None, synthetic=True)
    assert pending["review_state"] == "pending_adjudication" and pending["entities"] is None
    decision = {"adjudicator": "synthetic-fixture-only", "rationale": "Exercise the explicit decision path.",
                "selected_submission_id": review["submission_id"]}
    result = merge(assignment, document, [primary, review], decision, synthetic=True)
    assert result["review_state"] == "synthetic_adjudication" and not result["human_reviewed"]
    assert [primary, review] == saved


def test_lint_preserves_unresolved_questions_from_previous_templates():
    bundle = json.loads((FIXTURES / "annotation-lint-synthetic-v1.json").read_bytes())
    bundle["submission"]["questions"] = ["Review the negation scope."]

    report = lint_submission(bundle["assignment"], bundle["document"], bundle["submission"])

    assert report["status"] == "needs_clarification"
    assert report["questions"] == ["unresolved_question_1"]
    assert "Review the negation scope" not in json.dumps(report)


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
