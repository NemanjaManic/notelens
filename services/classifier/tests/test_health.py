"""F-011 classifier mock health and frozen authentication behavior."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from notelens_contracts.v1 import ContractValidationError, validate_record

import notelens_classifier.main as service
from conftest import REQUEST_ID

TOKEN = "synthetic-health-token"
ROUTES = ("/health/live", "/health/ready")


def client(settings):
    return TestClient(service.create_app(settings), base_url="http://127.0.0.1", client=("127.0.0.1", 50000))


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("headers", [[], [("X-Request-ID", REQUEST_ID)],
                                     [("X-Request-ID", "malformed")],
                                     [("X-Request-ID", REQUEST_ID), ("X-Request-ID", "bad")]])
def test_mock_health_ignores_incoming_ids(route, headers, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Health must not run classifier logic")
    monkeypatch.setattr(service, "mock_result", forbidden)
    with client(service.Settings(mode="mock")) as http:
        response = http.get(route, headers=headers)
    assert response.status_code == 200
    data = validate_record("LivenessResult" if route.endswith("live") else "HealthResult", response.json())
    assert data["service"] == "classifier" and data["mode"] == "mock" and data["version"]
    assert data["status"] == ("alive" if route.endswith("live") else "ok")
    if route.endswith("ready"):
        assert data["model_version"] is None and data["reason"] is None
    assert "x-request-id" not in response.headers


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("auth", [[], [("Authorization", "Bearer wrong")],
                                  [("Authorization", "Bearer " + TOKEN), ("Authorization", "Bearer wrong")],
                                  [("Authorization", "Bearer wrong"), ("Authorization", "Bearer " + TOKEN)]])
def test_health_denials_generate_new_diagnostic_id(route, auth):
    headers = [("X-Request-ID", REQUEST_ID), ("X-Request-ID", "invalid")] + auth
    with client(service.Settings(mode="mock", token=TOKEN)) as http:
        responses = [http.get(route, headers=headers), http.get(route, headers=headers)]
    ids = []
    for response in responses:
        assert response.status_code == 401
        data = validate_record("ErrorEnvelope", response.json())
        assert data["error"]["code"] == "unauthorized" and data["error"]["retryable"] is False
        assert response.headers.get_list("www-authenticate") == ["Bearer"]
        ids.append(data["request_id"])
        assert str(UUID(ids[-1])) == ids[-1] == response.headers["x-request-id"]
        assert ids[-1] != REQUEST_ID and TOKEN not in response.text
    assert ids[0] != ids[1]


@pytest.mark.parametrize("route", ROUTES)
def test_health_token_success_ignores_invalid_request_id(route):
    with client(service.Settings(mode="mock", token=TOKEN)) as http:
        response = http.get(route, headers=[("X-Request-ID", "invalid"), ("Authorization", "Bearer " + TOKEN)])
    assert response.status_code == 200 and "x-request-id" not in response.headers


def test_mock_not_ready_is_health_result_and_liveness_survives():
    with client(service.Settings(mode="mock", mock_readiness="not_ready")) as http:
        ready = http.get("/health/ready")
        live = http.get("/health/live")
    assert ready.status_code == 503
    data = validate_record("HealthResult", ready.json())
    assert data["status"] == "not_ready" and data["mode"] == "mock"
    assert data["reason"] and data["model_version"] is None and "error" not in data
    with pytest.raises(ContractValidationError):
        validate_record("ErrorEnvelope", ready.json())
    assert validate_record("LivenessResult", live.json())["status"] == "alive"


@pytest.mark.parametrize("mock_readiness,scenario", [("invalid-secret-marker", "supported"), ("ready", "invalid")])
def test_bad_mock_configuration_is_not_ready_without_echoing_settings(mock_readiness, scenario):
    with client(service.Settings(mode="mock", mock_readiness=mock_readiness, scenario=scenario)) as http:
        response = http.get("/health/ready")
    assert response.status_code == 503
    result = validate_record("HealthResult", response.json())
    assert result["status"] == "not_ready" and "invalid-secret-marker" not in response.text


def test_mock_readiness_environment_switch(monkeypatch):
    monkeypatch.setenv("NOTELENS_CLASSIFIER_MODE", "mock")
    monkeypatch.setenv("NOTELENS_CLASSIFIER_MOCK_READINESS", "not_ready")
    settings = service.Settings.from_environment()
    assert settings.mock_readiness == "not_ready"
    with client(settings) as http:
        assert http.get("/health/ready").status_code == 503


def test_live_mode_reports_unavailable_without_claiming_mock_readiness():
    with client(service.Settings(mode="live", token=TOKEN)) as http:
        response = http.get("/health/ready", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 503
    result = validate_record("HealthResult", response.json())
    assert result["mode"] == "live" and result["model_version"] is None


def test_health_auth_is_separate_from_business_id_admission(body):
    with client(service.Settings(mode="mock", token=TOKEN)) as http:
        health = http.get("/health/live", headers={"X-Request-ID": "bad"})
        business = http.post("/v1/classify", json=body, headers={"X-Request-ID": "bad"})
    assert health.status_code == 401
    assert business.status_code == 400
    assert validate_record("ErrorEnvelope", business.json())["error"]["code"] == "validation_failure"


def test_remote_unauthenticated_health_is_denied():
    with TestClient(service.create_app(service.Settings(mode="mock")), base_url="http://127.0.0.1",
                    client=("203.0.113.5", 50000)) as http:
        response = http.get("/health/ready", headers={"X-Forwarded-For": "127.0.0.1"})
    assert response.status_code == 401
    assert validate_record("ErrorEnvelope", response.json())["error"]["code"] == "unauthorized"
