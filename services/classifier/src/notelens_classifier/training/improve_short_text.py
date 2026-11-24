"""Fit and select a short-text classifier using the provisional development data."""

import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import sys
import warnings

import joblib
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE, accepted_category, load_model, score_rows
from notelens_classifier.training import draft_baseline as baseline


CONFIG = baseline.CONFIG.with_name("short-text-improvement-v1.json")
DEVELOPMENT_SUITE = baseline.ROOT / "services/classifier/tests/fixtures/model-check-short-v1.json"


def short_windows(text, width, count):
    words = text.split()
    if len(words) <= width:
        return []
    last = len(words) - width
    starts = sorted({round(last * step / (count - 1)) for step in range(count)})
    return [" ".join(words[start:start + width]) for start in starts]


def fit_candidate(train, recipe, config):
    counts = Counter(row[2] for row in train)
    class_weight = {label: len(train) / (len(LABELS) * counts[label]) for label in LABELS}
    texts, labels, weights = [], [], []
    for _, _, label, raw_text in train:
        text = baseline.prepare_training_text(raw_text)
        windows = short_windows(text, config["window_words"], config["windows_per_document"]) if recipe["windows"] else []
        texts.extend([text, *windows])
        labels.extend([label] * (1 + len(windows)))
        weights.append(1.0)
        if windows:
            weights.extend([config["total_window_weight_per_document"] / len(windows)] * len(windows))

    features = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    if recipe["characters"]:
        characters = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                                     max_features=60_000, sublinear_tf=True)
        features = FeatureUnion([("word", features), ("character", characters)],
                                transformer_weights={"character": 0.65})
    estimator = LogisticRegression(**config["logistic_regression"], class_weight=class_weight)
    pipeline = Pipeline([("tfidf", features), ("classifier", estimator)])
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        pipeline.fit(texts, labels, classifier__sample_weight=weights)
    return pipeline, len(texts) - len(train)


def score_examples(pipeline, texts):
    features = pipeline.named_steps["tfidf"].transform(texts)
    probabilities = list(score_rows(pipeline.named_steps["classifier"], features))
    return list(zip(probabilities, features.getnnz(axis=1) > 0, strict=True))


def forced_metrics(truth, scores, groups):
    predicted = [LABELS[probabilities.index(max(probabilities))] for probabilities, _ in scores]
    return baseline.metrics(truth, predicted, groups)


def evaluate_policy(document_truth, document_scores, short_truth, short_scores, threshold, minimum_margin):
    document_predictions = [
        accepted_category(probabilities, has_terms, threshold, minimum_margin)
        for probabilities, has_terms in document_scores
    ]
    short_predictions = [
        accepted_category(probabilities, has_terms, threshold, minimum_margin)
        for probabilities, has_terms in short_scores
    ]
    labeled = [(expected, actual) for expected, actual in zip(short_truth, short_predictions, strict=True)
               if expected in LABELS]
    short_expected, short_actual = zip(*labeled)
    document_results = baseline.selective_summary(document_truth, document_predictions)
    short_results = baseline.selective_summary(short_expected, short_actual)
    unrelated = sum(expected == "unrelated" and actual is not None
                    for expected, actual in zip(short_truth, short_predictions, strict=True))
    ambiguous = sum(expected == "ambiguous" and actual is not None
                    for expected, actual in zip(short_truth, short_predictions, strict=True))
    document_utility = (document_results["correct"] - document_results["incorrect"]) / len(document_truth)
    short_utility = (short_results["correct"] - short_results["incorrect"] - unrelated - ambiguous) / len(short_truth)
    return {
        "threshold": threshold, "minimum_margin": minimum_margin, "utility": (document_utility + short_utility) / 2,
        "documents": document_results, "short_specialties": short_results,
        "unrelated_accepted": unrelated, "ambiguous_accepted": ambiguous,
    }


def policy_rank(policy):
    return (policy["utility"], policy["short_specialties"]["correct"], policy["documents"]["correct"])


def run(output, reference_path):
    config_bytes = CONFIG.read_bytes()
    suite_bytes = DEVELOPMENT_SUITE.read_bytes()
    config, suite = json.loads(config_bytes), json.loads(suite_bytes)
    source, source_hash, split_hash = baseline.load_provisional_data()
    train, validation = source["train"], source["validation"]
    document_truth = [row[2] for row in validation]
    document_groups = [row[1] for row in validation]
    document_texts = [baseline.prepare_training_text(row[3]) for row in validation]
    short_examples = [(label, text) for label in LABELS for text in suite["specialties"][label]]
    short_examples += [("unrelated", text) for text in suite["unrelated"]]
    short_examples += [("ambiguous", text) for text in suite["ambiguous"]]
    short_truth, short_texts = zip(*short_examples)
    specialty_count = sum(label in LABELS for label in short_truth)

    reference = load_model(reference_path, config["reference_manifest_sha256"])
    reference_documents = score_examples(reference.pipeline, document_texts)
    reference_short = score_examples(reference.pipeline, short_texts)
    reference_results = {
        "full_forced_choice": forced_metrics(document_truth, reference_documents, document_groups),
        "short_forced_choice": forced_metrics(short_truth[:specialty_count], reference_short[:specialty_count],
                                             list(range(specialty_count))),
        "policy": evaluate_policy(document_truth, reference_documents, short_truth, reference_short,
                                  reference.threshold, reference.minimum_margin),
    }
    results = {}
    winner, best_pipeline = None, None
    for recipe in config["candidates"]:
        pipeline, windows = fit_candidate(train, recipe, config)
        documents = score_examples(pipeline, document_texts)
        short = score_examples(pipeline, short_texts)
        policy = max(
            (evaluate_policy(document_truth, documents, short_truth, short, threshold, minimum_margin)
             for threshold in config["thresholds"] for minimum_margin in config["minimum_margins"]),
            key=policy_rank,
        )
        name = recipe["name"]
        results[name] = {
            "training_windows": windows,
            "full_forced_choice": forced_metrics(document_truth, documents, document_groups),
            "short_forced_choice": forced_metrics(short_truth[:specialty_count], short[:specialty_count],
                                                 list(range(specialty_count))),
            "policy": policy,
        }
        if winner is None or policy_rank(policy) > policy_rank(results[winner]["policy"]):
            winner, best_pipeline = name, pipeline

    policy = results[winner]["policy"]
    if policy_rank(policy) <= policy_rank(reference_results["policy"]):
        raise ValueError("The candidates did not improve the development objective.")
    packages = {name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib")}
    joblib.dump(best_pipeline, output / MODEL_FILE)
    model_hash = baseline.sha((output / MODEL_FILE).read_bytes())
    config_hash = baseline.sha(config_bytes)
    identity = baseline.sha(json.dumps([model_hash, config_hash, policy["threshold"], policy["minimum_margin"]]).encode())
    manifest = {
        "stage": "development", "estimator": "logistic_regression", "labels": LABELS,
        "model_version": f"{config['experiment_id']}-{identity}",
        "artifact_sha256": model_hash, "packages": packages,
        "threshold": policy["threshold"], "minimum_margin": policy["minimum_margin"],
    }
    report = {
        "experiment_id": config["experiment_id"], "source_sha256": source_hash, "split_sha256": split_hash,
        "config_sha256": config_hash, "development_suite_sha256": baseline.sha(suite_bytes),
        "code_sha256": baseline.sha(Path(__file__).read_bytes()), "lock_sha256": baseline.sha(baseline.LOCK.read_bytes()),
        "reference_manifest_sha256": config["reference_manifest_sha256"],
        "python": sys.version.split()[0], "packages": packages, "training_documents": len(train),
        "validation_documents": len(validation), "short_development_cases": len(short_truth),
        "reference": reference_results, "candidates": results, "selected": winner, "test_scored": False,
    }
    for filename, value in ((MANIFEST_FILE, manifest), ("metrics.json", report)):
        (output / filename).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected": winner, "threshold": policy["threshold"], "minimum_margin": policy["minimum_margin"],
        "reference_utility": reference_results["policy"]["utility"], "candidate_utility": policy["utility"],
        "manifest_sha256": baseline.sha((output / MANIFEST_FILE).read_bytes()),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-model", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((baseline.ROOT / ".cache").resolve()) or not output.parent.is_dir():
        parser.error("Choose a new output directory in the ignored repository cache.")
    try:
        output.mkdir(exist_ok=False)
        run(output, args.reference_model)
    except (OSError, ValueError, KeyError, ConvergenceWarning):
        print("Short-text development run failed. Verify the input, dependencies and output path.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
