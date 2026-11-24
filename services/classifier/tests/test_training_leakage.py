"""Synthetic checks for provisional development-only data and feature boundaries."""

import csv
import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn", reason="Optional training dependency group is not installed")
from notelens_classifier.training import draft_baseline as baseline


def group(document_id, source_id, category, split):
    identifier = "group-" + baseline.sha(json.dumps([document_id], separators=(",", ":")).encode())
    return {"group_id": identifier, "draft_split": split, "flags": [], "labels": [category],
            "documents": [{"document_id": document_id, "source_row_id": source_id,
                           "category": category, "source_text_sha256": "synthetic"}]}


def test_test_partition_never_selected_for_training_or_validation():
    groups = [group("development", "1", "Neurology", "train"),
              group("holdout", "2", "Urology", "test")]
    selected = baseline.select_development({"groups": groups})
    assert set(selected) == {"1"}
    assert selected["1"]["split"] == "train"


def test_duplicate_document_or_flagged_partition_is_rejected():
    first = group("same", "1", "Neurology", "train")
    duplicate = group("same", "2", "Neurology", "validation")
    with pytest.raises(ValueError):
        baseline.select_development({"groups": [first, duplicate]})
    first["flags"] = ["unresolved_near_candidate"]
    with pytest.raises(ValueError):
        baseline.select_development({"groups": [first]})


def test_source_identity_cannot_cross_into_heldout_under_another_document_id():
    first = group("training", "same-source", "Neurology", "train")
    duplicate = group("heldout", "same-source", "Neurology", "test")
    with pytest.raises(ValueError, match="source row appears more than once"):
        baseline.select_development({"groups": [first, duplicate]})


def test_vectorizer_fits_only_training_text():
    config = json.loads((Path(__file__).resolve().parents[1] / "config/draft-baseline-v1.json").read_text(encoding="utf-8"))
    pipeline, caught = baseline.fit_pipeline(["training alpha", "training beta"], ["a", "b"], config)
    pipeline.predict(["validationonlymarker"])
    assert "training" in pipeline.named_steps["tfidf"].vocabulary_
    assert "validationonlymarker" not in pipeline.named_steps["tfidf"].vocabulary_
    assert not caught


@pytest.fixture
def frozen_baseline(monkeypatch):
    monkeypatch.syspath_prepend(str(baseline.ROOT))
    from notelens_classifier.training import frozen_baseline as module

    return module


def test_frozen_membership_uses_only_train_and_validation(tmp_path, frozen_baseline):
    summary = {"manifest_version": "fixture-v1", "source_sha256": "synthetic",
               "split_checksums": {}, "documents_per_split": {}}
    for split in ("train", "validation"):
        groups = []
        for index, label in enumerate(baseline.LABELS):
            doc_id = f"{split}-{index}"
            groups.append({
                "group_id": group(doc_id, "unused", label, split)["group_id"],
                "documents": [{"document_id": doc_id, "specialty": label}],
            })
        record = {"split": split, "manifest_version": "fixture-v1",
                  "source_sha256": "synthetic", "groups": groups}
        data = json.dumps(record).encode()
        (tmp_path / f"{split}.json").write_bytes(data)
        summary["split_checksums"][f"{split}.json"] = baseline.sha(data)
        summary["documents_per_split"][split] = len(groups)

    assert not (tmp_path / "test.json").exists()
    membership = frozen_baseline.read_membership(tmp_path, summary)
    assert set(membership) == {f"{split}-{i}" for split in ("train", "validation") for i in range(5)}
    (tmp_path / "validation.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="checksum"):
        frozen_baseline.read_membership(tmp_path, summary)


def test_frozen_cohorts_skip_unselected_text_and_pin_validation_digest(tmp_path, frozen_baseline):
    path = tmp_path / "source.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["", "description", "medical_specialty", "sample_name", "transcription", "keywords"])
        writer.writerow(["1", "unused marker", "Neurology", "", "Training input", "unused marker"])
        writer.writerow(["2", "", "Urology", "", "A\r\ncafe\u0301", ""])
        writer.writerow(["holdout", "", "Urology", "", "", ""])
    checksum = baseline.sha(path.read_bytes())
    prefix = f"mtsamples-{checksum[:16]}-"
    membership = {prefix + "1": ("train", "first-group", "Neurology"),
                  prefix + "2": ("validation", "second-group", "Urology")}
    digest = baseline.sha("A\ncafé".encode("utf-8"))
    parts = frozen_baseline.read_cohorts(path, checksum, membership, {prefix + "2": digest})
    assert parts == {"train": [(prefix + "1", "first-group", "Neurology", "Training input")],
                     "validation": [(prefix + "2", "second-group", "Urology", "A\ncafé")]}
    with pytest.raises(ValueError, match="validation text digest"):
        frozen_baseline.read_cohorts(path, checksum, membership, {prefix + "2": "changed"})
