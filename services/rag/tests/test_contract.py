"""Owner-local transport checks against the pinned, provisional P2 candidate."""

from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import tempfile
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
import pytest

from notelens_rag.contracts import ContractError, Contracts
from notelens_rag.main import DEMO_QUESTION, Settings, create_app


@pytest.fixture
def contracts():
    return Contracts()


@pytest.fixture
def client():
    with TestClient(create_app(Settings()), client=("127.0.0.1", 45000)) as instance:
        yield instance


def post(client, path="/v1/retrieve", payload=None, request_id=None):
    identifier = request_id or str(uuid4())
    return client.post(path, json=payload if payload is not None else {
        "schema_version": "1.0.0", "question": DEMO_QUESTION},
        headers={"X-Request-ID": identifier}), identifier


def check_error(response, contracts, status, code):
    assert response.status_code == status
    body = response.json()
    contracts.validate("ErrorEnvelope", body)
    assert body["error"]["code"] == code
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert str(UUID(body["request_id"])) == body["request_id"]


@pytest.mark.parametrize("path,definition", [
    ("/health/live", "LivenessResult"), ("/health/ready", "HealthResult")])
def test_health_is_truthful_mock_and_ignores_incoming_request_ids(client, contracts, path, definition):
    response = client.get(path, headers=[("X-Request-ID", "invalid"), ("X-Request-ID", "also-invalid")])
    assert response.status_code == 200
    contracts.validate(definition, response.json())
    assert response.json()["mode"] == "mock"
    if definition == "HealthResult":
        assert response.json()["model_version"] is None


@pytest.mark.parametrize("path,definition", [
    ("/v1/retrieve", "RetrievalResult"), ("/v1/literature-answer", "AnswerResult")])
def test_mock_business_responses_match_candidate_and_echo_request_id(client, contracts, path, definition):
    response, identifier = post(client, path)
    assert response.status_code == 200
    contracts.validate(definition, response.json())
    assert response.headers["X-Request-ID"] == identifier
    assert response.json()["mode"] == "mock"


def test_mock_answer_preserves_claim_source_component_links_and_rendering(client):
    response, _ = post(client, "/v1/literature-answer")
    body = response.json()
    assert body["text"] == "\n\n".join(claim["text"] for claim in body["claims"])
    sources = {source["source_id"]: source for source in body["sources"]}
    components = {component["component_id"]: component for component in body["components"]}
    for claim in body["claims"]:
        assert claim["scope"] == "general_information"
        assert claim["component_id"] in components
        for value in claim["source_ids"]:
            assert sources[value]["component_id"] == claim["component_id"]
            assert sources[value]["kind"] == "literature"
    assert all(component["mode"] == "mock" and component["provider"] == "mock"
               for component in components.values())
    assert any("synthetic" in warning.lower() for warning in body["warnings"])


@pytest.mark.parametrize("headers", [[], [("X-Request-ID", "bad")],
    [("X-Request-ID", "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA")],
    [("X-Request-ID", "11111111-1111-4111-8111-111111111111")] * 2])
def test_bad_or_duplicate_business_ids_get_new_diagnostic_id(client, contracts, headers):
    response = client.post("/v1/retrieve", json={"schema_version": "1.0.0", "question": DEMO_QUESTION}, headers=headers)
    check_error(response, contracts, 400, "validation_failure")
    assert response.headers["X-Request-ID"] not in [value for name, value in headers]


@pytest.mark.parametrize("payload", [None, {}, {"schema_version": "wrong", "question": DEMO_QUESTION},
    {"schema_version": "1.0.0", "question": "   "},
    {"schema_version": "1.0.0", "question": DEMO_QUESTION, "mode": "live"}])
def test_invalid_business_payloads_are_safe_envelopes(client, contracts, payload):
    response = client.post("/v1/retrieve", content=json.dumps(payload),
                           headers={"X-Request-ID": str(uuid4()), "Content-Type": "application/json"})
    check_error(response, contracts, 422, "validation_failure")


@pytest.mark.parametrize("body", [b'{"question":', b'{"number":NaN}', b'{"number":Infinity}', b'{"number":1e999}'])
def test_malformed_or_nonfinite_wire_json_is_rejected(client, contracts, body):
    response = client.post("/v1/retrieve", content=body,
                           headers={"X-Request-ID": str(uuid4()), "Content-Type": "application/json"})
    check_error(response, contracts, 400, "validation_failure")


@pytest.mark.parametrize("question", ["What is another topic?", "Sta je ovo?", "\u00bfQu\u00e9 es esto?"])
def test_unconfigured_language_or_real_question_handling_is_not_claimed(client, contracts, question):
    response, _ = post(client, payload={"schema_version": "1.0.0", "question": question})
    check_error(response, contracts, 422, "validation_failure")
    assert "fixture" in response.json()["error"]["message"].lower()


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_native_nonfinite_scores_are_rejected(contracts, client, value):
    response, _ = post(client)
    body = response.json()
    body["passages"][0]["score"] = value
    with pytest.raises(ContractError): contracts.validate("RetrievalResult", body)


@pytest.mark.parametrize("scenario", ["insufficient", "clarification"])
def test_static_mock_outcomes_have_no_fake_generator_metadata(contracts, scenario):
    with TestClient(create_app(Settings(scenario=scenario)), client=("127.0.0.1", 45000)) as instance:
        response, _ = post(instance, "/v1/literature-answer")
        assert response.status_code == 200
        body = response.json()
        contracts.validate("AnswerResult", body)
        assert body["evidence_state"] == "insufficient"
        assert body["claims"] == body["sources"] == body["components"] == []
        assert body["prompt_version"] is None
        assert (body["clarification"] is not None) == (scenario == "clarification")


@pytest.mark.parametrize("scenario,status,code", [
    ("timeout", 504, "timeout"), ("rate_limit", 429, "rate_limit"),
    ("provider_unavailable", 503, "provider_unavailable"), ("internal_error", 500, "internal_error")])
def test_server_selected_mock_failures_are_not_fake_success(contracts, scenario, status, code):
    with TestClient(create_app(Settings(scenario=scenario)), client=("127.0.0.1", 45000)) as instance:
        response, identifier = post(instance)
        check_error(response, contracts, status, code)
        assert response.headers["X-Request-ID"] == identifier


@pytest.mark.parametrize("path", ["/health/live", "/health/ready", "/v1/retrieve"])
def test_remote_calls_cannot_use_keyfree_loopback_exception(contracts, path):
    with TestClient(create_app(Settings()), client=("203.0.113.5", 45000)) as instance:
        if path.startswith('/health'):
            response = instance.get(path, headers={"X-Request-ID": "11111111-1111-4111-8111-111111111111",
                                                   "X-Forwarded-For": "127.0.0.1"})
            assert response.headers['X-Request-ID'] != '11111111-1111-4111-8111-111111111111'
        else: response, _ = post(instance)
        check_error(response, contracts, 401, "unauthorized")
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_configured_auth_is_required_even_on_loopback(contracts):
    with TestClient(create_app(Settings(service_token="synthetic-test-token")), client=("127.0.0.1", 45000)) as instance:
        check_error(instance.get('/health/live'), contracts, 401, 'unauthorized')
        response = instance.get('/health/live', headers={'Authorization': 'Bearer synthetic-test-token'})
        assert response.status_code == 200


def test_live_mode_is_not_ready_and_never_falls_back_to_mock(contracts):
    with TestClient(create_app(Settings(mode='live', service_token='synthetic-test-token')),
                    client=("127.0.0.1", 45000)) as instance:
        headers={'Authorization':'Bearer synthetic-test-token'}
        ready=instance.get('/health/ready',headers=headers)
        assert ready.status_code==503
        contracts.validate('HealthResult',ready.json())
        assert ready.json()['mode']=='live' and ready.json()['model_version'] is None
        headers['X-Request-ID']=str(uuid4())
        result=instance.post('/v1/retrieve',json={'schema_version':'1.0.0','question':DEMO_QUESTION},headers=headers)
        check_error(result,contracts,503,'configuration_required')


def test_concurrent_requests_keep_their_own_ids(client):
    identifiers=[str(uuid4()) for _ in range(12)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses=list(pool.map(lambda value: post(client,request_id=value)[0],identifiers))
    assert [response.headers['X-Request-ID'] for response in responses]==identifiers


def test_unexpected_mock_exception_does_not_disclose_payload_or_trace(client, contracts, caplog):
    def fail(*args): raise RuntimeError('PRIVATE_REQUEST_MARKER')
    client.app.state.mock_result=fail
    response,_=post(client)
    check_error(response,contracts,500,'internal_error')
    assert 'PRIVATE_REQUEST_MARKER' not in response.text+caplog.text


def test_pin_drift_is_detected_without_fetching_contracts(contracts):
    parent=Path(__file__).resolve().parents[1]/'.cache'/'test-runs'
    parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='contract-pin-',dir=parent) as directory:
        temporary=Path(directory).resolve()
        assert temporary.is_relative_to(parent.resolve())
        for path in contracts.directory.iterdir():
            if path.is_file(): (temporary/path.name).write_bytes(path.read_bytes())
        (temporary/'schema.json').write_bytes(b'{}')
        with pytest.raises(ContractError): Contracts(temporary)
