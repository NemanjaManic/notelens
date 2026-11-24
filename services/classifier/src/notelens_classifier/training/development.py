"""Compare trained candidates on development data only."""

import argparse
from collections import Counter
import csv
from importlib.metadata import version
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
import unicodedata

import joblib
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE, accepted_category, score_rows
from notelens_classifier.training import draft_baseline as baseline


CONFIG = baseline.CONFIG.with_name("development-comparison-v1.json")
FROZEN_EXPERIMENT = "c004-frozen-comparison-v1"


def compare(parts, baseline_config, comparison_config, *, canonical=False):
    train, validation = parts["train"], parts["validation"]
    prepare_text = str if canonical else baseline.prepare_training_text
    train_text = [prepare_text(row[3]) for row in train]
    validation_text = [prepare_text(row[3]) for row in validation]
    train_labels = [row[2] for row in train]
    truth = [row[2] for row in validation]
    groups = [row[1] for row in validation]

    started = perf_counter()
    logistic, warnings = baseline.fit_pipeline(train_text, train_labels, baseline_config)
    logistic_fit_seconds = perf_counter() - started
    features = logistic.named_steps["tfidf"]
    training_features = features.transform(train_text)
    validation_features = features.transform(validation_text)

    started = perf_counter()
    boosted = XGBClassifier(**comparison_config["xgboost"])
    boosted.fit(training_features, [LABELS.index(label) for label in train_labels])
    boosted_fit_seconds = perf_counter() - started
    candidates = {
        "logistic_regression": logistic,
        "xgboost": Pipeline([("tfidf", features), ("classifier", boosted)]),
    }

    counts = Counter(train_labels)
    majority = max(LABELS, key=counts.get)
    results = {"majority": baseline.metrics(truth, [majority] * len(truth), groups)}
    probabilities = {}
    for name, candidate in candidates.items():
        probabilities[name] = list(score_rows(candidate.named_steps["classifier"], validation_features))
        predictions = [LABELS[scores.index(max(scores))] for scores in probabilities[name]]
        results[name] = baseline.metrics(truth, predictions, groups)

    selected = max(candidates, key=lambda name: results[name]["macro_f1"])
    has_features = validation_features.getnnz(axis=1) > 0
    thresholds = [
        selective_metrics(truth, probabilities[selected], has_features, cutoff)
        for cutoff in comparison_config["thresholds"]
    ]
    chosen = max(thresholds, key=lambda item: (
        item["correct"] - item["incorrect"], item["coverage"], -item["threshold"]
    ))
    return candidates[selected], {
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_groups": len({row[1] for row in train}),
        "validation_groups": len(set(groups)),
        "training_support": dict(counts),
        "validation_group_support": {
            label: len({row[1] for row in validation if row[2] == label}) for label in LABELS
        },
        "majority_label": majority,
        "models": results,
        "selected": selected,
        "thresholds": thresholds,
        "chosen_policy": chosen,
        "logistic_convergence_warnings": warnings,
        "logistic_fit_seconds_including_tfidf": logistic_fit_seconds,
        "xgboost_estimator_fit_seconds": boosted_fit_seconds,
    }


def selective_metrics(truth, probabilities, has_features, threshold):
    predictions = [
        accepted_category(scores, features, threshold)
        for scores, features in zip(probabilities, has_features, strict=True)
    ]
    return {"threshold": threshold, **baseline.selective_summary(truth, predictions)}


def run(output: Path):
    parts, source_sha256, split_sha256 = baseline.load_provisional_data()
    return run_comparison(output, parts, {"source_sha256": source_sha256, "split_sha256": split_sha256})


def run_frozen(output: Path, split_dir: Path, split_sha256: str, handoff_dir: Path):
    from notelens_classifier.training import frozen_baseline

    parts, provenance = frozen_baseline.load_frozen_development(split_dir, split_sha256, handoff_dir)
    return run_comparison(
        output, parts, provenance, experiment_id=FROZEN_EXPERIMENT, loader_path=Path(frozen_baseline.__file__)
    )


def run_comparison(output, parts, provenance, *, experiment_id=None, loader_path=None):
    config_bytes, baseline_bytes = CONFIG.read_bytes(), baseline.CONFIG.read_bytes()
    config, baseline_config = json.loads(config_bytes), json.loads(baseline_bytes)
    canonical = loader_path is not None
    experiment_id = experiment_id or config["experiment_id"]
    model, report = compare(parts, baseline_config, config, canonical=canonical)
    if report["logistic_convergence_warnings"]:
        raise ValueError("Logistic baseline did not converge.")
    if not report["chosen_policy"]["coverage"]:
        raise ValueError("Development policy accepted no cases.")

    packages = {name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib", "xgboost-cpu")}
    sources = [Path(__file__), Path(baseline.__file__), Path(__file__).parents[1] / "inference.py"]
    if loader_path is not None:
        sources.append(loader_path)
    report.update(
        experiment_id=experiment_id, status="frozen split development" if canonical else "provisional development",
        labels=LABELS,
        python=sys.version.split()[0], unicode_version=unicodedata.unidata_version, packages=packages,
        comparison_config_sha256=baseline.sha(config_bytes), baseline_config_sha256=baseline.sha(baseline_bytes),
        lock_sha256=baseline.sha(baseline.LOCK.read_bytes()),
        code_sha256={path.name: baseline.sha(path.read_bytes()) for path in sources},
        test_scored=False, **provenance,
    )
    joblib.dump(model, output / MODEL_FILE)
    artifact_hash = baseline.sha((output / MODEL_FILE).read_bytes())
    model_packages = packages.copy()
    if report["selected"] == "logistic_regression":
        del model_packages["xgboost-cpu"]
    threshold = report["chosen_policy"]["threshold"]
    identity = baseline.sha(json.dumps([artifact_hash, threshold, report["comparison_config_sha256"]]).encode())
    manifest = {
        "stage": "development",
        "model_version": f"{experiment_id}-{identity}",
        "estimator": report["selected"],
        "labels": LABELS,
        "threshold": threshold,
        "packages": model_packages,
        "artifact_sha256": artifact_hash,
    }
    for filename, value in ((MANIFEST_FILE, manifest), ("metrics.json", report)):
        (output / filename).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "train_rows": report["train_rows"],
        "validation_rows": report["validation_rows"],
        "macro_f1": {name: result["macro_f1"] for name, result in report["models"].items()},
        "selected": report["selected"], "policy": report["chosen_policy"],
        "manifest_sha256": baseline.sha((output / MANIFEST_FILE).read_bytes()), "test_scored": False,
    }, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-dir", type=Path)
    parser.add_argument("--split-sha256")
    parser.add_argument("--handoff-dir", type=Path)
    args = parser.parse_args()
    frozen_args = (args.split_dir, args.split_sha256, args.handoff_dir)
    frozen = any(value is not None for value in frozen_args)
    if frozen and not all(frozen_args):
        parser.error("Supply --split-dir, --split-sha256 and --handoff-dir together.")
    if frozen:
        raw = baseline.SOURCE.parent.resolve()
        split_dir, handoff_dir = args.split_dir.resolve(), args.handoff_dir.resolve()
        if any(path == raw or not path.is_relative_to(raw) for path in (split_dir, handoff_dir)):
            parser.error("Use frozen inputs inside the ignored local MTSamples directory.")
    cache = (baseline.ROOT / ".cache").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(cache) or not output.parent.is_dir() or output.exists():
        parser.error("Choose a new output directory under the ignored repository cache.")
    try:
        with TemporaryDirectory(dir=output.parent) as staging:
            pending = Path(staging) / output.name
            pending.mkdir()
            if frozen:
                run_frozen(pending, split_dir, args.split_sha256.lower(), handoff_dir)
            else:
                run(pending)
            pending.rename(output)
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        print("Development run failed. Verify the audited input, dependencies and new output path.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
