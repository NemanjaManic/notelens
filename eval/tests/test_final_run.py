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


def limited_qa_bundle(bundle, tmp_path):
    """Synthetic setup only; no real final answers or human ratings."""
    path, freeze, save = bundle
    refs = json.loads((tmp_path / "extraction-references.json").read_bytes())
    preds = json.loads((tmp_path / "extraction-predictions.json").read_bytes())
    case, prediction = refs["cases"][0], preds["cases"][0]
    question, answer = case["qa"][0], prediction["qa"][0]
    qa_refs = {"version": "synthetic-final-qa", "kind": "permitted_benchmark", "partition": "final",
               "human_reviewed": True, "cases": [{"id": "qa-final", "case_version": "v1",
                   "group": "synthetic-final-test-group", "document": case["request"]["document"],
                   "expected_evidence_state": question["expected_evidence_state"]}]}
    qa_preds = {"version": "synthetic-saved-qa", "partition": "final", "system_versions": freeze["system_versions"],
                "cases": [{"id": "qa-final", "case_version": "v1", "result": answer["result"]}]}
    freeze["components"]["extraction"] = {"status": "unmeasured", "reason": "No final entity annotations supplied.",
        "approved_by": "synthetic unit test", "decision_record": "synthetic unmeasured decision"}
    freeze["components"]["answer-risk"] = {"status": "unmeasured", "reason": "No independent correctness labels supplied.",
        "approved_by": "synthetic unit test", "decision_record": "synthetic unmeasured decision"}
    freeze["components"]["qa"] = {
        "references": write_json(tmp_path / "qa-references.json", qa_refs),
        "predictions": write_json(tmp_path / "qa-predictions.json", qa_preds)}
    return path, freeze, save, qa_refs, qa_preds


def test_approved_unmeasured_f1_and_risk_do_not_create_dummy_scores(bundle, tmp_path):
    path, freeze, save, _refs, _preds = limited_qa_bundle(bundle, tmp_path)
    report, _ = execute(path, save(), tmp_path / "output")
    assert report["status"] == "pending"
    criteria = {row["metric"]: row for row in report["acceptance"]["criteria"]}
    assert criteria["entity_exact_f1"]["value"] is None
    assert criteria["answer_risk"]["value"] is None
    assert criteria["entity_exact_f1"]["status"] == "measurement_missing"
    assert report["components"]["qa"]["schema_validity"] == 1
    assert report["components"]["qa"]["span_validity"] == 1
    assert report["explicitly_unmeasured_components"] == ["answer-risk", "extraction"]


@pytest.mark.parametrize("problem", ["no-decision", "dummy-inputs", "no-qa", "wrong-case-version", "mock-output", "wrong-case-id"])
def test_limited_final_scope_still_rejects_unapproved_or_mismatched_artifacts(bundle, tmp_path, problem):
    path, freeze, save, refs, preds = limited_qa_bundle(bundle, tmp_path)
    if problem == "no-decision":
        freeze["components"]["extraction"]["decision_record"] = ""
    elif problem == "dummy-inputs":
        freeze["components"]["extraction"]["references"] = {"path": "dummy.json", "sha256": "0" * 64}
    elif problem == "no-qa":
        del freeze["components"]["qa"]
    elif problem == "wrong-case-version":
        preds["cases"][0]["case_version"] = "v2"
    elif problem == "wrong-case-id":
        preds["cases"][0]["id"] = "other-case"
    else:
        preds["cases"][0]["result"]["mode"] = "mock"
    if problem in {"wrong-case-version", "wrong-case-id", "mock-output"}:
        freeze["components"]["qa"]["predictions"] = write_json(tmp_path / "qa-predictions.json", preds)
    with pytest.raises(ValueError):
        execute(path, save(), tmp_path / "output")


def test_limited_final_technical_failure_is_not_a_correct_abstention(bundle, tmp_path):
    path, freeze, save, _refs, preds = limited_qa_bundle(bundle, tmp_path)
    preds["cases"][0]["result"] = None
    preds["cases"][0]["error"] = "provider_timeout"
    freeze["components"]["qa"]["predictions"] = write_json(tmp_path / "qa-predictions.json", preds)
    report, _ = execute(path, save(), tmp_path / "output")
    assert report["status"] == "failed"
    assert report["components"]["qa"]["counts"]["technical_errors"] == 1
    assert report["components"]["qa"]["schema_validity"] == 0
    assert report["components"]["answer-risk"]["status"] == "unmeasured"


def test_unmeasured_scope_does_not_waive_retrieval(bundle, tmp_path):
    path, freeze, save, _refs, _preds = limited_qa_bundle(bundle, tmp_path)
    freeze["components"]["retrieval"] = {"status": "unmeasured", "reason": "Test attempts an unapproved scope waiver.",
        "approved_by": "synthetic unit test", "decision_record": "not an authorized component waiver"}
    with pytest.raises(ValueError, match="Only approved missing extraction labels"):
        execute(path, save(), tmp_path / "output")


def test_limited_final_invalid_literal_quote_cannot_pass_structural_gate(bundle, tmp_path):
    path, freeze, save, _refs, preds = limited_qa_bundle(bundle, tmp_path)
    result = preds["cases"][0]["result"]
    result["sources"][0]["evidence"]["quote"] = "Invented quote absent from the canonical document."
    freeze["components"]["qa"]["predictions"] = write_json(tmp_path / "qa-predictions.json", preds)
    report, _ = execute(path, save(), tmp_path / "output")
    assert report["status"] == "failed"
    assert report["components"]["qa"]["span_validity"] == 0


def test_qa_only_component_cannot_mask_measured_extraction_failures(bundle, tmp_path):
    path, freeze, save = bundle
    measured = dict(freeze["components"]["extraction"])
    limited_qa_bundle(bundle, tmp_path)
    freeze["components"]["extraction"] = measured
    with pytest.raises(ValueError, match="cannot mask extraction errors"):
        execute(path, save(), tmp_path / "output")


def test_qa_component_requires_nonempty_case_inventory(bundle, tmp_path):
    path, freeze, save, refs, preds = limited_qa_bundle(bundle, tmp_path)
    refs["cases"], preds["cases"] = [], []
    freeze["components"]["qa"] = {
        "references": write_json(tmp_path / "qa-references.json", refs),
        "predictions": write_json(tmp_path / "qa-predictions.json", preds)}
    with pytest.raises(ValueError):
        execute(path, save(), tmp_path / "output")
