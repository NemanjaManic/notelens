"""Score C-003 validation predictions against the checksum-pinned C-002 handoff."""

import math
import re
from collections import Counter
from pathlib import Path

from .annotations import SPECIALTIES, candidate_groups, read_source_manifest


EXPORT_VERSION = "c003-d006-validation-v1"
POLICY = "forced_choice"
SCORE_TYPE = "logistic_regression_probability"


def classification_metrics(pairs: list[tuple[str, str]]) -> dict:
    counts = Counter(pairs)
    matrix = {truth: {prediction: counts[truth, prediction] for prediction in SPECIALTIES}
              for truth in SPECIALTIES}
    per_class = {}
    for label in SPECIALTIES:
        tp = matrix[label][label]
        support = sum(matrix[label].values())
        predicted = sum(matrix[truth][label] for truth in SPECIALTIES)
        per_class[label] = {
            "support": support, "predicted": predicted, "true_positives": tp,
            "precision": tp / predicted if predicted else 0.0,
            "recall": tp / support if support else 0.0,
            "f1": 2 * tp / (support + predicted) if support + predicted else 0.0,
        }
    correct = sum(matrix[label][label] for label in SPECIALTIES)
    return {"documents": len(pairs), "correct": correct, "accuracy": correct / len(pairs),
            "macro_f1": sum(row["f1"] for row in per_class.values()) / len(SPECIALTIES),
            "per_class": per_class, "confusion_matrix": matrix}


def evaluate_classification(prediction_path: Path, checksum_path: Path, manifest_path: Path) -> dict:
    checksum = checksum_path.read_text(encoding="ascii").strip()
    match = re.fullmatch(r"([0-9a-fA-F]{64})(?:[ \t]+\*?([^\r\n]+))?", checksum)
    if match is None or match[2] not in (None, prediction_path.name):
        raise ValueError("The SHA-256 sidecar must identify the supplied prediction file.")
    export, export_sha256 = read_source_manifest(prediction_path, expected_sha256=None, source_version=None)
    if export_sha256 != match[1].lower():
        raise ValueError("The prediction file does not match its SHA-256 sidecar.")
    if (export.get("export_version"), export.get("decision_policy"), export.get("score_type")) != (
        EXPORT_VERSION, POLICY, SCORE_TYPE
    ):
        raise ValueError("Expected the C-003 validation export with forced-choice probabilities.")

    versions = {key: export.get(key) for key in (
        "model_version", "preparation_version", "split_version", "handoff_version"
    )}
    if any(not isinstance(version, str) or not version.strip() for version in versions.values()):
        raise ValueError("The export must declare model, preparation, split and handoff versions.")
    handoff_sha256 = export.get("handoff_checksum")
    if not isinstance(handoff_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", handoff_sha256):
        raise ValueError("The export must pin the C-002 handoff checksum.")
    manifest, manifest_sha256 = read_source_manifest(
        manifest_path, expected_sha256=handoff_sha256, source_version=versions["handoff_version"])
    split_sha256 = export.get("split_checksum")
    if not isinstance(split_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", split_sha256):
        raise ValueError("The export must declare a valid split checksum.")
    if (manifest.get("kind"), manifest.get("canonicalization_version"), manifest.get("split_manifest_version"),
        manifest.get("split_manifest_sha256")) != (
        "permitted_benchmark", versions["preparation_version"], versions["split_version"], split_sha256
    ):
        raise ValueError("The export and manifest disagree on preparation or split provenance.")
    groups = candidate_groups(manifest)
    references = {row["doc_id"]: row for row in manifest["documents"]}
    if not references or any(row["split"] != "validation" for row in references.values()):
        raise ValueError("Classification replay requires validation-only references.")
    support = Counter(row["specialty"] for row in references.values())
    if support.keys() != set(SPECIALTIES):
        raise ValueError("Validation references must cover all five specialties.")

    documents = export.get("documents")
    if not isinstance(documents, list):
        raise ValueError("Prediction documents must be an array.")
    seen = set()
    pairs = []
    for row in documents:
        if not isinstance(row, dict) or not isinstance(row.get("doc_id"), str):
            raise ValueError("Each prediction must declare a document ID.")
        doc_id = row["doc_id"]
        if doc_id in seen or doc_id not in references:
            raise ValueError("Prediction document IDs must be unique and present in the manifest.")
        seen.add(doc_id)
        truth = references[doc_id]["specialty"]
        if row.get("true_specialty") != truth:
            raise ValueError("Exported labels disagree with the validation manifest.")
        if row.get("status") != POLICY or any(row.get(key) != versions[key] for key in (
            "model_version", "preparation_version", "split_version"
        )):
            raise ValueError("Prediction rows disagree with the declared policy or versions.")
        scores = row.get("scores")
        if (not isinstance(scores, dict) or scores.keys() != support.keys() or any(
            type(score) not in (int, float) or not 0 <= score <= 1 for score in scores.values()
        ) or not math.isclose(math.fsum(scores.values()), 1, rel_tol=0, abs_tol=1e-6)):
            raise ValueError("Each prediction needs normalized probabilities for the five specialties.")
        predicted = row.get("predicted_specialty")
        if predicted not in SPECIALTIES or scores[predicted] != max(scores.values()):
            raise ValueError("The forced-choice label must have a maximum probability.")
        pairs.append((truth, predicted))
    if seen != references.keys():
        raise ValueError("Prediction IDs must cover the entire validation manifest.")

    majority = max(SPECIALTIES, key=support.__getitem__)
    return {
        "label": "offline C-003 validation classification",
        "provenance": {**versions, "export_version": EXPORT_VERSION, "split_checksum": split_sha256,
                       "export_sha256": export_sha256, "handoff_checksum": manifest_sha256,
                       "decision_policy": POLICY, "score_type": SCORE_TYPE},
        "overall": {**classification_metrics(pairs), "coverage": 1.0},
        "validation_majority_baseline": {
            "specialty": majority, "selection": "Most frequent validation label; ties use contract label order.",
            **classification_metrics([(truth, majority) for truth, _ in pairs]),
        },
        "split_integrity": {
            "validation_documents": len(references), "validation_groups": len(groups),
            "unique_validation_canonical_hashes": len({row["text_sha256"] for row in references.values()}),
            "cross_split_leakage": "Unverified: full training and test group membership was unavailable.",
            "training_fitted_baseline": "Unavailable: training label counts or baseline predictions were not supplied.",
        },
    }
