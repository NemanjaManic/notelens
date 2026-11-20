"""Fit C-003 baselines and export validation predictions for D-006."""

import argparse
from collections import Counter
import csv
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
from tempfile import TemporaryDirectory

import joblib

from data.mtsamples.prepare_transcription import CANONICALIZATION_VERSION, prepare_transcription
from notelens_classifier.inference import LABELS, score_rows
from notelens_classifier.training import draft_baseline as baseline


EXPORT_VERSION = "c003-d006-validation-v1"
SPLITS = ("train", "validation")
GROUP_ID_PREFIX = "group-"


def checked_bytes(path, checksum):
    payload = path.read_bytes()
    if baseline.sha(payload) != checksum:
        raise ValueError("A pinned input differs from its checksum.")
    return payload


def read_membership(split_dir, summary):
    membership, group_ids = {}, set()
    for split in SPLITS:
        filename = f"{split}.json"
        partition = json.loads(checked_bytes(split_dir / filename, summary["split_checksums"][filename]))
        if (partition["split"] != split or partition["manifest_version"] != summary["manifest_version"]
                or partition["source_sha256"] != summary["source_sha256"]):
            raise ValueError("The partition differs from the frozen split.")
        labels = Counter()
        for group in partition["groups"]:
            gid, documents = group["group_id"], group["documents"]
            document_ids = sorted(doc["document_id"] for doc in documents)
            group_payload = json.dumps(document_ids, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            specialties = {doc["specialty"] for doc in documents}
            if (gid != GROUP_ID_PREFIX + baseline.sha(group_payload) or gid in group_ids
                    or len(specialties) != 1 or not specialties <= set(LABELS)):
                raise ValueError("Invalid or overlapping frozen duplicate group.")
            group_ids.add(gid)
            for doc in documents:
                doc_id, label = doc["document_id"], doc["specialty"]
                if doc_id in membership:
                    raise ValueError("A document appears more than once in development.")
                membership[doc_id] = (split, gid, label)
                labels[label] += 1
        if set(labels) != set(LABELS) or sum(labels.values()) != summary["documents_per_split"][split]:
            raise ValueError("Frozen development membership does not reconcile.")
    return membership


def validation_digests(handoff_dir, membership, split_checksum, split_version):
    checksum, filename = (handoff_dir / "manifest.sha256").read_text(encoding="ascii").split()
    if filename != "manifest.json":
        raise ValueError("The handoff checksum must name its manifest.")
    manifest = json.loads(checked_bytes(handoff_dir / filename, checksum))
    if (manifest["kind"] != "permitted_benchmark" or manifest["split_manifest_version"] != split_version
            or manifest["split_manifest_sha256"] != split_checksum
            or manifest["canonicalization_version"] != CANONICALIZATION_VERSION):
        raise ValueError("The D handoff does not match the frozen split and text preparation.")
    approved = {doc_id: entry for doc_id, entry in membership.items() if entry[0] == "validation"}
    digests = {}
    for doc in manifest["documents"]:
        doc_id = doc["doc_id"]
        if (doc_id in digests or approved.get(doc_id) != (doc["split"], doc["group_id"], doc["specialty"])
                or doc["permitted_for_annotation"] is not True):
            raise ValueError("The D handoff contains an unapproved or mismatched candidate.")
        digests[doc_id] = doc["text_sha256"]
    if digests.keys() != approved.keys():
        raise ValueError("The D handoff does not cover the frozen validation partition.")
    return digests, manifest["source_version"], checksum


def read_cohorts(source_path, source_checksum, membership, digests):
    """Canonicalize only rows selected by the two frozen development manifests."""
    payload = checked_bytes(source_path, source_checksum)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != ["", "description", "medical_specialty", "sample_name", "transcription", "keywords"]:
        raise ValueError("Unexpected audited CSV schema.")
    parts, seen = {split: [] for split in SPLITS}, set()
    for row in reader:
        doc_id = f"mtsamples-{source_checksum[:16]}-{row['']}"
        if doc_id not in membership:
            continue
        split, gid, label = membership[doc_id]
        if doc_id in seen or row["medical_specialty"].strip() != label:
            raise ValueError("Source document identity or specialty differs from the frozen split.")
        prepared = prepare_transcription(row["transcription"])
        if split == "validation" and prepared.text_sha256 != digests[doc_id]:
            raise ValueError("The validation text digest differs from D's handoff.")
        parts[split].append((doc_id, gid, label, prepared.text))
        seen.add(doc_id)
    if seen != membership.keys():
        raise ValueError("Frozen development documents are missing from the audited source.")
    return {split: sorted(rows) for split, rows in parts.items()}


def write_json(path, value):
    payload = (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return baseline.sha(payload)


def load_frozen_development(split_dir, split_checksum, handoff_dir):
    """Load checked train/validation cohorts with the D handoff's validation digests."""
    summary = json.loads(checked_bytes(split_dir / "manifest.json", split_checksum))
    if summary["status"] != "frozen local split membership":
        raise ValueError("Use a frozen local split.")
    source_checksum = summary["source_sha256"]
    audit = json.loads((baseline.DATA / "manifests/source.json").read_bytes())
    if source_checksum != audit["source"]["sha256"]:
        raise ValueError("Frozen split and C-001 source audit differ.")
    split_version = summary["manifest_version"]
    membership = read_membership(split_dir, summary)
    digests, handoff_version, handoff_checksum = validation_digests(
        handoff_dir, membership, split_checksum, split_version
    )
    parts = read_cohorts(baseline.SOURCE, source_checksum, membership, digests)
    return parts, {
        "source_sha256": source_checksum, "split_version": split_version, "split_sha256": split_checksum,
        "handoff_version": handoff_version, "handoff_sha256": handoff_checksum,
        "preparation_version": CANONICALIZATION_VERSION,
    }


def run(split_dir, split_checksum, handoff_dir, output):
    parts, provenance = load_frozen_development(split_dir, split_checksum, handoff_dir)
    train, validation = parts["train"], parts["validation"]
    config_bytes = baseline.CONFIG.read_bytes()
    config = json.loads(config_bytes)
    train_labels = [row[2] for row in train]
    counts = Counter(train_labels)
    majority = max(LABELS, key=counts.__getitem__)
    model, warnings = baseline.fit_pipeline([row[3] for row in train], train_labels, config)
    if warnings:
        raise ValueError("Logistic Regression did not converge with the pinned baseline settings.")
    features = model.named_steps["tfidf"].transform([row[3] for row in validation])
    probabilities = list(score_rows(model.named_steps["classifier"], features))
    predicted = [LABELS[scores.index(max(scores))] for scores in probabilities]
    truth, groups = [row[2] for row in validation], [row[1] for row in validation]

    with TemporaryDirectory(dir=output.parent) as staging:
        pending = Path(staging) / output.name
        pending.mkdir()
        model_path = pending / "baseline-model.joblib"
        joblib.dump(model, model_path)
        model_checksum = baseline.sha(model_path.read_bytes())
        versions = {"model_version": f"c003-tfidf-logistic-{model_checksum[:16]}",
                    "preparation_version": provenance["preparation_version"],
                    "split_version": provenance["split_version"]}
        export = {"export_version": EXPORT_VERSION, **versions, "split_checksum": split_checksum,
                  "handoff_version": provenance["handoff_version"], "handoff_checksum": provenance["handoff_sha256"],
                  "decision_policy": "forced_choice", "score_type": "logistic_regression_probability",
                  "documents": [
                      {"doc_id": row[0], "true_specialty": row[2], "predicted_specialty": prediction,
                       "status": "forced_choice", "scores": dict(zip(LABELS, scores, strict=True)), **versions}
                      for row, prediction, scores in zip(validation, predicted, probabilities, strict=True)
                  ]}
        predictions_checksum = write_json(pending / "predictions.json", export)
        (pending / "predictions.sha256").write_text(
            f"{predictions_checksum}  predictions.json\n", encoding="ascii", newline="\n"
        )
        metrics = {**versions, "source_sha256": provenance["source_sha256"], "split_checksum": split_checksum,
                   "handoff_checksum": provenance["handoff_sha256"], "config_sha256": baseline.sha(config_bytes),
                   "lock_sha256": baseline.sha(baseline.LOCK.read_bytes()), "model_sha256": model_checksum,
                   "predictions_sha256": predictions_checksum, "python": platform.python_version(),
                   "dependencies": {name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib")},
                   "train_rows": len(train), "validation_rows": len(validation),
                   "train_groups": len({row[1] for row in train}), "validation_groups": len(set(groups)),
                   "training_class_counts": dict(counts), "validation_class_counts": dict(Counter(truth)),
                   "majority_label": majority, "majority": baseline.metrics(truth, [majority] * len(truth), groups),
                   "tfidf_logistic": baseline.metrics(truth, predicted, groups), "test_scored": False}
        write_json(pending / "metrics.json", metrics)
        pending.rename(output)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--split-sha256", required=True)
    parser.add_argument("--handoff-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = baseline.SOURCE.parent.resolve()
    split_dir, handoff_dir, output = [path.resolve() for path in (args.split_dir, args.handoff_dir, args.output)]
    if any(path == raw or not path.is_relative_to(raw) for path in (split_dir, handoff_dir, output)):
        parser.error("Use directories inside the Git-ignored local MTSamples directory.")
    if output.exists() or not output.parent.is_dir():
        parser.error("Choose a new output directory under an existing local parent.")
    try:
        metrics = run(split_dir, args.split_sha256.lower(), handoff_dir, output)
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        parser.exit(1, f"C-003 export failed ({type(error).__name__}). Verify the input and output paths.\n")
    print(json.dumps({
        "model_version": metrics["model_version"], "train_rows": metrics["train_rows"],
        "validation_rows": metrics["validation_rows"], "majority_macro_f1": metrics["majority"]["macro_f1"],
        "tfidf_logistic_macro_f1": metrics["tfidf_logistic"]["macro_f1"], "test_scored": False,
    }))


if __name__ == "__main__":
    main()
