"""Protocol tests use synthetic declarations, never actual independent review evidence."""
import pytest

from notelens_eval.answer_review import DIMENSIONS
from notelens_eval.semantic_risk import PROTOCOL, digest, score_reviewed_packet
from notelens_extraction.demo import request


def inputs():
    packet = {"version": "d011-semantic-review-packet-v1", "cases": [
        {"id": "synthetic-case", "request": request("Does the patient report cough?"),
         "response": {"claims": [{"text": "The patient reports cough."}], "evidence_state": "sufficient",
                      "mode": "live", "answer_version": "synthetic-test", "prompt_version": "synthetic-test"}}]}
    record = {"kind": "synthetic_protocol_test", "rubric_version": "d-answer-review-rubric-v1",
              "review_form_version": "d-answer-review-form-v2", "review_id": "synthetic-review",
              "reviewer_alias": "synthetic independent reviewer", "case_id": "synthetic-case",
              "doc_id": packet["cases"][0]["request"]["document"]["doc_id"],
              "text_sha256": packet["cases"][0]["request"]["document"]["text_sha256"],
              "response_id": "synthetic-case", "response_sha256": digest(packet["cases"][0]["response"]),
              "mode": "live", "extractor_or_answer_version": "synthetic-test", "prompt_version": "synthetic-test",
              "reviewed_output": "document_answer", "prior_exposure": False, "self_authored_output": False,
              "preparation_involvement": False, "ai_assistance_disclosure": "Synthetic test only.",
              "independent_review": True, "human_reviewed": True, "exposure_note": "Synthetic test only.",
              "answerable_from_document": "yes", "response_action": "answer", "critical_error": False,
              "needs_adjudication": False, "rationale": "Synthetic test only.", "completed_at": "2026-11-23T12:00:00Z",
              "dimensions": dict.fromkeys(DIMENSIONS, 2), "issue_codes": [], "claim_source_notes": [], "component_outcomes": []}
    reviews = {"packet_sha256": digest(packet), "reviews": [record]}
    decision = {"version": PROTOCOL, "approved": True, "approved_by": "synthetic test approver", "decision_record": "test-only"}
    return packet, reviews, decision


def test_review_risk_and_uncertainty_do_not_assert_clinical_safety():
    p, r, d = inputs()
    report = score_reviewed_packet(p, r, d)
    assert report["overall"]["risk"] == 0
    assert report["zero_error_one_sided_95_upper"] > 0.9
    assert report["human_authorship_independently_verified"] is False


@pytest.mark.parametrize("field,value", [("human_reviewed", False), ("independent_review", False),
    ("preparation_involvement", True), ("ai_assistance_disclosure", "")])
def test_agent_or_ineligible_feedback_cannot_fill_independent_risk(field, value):
    p, r, d = inputs()
    r["reviews"][0][field] = value
    assert score_reviewed_packet(p, r, d)["risk"] is None


def test_undecided_protocol_and_unable_to_judge_are_not_passes():
    p, r, d = inputs()
    d["approved"] = False
    assert score_reviewed_packet(p, r, d)["status"] == "protocol_approval_pending"
    r["reviews"][0]["dimensions"]["source_support"] = "U"
    r["reviews"][0]["claim_source_notes"] = [{"dimension": "source_support", "reason": "Synthetic U", "minimum_correction": "Review source"}]
    assert score_reviewed_packet(p, r, d)["risk"] is None


def test_source_response_or_outcome_relabeling_is_rejected():
    for field, value in [("response_sha256", "0" * 64), ("text_sha256", "0" * 64), ("response_action", "abstain"),
                         ("mode", "mock"), ("prompt_version", "wrong"), ("response_id", "another-case")]:
        p, r, d = inputs()
        r["reviews"][0][field] = value
        with pytest.raises(ValueError):
            score_reviewed_packet(p, r, d)


def test_real_review_failure_is_counted_as_error_with_reason():
    p, r, d = inputs()
    r["reviews"][0]["dimensions"]["required_facts"] = 1
    r["reviews"][0]["claim_source_notes"] = [{"dimension": "required_facts", "reason": "Synthetic missing fact", "minimum_correction": "Add it"}]
    assert score_reviewed_packet(p, r, d)["overall"]["risk"] == 1


def test_technical_failure_keeps_source_answerability_and_is_not_a_rejection():
    p, r, d = inputs()
    p["cases"][0]["response"] = None
    r["packet_sha256"] = digest(p)
    row = r["reviews"][0]
    row.update(response_sha256=digest(None), response_action="operational_error", human_reviewed=False,
               independent_review=False, dimensions=dict.fromkeys(DIMENSIONS, None))
    report = score_reviewed_packet(p, r, d)
    assert report["overall"]["technical_errors"] == 1
    assert report["overall"]["answerable"] == 1
    assert report["overall"]["correct_rejections"] == 0 and report["overall"]["risk"] is None


def test_empty_packet_cannot_establish_risk():
    p, r, d = inputs()
    p["cases"] = []
    r.update(packet_sha256=digest(p), reviews=[])
    with pytest.raises(ValueError):
        score_reviewed_packet(p, r, d)


def test_cli_preserves_pending_reviews_without_publishing_a_risk(tmp_path):
    import json
    from notelens_eval.semantic_risk import main
    p, r, d = inputs()
    r["reviews"][0]["human_reviewed"] = False
    for name, value in (("packet", p), ("reviews", r), ("decision", d)):
        (tmp_path / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
    args = [part for name in ("packet", "reviews", "decision", "output")
            for part in (f"--{name}", str(tmp_path / f"{name}.json"))]
    assert main(args) == 2
    result = json.loads((tmp_path / "output.json").read_bytes())
    assert result["status"] == "review_pending" and result["risk"] is None
