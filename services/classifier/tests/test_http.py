"""HTTP boundary checks using the real ASGI app and synthetic request bodies."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from notelens_contracts.v1 import validate_record

import notelens_classifier.main as service
from conftest import REQUEST_ID, prepared


def assert_error(response, status, code, correlation=REQUEST_ID):
    assert response.status_code == status
    data = validate_record("ErrorEnvelope", response.json())
    assert data["error"]["code"] == code
    assert data["error"]["retryable"] is False
    assert data["request_id"] == response.headers["X-Request-ID"]
    assert str(UUID(data["request_id"])) == data["request_id"]
    if correlation:
        assert data["request_id"] == correlation
    return data


@pytest.mark.parametrize("headers", [[], [("X-Request-ID", "invalid")],
    [("X-Request-ID", REQUEST_ID), ("x-request-id", REQUEST_ID)]])
def test_invalid_correlation_rejected_before_body(client, headers):
    response = client.post("/v1/classify", content=b"not JSON", headers=headers)
    data = assert_error(response, 400, "validation_failure", correlation=None)
    assert data["request_id"] != REQUEST_ID


def test_header_names_are_case_insensitive(client, body):
    response = client.post("/v1/classify", json=body, headers={"x-request-id": REQUEST_ID})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == REQUEST_ID


@pytest.mark.parametrize("raw", [b"{", b"", b'{}{}', b'{"a":1,"a":2}',
                                b'{"score":NaN}', b'{"score":1e999}', b'\xff'])
def test_unsafe_or_malformed_json(client, raw):
    assert_error(client.post("/v1/classify", content=raw, headers={"X-Request-ID": REQUEST_ID}),
                 400, "validation_failure")


@pytest.mark.parametrize("case", ["digest", "version", "empty", "spaces", "normalization", "language", "missing_policy", "extra", "null"])
def test_invalid_input(client, body, case):
    if case == "digest": body["document"]["text_sha256"] = "0" * 64
    elif case == "version": body["schema_version"] = "9.9.9"
    elif case == "empty": body["document"] = prepared("")
    elif case == "spaces": body["document"] = prepared(" \n\t")
    elif case == "normalization": body["document"] = prepared("cafe\u0301")
    elif case == "language": body["document"]["language_validation"].update(outcome="inconclusive", language=None, reason="language_inconclusive")
    elif case == "missing_policy": del body["document"]["language_validation"]
    elif case == "extra": body["unexpected"] = "value"
    else: body = None
    import json
    assert_error(client.post("/v1/classify", content=json.dumps(body), headers={"X-Request-ID": REQUEST_ID}),
                 422, "validation_failure")


@pytest.mark.parametrize("length,status", [(100000, 200), (100001, 413)])
def test_document_limit_counts_code_points(client, length, status):
    body = {"schema_version": "1.0.0", "document": prepared("🩺" * length)}
    response = client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID})
    assert response.status_code == status
    if status == 413: assert_error(response, 413, "validation_failure")


@pytest.mark.parametrize("settings", [service.Settings(), service.Settings(mode="live"),
    service.Settings(mode="mock", scenario="invalid"), service.Settings(mode="other")])
def test_unavailable_configuration_never_falls_back(settings, body):
    with TestClient(service.create_app(settings), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        assert_error(client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID}),
                     503, "configuration_required")


def test_explicit_bearer_authentication(body):
    settings = service.Settings(mode="mock", token="synthetic-test-only-token")
    with TestClient(service.create_app(settings), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        for authorization in [None, "Bearer wrong", "Basic synthetic-test-only-token"]:
            headers = {"X-Request-ID": REQUEST_ID}
            if authorization: headers["Authorization"] = authorization
            response = client.post("/v1/classify", json=body, headers=headers)
            assert_error(response, 401, "unauthorized")
            assert response.headers["www-authenticate"] == "Bearer"
        response = client.post("/v1/classify", json=body,
            headers={"X-Request-ID": REQUEST_ID, "Authorization": "Bearer synthetic-test-only-token"})
        assert response.status_code == 200


def test_authenticated_live_mode_still_requires_a_model(body):
    with TestClient(service.create_app(service.Settings(mode="live", token="synthetic-test-token")),
                    base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        response = client.post("/v1/classify", json=body,
            headers={"X-Request-ID": REQUEST_ID, "Authorization": "Bearer synthetic-test-token"})
        data = assert_error(response, 503, "configuration_required")
        assert "classifier configuration" in data["error"]["message"]


def test_unauthenticated_remote_peer_is_not_admitted(body):
    with TestClient(service.create_app(service.Settings(mode="mock")),
                    base_url="http://127.0.0.1", client=("203.0.113.5", 50000)) as client:
        response = client.post("/v1/classify", json=body,
            headers={"X-Request-ID": REQUEST_ID, "X-Forwarded-For": "127.0.0.1"})
        assert_error(response, 503, "configuration_required")


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_generated_output_becomes_safe_error(client, body, monkeypatch, number):
    original = service.mock_result
    def bad_result(document, scenario):
        value = original(document, scenario)
        value["scores"][0]["score"] = number
        return value
    monkeypatch.setattr(service, "mock_result", bad_result)
    assert_error(client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID}),
                 500, "internal_error")


def test_health_is_not_claimed_before_f004_checkpoint(client):
    assert client.get("/health/live").status_code == 404
    assert client.get("/health/ready").status_code == 404
