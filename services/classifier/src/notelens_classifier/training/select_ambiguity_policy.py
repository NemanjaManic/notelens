"""Select an ambiguity policy for the pinned local classifier without refitting it."""

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import product
import json
from pathlib import Path
import sys

from notelens_classifier.inference import (
    LABELS, MANIFEST_FILE, MODEL_FILE, AmbiguityPolicy, LexicalEvidence, SectionPrediction,
    accepted_category, lexical_evidence, load_model, score_rows, score_sections, word_evidence_index,
)
from notelens_classifier.training import draft_baseline as baseline


CONFIG = baseline.CONFIG.with_name("ambiguity-policy-v1.json")
FIXTURES = baseline.ROOT / "services/classifier/tests/fixtures"
DEVELOPMENT_SUITES = ("model-check-short-v1.json", "model-check-short-v2.json")


@dataclass(frozen=True)
class Observation:
    expected: str
    reference: str | None
    scores: tuple[float, ...]
    lexical_evidence: LexicalEvidence
    sections: list[SectionPrediction]
    word_count: int


def observe(model, examples, lookup):
    labels, texts = zip(*examples, strict=True)
    features = model.pipeline.named_steps["tfidf"].transform(texts).tocsr()
    scores = score_rows(model.pipeline.named_steps["classifier"], features)
    observed = []
    for index, (expected, text, probabilities) in enumerate(zip(labels, texts, scores, strict=True)):
        row = features[index]
        predicted = accepted_category(probabilities, bool(row.nnz), model.threshold, model.minimum_margin)
        if predicted:
            evidence = lexical_evidence(row, predicted, lookup)
            sections = score_sections(model.pipeline, text, lookup)
            observed.append(Observation(expected, predicted, probabilities, evidence, sections, len(text.split())))
        else:
            observed.append(Observation(expected, None, probabilities, LexicalEvidence(), [], 0))
    return observed


def summarize(observations, policy):
    actual, predicted = [], []
    reasons = Counter()
    unrelated_accepted = ambiguous_accepted = low_information_accepted = 0
    for row in observations:
        category = row.reference
        if category and policy:
            strength = getattr(row.lexical_evidence, policy.document_evidence_kind)
            reason = policy.abstention_reason(strength, row.scores, row.sections, row.word_count)
            if reason:
                reasons[reason] += 1
                category = None
        if row.expected in LABELS:
            actual.append(row.expected)
            predicted.append(category)
        elif category:
            unrelated_accepted += row.expected == "unrelated"
            ambiguous_accepted += row.expected == "ambiguous"
            low_information_accepted += row.expected == "low_information"
    specialties = baseline.selective_summary(actual, predicted)
    net_correct = (specialties["correct"] - specialties["incorrect"] - unrelated_accepted
                   - ambiguous_accepted - low_information_accepted)
    return {
        "specialties": specialties,
        "unrelated_accepted": unrelated_accepted,
        "ambiguous_accepted": ambiguous_accepted,
        "low_information_accepted": low_information_accepted,
        "policy_abstentions": dict(reasons),
        "utility": net_correct / len(observations),
    }


def assess(documents, short, policy):
    full = summarize(documents, policy)
    synthetic = summarize(short, policy)
    return {"documents": full, "synthetic": synthetic, "utility": (full["utility"] + synthetic["utility"]) / 2}


def run(reference, output):
    config_bytes = CONFIG.read_bytes()
    config = json.loads(config_bytes)
    model = load_model(reference, config["reference_manifest_sha256"])
    lookup = word_evidence_index(model.pipeline)
    parts, source_hash, split_hash = baseline.load_provisional_data()
    documents = [(row[2], baseline.prepare_training_text(row[3])) for row in parts["validation"]]
    short = []
    suite_hashes = {}
    for name in DEVELOPMENT_SUITES:
        raw = (FIXTURES / name).read_bytes()
        suite_hashes[name] = baseline.sha(raw)
        suite = json.loads(raw)
        short.extend((label, text) for label in LABELS for text in suite["specialties"][label])
        short.extend(("unrelated", text) for text in suite["unrelated"])
        short.extend(("ambiguous", text) for text in suite["ambiguous"])
    full_observed, short_observed = observe(model, documents, lookup), observe(model, short, lookup)
    reference_scores = assess(full_observed, short_observed, None)

    trials = []
    for params in product(config["minimum_word_evidence"], config["segment_thresholds"], config["segment_margins"],
                          config["competing_score_ratios"], config["minimum_section_shares"]):
        policy = AmbiguityPolicy(*params)
        results = assess(full_observed, short_observed, policy)
        trials.append((policy, results))
    selected, results = max(trials, key=lambda trial: (
        trial[1]["utility"], -trial[1]["synthetic"]["ambiguous_accepted"], trial[1]["documents"]["specialties"]["correct"]
    ))
    if results["utility"] <= reference_scores["utility"]:
        raise ValueError("No policy improved the development objective.")

    reference_manifest = (reference / MANIFEST_FILE).read_bytes()
    if baseline.sha(reference_manifest) != config["reference_manifest_sha256"]:
        raise ValueError("Reference manifest checksum mismatch.")
    manifest = json.loads(reference_manifest)
    raw_model = (reference / MODEL_FILE).read_bytes()
    if baseline.sha(raw_model) != manifest["artifact_sha256"]:
        raise ValueError("Reference model checksum mismatch.")
    policy_config = asdict(selected)
    version_hash = baseline.sha(json.dumps([config["reference_manifest_sha256"], policy_config]).encode())
    manifest.update(model_version=f"{config['experiment_id']}-{version_hash}", ambiguity_policy=policy_config)
    (output / MODEL_FILE).write_bytes(raw_model)
    (output / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_hash = baseline.sha((output / MANIFEST_FILE).read_bytes())
    metrics = {
        "source_sha256": source_hash, "split_sha256": split_hash, "config_sha256": baseline.sha(config_bytes),
        "reference_manifest_sha256": config["reference_manifest_sha256"], "manifest_sha256": manifest_hash,
        "development_suites": suite_hashes, "validation_documents": len(documents), "short_cases": len(short),
        "grid_size": len(trials), "selected": policy_config, "reference": reference_scores, "candidate": results,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest_sha256": manifest_hash, "selected": policy_config,
                      "reference_utility": reference_scores["utility"], "candidate_utility": results["utility"]}, indent=2))


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
        print("Ambiguity policy selection failed. Verify the audited input and reference model.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
