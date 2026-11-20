"""Compare document evidence signals with the existing model and section policy."""

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys

from notelens_classifier.inference import LABELS, MANIFEST_FILE, MODEL_FILE, load_model, word_evidence_index
from notelens_classifier.training import draft_baseline as baseline
from notelens_classifier.training.select_ambiguity_policy import FIXTURES, assess, observe


CONFIG = baseline.CONFIG.with_name("lexical-evidence-v1.json")


def development_examples(config):
    examples, hashes = [], {}
    for name, low_indexes in config["development_low_information_cases"].items():
        raw = (FIXTURES / name).read_bytes()
        suite = json.loads(raw)
        hashes[name] = baseline.sha(raw)
        examples.extend((label, text) for label in LABELS for text in suite["specialties"][label])
        examples.extend(("unrelated", text) for text in suite["unrelated"])
        examples.extend(
            ("low_information" if index in low_indexes else "ambiguous", text)
            for index, text in enumerate(suite["ambiguous"], start=1)
        )
    return examples, hashes


def rank(result):
    synthetic = result["synthetic"]
    inappropriate = synthetic["low_information_accepted"] + synthetic["ambiguous_accepted"] + synthetic["unrelated_accepted"]
    return result["utility"], -inappropriate, synthetic["specialties"]["coverage"]


def run(reference, output):
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    model = load_model(reference, config["reference_manifest_sha256"])
    if model.ambiguity_policy is None:
        raise ValueError("The reference bundle must contain the section policy.")
    lookup = word_evidence_index(model.pipeline)
    parts, source_sha256, split_sha256 = baseline.load_provisional_data()
    documents = [(row[2], baseline.prepare_training_text(row[3])) for row in parts["validation"]]
    short, suite_hashes = development_examples(config)
    full_observed, short_observed = observe(model, documents, lookup), observe(model, short, lookup)
    reference_results = assess(full_observed, short_observed, model.ambiguity_policy)

    raw_manifest = (reference / MANIFEST_FILE).read_bytes()
    payload = json.loads(raw_manifest)
    raw_model = (reference / MODEL_FILE).read_bytes()
    if (baseline.sha(raw_manifest) != config["reference_manifest_sha256"]
            or baseline.sha(raw_model) != payload["artifact_sha256"]):
        raise ValueError("The reference manifest or model changed.")
    candidates = {}
    for method in config["methods"]:
        trials = []
        for minimum in config["minimum_support"]:
            policy = replace(model.ambiguity_policy, document_evidence_kind=method, minimum_document_evidence=minimum)
            trials.append((policy, assess(full_observed, short_observed, policy)))
        policy, result = max(trials, key=lambda trial: rank(trial[1]))
        policy_record = asdict(policy)
        identity = baseline.sha(json.dumps([config["reference_manifest_sha256"], policy_record]).encode())
        manifest = {**payload, "model_version": f"{config['experiment_id']}-{identity}", "ambiguity_policy": policy_record}
        candidate_dir = output / method
        candidate_dir.mkdir()
        (candidate_dir / MODEL_FILE).write_bytes(raw_model)
        manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
        (candidate_dir / MANIFEST_FILE).write_bytes(manifest_bytes)
        candidates[method] = {**result, "minimum_support": policy.document_minimum,
                              "manifest_sha256": baseline.sha(manifest_bytes)}

    selected = max(candidates, key=lambda method: rank(candidates[method]))
    improved = rank(candidates[selected]) > rank(reference_results)
    report = {
        "experiment_id": config["experiment_id"], "source_sha256": source_sha256, "split_sha256": split_sha256,
        "config_sha256": baseline.sha(config_bytes), "reference_manifest_sha256": config["reference_manifest_sha256"],
        "code_sha256": baseline.sha(Path(__file__).read_bytes()), "development_suites": suite_hashes,
        "validation_documents": len(documents), "synthetic_cases": len(short), "reference": reference_results,
        "candidates": candidates, "selected_on_development": selected,
        "improved_development_objective": improved, "test_scored": False,
    }
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {"minimum": values["minimum_support"], "utility": values["utility"],
                             "manifest_sha256": values["manifest_sha256"]} for name, values in candidates.items()},
                     indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((baseline.ROOT / ".cache").resolve()) or not output.parent.is_dir():
        parser.error("Choose a new output directory in the ignored repository cache.")
    try:
        output.mkdir(exist_ok=False)
        run(args.reference_model, output)
    except (OSError, ValueError, KeyError):
        print("Lexical evidence comparison failed. Verify the audited inputs and reference bundle.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
