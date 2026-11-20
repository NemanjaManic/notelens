"""Exercise request failures and empty evidence through the RAG HTTP boundary."""

from decimal import Decimal

from fastapi.testclient import TestClient
import httpx2 as httpx
import pytest

from notelens_rag.contracts import Contracts
from notelens_rag.embeddings import TokenBudget
from notelens_rag.main import Settings, create_app
from notelens_rag.retrieval import CandidateRetriever

from test_answers import context
from test_embeddings import make_embedder
from test_retrieval import Embedder, index
from test_runtime import send, service_factory


def assert_error(response, identifier, status, code):
    body = response.json()
    Contracts().validate('ErrorEnvelope', body)
    assert response.status_code == status
    assert response.headers['X-Request-ID'] == body['request_id'] == identifier
    assert body['error']['code'] == code
    assert body['error']['retryable'] is False
    assert 'retrieval_provenance' not in body and 'claims' not in body


@pytest.mark.parametrize('upstream_status,expected_status,code', [
    ('timeout', 504, 'timeout'), (429, 429, 'rate_limit'),
    (503, 503, 'provider_unavailable'), (401, 503, 'configuration_required'),
    ('budget', 429, 'budget_exceeded'),
])
def test_embedding_sdk_failure_stops_search_and_generation(service_factory, index, make_embedder,
                                                          upstream_status, expected_status, code):
    service, request, calls = service_factory()
    service.mode = index.spec['mode'] = 'live'
    fixture = {'payload': {'error': {'message': 'PRIVATE_PROVIDER_BODY'}}}
    if upstream_status == 'timeout':
        fixture['fail'] = lambda native: httpx.ReadTimeout('PRIVATE_PROVIDER_BODY', request=native)
    elif upstream_status == 'budget':
        fixture['budget'] = TokenBudget(Decimal('0.000000001'), Decimal('0.02'))
    else:
        fixture['status'] = upstream_status
    embedder, embedding_calls = make_embedder(**fixture)
    retriever = CandidateRetriever(index)
    service.rank = lambda payload: retriever.retrieve(payload, embedder)
    app = create_app(Settings(mode='live', service_token='fixture-only'), backend=service)
    with TestClient(app) as client:
        response, identifier = send(client, request, token='fixture-only')
    assert_error(response, identifier, expected_status, code)
    assert 'PRIVATE_PROVIDER_BODY' not in response.text and request['question'] not in response.text
    assert len(embedding_calls) == (0 if upstream_status == 'budget' else 1)
    assert index.collection.calls == [] and calls['assessment'] == calls['generation'] == 0


@pytest.mark.parametrize('path', ['/v1/retrieve', '/v1/literature-answer'])
def test_completed_empty_search_is_insufficient_without_model_calls(service_factory, context, path):
    service, request, calls = service_factory()
    service.rank = lambda payload: {**context[1], 'passages': []}
    app = create_app(Settings(), backend=service)
    with TestClient(app, client=('127.0.0.1', 45000)) as client:
        response, identifier = send(client, request, path)
    assert response.status_code == 200 and response.headers['X-Request-ID'] == identifier
    body = response.json()
    if path == '/v1/retrieve':
        Contracts().validate('RetrievalResult', body)
        assert body['state'] == 'insufficient' and body['passages'] == []
    else:
        Contracts().validate('AnswerResult', body)
        assert body['route'] == 'none' and body['evidence_state'] == 'insufficient'
        assert body['prompt_version'] is None and body['attempted_routes'] == ['literature']
        assert body['claims'] == body['sources'] == body['components'] == []
        assert body['retrieval_provenance']['state'] == 'insufficient'
        assert body['retrieval_provenance']['index_version'] == context[1]['index_version']
    assert calls['assessment'] == calls['generation'] == 0


def test_malformed_empty_context_cannot_be_returned_as_completed_search(service_factory, context):
    service, request, calls = service_factory()
    service.rank = lambda payload: {**context[1], 'passages': [], 'question_sha256': 'another-question'}
    app = create_app(Settings(), backend=service)
    with TestClient(app, client=('127.0.0.1', 45000)) as client:
        response, identifier = send(client, request)
    assert_error(response, identifier, 500, 'internal_error')
    assert calls['assessment'] == calls['generation'] == 0


def test_unavailable_index_is_an_error_before_embedding(service_factory, index):
    service, request, calls = service_factory()
    embedder = Embedder()
    def verify():
        raise OSError('PRIVATE_INDEX_PATH')
    index.verify = verify
    retriever = CandidateRetriever(index)
    service.rank = lambda payload: retriever.retrieve(payload, embedder)
    app = create_app(Settings(), backend=service)
    with TestClient(app, client=('127.0.0.1', 45000)) as client:
        response, identifier = send(client, request)
    assert_error(response, identifier, 503, 'configuration_required')
    assert 'PRIVATE_INDEX_PATH' not in response.text
    assert embedder.calls == [] and calls['assessment'] == calls['generation'] == 0
