"""F-004 scaffold consumer evidence; this does not close the later C-009 gate."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from notelens_contracts.v1 import ContractValidationError, validate_record

from notelens_classifier.main import Settings, create_app
from conftest import REQUEST_ID

LABELS = ["Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology", "Neurology", "Urology"]


@pytest.mark.parametrize("scenario,fixture", [
    ("supported", "classification-supported"),
    ("uncertain", "classification-uncertain"),
    ("unsupported_skipped", "classification-unsupported"),
    ("unsupported_performed", "classification-unsupported-performed"),
])
def test_scenarios_match_frozen_examples_and_actual_identity(scenario, fixture, body, shared_payloads):
    before = deepcopy(body)
    with TestClient(create_app(Settings(mode="mock", scenario=scenario)),
                    base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        response = client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID})
    assert response.status_code == 200
    result = validate_record("ClassificationResult", response.json(), document=body["document"])
    expected = deepcopy(shared_payloads[fixture])
    expected.update(doc_id=body["document"]["doc_id"], text_sha256=body["document"]["text_sha256"])
    assert result == expected
    assert body == before
    assert result["mode"] == "mock"
    if scenario == "unsupported_skipped":
        assert result["scores"] == []
        assert result["model_version"] is None and result["score_kind"] is None
    else:
        assert [entry["category"] for entry in result["scores"]] == LABELS


@pytest.mark.parametrize("fixture", ["classification-supported", "classification-probability"])
@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_installed_bindings_reject_native_nonfinite_scores(shared_payloads, fixture, number):
    payload = deepcopy(shared_payloads[fixture])
    payload["scores"][0]["score"] = number
    with pytest.raises(ContractValidationError) as error:
        validate_record("ClassificationResult", payload)
    assert [(item.rule, item.path) for item in error.value.issues] == [("NUMBER_FINITE", "/scores/0/score")]


@pytest.mark.parametrize("mutation", ["duplicate", "order", "skipped_model", "live_unsupported"])
def test_installed_bindings_enforce_relationship_rules(shared_payloads, mutation):
    fixture = "classification-unsupported" if mutation in {"skipped_model", "live_unsupported"} else "classification-supported"
    result = deepcopy(shared_payloads[fixture])
    if mutation == "duplicate":
        result["scores"][1]["category"] = result["scores"][0]["category"]
    elif mutation == "order":
        result["scores"].reverse()
    elif mutation == "skipped_model":
        result["model_version"] = "unused-model"
    else:
        result["mode"] = "live"
    with pytest.raises(ContractValidationError):
        validate_record("ClassificationResult", result)
