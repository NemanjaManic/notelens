"""Verify one partial completion, prior-cost carry, and closed execution gates."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from types import SimpleNamespace

import httpx2 as httpx
import openai
import pytest

from notelens_rag.answer_trial import INPUT_LIMIT, LIMIT, PARAMETERS, prepare_from_history
from notelens_rag.answers import PARTIAL_POLICY, answer_request
from notelens_rag.assessment_trial import AssessmentError, AssessmentSettings, _money
from notelens_rag.embeddings import identity
from notelens_rag.partial_answer_trial import PublicPartialAnswerTrial
from notelens_rag.support import support_context_sha256

from test_answers import context, envelope, output
from test_assessment_trial import trial
from test_answer_trial import answer_run, make_trial


@pytest.fixture
def partial_run(answer_run, context):
    coverage, prior_plan, _, _ = answer_run
    request, candidates, requirements, assessment = deepcopy(context)
    candidates['mode'] = 'live'
    assessment['parts'][1].update(status='not_supported', reason='Missing duration.', evidence=[])
    digest = support_context_sha256(request, candidates, requirements)
    inputs = {'request': request, 'candidates': candidates, 'requirements': requirements}
    coverage.cases = {'CQ-02': SimpleNamespace(context_sha256=digest, inputs_json=json.dumps(inputs))}
    coverage.scope_sha256 = 'synthetic-coverage-scope'
    cache = coverage.folder/'results/CQ-02.json'
    cache.parent.mkdir()
    cache.write_text(json.dumps({'question_id': 'CQ-02', 'scope_sha256': coverage.scope_sha256,
        'context_sha256': digest, 'result': {'decision': {'coverage': 'partial', 'parts': assessment['parts'],
                                                        'context_sha256': digest}}}), encoding='utf-8')
    coverage._ledger()['attempts'][0].update(question_id='CQ-02', result_sha256=hashlib.sha256(cache.read_bytes()).hexdigest())
    coverage._ledger()['attempts'][1]['question_id'] = 'CQ-08'
    ledger_path = coverage.folder/'usage.json'
    ledger_path.write_text(json.dumps(coverage._ledger()), encoding='utf-8')
    prior_plan['coverage_ledger_sha256'] = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
    previous = make_trial(answer_run, [], approved=True)
    previous.run(execute=True, budget_usd=LIMIT)
    prepared = prepare_from_history(coverage, 'CQ-02')
    plan = {'format_version': 'public-partial-answer-trial-v1', 'question_id': 'CQ-02', 'model': 'gpt-6-luna',
        'parameters': asdict(PARAMETERS), 'partial_policy': PARTIAL_POLICY,
        'context_sha256': prepared.context_sha256, 'prompt_sha256': prepared.prompt_sha256,
        'request_sha256': identity(answer_request(prepared, PARAMETERS)), 'max_attempts': 1, 'automatic_retries': 0,
        'previous_answer_scope_sha256': previous.scope_sha256,
        'previous_answer_ledger_sha256': hashlib.sha256((previous.folder/'usage.json').read_bytes()).hexdigest(),
        'previous_answer_result_sha256': hashlib.sha256((previous.folder/'results/CQ-01.json').read_bytes()).hexdigest(),
        'limits': {'max_input_tokens': INPUT_LIMIT, 'max_usd': LIMIT},
        'prices': {'input_usd_per_million': '0.10', 'output_usd_per_million': '0.50'},
        'execution_approved': False, 'approval': None}
    return previous, plan, previous.folder.parent/'partial-answer'


def session(partial_run, events, *, approved=False, tokens=100, unsupported=False):
    previous, plan, folder = partial_run

    def send(request):
        payload = json.loads(request.content)
        if request.url.path.endswith('/input_tokens'):
            events.append(('count', payload))
            return httpx.Response(200, json={'object': 'response.input_tokens', 'input_tokens': tokens})
        events.append(('generate', payload))
        ledger = json.loads((folder/'usage.json').read_text())
        assert ledger['attempts'][0]['status'] == 'reserved'
        inherited = _money(previous._ledger()['reserved_usd'])
        assert _money(ledger['reserved_usd']) == inherited + _money('0.000266')
        value = output('partial')
        if unsupported:
            value['claims'].append({'requirement_id': 'duration', 'text': 'Synthetic unsupported claim.', 'evidence_ids': ['e1']})
        return httpx.Response(200, json=envelope(value) | {'service_tier': 'default'})

    def factory():
        return openai.OpenAI(api_key='only-test-key', max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(send)))

    runner = PublicPartialAnswerTrial(previous, plan, folder, client_factory=factory,
        settings=AssessmentSettings(api_key='only-test-key', enabled=True))
    if approved:
        runner.plan.update(execution_approved=True, approval={
            'actor': 'Nemanja (A)', 'date': '2026-11-19', 'scope_sha256': runner.scope_sha256})
    return runner


def test_pending_partial_has_no_new_directory_lock_or_calls(partial_run):
    events = []
    runner = session(partial_run, events)
    assert runner.preflight()['execution_approved'] is False
    with pytest.raises(AssessmentError) as failure:
        runner.run(execute=True, budget_usd=LIMIT)
    assert failure.value.code == 'execution_not_approved'
    assert not runner.folder.exists() and events == []
    assert not any(folder.joinpath('.build.lock').exists() for folder in runner._history_folders())


def test_partial_completion_preserves_gap_exact_quote_and_cumulative_budget(partial_run):
    events = []
    runner = session(partial_run, events, approved=True)
    prior_files = {path: path.read_bytes() for folder in runner._history_folders() for path in folder.rglob('*.json')}
    result = runner.run(execute=True, budget_usd=LIMIT)
    assert [kind for kind, _ in events] == ['count', 'generate']
    counted, sent = (payload for _, payload in events)
    assert all(sent[key] == value for key, value in counted.items())
    assert sent['store'] is False and sent['tools'] == [] and sent['max_output_tokens'] == 512
    payload = json.loads(sent['input'])
    assert [part['requirement_id'] for part in payload['supported_parts']] == ['cause']
    assert {item['requirement_id'] for item in payload['evidence']} == {'cause'}
    body = json.loads(result['result']['body_json'])
    assert body['evidence_state'] == 'partial' and body['retrieval_provenance']['state'] == 'sufficient'
    assert len(body['claims']) == 1 and any('Duration' in warning for warning in body['warnings'])
    trace, = json.loads(result['result']['quote_trace_json'])
    source, = body['sources']
    assert source['text'][trace['start']:trace['end']] == trace['quote']
    runner.settings = AssessmentSettings()
    runner.client_factory = lambda: pytest.fail('Cached replay created a provider.')
    assert runner.run()['cache_hit'] is True and len(events) == 2
    assert all(path.read_bytes() == before for path, before in prior_files.items())


@pytest.mark.parametrize('tokens,unsupported,code,expected_events', [
    (INPUT_LIMIT+1, False, 'input_limit_exceeded', ['count']),
    (100, True, 'invalid_answer', ['count', 'generate']),
])
def test_invalid_count_or_unsupported_part_stops_one_attempt(partial_run, tokens, unsupported, code, expected_events):
    events = []
    runner = session(partial_run, events, approved=True, tokens=tokens, unsupported=unsupported)
    with pytest.raises(AssessmentError) as failure:
        runner.run(execute=True, budget_usd=LIMIT)
    assert failure.value.code == code and [kind for kind, _ in events] == expected_events
    ledger = json.loads((runner.folder/'usage.json').read_text())
    assert ledger['halted'] and ledger['attempts'][0]['status'] == 'failed'
    with pytest.raises(AssessmentError) as again:
        runner.run(execute=True, budget_usd=LIMIT)
    assert again.value.code == 'trial_retry_not_approved' and len(events) == len(expected_events)


@pytest.mark.parametrize('field', ['request_sha256', 'context_sha256', 'partial_policy', 'parameters'])
def test_changed_preparation_is_rejected_before_provider(partial_run, field):
    previous, plan, folder = partial_run
    plan[field] = 'changed'
    with pytest.raises(AssessmentError) as failure:
        PublicPartialAnswerTrial(previous, plan, folder)
    assert failure.value.code == 'partial_answer_scope_invalid' and not folder.exists()


@pytest.mark.parametrize('field', ['previous_answer_scope_sha256', 'previous_answer_ledger_sha256',
                                 'previous_answer_result_sha256'])
def test_changed_predecessor_is_rejected_before_provider(partial_run, field):
    events = []
    runner = session(partial_run, events, approved=True)
    runner.plan[field] = 'changed'
    with pytest.raises(AssessmentError) as failure:
        runner.run(execute=True, budget_usd=LIMIT)
    assert failure.value.code == 'partial_answer_history_invalid'
    assert events == [] and not runner.folder.exists()


def test_previous_folder_cannot_be_used_as_new_ledger(partial_run):
    previous, plan, _ = partial_run
    with pytest.raises(AssessmentError) as failure:
        PublicPartialAnswerTrial(previous, plan, previous.folder)
    assert failure.value.code == 'partial_answer_scope_invalid'
