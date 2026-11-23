"""Exercise final-run control flow using synthetic unit-test approvals and outputs."""

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from notelens_eval.final_run import execute
from notelens_eval.run import EVAL_ROOT, produce


def write_json(path, value):
    raw = (json.dumps(value, indent=2) + "\n").encode()
    path.write_bytes(raw)
    return {"path": path.name, "sha256": hashlib.sha256(raw).hexdigest()}


def live_fixture(value):
    if isinstance(value, dict):
        if value.get("mode") == "mock":
            value["mode"] = "live"
        for child in value.values():
            live_fixture(child)
    elif isinstance(value, list):
        for child in value:
            live_fixture(child)


@pytest.fixture
def bundle(tmp_path):
    owner = json.loads((EVAL_ROOT / "reports/final/c008-owner-classification-evidence-v1.json").read_bytes())
    versions = {"rag": "synthetic-test-rag", "classifier": owner["source"]["published_frozen_model_manifest_sha256"],
                "extraction": "synthetic-test-extraction"}
    references = json.loads((EVAL_ROOT / "fixtures/smoke-references.json").read_bytes())
    predictions = produce(references)
    references.update(kind="permitted_benchmark", partition="final", human_reviewed=True)
    for case in references["cases"]:
        case["group"] = "synthetic-final-test-group"
        text = case["request"]["document"]["text"]
        for entity in case["entities"]:
            entity.setdefault("procedure_status", "performed" if entity["type"] == "procedure" else None)
            entity["evidence"] = [{"start": 0, "end": len(text), "quote": text}]
    live_fixture(predictions)
    predictions.update(partition="final", system_versions=versions)
    retrieval = {"version": "synthetic-test-references", "kind": "permitted_benchmark", "partition": "final",
                 "human_reviewed": True, "cases": [{"id": "retrieval-case", "group": "synthetic-final-test-group",
                     "required_topic_ids": ["topic"], "required_passage_groups": [["passage"]], "source_scope": "single"}]}
    ranked = {"version": "synthetic-test-output", "partition": "final", "system_versions": versions,
              "cases": [{"id": "retrieval-case", "ranked_passages": [{"topic_id": "topic", "passage_id": "passage"}]}]}
    risk = {"version": "synthetic-test-review", "kind": "permitted_benchmark", "partition": "final",
            "human_reviewed": True, "cases": [{"id": "answer-case", "group": "synthetic-final-test-group",
                                                "answerable": True, "answer_correct": True}]}
    answered = {"version": "synthetic-test-output", "partition": "final", "system_versions": versions,
                "cases": [{"id": "answer-case", "outcome": "answered", "confidence": None}]}
    acceptance = json.loads((EVAL_ROOT / "config/acceptance.json").read_bytes())
    for row in acceptance["criteria"].values():
        if row["kind"] == "quality":
            row.update(threshold=1 if row["direction"] == "maximum" else 0,
                       decision_by="synthetic unit test", decision_record="synthetic test decision")
    freeze = {
        "version": "notelens-final-evaluation-v1", "approved": True, "partition": "final",
        "approved_by": "synthetic unit test", "scope": "Synthetic control-flow regression only",
        "reason": "No actual final examples or real provider outputs are used by this unit test.",
        "run_id": "synthetic-test-run", "execution": "saved_outputs", "system_versions": versions,
        "development_groups": write_json(tmp_path / "development.json", {"group_ids": ["synthetic-development-group"]}),
        "acceptance": write_json(tmp_path / "acceptance.json", acceptance),
        "components": {
            "extraction": {"mode": "live", "references": write_json(tmp_path / "extraction-references.json", references),
                           "predictions": write_json(tmp_path / "extraction-predictions.json", predictions)},
            "retrieval": {"references": write_json(tmp_path / "retrieval-references.json", retrieval),
                          "predictions": write_json(tmp_path / "retrieval-predictions.json", ranked)},
            "answer-risk": {"references": write_json(tmp_path / "risk-references.json", risk),
                            "predictions": write_json(tmp_path / "risk-predictions.json", answered)},
            "classification": {"report": write_json(tmp_path / "classification.json", owner)},
        },
    }
    path = tmp_path / "freeze.json"

    def save():
        return write_json(path, freeze)["sha256"]

    return path, freeze, save


def test_final_cli_scores_pinned_saved_outputs_without_provider_calls(bundle, tmp_path):
    path, freeze, save = bundle
    pin = save()
    result = subprocess.run([sys.executable, "-B", "-m", "notelens_eval.run", "--profile", "final",
                             "--require-freeze", "--freeze", str(path), "--freeze-sha256", pin,
                             "--output", str(tmp_path / "output")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    target = tmp_path / "output" / freeze["run_id"]
    report = json.loads((target / "results.json").read_bytes())
    assert report["status"] == "passed" and report["new_provider_calls"] == 0
    assert report["components"]["classification"]["overall"]["documents"] == 183
    assert (target / "report.md").exists()
    assert "The patient" not in (target / "report.md").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        execute(path, pin, tmp_path / "second-output")


@pytest.mark.parametrize("change", ["unapproved", "bad-freeze-hash", "changed-artifact", "development-overlap", "wrong-version", "missing-component"])
def test_final_run_rejects_unfrozen_or_inconsistent_input(bundle, tmp_path, change):
    path, freeze, save = bundle
    if change == "unapproved":
        freeze["approved"] = False
    elif change == "missing-component":
        del freeze["components"]["answer-risk"]
    elif change == "development-overlap":
        freeze["development_groups"] = write_json(tmp_path / "development.json", {"group_ids": ["synthetic-final-test-group"]})
    elif change == "wrong-version":
        freeze["system_versions"]["rag"] = "different-rag"
    pin = save()
    if change == "bad-freeze-hash":
        pin = "0" * 64
    if change == "changed-artifact":
        (tmp_path / "retrieval-predictions.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        execute(path, pin, tmp_path / "output")
    assert not (tmp_path / "output" / freeze["run_id"]).exists()


def test_pending_thresholds_remain_pending(bundle, tmp_path):
    path, freeze, save = bundle
    config = json.loads((tmp_path / "acceptance.json").read_bytes())
    config["criteria"]["entity_exact_f1"]["threshold"] = None
    freeze["acceptance"] = write_json(tmp_path / "acceptance.json", config)
    report, target = execute(path, save(), tmp_path / "output")
    assert report["status"] == "pending"
    assert target.is_dir()


def test_parallel_final_attempts_claim_one_receipt(bundle, tmp_path):
    path, freeze, save = bundle
    pin = save()

    def attempt(_index):
        try:
            execute(path, pin, tmp_path / "output")
            return True
        except FileExistsError:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sum(executor.map(attempt, range(2))) == 1
