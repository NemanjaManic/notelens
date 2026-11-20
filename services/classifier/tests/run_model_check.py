"""Measure a trusted development classifier on hand-written synthetic examples."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from fastapi.testclient import TestClient
from notelens_contracts.v1 import validate_record

from conftest import REQUEST_ID, prepared
from notelens_classifier.inference import LABELS, load_model
from notelens_classifier.main import Settings, create_app
from notelens_classifier.training.draft_baseline import metrics, selective_summary


DEFAULT_SUITE = Path(__file__).with_name("fixtures") / "model-check-short-v1.json"


def evaluate(model, suite):
    token = "synthetic-development-check"
    headers = {"Authorization": "Bearer " + token, "X-Request-ID": REQUEST_ID}
    app = create_app(Settings(mode="live", token=token), model=model)
    examples = [(label, text) for label in LABELS for text in suite["specialties"][label]]
    examples += [("unrelated", text) for text in suite["unrelated"]]
    examples += [("ambiguous", text) for text in suite["ambiguous"]]
    examples += [("low_information", text) for text in suite.get("low_information", ())]
    cases = []
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        ready = client.get("/health/ready", headers=headers)
        assert ready.status_code == 200
        assert validate_record("HealthResult", ready.json())["model_version"] == model.model_version
        for index, (expected, text) in enumerate(examples, start=1):
            document_id = f"synthetic-model-check-{index:02}"
            document = prepared(text, document_id)
            body = {"schema_version": "1.0.0", "document": document}
            result = client.post("/v1/classify", json=body, headers=headers)
            repeat = client.post("/v1/classify", json=body, headers=headers)
            assert result.status_code == repeat.status_code == 200
            assert result.headers["X-Request-ID"] == repeat.headers["X-Request-ID"] == REQUEST_ID
            assert result.headers["Cache-Control"] == "no-store"
            record = validate_record("ClassificationResult", result.json(), document=document)
            assert record == repeat.json()
            assert record["mode"] == "live" and record["model_version"] == model.model_version
            assert record["classification_execution"] == "performed"
            top = max(record["scores"], key=lambda score: score["score"])
            cases.append({
                "id": document_id, "expected": expected, "status": record["status"],
                "category": record["category"], "top_category": top["category"], "top_score": top["score"],
            })
    supported = [case for case in cases if case["expected"] in LABELS]
    truth = [case["expected"] for case in supported]
    return {
        "model_version": model.model_version,
        "threshold": model.threshold,
        "minimum_margin": model.minimum_margin,
        "contract_checked": len(cases),
        "repeat_checked": len(cases),
        "specialty_forced_choice": metrics(
            truth, [case["top_category"] for case in supported], [case["id"] for case in supported]
        ),
        "specialty_selective": selective_summary(truth, [case["category"] for case in supported]),
        "unrelated_accepted": sum(case["category"] is not None for case in cases if case["expected"] == "unrelated"),
        "ambiguous_accepted": sum(case["category"] is not None for case in cases if case["expected"] == "ambiguous"),
        "low_information_accepted": sum(
            case["category"] is not None for case in cases if case["expected"] == "low_information"
        ),
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-model", required=True, type=Path)
    parser.add_argument("--model-manifest-sha256", required=True)
    parser.add_argument("--suite-file", type=Path, default=DEFAULT_SUITE)
    args = parser.parse_args()
    suite_bytes = args.suite_file.read_bytes()
    model = load_model(args.development_model, args.model_manifest_sha256)
    report = evaluate(model, json.loads(suite_bytes))
    report["model_manifest_sha256"] = args.model_manifest_sha256
    report["check_source_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    report["suite_sha256"] = sha256(suite_bytes).hexdigest()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
