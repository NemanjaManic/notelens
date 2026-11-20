"""Selective QA metrics from independent correctness labels and observed outcomes."""

import math

from .retrieval_metrics import indexed_cases


def ratio(count: int, total: int) -> float | None:
    return count / total if total else None


def evaluate_answer_risk(references: dict, predictions: dict) -> dict:
    expected = indexed_cases(references["cases"])
    actual = indexed_cases(predictions["cases"])
    if expected.keys() != actual.keys():
        raise ValueError("Answer references and predictions must have the same case IDs.")
    answerable = answered_on_answerable = unanswerable = correct_rejections = 0
    technical_errors = abstentions = 0
    answers = []
    for case_id, reference in expected.items():
        can_answer = reference["answerable"]
        if type(can_answer) is not bool:
            raise ValueError("Every case requires a Boolean answerability judgment.")
        answerable += int(can_answer)
        unanswerable += int(not can_answer)
        prediction = actual[case_id]
        outcome = prediction["outcome"]
        correct = reference.get("answer_correct")
        confidence = prediction.get("confidence")
        if outcome == "answered":
            if type(correct) is not bool:
                raise ValueError("Every emitted answer requires an independent correctness judgment.")
            if confidence is not None and (
                type(confidence) not in (float, int) or not 0 <= confidence <= 1 or not math.isfinite(confidence)
            ):
                raise ValueError("Confidence must be within zero and one.")
            answers.append((confidence, correct))
            answered_on_answerable += int(can_answer)
        elif outcome in ("abstained", "technical_error"):
            if correct is not None or confidence is not None:
                raise ValueError("Only emitted answers can have correctness or confidence values.")
            abstentions += int(outcome == "abstained")
            technical_errors += int(outcome == "technical_error")
            correct_rejections += int(not can_answer and outcome == "abstained")
        else:
            raise ValueError("Unknown answer outcome.")

    total = len(expected)
    errors = sum(not correct for _, correct in answers)
    curve = []
    if answers and all(confidence is not None for confidence, _ in answers):
        by_confidence = {}
        for confidence, correct in answers:
            count, mistakes = by_confidence.get(confidence, (0, 0))
            by_confidence[confidence] = count + 1, mistakes + int(not correct)
        accepted = mistakes = 0
        for threshold, (count, errors_at_threshold) in sorted(by_confidence.items(), reverse=True):
            accepted += count
            mistakes += errors_at_threshold
            curve.append({
                "minimum_confidence": threshold, "accepted": accepted, "incorrect": mistakes,
                "coverage": accepted / total, "risk": mistakes / accepted,
            })

    return {
        "label": "offline answer risk and coverage",
        "reference_version": references["version"], "prediction_version": predictions["version"],
        "overall": {
            "cases": total, "answered": len(answers), "incorrect_answers": errors,
            "abstentions": abstentions, "technical_errors": technical_errors,
            "coverage": len(answers) / total, "risk": ratio(errors, len(answers)),
            "answerable": answerable, "answered_on_answerable": answered_on_answerable,
            "answer_rate_on_answerable": ratio(answered_on_answerable, answerable),
            "unanswerable": unanswerable, "correct_rejections": correct_rejections,
            "correct_rejection_rate": ratio(correct_rejections, unanswerable),
        },
        "confidence_curve": curve,
    }
