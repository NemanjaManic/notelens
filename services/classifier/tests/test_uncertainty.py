from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from notelens_classifier.inference import (
    LABELS, AmbiguityPolicy, SectionPrediction, WordEvidenceIndex, accepted_category, independent_sections,
    lexical_evidence,
)


@pytest.mark.parametrize(("scores", "features", "threshold", "expected"), [
    ((0.6, 0.1, 0.1, 0.1, 0.1), True, 0.6, LABELS[0]),
    ((0.59, 0.14, 0.12, 0.1, 0.05), True, 0.6, None),
    ((0.45, 0.45, 0.04, 0.03, 0.03), True, 0.4, None),
    ((0.9, 0.05, 0.02, 0.02, 0.01), False, 0.6, None),
])
def test_uncertainty_threshold_ties_and_unseen_vocabulary(scores, features, threshold, expected):
    assert accepted_category(scores, features, threshold) == expected


def test_minimum_margin_abstains_when_the_top_two_scores_are_close():
    assert accepted_category((0.5, 0.4, 0.04, 0.04, 0.02), True, 0.4, 0.15) is None
    assert accepted_category((0.5, 0.25, 0.125, 0.0625, 0.0625), True, 0.4, 0.25) == LABELS[0]


def test_independent_sections_keep_clauses_and_ignore_explicitly_negated_parts():
    assert independent_sections("Colonoscopy found a polyp, one about an ankle fracture.") == [
        "Colonoscopy found a polyp", "one about an ankle fracture."
    ]
    assert independent_sections("The EEG captured a seizure. No fracture and no urinary retention.") == []
    assert independent_sections("A fracture was documented; the patient denies hematuria.") == []


def test_ambiguity_policy_requires_independent_specialty_evidence():
    policy = AmbiguityPolicy(
        minimum_word_evidence=0.3, segment_threshold=0.4, segment_margin=0.1, competing_score_ratio=0.5,
        minimum_section_share=0.2,
    )
    cardiac = SectionPrediction((0.6, 0.1, 0.1, 0.1, 0.1), 0.9, 10)
    urinary = SectionPrediction((0.1, 0.1, 0.1, 0.1, 0.6), 0.8, 8)
    weak_urinary = SectionPrediction(urinary.scores, 0.1, 8)
    tied = SectionPrediction((0.4, 0.0, 0.1, 0.1, 0.4), 0.8, 8)
    competing = (0.5, 0.05, 0.05, 0.05, 0.35)
    assert policy.abstention_reason(0.2, competing, [], 20) == "limited_word_evidence"
    assert policy.abstention_reason(0.9, competing, [cardiac, urinary], 20) == "conflicting_sections"
    assert policy.abstention_reason(0.9, competing, [cardiac, urinary], 48) is None
    assert policy.abstention_reason(0.9, cardiac.scores, [cardiac, urinary], 20) is None
    assert policy.abstention_reason(0.9, competing, [cardiac, cardiac, weak_urinary, tied], 38) is None

    document_only = replace(policy, document_evidence_kind="two_words", minimum_document_evidence=0.7)
    assert document_only.abstention_reason(0.6, competing, [cardiac, urinary], 20) == "limited_word_evidence"
    assert document_only.abstention_reason(0.9, competing, [cardiac, urinary], 20) == "conflicting_sections"


def test_lexical_evidence_counts_distinct_features_and_phrase_support():
    label = LABELS[0]
    index = WordEvidenceIndex(words={label: {3: 0.4, 6: 0.3}}, phrases={label: {8: 0.55}})
    evidence = lexical_evidence(SimpleNamespace(indices=[3, 3, 6, 8, 12]), label, index)
    assert evidence.single_word == 0.4
    assert evidence.two_words == pytest.approx(0.7)
    assert evidence.word_or_phrase == pytest.approx(0.95)


def test_frozen_policy_preserves_abstentions_in_confusion_counts(monkeypatch):
    pytest.importorskip("sklearn", reason="Optional training dependency group is not installed")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3]))
    from notelens_classifier.inference import LexicalEvidence
    from notelens_classifier.training.frozen_uncertainty import Decision, apply_score_gate, validation_metrics
    from notelens_classifier.training.select_ambiguity_policy import Observation

    observations = [
        Observation(LABELS[0], LABELS[0], (0.8, 0.05, 0.05, 0.05, 0.05), LexicalEvidence(), [], 1),
        Observation(LABELS[1], None, (0.1, 0.7, 0.1, 0.05, 0.05), LexicalEvidence(), [], 0),
        Observation(LABELS[2], LABELS[2], (0.05, 0.42, 0.45, 0.05, 0.03), LexicalEvidence(), [], 1),
    ]
    assert [row.reference for row in apply_score_gate(observations, 0.4, 0.1)] == [LABELS[0], None, None]
    metrics = validation_metrics(observations, ["first", "second", "third"], Decision(0.4, 0.1))
    assert metrics["accuracy"] == pytest.approx(1 / 3)
    assert metrics["confusion_columns"][-1] == "uncertain"
    assert metrics["confusion_matrix"][0] == [1, 0, 0, 0, 0, 0]
    assert metrics["confusion_matrix"][1] == metrics["confusion_matrix"][2] == [0, 0, 0, 0, 0, 1]
