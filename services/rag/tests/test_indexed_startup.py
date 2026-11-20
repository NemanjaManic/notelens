"""Exercise explicit startup with a real local index and key-free adapters."""

from contextlib import ExitStack
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
import httpx2 as httpx
import pytest

pytest.importorskip('chromadb', reason='Indexed startup requires the optional indexing extra.')

from notelens_rag.answers import OfflineLiteratureGenerator
from notelens_rag.assessor import AssessmentParameters
from notelens_rag.embeddings import EmbeddingBatch, plan_corpus
from notelens_rag.evidence_selection import OfflineSelectionAssessor, SELECTION_FORMAT
from notelens_rag.indexing import build_index, index_folder, index_specification, load_index
from notelens_rag.ingestion import load_corpus
from notelens_rag.main import DEMO_QUESTION, Settings, create_app
from notelens_rag.question_parts import OfflineQuestionDecomposer
from notelens_rag.runtime import IndexedBackend

from test_answers import envelope
from test_corpus_adapter import MANIFEST, prepared_repository
from test_index_version import Encoder, FakeEmbedder
from test_runtime import send


QUESTION = 'Does the synthetic example report chest pain?'
REQUEST = {'schema_version': '1.0.0', 'question': QUESTION}
PARAMETERS = AssessmentParameters(max_output_tokens=512, reasoning_effort='none', timeout_seconds=10)


@pytest.fixture
def indexed_repository(prepared_repository):
    # Chroma may retain open Windows file handles for the lifetime of the test process.
    with TemporaryDirectory(prefix='indexed-startup-', dir=prepared_repository.parent,
                            ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        copytree(prepared_repository / 'data', root / 'data')
        yield root


@pytest.fixture
def indexed_startup(indexed_repository, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail('Indexed startup tests attempted a network connection.')

    monkeypatch.setattr('socket.create_connection', no_network)
    monkeypatch.setattr('notelens_rag.embeddings.local_tokenizer', Encoder)
    root = indexed_repository
    corpus = load_corpus(repository_root=root)
    plan = plan_corpus(corpus)
    spec = index_specification(plan, mode='mock')
    calls = []

    class LocalEmbedder:
        mode = 'mock'

        def embed(self, texts):
            assert texts == [QUESTION]
            calls.append('embed')
            vector = (1.0,) + (0.0,) * (spec['dimensions'] - 1)
            return EmbeddingBatch((vector,), len(QUESTION))

    def respond(native):
        body = json.loads(native.content)
        payload = json.loads(body['input'])
        match body['text']['format']['name']:
            case 'notelens_question_parts':
                calls.append('decompose')
                output = {'question_sha256': payload['question_sha256'], 'status': 'ready',
                          'parts': [{'description': 'Whether chest pain was reported', 'anchor': 'chest pain'}]}
            case 'notelens_support_assessment':
                calls.append('assess')
                evidence = next(item for item in payload['evidence_options'] if 'No chest pain.' in item['quote'])
                output = {'requirements_cover_question': True, 'assessment': {
                    'format_version': SELECTION_FORMAT, 'context_sha256': payload['context_sha256'],
                    'selection_sha256': payload['selection_sha256'], 'parts': [
                        {'requirement_id': 'part-1', 'status': 'supported', 'reason': 'Chest pain is explicitly absent.',
                         'evidence_ids': [evidence['evidence_id']]}]}}
            case 'notelens_literature_answer':
                calls.append('generate')
                evidence, = payload['evidence']
                assert 'No chest pain.' in evidence['quote']
                output = {'language': 'en', 'claims': [{'requirement_id': 'part-1',
                          'text': 'The synthetic example reports no chest pain.',
                          'evidence_ids': [evidence['evidence_id']]}]}
            case other:
                pytest.fail(f'Unexpected simulated SDK operation {other}.')
        return httpx.Response(200, json=envelope(output))

    def build():
        return build_index(corpus, repository_root=root, plan=plan, embedder=FakeEmbedder(), max_usd=Decimal('0.10'))

    with ExitStack() as resources:
        adapters = []
        for adapter in (OfflineQuestionDecomposer, OfflineSelectionAssessor, OfflineLiteratureGenerator):
            client = adapter(transport=httpx.MockTransport(respond), parameters=PARAMETERS)
            resources.callback(client.close)
            adapters.append(client)
        requirements, assessor, generator = adapters
        backend = IndexedBackend(index_version=spec['index_version'], model_version='indexed-startup-fixture',
                                 embedder=LocalEmbedder(), admit=lambda request: request == REQUEST,
                                 requirements=requirements, assessor=assessor, generator=generator)
        settings = Settings(corpus_manifest=MANIFEST, repository_root=str(root),
                            expected_corpus_version=corpus.corpus_version)
        yield settings, backend, build, index_folder(root, spec), calls


def test_pinned_startup_is_ready_and_serves_both_routes(indexed_startup):
    settings, backend, build, folder, calls = indexed_startup
    build()
    before = {name: (folder / name).read_bytes() for name in ('manifest.json', 'usage.json')}
    app = create_app(settings, indexed_backend=backend)
    with TestClient(app, client=('127.0.0.1', 45000)) as client:
        ready = client.get('/health/ready')
        assert ready.status_code == 200 and ready.json()['mode'] == 'mock'
        assert calls == []
        rejected, _ = send(client, REQUEST | {'question': 'An unregistered fixture?'})
        assert rejected.status_code == 422 and calls == []
        retrieved, identifier = send(client, REQUEST, '/v1/retrieve')
        assert retrieved.status_code == 200 and retrieved.headers['X-Request-ID'] == identifier
        assert retrieved.json()['index_version'] == backend.index_version
        assert calls == ['decompose', 'embed', 'assess']
        answer, identifier = send(client, REQUEST)
        assert answer.status_code == 200 and answer.headers['X-Request-ID'] == identifier
        body = answer.json()
        assert body['evidence_state'] == 'sufficient' and body['mode'] == 'mock'
        assert body['text'] == 'The synthetic example reports no chest pain.'
        assert 'No chest pain.' in body['sources'][0]['text']
        assert calls == ['decompose', 'embed', 'assess', 'decompose', 'embed', 'assess', 'generate']
    assert before == {name: (folder / name).read_bytes() for name in before}


@pytest.mark.parametrize('failure', ['missing_index', 'wrong_index', 'missing_chroma', 'unpinned_corpus', 'wrong_corpus'])
def test_invalid_startup_keeps_liveness_and_fails_closed(indexed_startup, failure):
    settings, backend, build, folder, calls = indexed_startup
    if failure == 'wrong_index':
        build()
        backend = replace(backend, index_version='0' * 64)
    elif failure == 'missing_chroma':
        folder.mkdir(parents=True)
        (folder / 'manifest.json').write_text('{"status":"complete"}', encoding='utf-8')
    elif failure == 'unpinned_corpus':
        settings = replace(settings, expected_corpus_version=None)
    elif failure == 'wrong_corpus':
        settings = replace(settings, expected_corpus_version='0' * 64)
    chroma_existed = (folder / 'chroma').exists()
    with TestClient(create_app(settings, indexed_backend=backend), client=('127.0.0.1', 45000)) as client:
        assert client.get('/health/live').status_code == 200
        ready = client.get('/health/ready')
        assert ready.status_code == 503 and ready.json()['status'] == 'not_ready'
        response, identifier = send(client, REQUEST | {'question': DEMO_QUESTION})
        assert response.status_code == 503 and response.headers['X-Request-ID'] == identifier
        assert response.json()['error']['code'] == 'configuration_required'
        assert settings.repository_root not in ready.text + response.text
    assert (folder / 'chroma').exists() == chroma_existed and calls == []


def test_live_index_startup_requires_auth_and_matching_adapter_mode(indexed_startup):
    settings, backend, _, _, calls = indexed_startup
    settings = replace(settings, mode='live')
    with patch('notelens_rag.indexing.load_index', side_effect=AssertionError('The wrong mode opened an index.')) as loader:
        with pytest.raises(ValueError):
            create_app(settings, indexed_backend=backend)
        with TestClient(create_app(replace(settings, service_token='fixture-token'), indexed_backend=backend)) as client:
            assert client.get('/health/ready').status_code == 401
            assert client.get('/health/ready', headers={'Authorization': 'Bearer fixture-token'}).status_code == 503
        loader.assert_not_called()
    assert calls == []
