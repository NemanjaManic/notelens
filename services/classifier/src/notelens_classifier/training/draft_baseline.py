"""Run one provisional train/validation baseline; never score the draft test split."""

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unicodedata
import warnings

import joblib
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline

from notelens_classifier.inference import LABELS


ROOT = Path(__file__).resolve().parents[5]
DATA = ROOT / "data/mtsamples"
SOURCE = DATA / "raw/mtsamples.csv"
DRAFT = DATA / "raw/c002-provisional.json"
CONFIG = ROOT / "services/classifier/config/draft-baseline-v1.json"
LOCK = ROOT / "services/classifier/uv.lock"
OUT = ROOT / ".cache/c002-draft-baseline-v1"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare_training_text(text):
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def select_development(manifest):
    """Validate all group metadata; return only train/validation document mappings."""
    selected = {}
    ids, groups, source_ids = set(), set(), set()
    for group in manifest["groups"]:
        gid, split = group["group_id"], group["draft_split"]
        if gid in groups or not group["documents"] or split not in (None, "train", "validation", "test"):
            raise ValueError("Invalid group or partition.")
        groups.add(gid)
        if group["flags"] and split is not None:
            raise ValueError("Flagged group assigned to a partition.")
        member_ids = sorted(item["document_id"] for item in group["documents"])
        expected_gid = "group-" + sha(json.dumps(member_ids, ensure_ascii=True, separators=(",", ":")).encode())
        if gid != expected_gid:
            raise ValueError("Group membership digest mismatch.")
        for item in group["documents"]:
            doc_id = item["document_id"]
            source_id = item["source_row_id"]
            if doc_id in ids or source_id in source_ids:
                raise ValueError("A document or source row appears more than once.")
            ids.add(doc_id)
            source_ids.add(source_id)
            if split in ("train", "validation"):
                if group["flags"] or group["labels"] != [item["category"]] or item["category"] not in LABELS:
                    raise ValueError("Invalid development group or label.")
                selected[source_id] = {**item, "group_id": gid, "split": split}
    return selected


def read_development(source_path, selected):
    """Stream CSV rows; discard non-development rows without storing or scoring them."""
    parts = {"train": [], "validation": []}
    with source_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != ["", "description", "medical_specialty", "sample_name", "transcription", "keywords"]:
            raise ValueError("Unexpected source schema.")
        for row in reader:
            item = selected.get(row.get(""))
            if item is None:
                continue
            text = row["transcription"]
            if row["medical_specialty"].strip() != item["category"] or sha(text.encode("utf-8")) != item["source_text_sha256"]:
                raise ValueError("Source text or label mismatch.")
            parts[item["split"]].append((item["document_id"], item["group_id"], item["category"], text))
    if sum(map(len, parts.values())) != len(selected):
        raise ValueError("Development documents missing from source.")
    for rows in parts.values():
        rows.sort(key=lambda x: x[0])
        if set(row[2] for row in rows) != set(LABELS):
            raise ValueError("Development split does not support all classes.")
    if {r[1] for r in parts["train"]} & {r[1] for r in parts["validation"]}:
        raise ValueError("Training and validation share groups.")
    return parts


def load_provisional_data():
    draft_bytes = DRAFT.read_bytes()
    draft = json.loads(draft_bytes)
    if not draft["status"].startswith("DRAFT"):
        raise ValueError("This command requires the provisional split.")
    expected_source = json.loads((DATA / "manifests/source.json").read_text(encoding="utf-8"))["source"]["sha256"]
    with SOURCE.open("rb") as source:
        source_hash = hashlib.file_digest(source, "sha256").hexdigest()
    if source_hash != expected_source or draft["source_sha256"] != expected_source:
        raise ValueError("Source or split checksum mismatch.")
    parts = read_development(SOURCE, select_development(draft))
    return parts, expected_source, sha(draft_bytes)


def fit_pipeline(train_texts, train_labels, config):
    features = dict(config["tfidf"])
    features["ngram_range"] = tuple(features["ngram_range"])
    pipeline = Pipeline([("tfidf", TfidfVectorizer(**features)),
                         ("classifier", LogisticRegression(**config["logistic_regression"]))])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        pipeline.fit(train_texts, train_labels)
    return pipeline, [str(w.message) for w in caught if issubclass(w.category, ConvergenceWarning)]


def metrics(true, predicted, groups):
    counts = Counter(groups)
    weights = [1 / counts[group] for group in groups]
    return {"accuracy": accuracy_score(true, predicted),
            "macro_f1": f1_score(true, predicted, labels=LABELS, average="macro", zero_division=0),
            "weighted_f1": f1_score(true, predicted, labels=LABELS, average="weighted", zero_division=0),
            "group_adjusted_macro_f1": f1_score(true, predicted, labels=LABELS, average="macro", sample_weight=weights, zero_division=0),
            "per_class": classification_report(true, predicted, labels=LABELS, target_names=LABELS, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(true, predicted, labels=LABELS).tolist()}


def selective_summary(truth, predictions):
    comparisons = list(zip(truth, predictions, strict=True))
    accepted = sum(predicted is not None for predicted in predictions)
    correct = sum(actual == predicted for actual, predicted in comparisons)
    support = Counter(truth)
    rejected = Counter(actual for actual, predicted in comparisons if predicted is None)
    return {
        "correct": correct,
        "incorrect": accepted - correct,
        "rejected": len(truth) - accepted,
        "coverage": accepted / len(truth),
        "error_among_accepted": (accepted - correct) / accepted if accepted else None,
        "per_class_rejected": {label: rejected[label] for label in LABELS},
        "per_class_rejection_rate": {
            label: rejected[label] / support[label] if support[label] else None for label in LABELS
        },
    }


def main():
    if OUT.exists():
        raise ValueError("Experiment output exists; preserve it and select a new experiment version.")
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    parts, expected_source, draft_hash = load_provisional_data()
    train, val = parts["train"], parts["validation"]
    counts = Counter(row[2] for row in train)
    majority = max(LABELS, key=lambda label: counts[label])
    started = time.perf_counter()
    model, convergence = fit_pipeline([r[3] for r in train], [r[2] for r in train], config)
    fit_seconds = time.perf_counter() - started
    started = time.perf_counter()
    predictions = model.predict([r[3] for r in val])
    predict_seconds = time.perf_counter() - started
    truth, group_ids = [r[2] for r in val], [r[1] for r in val]
    results = {"status": "exploratory only; provisional split; no final-test evaluation or model selection",
               "experiment_id": config["experiment_id"], "source_sha256": expected_source,
               "draft_sha256": draft_hash, "config_sha256": sha(config_bytes),
               "lock_sha256": sha(LOCK.read_bytes()), "script_sha256": sha(Path(__file__).read_bytes()),
               "python": platform.python_version(), "scikit_learn": sklearn.__version__,
               "platform": platform.platform(), "labels": LABELS, "train_rows": len(train),
               "validation_rows": len(val), "train_groups": len({r[1] for r in train}),
               "validation_groups": len(set(group_ids)), "training_class_counts": dict(counts),
               "validation_group_support": {label: len({r[1] for r in val if r[2] == label}) for label in LABELS},
               "majority_label": majority, "majority": metrics(truth, [majority] * len(val), group_ids),
               "tfidf_logistic": metrics(truth, predictions, group_ids),
               "fit_seconds": fit_seconds, "validation_predict_seconds": predict_seconds,
               "convergence_warnings": convergence, "test_scored": False}
    OUT.mkdir(parents=True, exist_ok=False)
    joblib.dump(model, OUT / "development-model.joblib")
    results["model_bytes"] = (OUT / "development-model.joblib").stat().st_size
    results["model_sha256"] = sha((OUT / "development-model.joblib").read_bytes())
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": results["status"], "train_rows": len(train), "validation_rows": len(val),
                      "majority_macro_f1": results["majority"]["macro_f1"],
                      "tfidf_logistic_macro_f1": results["tfidf_logistic"]["macro_f1"],
                      "convergence_warnings": len(convergence), "test_scored": False}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, UnicodeError, csv.Error):
        print("Development run failed: verify source, provisional manifest, dependencies and output directory.", file=sys.stderr)
        sys.exit(1)
