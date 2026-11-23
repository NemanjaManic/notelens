"""Offline HTTP/provider execution checks with synthetic responses and credentials."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from notelens_extraction.approved_provider import ServiceBudget, configured_provider
from notelens_extraction.config import Settings
from notelens_extraction.demo import request
from notelens_extraction.errors import ServiceError
from notelens_extraction.main import create_app
from notelens_extraction.openai_trial import MODEL, OpenAIResponsesProvider
from notelens_extraction.providers import FakeProvider, UnconfiguredLiveProvider


@pytest.fixture
def policy():
    return {
        "version": "d-extraction-provider-policy-v1", "approved": True,
        "approved_by": "synthetic test approver", "operator": "offline test",
        "scope": "Synthetic offline regression only", "model_access_confirmed": True,
        "model": MODEL, "receipt_path": "execution.receipt", "automatic_retries": 0,
        "max_input_tokens": 100_000, "max_output_tokens": 512,
        "max_provider_calls": 2, "remaining_budget_usd": "0.10",
        "input_usd_per_million_tokens": "0.10", "output_usd_per_million_tokens": "0.50",
        "timeout_seconds": 30,
    }


def live_fixture(value):
    if isinstance(value, dict):
        if value.get("mode") == "mock":
            value["mode"] = "live"
        if value.get("provider") == "literal-fixture":
            value.update(provider="openai", model=MODEL)
        for child in value.values():
            live_fixture(child)
    elif isinstance(value, list):
        for child in value:
            live_fixture(child)
    return value


def fixture_transport(payload):
    source = json.loads(payload["input"])
    operation = "answer" if "question" in source else "extract"
    result = live_fixture(json.loads(FakeProvider().generate(operation, source, "", repair=False)))
    return {"object": "response", "model": MODEL, "status": "completed", "output": [{
        "type": "message", "role": "assistant", "status": "completed",
        "content": [{"type": "output_text", "text": json.dumps(result)}],
    }]}


def test_bad_input_format_does_not_claim_execution_receipt(tmp_path, policy):
    policy["input_format"] = "unsupported"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(ValueError, match="input format"):
        configured_provider(path, api_key="offline-test", service_token="offline-token")
    assert not (tmp_path / policy["receipt_path"]).exists()


def test_policy_selects_message_input_before_transport(tmp_path, policy, monkeypatch):
    policy["input_format"] = "messages"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy))
    send = Mock()
    monkeypatch.setattr("notelens_extraction.approved_provider.ResponsesTransport", Mock(return_value=send))
    provider = configured_provider(path, api_key="offline-test", service_token="offline-token")
    payload = provider.prepare("answer", request("A synthetic question"), "Synthetic instruction")
    assert json.loads(payload["input"][0]["content"][0]["text"]) == request("A synthetic question")
    send.assert_not_called()


@pytest.mark.parametrize("question,state", [
    ("What does the document say about chest pain?", "sufficient"),
    ("What does the document say about chest pain and the patient's age?", "partial"),
    ("What is the patient's age?", "insufficient"),
    ("Can NoteLens recommend a treatment?", "insufficient"),
])
def test_configured_provider_http_preserves_app_identity_and_outcomes(question, state):
    send = Mock(side_effect=fixture_transport)
    provider = OpenAIResponsesProvider(send, model=MODEL, max_output_tokens=512)
    client = TestClient(create_app(provider, token="private-test-token"))
    headers = {"Authorization": "Bearer private-test-token", "X-Request-ID": str(uuid.uuid4())}
    assert client.get("/health/ready", headers=headers).json()["mode"] == "live"
    payload = request(question)
    payload["document"]["doc_id"] = str(uuid.uuid4())
    response = client.post("/v1/document-answer", json=payload, headers=headers)
    assert response.status_code == 200
    result = response.json()
    assert result["mode"] == "live" and result["evidence_state"] == state
    for source in result["sources"]:
        assert source["doc_id"] == payload["document"]["doc_id"]
        assert source["text_sha256"] == payload["document"]["text_sha256"]
    if state == "insufficient":
        assert not result["claims"] and not result["sources"]
    assert response.headers["X-Generation-Attempts"] == "1"
    send.assert_called_once()


def test_http_extraction_and_summary_keep_both_repeated_passages():
    from pathlib import Path

    document = json.loads((Path(__file__).resolve().parents[3] / "contracts/v1/fixtures/documents.json").read_bytes())["offset"]
    document["doc_id"] = str(uuid.uuid4())
    send = Mock(side_effect=fixture_transport)
    client = TestClient(create_app(OpenAIResponsesProvider(send, model=MODEL, max_output_tokens=512), token="token"))
    response = client.post("/v1/extract", json={"schema_version": "1.0.0", "document": document},
                           headers={"Authorization": "Bearer token", "X-Request-ID": str(uuid.uuid4())})
    assert response.status_code == 200
    result = response.json()
    assert (result["doc_id"], result["text_sha256"]) == (document["doc_id"], document["text_sha256"])
    assert [(item["evidence"][0]["start"], item["evidence"][0]["end"]) for item in result["items"]] == [(7, 21), (47, 61)]
    assert result["summary"]["status"] == "completed"
    assert len(result["summary"]["result"]["claims"]) == 2
    send.assert_called_once()


def test_explicit_policy_reaches_existing_http_transport_and_claims_receipt(tmp_path, policy, monkeypatch):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    transport = Mock(return_value=fixture_transport)
    monkeypatch.setattr("notelens_extraction.approved_provider.ResponsesTransport", transport)
    provider = configured_provider(path, api_key="offline-only", service_token="token")
    assert provider.configured and provider.model == MODEL
    assert transport.call_args.kwargs["receipt"] == tmp_path / "execution.receipt"
    assert transport.call_args.kwargs["timeout_seconds"] == 30


@pytest.mark.parametrize("field,value", [
    ("approved", False), ("model_access_confirmed", False), ("automatic_retries", 1),
    ("max_provider_calls", True), ("remaining_budget_usd", "NaN"),
    ("max_input_tokens", 0), ("approved_by", ""),
])
def test_incomplete_policy_stays_unconfigured_without_touching_receipt(tmp_path, policy, monkeypatch, field, value):
    policy[field] = value
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-only")
    provider = Settings(mode="live", service_token="token", provider_policy=str(path)).provider()
    assert isinstance(provider, UnconfiguredLiveProvider)
    assert not (tmp_path / "execution.receipt").exists()


def test_concurrent_budget_calls_and_oversized_request_are_blocked(policy):
    budget = ServiceBudget(policy)
    payload = {"model": MODEL, "max_output_tokens": 512}

    def reserve(_index):
        try:
            budget.reserve(payload, "unused")
            return True
        except ServiceError:
            return False

    with ThreadPoolExecutor(max_workers=8) as executor:
        assert sum(executor.map(reserve, range(10))) == 2
    other = ServiceBudget(policy)
    with pytest.raises(ServiceError, match="bounds"):
        other.reserve({**payload, "input": "x" * policy["max_input_tokens"]}, "unused")


def test_failed_network_attempt_consumes_balance_and_restart_keeps_receipt(tmp_path, policy, monkeypatch):
    from functools import partial
    from notelens_extraction.openai_transport import ResponsesTransport

    policy["remaining_budget_usd"] = "0.010256"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    connection = Mock()
    connection.return_value.getresponse.side_effect = TimeoutError("private detail")
    monkeypatch.setattr("notelens_extraction.approved_provider.ResponsesTransport",
                        partial(ResponsesTransport, connect=connection))
    provider = configured_provider(path, api_key="offline-only", service_token="token")
    from notelens_extraction.service import run

    with pytest.raises(ServiceError) as timeout:
        run(request(), "extract", provider)
    assert timeout.value.code == "timeout" and "private" not in timeout.value.message
    with pytest.raises(ServiceError, match="balance"):
        run(request(), "extract", provider)
    connection.assert_called_once()
    with pytest.raises(FileExistsError):
        configured_provider(path, api_key="offline-only", service_token="token")
    assert "offline-only" not in (tmp_path / "execution.receipt").read_text()


def test_wrong_component_model_is_rejected_over_http_without_retry():
    def incorrect(payload):
        response = fixture_transport(payload)
        result = json.loads(response["output"][0]["content"][0]["text"])
        result["components"][0]["model"] = "different-model"
        response["output"][0]["content"][0]["text"] = json.dumps(result)
        return response

    send = Mock(side_effect=incorrect)
    client = TestClient(create_app(OpenAIResponsesProvider(send, model=MODEL, max_output_tokens=512), token="token"))
    response = client.post("/v1/document-answer", json=request("What does the document say about chest pain?"),
                           headers={"Authorization": "Bearer token", "X-Request-ID": str(uuid.uuid4())})
    assert response.status_code == 502
    send.assert_called_once()
