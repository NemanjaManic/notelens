"""Answer coverage and independently judged error risk regressions."""

import pytest

from notelens_eval.answer_risk import evaluate_answer_risk


def evaluate(rows):
    references, predictions = [], []
    for index, (answerable, outcome, correct, confidence) in enumerate(rows):
        references.append({"id": str(index), "answerable": answerable, "answer_correct": correct})
        predictions.append({"id": str(index), "outcome": outcome, "confidence": confidence})
    return evaluate_answer_risk({"version": "review", "cases": references},
                                {"version": "run", "cases": predictions})


def test_risk_curve_preserves_ties_and_excludes_errors_from_rejections():
    report = evaluate([
        (True, "answered", True, 0.9),
        (True, "answered", False, 0.6),
        (False, "answered", False, 0.6),
        (False, "technical_error", None, None),
        (False, "abstained", None, None),
        (True, "abstained", None, None),
    ])
    totals = report["overall"]
    assert totals["risk"] == 2 / 3
    assert totals["coverage"] == 0.5
    assert totals["answer_rate_on_answerable"] == 2 / 3
    assert totals["correct_rejection_rate"] == 1 / 3
    assert totals["technical_errors"] == 1
    assert [(point["accepted"], point["incorrect"]) for point in report["confidence_curve"]] == [(1, 0), (3, 2)]


def test_always_abstaining_has_no_measured_risk_or_answer_coverage():
    report = evaluate([(True, "abstained", None, None), (False, "abstained", None, None)])
    assert report["overall"]["risk"] is None
    assert report["overall"]["coverage"] == 0
    assert report["overall"]["answer_rate_on_answerable"] == 0
    assert report["overall"]["correct_rejection_rate"] == 1
    assert report["confidence_curve"] == []


def test_unreviewed_answers_are_rejected_and_missing_scores_suppress_curve():
    with pytest.raises(ValueError, match="correctness"):
        evaluate([(True, "answered", None, 1)])
    report = evaluate([(True, "answered", True, 1), (True, "answered", True, None)])
    assert report["overall"]["risk"] == 0
    assert report["confidence_curve"] == []
