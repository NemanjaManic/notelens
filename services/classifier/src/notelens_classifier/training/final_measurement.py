"""Measure a reviewed and frozen classifier on separately held-out prepared records."""

import argparse
import json
from pathlib import Path
import sys

from notelens_contracts.v1 import validate_record

from notelens_classifier.inference import LABELS, load_model
from notelens_classifier.training import draft_baseline as baseline


def measure(freeze_path: Path, freeze_sha256: str, model_dir: Path, test_path: Path, runs_dir: Path):
    raw_freeze = freeze_path.read_bytes()
    if baseline.sha(raw_freeze) != freeze_sha256:
        raise ValueError("Final freeze checksum mismatch.")
    freeze = json.loads(raw_freeze)
    if (freeze["stage"] != "approved-final" or not freeze["review_reference"].strip()
            or not freeze["version"].strip() or not freeze["reason"].strip()
            or freeze["majority_label"] not in LABELS):
        raise ValueError("Final measurement requires a recorded review and a frozen version.")
    development_documents = set(freeze["development_document_ids"])
    development_groups = set(freeze["development_group_ids"])
    if not development_documents or not development_groups:
        raise ValueError("Missing frozen development identities.")

    model = load_model(model_dir, freeze["model_manifest_sha256"], stage="frozen")
    output = runs_dir / baseline.sha(freeze["version"].strip().encode("utf-8"))
    # Reserve the run before opening held-out records. An interrupted run still consumed access.
    output.mkdir(exist_ok=False)
    raw_test = test_path.read_bytes()
    if baseline.sha(raw_test) != freeze["locked_test_sha256"]:
        raise ValueError("Locked test checksum mismatch.")
    holdout = json.loads(raw_test)
    if holdout["stage"] != "locked-test":
        raise ValueError("A locked test artifact is required.")

    ids, group_labels = set(), {}
    documents, truth, groups = [], [], []
    for row in holdout["rows"]:
        document = validate_record("PreparedDocument", row["document"])
        document_id, group, label = document["doc_id"], row["group_id"], row["category"]
        if (document_id in ids or document_id in development_documents or not group
                or group in development_groups or label not in LABELS
                or group_labels.setdefault(group, label) != label
                or document["source"]["kind"] not in ("builtin_public", "public_text", "synthetic_text")):
            raise ValueError("Invalid held-out identity, provenance, group, or category.")
        ids.add(document_id)
        documents.append(document)
        truth.append(label)
        groups.append(group)
    if set(truth) != set(LABELS):
        raise ValueError("Locked test requires support for all five categories.")

    forced, selective = [], []
    for document in documents:
        result = model.classify(document)
        validate_record("ClassificationResult", result, document=document)
        strongest = max(result["scores"], key=lambda score: score["score"])
        forced.append(strongest["category"])
        selective.append(result["category"])
    report = {
        "freeze_version": freeze["version"],
        "freeze_sha256": freeze_sha256,
        "locked_test_sha256": freeze["locked_test_sha256"],
        "model_manifest_sha256": freeze["model_manifest_sha256"],
        "model_version": model.model_version,
        "rows": len(truth),
        "groups": len(set(groups)),
        "group_support": {label: sum(actual == label for actual in group_labels.values()) for label in LABELS},
        "majority": baseline.metrics(truth, [freeze["majority_label"]] * len(truth), groups),
        "forced_choice": baseline.metrics(truth, forced, groups),
        "selective": baseline.selective_summary(truth, selective),
    }
    pending = output / "metrics.pending"
    with pending.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    pending.replace(output / "metrics.json")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--freeze-sha256", required=True, help="Checksum from the recorded review.")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--locked-test", type=Path, required=True)
    args = parser.parse_args()
    runs = baseline.ROOT / ".cache/classifier-final-runs"
    runs.mkdir(parents=True, exist_ok=True)
    try:
        report = measure(args.freeze, args.freeze_sha256, args.model, args.locked_test, runs)
    except Exception:
        print("Final measurement failed. Verify the review, artifacts and previous run records.", file=sys.stderr)
        return 1
    print(json.dumps({"freeze_version": report["freeze_version"], "rows": report["rows"], "groups": report["groups"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
