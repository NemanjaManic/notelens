"""Select an uncertainty policy for the frozen C-004 Logistic Regression model."""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, dataclass, replace
from itertools import product
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from notelens_classifier.inference import (
    LABELS, MANIFEST_FILE, MODEL_FILE, AmbiguityPolicy, accepted_category, load_model, word_evidence_index,
)
from notelens_classifier.training import draft_baseline as baseline, frozen_baseline
from notelens_classifier.training.compare_lexical_evidence import CONFIG as LEXICAL_CONFIG, development_examples, rank
from notelens_classifier.training.select_ambiguity_policy import FIXTURES, assess, observe, policy_prediction, summarize


CONFIG = baseline.CONFIG.with_name("c005-frozen-uncertainty-v1.json")


@dataclass(frozen=True)
class Decision:
    threshold: float
    minimum_margin: float
    ambiguity_policy: AmbiguityPolicy | None = None


def apply_score_gate(rows, threshold, margin):
    return [replace(row, reference=accepted_category(row.scores, row.reference is not None, threshold, margin))
            for row in rows]


def select_policies(documents, synthetic, config, phrase_features):
    methods = ("single_word", "two_words", "word_or_phrase") if phrase_features else ("single_word", "two_words")
    policies = {"score_only": [None]}
    for method in methods:
        policies[method] = [
            AmbiguityPolicy(**config["section_policy"], document_evidence_kind=method,
                            minimum_document_evidence=minimum)
            for minimum in config["minimum_document_evidence"]
        ]

    best, trials = {}, 0
    for threshold, margin in product(config["thresholds"], config["minimum_margins"]):
        admitted_documents = apply_score_gate(documents, threshold, margin)
        admitted_synthetic = apply_score_gate(synthetic, threshold, margin)
        for method, family in policies.items():
            for policy in family:
                result = assess(admitted_documents, admitted_synthetic, policy)
                trials += 1
                if method not in best or rank(result) > rank(best[method][1]):
                    best[method] = Decision(threshold, margin, policy), result
    winner = max(best, key=lambda method: rank(best[method][1]))
    return winner, best, trials


def validation_metrics(observations, groups, decision):
    admitted = apply_score_gate(observations, decision.threshold, decision.minimum_margin)
    truth = [row.expected for row in admitted]
    choices = [policy_prediction(row, decision.ambiguity_policy)[0] or "uncertain" for row in admitted]
    metrics = baseline.metrics(truth, choices, groups)
    columns = (*LABELS, "uncertain")
    counts = Counter(zip(truth, choices, strict=True))
    metrics["confusion_columns"] = columns
    metrics["confusion_matrix"] = [[counts[expected, predicted] for predicted in columns] for expected in LABELS]
    return metrics


def calibration(observations):
    """Summarize raw top-score reliability on the same validation cohort."""
    bins = [{"count": 0, "confidence_sum": 0.0, "correct": 0} for _ in range(10)]
    squared_error = 0.0
    for row in observations:
        confidence = max(row.scores)
        bucket = bins[min(9, int(confidence * 10))]
        bucket["count"] += 1
        bucket["confidence_sum"] += confidence
        bucket["correct"] += LABELS[row.scores.index(confidence)] == row.expected
        squared_error += sum((score - (label == row.expected)) ** 2
                             for label, score in zip(LABELS, row.scores, strict=True))
    count = len(observations)
    return {
        "top_label_ece_10_bins": sum(abs(item["confidence_sum"] - item["correct"]) for item in bins) / count,
        "multiclass_brier_sum": squared_error / count,
        "bins": [{"lower": index / 10, "upper": (index + 1) / 10, **item}
                 for index, item in enumerate(bins) if item["count"]],
    }


def follow_up_examples(suite):
    return (
        [(label, text) for label in LABELS for text in suite["specialties"][label]]
        + [(kind, text) for kind in ("unrelated", "ambiguous", "low_information") for text in suite[kind]]
    )


def run(reference, reference_pin, split_dir, split_pin, handoff, output):
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    reference_bytes = frozen_baseline.checked_bytes(reference / MANIFEST_FILE, reference_pin)
    reference_manifest = json.loads(reference_bytes)
    model = load_model(reference, reference_pin)
    if reference_manifest["estimator"] != "logistic_regression" or model.ambiguity_policy is not None:
        raise ValueError("Use the C-004 Logistic Regression bundle without an ambiguity policy.")
    if (min(config["thresholds"]) < model.threshold or min(config["minimum_margins"]) < model.minimum_margin):
        raise ValueError("The policy grid must preserve the reference observation floor.")
    parts, provenance = frozen_baseline.load_frozen_development(split_dir, split_pin, handoff)
    c004 = json.loads((reference / "metrics.json").read_bytes())
    if (c004["experiment_id"] != "c004-frozen-comparison-v1" or c004["test_scored"] is not False
            or any(c004.get(key) != value for key, value in provenance.items())):
        raise ValueError("C-004 metrics are not bound to this frozen development split.")

    lookup = word_evidence_index(model.pipeline)
    documents = observe(model, [(row[2], row[3]) for row in parts["validation"]], lookup)
    synthetic_examples, development_hashes = development_examples(json.loads(LEXICAL_CONFIG.read_bytes()))
    synthetic = observe(model, synthetic_examples, lookup)
    phrase_features = sum(map(len, lookup.phrases.values()))
    winner, best, trials = select_policies(documents, synthetic, config, phrase_features)
    selected, selected_results = best[winner]
    reference_decision = Decision(model.threshold, model.minimum_margin)
    reference_results = assess(documents, synthetic, None)

    # The fixed follow-up suite is scored only after the development choice.
    suite_bytes = (FIXTURES / config["follow_up_suite"]).read_bytes()
    follow_up = observe(model, follow_up_examples(json.loads(suite_bytes)), lookup)

    def follow_up_result(decision):
        gated = apply_score_gate(follow_up, decision.threshold, decision.minimum_margin)
        return summarize(gated, decision.ambiguity_policy)

    groups = [row[1] for row in parts["validation"]]
    policy_values = asdict(selected)
    if policy_values["ambiguity_policy"] is None:
        del policy_values["ambiguity_policy"]
    identity = baseline.sha(json.dumps([reference_pin, policy_values], sort_keys=True).encode("utf-8"))
    manifest = {**reference_manifest, **policy_values, "model_version": f"{config['experiment_id']}-{identity}"}
    raw_model = frozen_baseline.checked_bytes(reference / MODEL_FILE, manifest["artifact_sha256"])
    (output / MODEL_FILE).write_bytes(raw_model)
    manifest_sha256 = frozen_baseline.write_json(output / MANIFEST_FILE, manifest)
    report = {
        **provenance, "experiment_id": config["experiment_id"], "config_sha256": baseline.sha(config_bytes),
        "reference_manifest_sha256": reference_pin, "manifest_sha256": manifest_sha256,
        "grid_trials": trials, "development_suites": development_hashes, "development_synthetic_cases": len(synthetic),
        "follow_up_suite_sha256": baseline.sha(suite_bytes), "follow_up_cases": len(follow_up),
        "validation_documents": len(documents), "phrase_features": phrase_features, "selected_family": winner,
        "selected": policy_values, "reference": reference_results, "candidate": selected_results,
        "families": {name: {"decision": asdict(decision), "development": metrics,
                            "follow_up": follow_up_result(decision)}
                     for name, (decision, metrics) in best.items()},
        "reference_follow_up": follow_up_result(reference_decision),
        "validation_metrics": {
            "reference": validation_metrics(documents, groups, reference_decision),
            "selected": validation_metrics(documents, groups, selected),
        },
        "raw_validation_calibration": calibration(documents), "test_scored": False,
    }
    frozen_baseline.write_json(output / "metrics.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("reference-model", "split-dir", "handoff-dir", "output"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--reference-manifest-sha256", required=True)
    parser.add_argument("--split-sha256", required=True)
    args = parser.parse_args()
    cache = (baseline.ROOT / ".cache").resolve()
    raw = baseline.SOURCE.parent.resolve()
    reference, split_dir, handoff, output = [
        path.resolve() for path in (args.reference_model, args.split_dir, args.handoff_dir, args.output)
    ]
    if not reference.is_relative_to(cache) or not output.is_relative_to(cache) or output.exists():
        parser.error("Choose local model and new output directories inside the ignored cache.")
    if not all(path.is_relative_to(raw) for path in (split_dir, handoff)):
        parser.error("Use frozen inputs inside the ignored local MTSamples directory.")
    try:
        with TemporaryDirectory(dir=output.parent) as staging:
            pending = Path(staging) / output.name
            pending.mkdir()
            report = run(reference, args.reference_manifest_sha256.lower(), split_dir, args.split_sha256.lower(),
                         handoff, pending)
            pending.rename(output)
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        parser.exit(1, f"C-005 selection failed ({type(error).__name__}). Verify the frozen inputs.\n")
    print(json.dumps({key: report[key] for key in
                      ("selected_family", "selected", "manifest_sha256", "grid_trials", "test_scored")}))


if __name__ == "__main__":
    main()
