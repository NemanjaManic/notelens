"""Exercise the composed service through its frozen HTTP boundary with simulated SDK calls."""

from copy import deepcopy
import json
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx2 as httpx
import pytest

from notelens_rag.answers import OfflineLiteratureGenerator, PARTIAL_POLICY
from notelens_rag.assessor import OfflineLunaAssessor
from notelens_rag.contracts import Contracts
from notelens_rag.main import Settings, create_app
from notelens_rag.runtime import RagService, RagServiceError

from test_answers import context, envelope, output, PARAMETERS


@pytest.fixture
def service_factory(context):
    clients = []
    def create(coverage='full', *, policy=None, fail=None, admitted=True, healthy=True):
        request, candidates, requirements, assessment = deepcopy(context)
        if coverage != 'full':
            for index in ([1] if coverage == 'partial' else [0, 1]):
                assessment['parts'][index].update(status='not_supported', evidence=[])
        calls = {'admission': 0, 'requirements': 0, 'ranking': 0, 'assessment': 0, 'generation': 0}
        def assess_send(native):
            calls['assessment'] += 1
            if fail:
                return httpx.Response(fail, json={'error': {'message': 'Sensitive provider body'}})
            return httpx.Response(200, json=envelope({'requirements_cover_question': True, 'assessment': assessment}))
        def generate_send(native):
            calls['generation'] += 1
            return httpx.Response(200, json=envelope(output(coverage)))
        assessor = OfflineLunaAssessor(transport=httpx.MockTransport(assess_send), parameters=PARAMETERS)
        generator = OfflineLiteratureGenerator(transport=httpx.MockTransport(generate_send), parameters=PARAMETERS)
        clients.extend([assessor, generator])
        def admit(value):
            calls['admission'] += 1
            return admitted and value == request
        def parts(value):
            calls['requirements'] += 1
            return deepcopy(requirements)
        def rank(value):
            calls['ranking'] += 1
            return deepcopy(candidates)
        service = RagService(mode='mock', admit=admit, rank=rank, requirements=parts,
            assessor=assessor, generator=generator, health_check=lambda: healthy,
            model_version='mock-luna-cited-answer-v1', partial_policy=policy)
        return service, request, calls
    yield create
    for client in clients:
        client.close()


def send(client, request, path='/v1/literature-answer', *, token=None, identifier=None):
    identifier = identifier or str(uuid4())
    headers = {'X-Request-ID': identifier}
    if token:
        headers['Authorization'] = 'Bearer '+token
    return client.post(path, json=request, headers=headers), identifier


def test_http_full_pipeline_not_static_demo_and_both_frozen_operations(service_factory):
    service, request, calls = service_factory()
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        health = client.get('/health/ready').json()
        assert health['status'] == 'ok' and health['mode'] == 'mock'
        assert health['model_version'] is None
        assert calls['assessment'] == calls['generation'] == 0
        response, identifier = send(client, request, '/v1/retrieve')
        assert response.status_code == 200 and response.json()['state'] == 'sufficient'
        assert response.headers['X-Request-ID'] == identifier
        assert calls['assessment'] == 1 and calls['generation'] == 0
        response, identifier = send(client, request)
        assert response.status_code == 200 and response.headers['X-Request-ID'] == identifier
        Contracts().validate('AnswerResult', response.json())
        assert response.json()['text'] == 'Condition A is caused by agent A.\n\nCondition A lasts two days.'
        assert calls['assessment'] == 2 and calls['generation'] == 1
        assert service.__dict__.keys().isdisjoint({'request', 'candidates', 'history', 'cache'})


@pytest.mark.parametrize('coverage,policy,state,generations', [
    ('full', None, 'sufficient', 1), ('partial', PARTIAL_POLICY, 'partial', 1), ('none', None, 'insufficient', 0)])
def test_http_coverage_claims_gaps_and_abstention(service_factory, coverage, policy, state, generations):
    service, request, calls = service_factory(coverage, policy=policy)
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        response, _ = send(client, request)
    assert response.status_code == 200 and response.json()['evidence_state'] == state
    Contracts().validate('AnswerResult', response.json())
    assert calls['generation'] == generations
    if coverage == 'none':
        assert response.json()['sources'] == response.json()['components'] == []
    if coverage == 'partial':
        assert any('Duration' in warning for warning in response.json()['warnings'])


def test_unconfirmed_partial_gate_is_not_silently_enabled(service_factory):
    service, request, calls = service_factory('partial')
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        response, _ = send(client, request)
    assert response.status_code == 503 and response.json()['error']['code'] == 'configuration_required'
    assert calls['generation'] == 0


@pytest.mark.parametrize('admitted,healthy,status,code', [
    (False, True, 422, 'validation_failure'), (True, False, 503, 'configuration_required')])
def test_input_admission_and_readiness_precede_provider_calls(service_factory, admitted, healthy, status, code):
    service, request, calls = service_factory(admitted=admitted, healthy=healthy)
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        response, _ = send(client, request)
        ready = client.get('/health/ready')
    assert response.status_code == status and response.json()['error']['code'] == code
    assert ready.status_code == (200 if healthy else 503)
    assert calls['assessment'] == calls['generation'] == calls['ranking'] == calls['requirements'] == 0


@pytest.mark.parametrize('failure,status,code', [(429, 429, 'rate_limit'), (500, 503, 'provider_unavailable'),
                                             (401, 503, 'configuration_required')])
def test_http_provider_failures_preserve_request_id_without_bodies(service_factory, failure, status, code):
    service, request, calls = service_factory(fail=failure)
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        response, identifier = send(client, request)
    assert response.status_code == status
    Contracts().validate('ErrorEnvelope', response.json())
    assert response.json()['error']['code'] == code and response.json()['request_id'] == identifier
    assert 'Sensitive' not in response.text and request['question'] not in response.text
    assert calls['assessment'] == 1 and calls['generation'] == 0


def test_authentication_correlation_and_malformed_json_cannot_spend(service_factory):
    service, request, calls = service_factory()
    with TestClient(create_app(Settings(service_token='fixture-service-token'), backend=service)) as client:
        response, _ = send(client, request)
        assert response.status_code == 401
        response, _ = send(client, request, token='fixture-service-token', identifier='bad-id')
        assert response.status_code == 400
        response = client.post('/v1/literature-answer', content=b'{"question":1,"question":2}',
            headers={'Authorization': 'Bearer fixture-service-token', 'X-Request-ID': str(uuid4())})
        assert response.status_code == 400
    assert calls['assessment'] == calls['generation'] == calls['ranking'] == 0


def test_unexpected_backend_exception_is_redacted(service_factory):
    service, request, calls = service_factory()
    def fail(value):
        raise RuntimeError('Sensitive question and provider data')
    service.rank = fail
    with TestClient(create_app(Settings(), backend=service), client=('127.0.0.1', 45000)) as client:
        response, _ = send(client, request)
    assert response.status_code == 500 and 'Sensitive' not in response.text


def test_live_backend_requires_matching_mode_and_explicit_service_token(service_factory):
    service, _, _ = service_factory()
    with pytest.raises(ValueError):
        create_app(Settings(mode='live', service_token='fixture'), backend=service)
    service.mode = 'live'
    with pytest.raises(ValueError):
        create_app(Settings(mode='live'), backend=service)


def test_no_new_backend_is_activated_by_default():
    app = create_app(Settings(mode='live', service_token='fixture'))
    assert app.state.backend is None
    with TestClient(app) as client:
        result = client.get('/health/ready', headers={'Authorization': 'Bearer fixture'})
    assert result.status_code == 503 and result.json()['model_version'] is None


def test_health_callback_failure_is_not_a_ready_service(service_factory):
    service, _, _ = service_factory()
    def fail():
        raise RuntimeError('Secret backend detail')
    service.health_check = fail
    assert service.is_ready() is False
