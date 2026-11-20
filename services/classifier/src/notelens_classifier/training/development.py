"""Compare trained candidates on the provisional development split only."""

import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import sys
from time import perf_counter
import unicodedata

import joblib
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE, accepted_category, score_rows
from notelens_classifier.training import draft_baseline as baseline


CONFIG = baseline.CONFIG.with_name("development-comparison-v1.json")


def compare(parts, baseline_config, comparison_config):
    train, validation = parts["train"], parts["validation"]
    train_text = [baseline.prepare_training_text(row[3]) for row in train]
    validation_text = [baseline.prepare_training_text(row[3]) for row in validation]
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
    config_bytes, baseline_bytes = CONFIG.read_bytes(), baseline.CONFIG.read_bytes()
    config, baseline_config = json.loads(config_bytes), json.loads(baseline_bytes)
    parts, source_sha256, split_sha256 = baseline.load_provisional_data()
    model, report = compare(parts, baseline_config, config)
    if report["logistic_convergence_warnings"]:
        raise ValueError("Logistic baseline did not converge.")
    if not report["chosen_policy"]["coverage"]:
        raise ValueError("Development policy accepted no cases.")

    packages = {name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib", "xgboost-cpu")}
    report.update(
        experiment_id=config["experiment_id"], status="provisional development", labels=LABELS,
        python=sys.version.split()[0], unicode_version=unicodedata.unidata_version, packages=packages,
        source_sha256=source_sha256, split_sha256=split_sha256,
        comparison_config_sha256=baseline.sha(config_bytes), baseline_config_sha256=baseline.sha(baseline_bytes),
        lock_sha256=baseline.sha(baseline.LOCK.read_bytes()),
        code_sha256={path.name: baseline.sha(path.read_bytes()) for path in
                     (Path(__file__), Path(baseline.__file__), Path(__file__).parents[1] / "inference.py")},
        test_scored=False,
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
        "model_version": f"{config['experiment_id']}-{identity}",
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cache = (baseline.ROOT / ".cache").resolve()
    output = args.output.resolve()
    if not output.is_relative_to(cache) or not output.parent.is_dir():
        parser.error("Choose a new output directory under the ignored repository cache.")
    try:
        output.mkdir(exist_ok=False)
        run(output)
    except (OSError, ValueError, KeyError):
        print("Development run failed. Verify the audited input, dependencies and new output path.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
