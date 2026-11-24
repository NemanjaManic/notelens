"""Development comparison uses the same train-fitted vocabulary and validation cohort."""

import json

import pytest

pytest.importorskip("xgboost", reason="Optional comparison dependency group is not installed")

from notelens_classifier.inference import LABELS
from notelens_classifier.training import development


def test_comparison_does_not_fit_validation_vocabulary():
    names = ("cardiac", "ortho", "gastric", "neuro", "urologic")
    train = [(str(i), f"train-{i}", label, term * 2) for i, (label, term) in enumerate(zip(LABELS, names))]
    validation = [
        (str(i + 5), f"validation-{i}", label, term * 2 + " validationmarker")
        for i, (label, term) in enumerate(zip(LABELS, names))
    ]
    baseline_config = json.loads(development.baseline.CONFIG.read_bytes())
    comparison_config = json.loads(development.CONFIG.read_bytes())
    comparison_config["xgboost"]["n_estimators"] = 2
    model, metrics = development.compare(
        {"train": train, "validation": validation}, baseline_config, comparison_config
    )
    vocabulary = model.named_steps["tfidf"].vocabulary_
    assert set(vocabulary) == {term * 2 for term in names}
    assert metrics["validation_group_support"] == dict.fromkeys(LABELS, 1)
    for candidate in ("majority", "logistic_regression", "xgboost"):
        matrix = metrics["models"][candidate]["confusion_matrix"]
        assert [sum(row) for row in matrix] == [1] * len(LABELS)


def test_development_runner_refuses_non_draft_split_before_opening_source(monkeypatch, tmp_path):
    split = tmp_path / "split.json"
    split.write_text('{"status": "frozen"}', encoding="utf-8")
    monkeypatch.setattr(development.baseline, "DRAFT", split)
    monkeypatch.setattr(development.baseline, "SOURCE", tmp_path / "unavailable-holdout.csv")
    with pytest.raises(ValueError, match="requires the provisional split"):
        development.run(tmp_path)


def test_frozen_comparison_rejects_wrong_split_pin_before_opening_source(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(development.baseline.ROOT))
    monkeypatch.setattr(development.baseline, "SOURCE", tmp_path / "unavailable-source.csv")
    (tmp_path / "manifest.json").write_bytes(b'{"status": "frozen local split membership"}')
    output = tmp_path / "comparison"
    with pytest.raises(ValueError, match="pinned input differs"):
        development.run_frozen(output, tmp_path, "0" * 64, tmp_path)
    assert not output.exists()
