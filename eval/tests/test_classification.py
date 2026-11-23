import hashlib
import json

import pytest

from notelens_eval.annotations import SPECIALTIES
from notelens_eval.classification import classification_metrics, evaluate_classification


def write_json(path, record):
    raw = json.dumps(record).encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def test_fixed_label_metrics_handle_classes_absent_from_a_scoring_slice():
    report = classification_metrics([(SPECIALTIES[0], SPECIALTIES[0])])
    assert report["accuracy"] == 1
    assert report["macro_f1"] == 0.2
    assert report["per_class"][SPECIALTIES[1]]["recall"] == 0


@pytest.fixture
def inputs(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    predictions_path = tmp_path / "predictions.json"
    checksum_path = tmp_path / "predictions.sha256"
    manifest = {
        "kind": "permitted_benchmark", "source_version": "c002-development",
        "canonicalization_version": "nfc-lf-v1", "split_manifest_version": "split-v1",
        "split_manifest_sha256": "a" * 64,
        "documents": [{"doc_id": str(index), "group_id": str(index), "specialty": label,
                       "split": "validation", "permitted_for_annotation": True,
                       "text_sha256": hashlib.sha256(label.encode()).hexdigest()}
                      for index, label in enumerate(SPECIALTIES)],
    }
    manifest_hash = write_json(manifest_path, manifest)
    versions = {"model_version": "c003-model", "preparation_version": "nfc-lf-v1", "split_version": "split-v1"}
    rows = []
    for index, truth in enumerate(SPECIALTIES):
        predicted = SPECIALTIES[0] if index == 1 else truth
        rows.append({**versions, "doc_id": str(index), "true_specialty": truth, "predicted_specialty": predicted,
                     "status": "forced_choice", "scores": {label: int(label == predicted) for label in SPECIALTIES}})
    export = {
        **versions, "export_version": "c003-d006-validation-v1", "decision_policy": "forced_choice",
        "score_type": "logistic_regression_probability", "handoff_version": "c002-development",
        "handoff_checksum": manifest_hash, "split_checksum": "a" * 64, "documents": rows,
    }

    def save():
        digest = write_json(predictions_path, export)
        checksum_path.write_text(f"{digest}  predictions.json\n", encoding="ascii")

    save()
    return (predictions_path, checksum_path, manifest_path), export, save


def test_replay_scores_manifest_labels_and_keeps_confusion_orientation(inputs):
    paths, _, _ = inputs
    report = evaluate_classification(*paths)
    first, second = SPECIALTIES[:2]
    assert report["overall"]["accuracy"] == 0.8
    assert report["overall"]["macro_f1"] == pytest.approx((3 + 2 / 3) / 5)
    assert report["overall"]["confusion_matrix"][second][first] == 1
    assert report["overall"]["per_class"][second]["recall"] == 0
    assert report["validation_majority_baseline"]["accuracy"] == 0.2
    assert report["split_integrity"]["validation_groups"] == 5
    assert "doc_id" not in json.dumps(report)


def test_replay_rejects_changed_input_bytes(inputs):
    paths, _, _ = inputs
    paths[0].write_bytes(paths[0].read_bytes() + b"\n")
    with pytest.raises(ValueError, match="sidecar"):
        evaluate_classification(*paths)


@pytest.mark.parametrize("issue, message", [
    ("missing", "entire validation manifest"),
    ("duplicate", "unique and present"),
    ("truth", "labels disagree"),
    ("scores", "normalized probabilities"),
    ("split", "preparation or split provenance"),
])
def test_replay_rejects_inconsistent_exports_even_with_updated_checksum(inputs, issue, message):
    paths, export, save = inputs
    rows = export["documents"]
    if issue == "missing":
        rows.pop()
    elif issue == "duplicate":
        rows.append(rows[0])
    elif issue == "truth":
        rows[0]["true_specialty"] = SPECIALTIES[1]
    elif issue == "scores":
        rows[0]["scores"][SPECIALTIES[0]] = 0.9
    else:
        export["split_checksum"] = "b" * 64
    save()
    with pytest.raises(ValueError, match=message):
        evaluate_classification(*paths)
