"""Exercise the final-run guards with a synthetic five-label test package only."""

from hashlib import sha256
import json

import pytest

pytest.importorskip("sklearn", reason="Optional training dependency group is not installed")

from conftest import prepared
from notelens_classifier.inference import LABELS, MANIFEST_FILE
from notelens_classifier.training.final_measurement import measure


@pytest.fixture
def frozen_rehearsal(model_bundle):
    root, _ = model_bundle
    manifest_path = root / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["stage"] = "frozen"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    holdout = root / "synthetic-locked-test.json"
    records = [
        {"category": label, "group_id": f"holdout-group-{i}",
         "document": prepared(word, f"holdout-{i}")}
        for i, (label, word) in enumerate(zip(LABELS, ("cardiac", "orthopedic", "gastric", "neuro", "urologic")))
    ]
    holdout.write_text(json.dumps({"stage": "locked-test", "rows": records}), encoding="utf-8")
    runs = root / "runs"
    runs.mkdir()
    approval = {
        "stage": "approved-final", "review_reference": "Synthetic rehearsal only",
        "version": "synthetic-v1", "reason": "Exercise the code path with invented data",
        "majority_label": LABELS[0], "development_group_ids": ["development-group"],
        "development_document_ids": ["development-document"],
        "model_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
        "locked_test_sha256": sha256(holdout.read_bytes()).hexdigest(),
    }
    return root, holdout, runs, approval


def freeze_file(root, approval):
    path = root / "freeze.json"
    data = json.dumps(approval).encode()
    path.write_bytes(data)
    return path, sha256(data).hexdigest()


def test_synthetic_measurement_reserves_repeat_attempt_before_reading_holdout(frozen_rehearsal):
    root, test, runs, approval = frozen_rehearsal
    freeze, digest = freeze_file(root, approval)
    report = measure(freeze, digest, root, test, runs)
    assert report["forced_choice"]["macro_f1"] == 1
    assert report["majority"]["accuracy"] == 0.2
    assert report["selective"]["coverage"] == 1
    assert report["groups"] == len(LABELS)
    version_digest = sha256(approval["version"].encode()).hexdigest()
    assert json.loads((runs / version_digest / "metrics.json").read_bytes()) == report
    approval["reason"] = "Changed receipt bytes, same version"
    freeze, digest = freeze_file(root, approval)
    with pytest.raises(FileExistsError):
        measure(freeze, digest, root, root / "unavailable-test.json", runs)


def test_draft_freeze_is_rejected_before_heldout_access(frozen_rehearsal):
    root, _, runs, approval = frozen_rehearsal
    approval["stage"] = "development"
    freeze, digest = freeze_file(root, approval)
    with pytest.raises(ValueError, match="requires a recorded review"):
        measure(freeze, digest, root, root / "unavailable-test.json", runs)
    assert not list(runs.iterdir())


def test_development_model_is_rejected_before_heldout_access(frozen_rehearsal):
    root, _, runs, approval = frozen_rehearsal
    manifest_path = root / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["stage"] = "development"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    approval["model_manifest_sha256"] = sha256(manifest_path.read_bytes()).hexdigest()
    freeze, digest = freeze_file(root, approval)
    with pytest.raises(ValueError, match="Invalid development model manifest"):
        measure(freeze, digest, root, root / "unavailable-test.json", runs)
    assert not list(runs.iterdir())


def test_development_group_overlap_consumes_attempt_without_metrics(frozen_rehearsal):
    root, test, runs, approval = frozen_rehearsal
    approval["development_group_ids"] = ["holdout-group-0"]
    freeze, digest = freeze_file(root, approval)
    with pytest.raises(ValueError, match="Invalid held-out identity"):
        measure(freeze, digest, root, test, runs)
    version_digest = sha256(approval["version"].encode()).hexdigest()
    assert (runs / version_digest).is_dir()
    assert not (runs / version_digest / "metrics.json").exists()
