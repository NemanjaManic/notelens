"""Run the one-answer trial through the SDK in memory with synthetic history."""

from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import httpx2 as httpx
import openai
import pytest

from notelens_rag.answer_trial import INPUT_LIMIT, LIMIT, PARAMETERS, PublicAnswerTrial, prepare_from_history
from notelens_rag.answers import answer_request
from notelens_rag.assessment_trial import AssessmentError, AssessmentSettings
from notelens_rag.embeddings import identity
from notelens_rag.support import support_context_sha256

from test_answers import context, envelope, output
from test_assessment_trial import trial


@pytest.fixture
def answer_run(context, trial):
    request, candidates, requirements, assessment = deepcopy(context)
    candidates['mode'] = 'live'
    digest = support_context_sha256(request, candidates, requirements)
    inputs = {'request': request, 'candidates': candidates, 'requirements': requirements}
    parent = trial[2]
    folders = [parent/name for name in ('original', 'retry', 'selection', 'coverage')]
    for folder in folders:
        folder.mkdir()
    original, retry, selection, coverage_folder = folders
    source = SimpleNamespace(scope_sha256='fixture-selection', folder=selection,
        cases={'CQ-01': SimpleNamespace(context_sha256=digest, inputs_json=json.dumps(inputs))})
    cache = selection/'results/CQ-01.json'
    cache.parent.mkdir()
    cache.write_text(json.dumps({'question_id': 'CQ-01', 'scope_sha256': source.scope_sha256,
        'context_sha256': digest, 'result': {'decision': {'coverage': 'full', 'parts': assessment['parts'],
                                                         'context_sha256': digest}}}), encoding='utf-8')
    source._ledger = lambda: {'attempts': [{'question_id': 'CQ-01', 'status': 'confirmed',
        'result_sha256': hashlib.sha256(cache.read_bytes()).hexdigest()}]}
    ledger = {'halted': False, 'attempts': [{'status': 'confirmed'}, {'status': 'confirmed'}],
              'reserved_usd': '0.0087813', 'confirmed_usd': '0.0032421'}
    history = coverage_folder/'usage.json'
    history.write_text(json.dumps(ledger), encoding='utf-8')
    coverage = SimpleNamespace(original_folder=original, retry_folder=retry, previous_folder=selection,
        folder=coverage_folder, _ledger=lambda: ledger, _previous_selection=lambda: source)
    prepared = prepare_from_history(coverage, 'CQ-01')
    plan = {'format_version': 'public-literature-answer-trial-v1', 'question_id': 'CQ-01', 'model': 'gpt-6-luna',
        'context_sha256': digest, 'prompt_sha256': prepared.prompt_sha256,
        'request_sha256': identity(answer_request(prepared, PARAMETERS)), 'max_attempts': 1, 'automatic_retries': 0,
        'coverage_ledger_sha256': hashlib.sha256(history.read_bytes()).hexdigest(),
        'limits': {'max_input_tokens': INPUT_LIMIT, 'max_usd': LIMIT},
        'prices': {'input_usd_per_million': '0.10', 'output_usd_per_million': '0.50'}}
    return coverage, plan, parent/'answer', history


def make_trial(answer_run, events, *, approved=False, tokens=100, fail=False):
    coverage, plan, folder, _ = answer_run

    def transport(request):
        payload = json.loads(request.content)
        assert payload['text']['format']['name'] == 'notelens_literature_answer'
        if request.url.path.endswith('/input_tokens'):
            events.append(('count', payload))
            return httpx.Response(200, json={'object': 'response.input_tokens', 'input_tokens': tokens})
        events.append(('generate', payload))
        ledger = json.loads((folder/'usage.json').read_text())
        assert ledger['attempts'][0]['status'] == 'reserved'
        assert ledger['reserved_usd'] == '0.0090473'
        claims = output()
        if fail:
            claims['claims'][0]['evidence_ids'] = ['unoffered']
        return httpx.Response(200, json=envelope(claims) | {'service_tier': 'default'})

    def client_factory():
        return openai.OpenAI(api_key='only-test-key', max_retries=0,
                             http_client=httpx.Client(transport=httpx.MockTransport(transport)))

    session = PublicAnswerTrial(coverage, plan, folder, client_factory=client_factory,
                                settings=AssessmentSettings(api_key='only-test-key', enabled=True))
    if approved:
        session.plan.update(execution_approved=True, approval={
            'actor': 'Nemanja (A)', 'date': '2026-11-18', 'scope_sha256': session.scope_sha256})
    return session


def test_pending_scope_creates_no_ledger_or_sdk_call(answer_run):
    events = []
    session = make_trial(answer_run, events)
    with pytest.raises(AssessmentError) as failure:
        session.run(execute=True, budget_usd=LIMIT)
    assert failure.value.code == 'execution_not_approved'
    assert not session.folder.exists() and events == []


def test_exact_native_requests_reserve_then_cache_and_replay(answer_run):
    events = []
    session = make_trial(answer_run, events, approved=True)
    old = answer_run[3].read_bytes()
    saved = session.run(execute=True, budget_usd=LIMIT)
    assert [event[0] for event in events] == ['count', 'generate']
    assert all(events[1][1][key] == value for key, value in events[0][1].items())
    assert events[1][1]['tools'] == [] and events[1][1]['store'] is False
    answer = json.loads(saved['result']['body_json'])
    assert answer['evidence_state'] == 'sufficient' and len(answer['claims']) == 2
    assert saved['cache_hit'] is False
    session.settings = AssessmentSettings()
    assert session.run()['cache_hit'] is True
    assert len(events) == 2 and answer_run[3].read_bytes() == old


@pytest.mark.parametrize('failure,tokens,expected_events', [
    ('input_limit_exceeded', INPUT_LIMIT+1, ['count']), ('invalid_answer', 100, ['count', 'generate']),
])
def test_bad_count_or_citation_halts_without_another_attempt(answer_run, failure, tokens, expected_events):
    events = []
    session = make_trial(answer_run, events, approved=True, tokens=tokens, fail=True)
    with pytest.raises(AssessmentError) as error:
        session.run(execute=True, budget_usd=LIMIT)
    assert error.value.code == failure
    assert [event[0] for event in events] == expected_events
    ledger = json.loads((session.folder/'usage.json').read_text())
    assert ledger['halted'] is True and ledger['attempts'][0]['status'] == 'failed'
    with pytest.raises(AssessmentError) as stopped:
        session.run(execute=True, budget_usd=LIMIT)
    assert stopped.value.code == 'trial_retry_not_approved' and len(events) == len(expected_events)
