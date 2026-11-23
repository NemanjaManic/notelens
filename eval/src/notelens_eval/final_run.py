"""Evaluate checksum-pinned saved outputs after an explicit final freeze."""

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from pathlib import Path

from .acceptance import evaluate as evaluate_acceptance
from .annotations import SPECIALTIES, lint_submission
from .answer_risk import evaluate_answer_risk
from .classification import classification_metrics
from .retrieval_metrics import evaluate_retrieval, indexed_cases


COMPONENTS = {"extraction", "retrieval", "answer-risk", "classification"}


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate field in a frozen JSON artifact.")
        result[name] = value
    return result


def read_json(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)


def pinned_artifact(root, declaration):
    name, expected = declaration["path"], declaration["sha256"]
    if not isinstance(name, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Every frozen artifact requires a path and exact SHA-256.")
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Frozen artifacts must stay inside the approved bundle.")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("A frozen artifact differs from its approved SHA-256.")
    return read_json(raw)


def validate_references(references, development_groups, *, extraction=False):
    if (references.get("kind") != "permitted_benchmark"
            or references.get("partition") != "final"
            or references.get("human_reviewed") is not True):
        raise ValueError("Final references require explicit permitted, final and human-review declarations.")
    cases = references["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("A final reference component must contain cases.")
    indexed_cases(cases)
    for case in cases:
        group = case.get("group")
        if not isinstance(group, str) or not group.strip() or group in development_groups:
            raise ValueError("Final source groups must be declared and separate from development.")
        if extraction:
            document = case["request"]["document"]
            assignment = {
                "assignment_id": case["id"], "doc_id": document["doc_id"],
                "text_sha256": document["text_sha256"], "primary": "final-reference",
            }
            submission = {
                **assignment, "role": "primary", "annotator": "final-reference",
                "submission_id": case["id"], "complete_document_review": True,
                "entities": case["entities"], "unresolved_questions": [],
            }
            lint = lint_submission(assignment, document, submission)
            if lint["errors"] or lint["questions"]:
                raise ValueError("Final extraction references contain invalid or unresolved annotations.")
            questions = case["qa"]
            if questions:
                indexed_cases(questions)
            for question in questions:
                state = question["expected_evidence_state"]
                if (type(question["answerable"]) is not bool
                        or state not in {"sufficient", "partial", "insufficient"}
                        or (state == "insufficient") != (not question["answerable"])):
                    raise ValueError("Final question answerability and evidence-state references are inconsistent.")


def classification_report(report, expected_manifest):
    """Verify C's aggregate final evidence without opening its held-out texts."""
    if (report.get("version") != "d009-c008-owner-final-classification-evidence-v1"
            or report["source"]["published_frozen_model_manifest_sha256"] != expected_manifest):
        raise ValueError("Classification evidence differs from the frozen owner artifact.")
    matrix = report["forced_choice"]["confusion_matrix"]
    labels = report["forced_choice"]["labels"]
    if labels != list(SPECIALTIES) or len(matrix) != len(labels):
        raise ValueError("Final classification evidence requires the five frozen labels.")
    pairs = []
    for truth, row in zip(labels, matrix, strict=True):
        if len(row) != len(labels) or any(type(value) is not int or value < 0 for value in row):
            raise ValueError("Invalid final classification confusion matrix.")
        for predicted, count in zip(labels, row, strict=True):
            pairs.extend([(truth, predicted)] * count)
    if not pairs or len(pairs) != report["run"]["documents"]:
        raise ValueError("Classification matrix and document counts differ.")
    actual = classification_metrics(pairs)
    supplied = report["forced_choice"]
    if (actual["correct"] != supplied["correct"]
            or not math.isclose(actual["accuracy"], supplied["accuracy"], abs_tol=1e-8)
            or not math.isclose(actual["macro_f1"], supplied["macro_f1"], abs_tol=0.00005)):
        raise ValueError("Classification aggregates differ from the pinned matrix.")
    return {"label": "C-owned locked final classification evidence", "overall": actual,
            "model_manifest_sha256": expected_manifest, "source_run": report["run"]["id"]}


def execute(freeze_path: Path, expected_sha256: str, output_root: Path):
    """Score saved outputs, publish aggregate results atomically, and preserve inputs."""
    from .run import evaluate as evaluate_extraction

    freeze_path = freeze_path.resolve()
    raw = freeze_path.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("The final freeze differs from its approved SHA-256.")
    freeze = read_json(raw)
    if (freeze.get("version") != "notelens-final-evaluation-v1"
            or freeze.get("approved") is not True or freeze.get("partition") != "final"
            or freeze.get("execution") != "saved_outputs"):
        raise ValueError("An approved final freeze for saved-output scoring is required.")
    for field in ("approved_by", "scope", "reason"):
        if not isinstance(freeze.get(field), str) or not freeze[field].strip():
            raise ValueError("The final freeze requires a named approval, scope and reason.")
    run_id = freeze["run_id"]
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", run_id):
        raise ValueError("Invalid final run ID.")
    if set(freeze["components"]) != COMPONENTS:
        raise ValueError("The system final run requires extraction, retrieval, answer risk and classification evidence.")
    versions = freeze["system_versions"]
    if any(not isinstance(versions.get(name), str) or not versions[name].strip()
           for name in ("rag", "classifier", "extraction")):
        raise ValueError("Freeze the selected RAG, classifier and extraction versions.")
    root = freeze_path.parent
    development = pinned_artifact(root, freeze["development_groups"])
    groups = development["group_ids"]
    if not isinstance(groups, list) or not groups or any(not isinstance(group, str) or not group for group in groups):
        raise ValueError("The development-group exclusion artifact must be explicit and nonempty.")
    acceptance = pinned_artifact(root, freeze["acceptance"])
    # Claim this approved execution before opening final case/reference artifacts.
    receipt = root / f".final-{expected_sha256}.receipt"
    with receipt.open("x", encoding="ascii") as handle:
        handle.write(f"NoteLens saved-output final evaluation {run_id}\n")

    reports = {}
    sample_count = 0
    for name, declaration in freeze["components"].items():
        if name == "classification":
            reports[name] = classification_report(pinned_artifact(root, declaration["report"]), versions["classifier"])
            sample_count += reports[name]["overall"]["documents"]
            continue
        references = pinned_artifact(root, declaration["references"])
        predictions = pinned_artifact(root, declaration["predictions"])
        validate_references(references, set(groups), extraction=name == "extraction")
        if predictions.get("partition") != "final" or predictions.get("system_versions") != versions:
            raise ValueError("Saved predictions must identify the final partition and frozen system versions.")
        if name == "extraction":
            if declaration.get("mode") != "live":
                raise ValueError("Final provider evaluation requires explicitly live-mode saved outputs.")
            reports[name] = evaluate_extraction(references, predictions, expected_mode="live")
            reports[name]["label"] = "Frozen final extraction and document-answer scoring"
            reports[name]["reference_review_declared"] = True
            reports[name]["unavailable"].pop("real_model_performance", None)
        else:
            scorer = evaluate_retrieval if name == "retrieval" else evaluate_answer_risk
            reports[name] = scorer(references, predictions)
        sample_count += len(references["cases"])

    extraction = reports["extraction"]
    expected_records = extraction["counts"]["documents"] + extraction["counts"]["qa"]
    metrics = {
        "schema_validity": extraction["record_validation"]["schema_valid"] / expected_records,
        "span_validity": sum(extraction["valid_returned_records"].values()) / expected_records,
        "entity_exact_f1": extraction["entities_exact"].get("f1"),
        "topic_recall_at_5": reports["retrieval"]["overall"]["topic_recall_at_5"],
        "answer_risk": reports["answer-risk"]["overall"]["risk"],
    }
    if not set(metrics).issubset(acceptance["criteria"]):
        raise ValueError("Final acceptance requires the structural, extraction, retrieval and answer-risk criteria.")
    decision = evaluate_acceptance(acceptance, {
        "version": run_id, "acceptance_version": acceptance["version"],
        "sample_count": sample_count, "metrics": metrics,
    })
    report = {
        "version": "notelens-final-results-v1", "run_id": run_id,
        "freeze_sha256": expected_sha256, "system_versions": versions,
        "scope": freeze["scope"], "execution": "saved_outputs",
        "status": decision["status"], "acceptance": decision,
        "sample_count_unit": "Component case observations, including owner classification documents; source groups can be shared across components.",
        "components": reports, "new_provider_calls": 0,
        "scorer_source_sha256": {
            name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("final_run.py", "run.py", "metrics.py", "classification.py",
                         "retrieval_metrics.py", "answer_risk.py", "acceptance.py", "annotations.py")
        },
        "limitations": [
            "Scores existing frozen outputs and C's pinned aggregate classification evidence.",
            "Source support and English quality require the recorded human review; literal validity alone does not establish them.",
            "Project release and platform acceptance retain their named owner decisions.",
        ],
    }
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / run_id
    if target.exists():
        raise FileExistsError("The final run output already exists.")
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}-", dir=output_root))
    try:
        (temporary / "results.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        lines = ["# Frozen final evaluation", "", f"Run `{run_id}`. Status **{report['status']}**.", "",
                 f"Freeze SHA-256 `{expected_sha256}`.", "", "| Metric | Measured | Threshold | Status |",
                 "| --- | --- | --- | --- |"]
        for row in decision["criteria"]:
            lines.append(f"| {row['metric']} | {row['value']} | {row['threshold']} | {row['status']} |")
        lines.extend(["", "## Limits", "", *[f"- {item}" for item in report["limitations"]], ""])
        (temporary / "report.md").write_text("\n".join(lines), encoding="utf-8")
        os.rename(temporary, target)
    finally:
        if temporary.exists() and temporary.resolve().parent == output_root:
            shutil.rmtree(temporary)
    return report, target
