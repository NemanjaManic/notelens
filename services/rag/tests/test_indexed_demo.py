"""Verify the portable synthetic launcher through the production-shaped routes."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

pytest.importorskip('chromadb', reason='The portable indexed profile needs the optional indexing extra.')


@pytest.fixture(scope='module')
def demo():
    directory = Path(__file__).resolve().parents[3] / 'docs/rag/evaluation'
    with pytest.MonkeyPatch.context() as changes:
        changes.syspath_prepend(str(directory))
        spec = importlib.util.spec_from_file_location('notelens_indexed_demo_test', directory / 'serve_indexed_demo.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module


@pytest.fixture(scope='module')
def index_root():
    cache = Path(__file__).resolve().parents[1] / '.cache'
    cache.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='portable-indexed-demo-', dir=cache,
                            ignore_cleanup_errors=True) as directory:
        yield Path(directory)


@pytest.fixture
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('The portable indexed fixture requested a provider, tokenizer download or external connection.')
    monkeypatch.setattr('openai.OpenAI', forbidden)
    monkeypatch.setattr('socket.create_connection', forbidden)
    monkeypatch.setattr('notelens_rag.embeddings.local_tokenizer', forbidden)


def post(client, question, path='/v1/literature-answer', token=None):
    identifier = str(uuid4())
    headers = {'X-Request-ID': identifier}
    if token is not None:
        headers['Authorization'] = f'Bearer {token}'
    response = client.post(path, json={'schema_version': '1.0.0', 'question': question}, headers=headers)
    assert response.headers['X-Request-ID'] == identifier
    return response


def test_full_partial_and_missing_support_use_the_index_and_skip_unsupported_generation(demo, index_root, offline, monkeypatch):
    compositions = []
    generate = demo._generate

    def tracked_generation(prepared, *, partial_policy):
        compositions.append(prepared)
        return generate(prepared, partial_policy=partial_policy)

    monkeypatch.setattr(demo, '_generate', tracked_generation)
    with TestClient(demo._app(index_root, None), client=('127.0.0.1', 45000)) as client:
        for question, expected in ((demo.DEMO_QUESTION, 'sufficient'), (demo.PARTIAL_QUESTION, 'partial'),
                                   (demo.MISSING_QUESTION, 'insufficient')):
            retrieved = post(client, question, '/v1/retrieve')
            answered = post(client, question)
            assert retrieved.status_code == answered.status_code == 200
            body = answered.json()
            assert body['evidence_state'] == expected and body['mode'] == 'mock'
            assert retrieved.json()['state'] == ('insufficient' if expected == 'insufficient' else 'sufficient')
            assert retrieved.json()['passages'][0]['passage_id'] == demo.DEMO_PASSAGE
            assert body['retrieval_provenance']['index_version'] == retrieved.json()['index_version']
            if expected == 'insufficient':
                assert body['claims'] == body['sources'] == []
                assert body['route'] == 'none' and body['prompt_version'] is None
            else:
                assert len(body['claims']) == 1
                assert body['claims'][0]['text'] == body['sources'][0]['text'] == demo.TOPIC_TEXT
                assert body['claims'][0]['source_ids'] == [demo.DEMO_PASSAGE]
            if expected == 'partial':
                assert any('Start date' in warning for warning in body['warnings'])
    assert len(compositions) == 2


def test_configured_token_is_required_by_health_and_business_routes(demo, index_root, offline):
    token = 'synthetic-indexed-demo-token'
    with TestClient(demo._app(index_root, token), client=('127.0.0.1', 45000)) as client:
        for path in ('/health/live', '/health/ready'):
            assert client.get(path).status_code == 401
            assert client.get(path, headers={'Authorization': f'Bearer {token}'}).status_code == 200
        denied = post(client, demo.DEMO_QUESTION)
        assert denied.status_code == 401 and denied.json()['error']['code'] == 'unauthorized'
        assert post(client, demo.DEMO_QUESTION, token=token).status_code == 200


def test_unknown_question_is_rejected_before_ranking(demo, index_root, offline, monkeypatch):
    app = demo._app(index_root, None)

    def no_ranking(*args, **kwargs):
        pytest.fail('An unregistered question reached the indexed retriever.')

    monkeypatch.setattr(demo.CandidateRetriever, 'retrieve', no_ranking)
    with TestClient(app, client=('127.0.0.1', 45000)) as client:
        for path in ('/v1/retrieve', '/v1/literature-answer'):
            response = post(client, 'An unregistered synthetic question?', path)
            assert response.status_code == 422 and response.json()['error']['code'] == 'validation_failure'


def test_disabled_mock_readiness_keeps_the_indexed_process_alive(demo, index_root, offline):
    with TestClient(demo._app(index_root, None, mock_ready=False), client=('127.0.0.1', 45000)) as client:
        live = client.get('/health/live')
        ready = client.get('/health/ready')
        assert live.status_code == 200 and live.json()['status'] == 'alive'
        assert ready.status_code == 503 and ready.json()['status'] == 'not_ready'
