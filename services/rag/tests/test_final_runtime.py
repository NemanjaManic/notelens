"""Verify final-run admission, durable accounting and failure deadlines offline."""

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import socket
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from notelens_rag import final_runtime as runtime
from notelens_rag.assessor import AssessmentError
from notelens_rag.main import Settings, create_app
from notelens_rag.mock import result as mock_result
from notelens_rag.runtime import RagServiceError
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Network and live client construction are forbidden in this suite.')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(runtime.openai, 'OpenAI', forbidden)


@pytest.fixture
def policy():
    return {'format_version': runtime.FORMAT, 'app_sha': runtime.APP_SHA, 'approved': False,
            'pricing_confirmed': False, 'approval_id': None, 'operator': None,
            'question_sha256': [hashlib.sha256(f'Synthetic question {i}'.encode()).hexdigest() for i in range(16)],
            'provider_timeout_seconds': 30, 'wall_clock_seconds': 3600, 'a_budget_usd': '0.08',
            'automatic_retries': 0, 'run_id': str(uuid4()),
            'receipt_path': 'services/rag/.cache/final/synthetic/receipt.json'}


@pytest.fixture
def ledger(tmp_path, policy):
    result = runtime.Ledger(policy, tmp_path / 'receipt.json', 'a' * 64)
    yield result
    result.stop_watchdog()


def admit(ledger, number=0):
    request = {'schema_version': '1.0.0', 'question': f'Synthetic question {number}'}
    ledger.admit(request, str(uuid4()))
    return request


def fake_client(*, counted=10, output_tokens=2, native_input=10):
    counts, generations = [], []

    def count(**payload):
        counts.append(payload)
        body = {'object': 'response.input_tokens', 'input_tokens': counted}
        return SimpleNamespace(http_response=SimpleNamespace(content=json.dumps(body).encode()))

    def generate(**payload):
        generations.append(payload)
        body = {'object': 'response', 'model': runtime.MODEL, 'status': 'completed', 'error': None,
                'incomplete_details': None, 'service_tier': 'default',
                'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
                            'content': [{'type': 'output_text', 'text': '{}'}]}],
                'usage': {'input_tokens': native_input, 'output_tokens': output_tokens,
                          'total_tokens': native_input + output_tokens}}
        return SimpleNamespace(http_response=SimpleNamespace(json=lambda: body, content=json.dumps(body).encode(),
                                                             headers={'x-request-id': 'req_synthetic'}))

    client = SimpleNamespace(responses=SimpleNamespace(
        input_tokens=SimpleNamespace(with_raw_response=SimpleNamespace(count=count)),
        with_raw_response=SimpleNamespace(create=generate)))
    return client, counts, generations


def test_complete_16_case_request_ceiling_and_overflow_is_blocked(ledger):
    for i in range(16):
        admit(ledger, i)
        for stage, limit in runtime.INPUT_LIMITS.items():
            ledger.operation(stage + '_count', lambda: 10)
            ledger.operation(stage, lambda: None, reserve=runtime._cost(limit, 512))
        ledger.operation('embedding', lambda: None, reserve=runtime._cost(128, embedding=True))
    assert ledger.state['provider_attempts'] == 112
    assert ledger.state['generation_attempts'] == ledger.state['free_count_attempts'] == 48
    assert ledger.state['embedding_attempts'] == 16
    assert Decimal(ledger.state['reserved_usd']) == Decimal('0.075584256')
    before = ledger.state['provider_attempts']
    with pytest.raises(AssessmentError):
        admit(ledger, 16)
    assert ledger.state['provider_attempts'] == before
    assert ledger.state['status'] == 'halted'


def test_restart_cannot_reset_receipt_or_allowance(ledger, policy):
    admit(ledger)
    raw = ledger.path.read_bytes()
    with pytest.raises(FileExistsError):
        runtime.Ledger(policy, ledger.path, 'a' * 64)
    assert ledger.path.read_bytes() == raw


def test_later_rejected_request_preserves_original_stop_reason(ledger):
    admit(ledger)
    ledger.halt('rate_limit')
    raw = ledger.path.read_bytes()
    with pytest.raises(RagServiceError):
        runtime.BoundedBackend(None, ledger).retrieve({'schema_version': '1.0.0', 'question': 'Synthetic question 0'})
    assert ledger.state['stop_code'] == 'rate_limit'
    assert ledger.path.read_bytes() == raw


def test_unapproved_question_and_duplicate_request_id_do_not_dispatch(ledger):
    request = admit(ledger)
    with pytest.raises(AssessmentError):
        ledger.admit(request, str(uuid4()))
    assert ledger.state['provider_attempts'] == 0
    assert len(ledger.state['requests']) == 1


def test_provider_error_keeps_reserved_cost_and_prevents_further_calls(ledger):
    admit(ledger)

    def failure():
        raise AssessmentError('rate_limit')

    with pytest.raises(AssessmentError):
        ledger.operation('answer', failure, reserve=Decimal('0.001'))
    assert ledger.state['reserved_usd'] == '0.001'
    assert ledger.state['provider_attempts'] == 1
    with pytest.raises(AssessmentError):
        ledger.operation('support', lambda: pytest.fail('A second provider call was attempted.'))
    assert ledger.state['provider_attempts'] == 1
    assert ledger.current['operations'][0]['status'] == 'failed_reserved'


def test_hard_deadline_does_not_accept_late_result_or_dispatch_next_operation(ledger, monkeypatch):
    admit(ledger)
    monkeypatch.setattr(runtime, 'TIMEOUT', .02)

    def slow():
        time.sleep(.08)
        return 'late source or answer body'

    started = time.monotonic()
    with pytest.raises(AssessmentError):
        ledger.operation('answer', slow, reserve=Decimal('0.001'))
    assert time.monotonic() - started < .07
    raw = ledger.path.read_bytes()
    time.sleep(.10)
    assert ledger.path.read_bytes() == raw
    assert ledger.state['reserved_usd'] == '0.001'
    assert ledger.current['operations'][0]['status'] == 'uncertain_timeout_reserved'
    assert b'late source' not in raw


def test_wall_clock_check_stops_before_provider_dispatch(ledger):
    admit(ledger)
    ledger.deadline = ledger.clock() - 1
    with pytest.raises(AssessmentError):
        ledger.operation('answer', lambda: pytest.fail('Expired run dispatched a request.'))
    assert ledger.state['provider_attempts'] == 0
    assert ledger.state['stop_code'] == 'wall_clock_limit'


def test_idle_watchdog_persists_halt_without_waiting_for_another_request(ledger):
    ledger.deadline = ledger.clock() + .02
    limit = time.monotonic() + 2
    receipt = {}
    while time.monotonic() < limit:
        # Observe the durable result after the watchdog finishes its atomic write.
        with ledger.receipt_lock:
            receipt = json.loads(ledger.path.read_bytes())
        if receipt.get('stop_code') == 'wall_clock_limit':
            break
        time.sleep(.01)
    assert receipt.get('stop_code') == 'wall_clock_limit'
    assert receipt['status'] == 'halted'
    assert ledger.state['provider_attempts'] == 0


def test_count_payload_is_free_but_counted_and_generation_reserved(ledger):
    admit(ledger)
    client, counts, generations = fake_client()
    providers = runtime.Providers(ledger, client, None, None)
    payload = {'model': runtime.MODEL, 'input': 'unlogged synthetic input', 'max_output_tokens': 512,
               'store': False, 'stream': False, 'background': False}
    providers.complete('question_parts', payload)
    assert len(counts) == len(generations) == 1
    assert 'max_output_tokens' not in counts[0] and 'store' not in counts[0]
    assert generations[0]['service_tier'] == 'default'
    assert ledger.state['provider_attempts'] == 2
    assert ledger.state['free_count_attempts'] == ledger.state['generation_attempts'] == 1
    assert Decimal(ledger.state['reserved_usd']) == runtime._cost(10, 512)
    assert ledger.current['operations'][1]['provider_request_id'] == 'req_synthetic'
    assert b'unlogged synthetic input' not in ledger.path.read_bytes()


@pytest.mark.parametrize('counted,native_input,output_tokens', [(4097, 10, 2), (10, True, 2), (10, 10, 513)])
def test_bad_count_or_usage_stops_without_additional_dispatch(ledger, counted, native_input, output_tokens):
    admit(ledger)
    client, counts, generations = fake_client(counted=counted, native_input=native_input, output_tokens=output_tokens)
    providers = runtime.Providers(ledger, client, None, None)
    with pytest.raises(AssessmentError):
        providers.complete('question_parts', {'model': runtime.MODEL, 'input': 'synthetic'})
    assert len(counts) == 1
    assert len(generations) == (0 if counted > 4096 else 1)
    assert ledger.state['status'] == 'halted'


def test_valid_insufficient_result_is_not_a_failure_and_receipt_has_no_body(ledger):
    backend = SimpleNamespace(answer=lambda request: {'text': 'Synthetic unsupported output', 'claims': []})
    guarded = runtime.BoundedBackend(backend, ledger)
    context = runtime.REQUEST_ID.set(str(uuid4()))
    try:
        result = guarded.answer({'schema_version': '1.0.0', 'question': 'Synthetic question 0'})
    finally:
        runtime.REQUEST_ID.reset(context)
    assert result['claims'] == []
    assert ledger.state['status'] == 'running'
    raw = ledger.path.read_bytes()
    assert b'Synthetic question 0' not in raw and b'Synthetic unsupported output' not in raw
    assert ledger.state['requests'][0]['status'] == 'completed'


def test_separate_retrieve_is_denied_before_any_provider_operation(ledger):
    guarded = runtime.BoundedBackend(None, ledger)
    with pytest.raises(RagServiceError):
        guarded.retrieve({'schema_version': '1.0.0', 'question': 'Synthetic question 0'})
    assert ledger.state['provider_attempts'] == 0


def test_preflight_uses_no_provider_or_credentials(policy, tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, 'read_policy', lambda path, root: (
        policy | {'question_sha256': []}, {'corpus': {'version': 'x'}, 'corpus_artifact_sha256': 'a'},
        tmp_path / 'absent.json', 'b' * 64))
    monkeypatch.setattr(runtime, 'load_corpus', lambda **kwargs: SimpleNamespace(passage_count=617, artifact_sha256='a'))
    monkeypatch.setattr(runtime, 'local_tokenizer', lambda: None)
    result = runtime.preflight(Path('unused'))
    assert result['status'] == 'preflight_blocked'
    assert result['provider_calls'] == 0
    assert result['max_generation_input_tokens'] == 451072
    assert result['max_generation_output_tokens'] == 24576
    assert result['max_embedding_input_tokens'] == 2048


def test_serve_requires_approval_before_constructing_live_clients(monkeypatch):
    monkeypatch.setattr(runtime, 'preflight', lambda path, root: {'status': 'preflight_blocked'})
    with pytest.raises(AssessmentError):
        runtime.build_app(Path('unused'))


def test_long_query_is_rejected_before_count_or_generation(ledger):
    client, counts, generations = fake_client()
    encoder = SimpleNamespace(encode=lambda text, **kwargs: list(range(len(text))))
    providers = runtime.Providers(ledger, client, None, encoder)
    with pytest.raises(AssessmentError):
        providers.requirements({'schema_version': '1.0.0', 'question': 'x' * 129})
    assert counts == generations == []
    assert ledger.state['provider_attempts'] == 0


def test_startup_failure_halts_receipt_and_closes_constructed_client(tmp_path, policy, monkeypatch):
    path = tmp_path / 'startup.json'
    closed = []
    monkeypatch.setattr(runtime, 'preflight', lambda *a, **k: {'status': 'preflight_ready_for_operator_checks'})
    monkeypatch.setattr(runtime, 'read_policy', lambda *a, **k: (policy, {}, path, 'a' * 64))
    monkeypatch.setattr(runtime, 'local_tokenizer', lambda: None)
    monkeypatch.setattr(runtime.openai, 'OpenAI', lambda **kwargs: SimpleNamespace(close=lambda: closed.append('client')))

    def fail(**kwargs):
        raise ValueError('Synthetic startup failure with no provider calls.')

    monkeypatch.setattr(runtime, 'OpenAIEmbedder', fail)
    monkeypatch.setenv('NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS', 'true')
    monkeypatch.setenv('NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS', 'true')
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-unused-key')
    monkeypatch.setenv('NOTELENS_RAG_SERVICE_TOKEN', 'synthetic-unused-token')
    with pytest.raises(AssessmentError):
        runtime.build_app(Path('unused'))
    assert closed == ['client']
    assert json.loads(path.read_bytes())['stop_code'] == 'startup_configuration_error'


def test_authenticated_http_readiness_success_identity_and_overflow(ledger):
    body = mock_result('literature-answer', 'sufficient')
    body['mode'] = body['retrieval_provenance']['mode'] = 'live'
    for component in body['components']:
        component.update(mode='live', provider='openai', model=runtime.MODEL)
    underlying = SimpleNamespace(mode='live', model_version=runtime.MODEL, is_ready=lambda: True,
                                 answer=lambda request: body)
    app = create_app(Settings(mode='live', service_token='synthetic-token'),
                     backend=runtime.BoundedBackend(underlying, ledger))
    runtime.attach_request_identity(app)
    with TestClient(app) as client:
        assert client.get('/health/ready').status_code == 401
        assert client.get('/health/ready', headers={'Authorization': 'Bearer synthetic-token'}).status_code == 200
        assert ledger.state['provider_attempts'] == 0 and ledger.state['requests'] == []
        for i in range(16):
            identifier = str(uuid4())
            headers = {'Authorization': 'Bearer synthetic-token', 'X-Request-ID': identifier}
            response = client.post('/v1/literature-answer', headers=headers,
                                   json={'schema_version': '1.0.0', 'question': f'Synthetic question {i}'})
            assert response.status_code == 200
            assert response.headers['X-Request-ID'] == identifier
            assert response.json()['mode'] == 'live'
        assert len(ledger.state['requests']) == 16
        response = client.post('/v1/literature-answer', headers={
            'Authorization': 'Bearer synthetic-token', 'X-Request-ID': str(uuid4())},
            json={'schema_version': '1.0.0', 'question': 'Synthetic question 16'})
        assert response.status_code == 422
        assert ledger.state['provider_attempts'] == 0
