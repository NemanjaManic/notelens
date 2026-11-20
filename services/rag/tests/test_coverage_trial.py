"""Prepare two ordered v2 probes without leaking expected verdicts or resetting usage."""

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import socket

import httpx2 as httpx
import openai
import pytest

from test_assessment_trial import trial
from test_selection_trial import history as previous_history, approve as approve_single
from notelens_rag.assessment_trial import AssessmentError, AssessmentSettings
from notelens_rag.assessor import prepare_assessment, assessment_request
from notelens_rag.evidence_selection import prepare_selection, PROMPT_VERSION, EVIDENCE_POLICY
from notelens_rag.embeddings import identity
from notelens_rag.coverage_trial import PublicCoverageTrial


def approve(session):
    session.proposal['execution_approved'] = True
    session.proposal['approval'] = {'actor': 'Synthetic test approval', 'date': '2026-11-18',
                                   'scope_sha256': session.scope_sha256}


@pytest.fixture(autouse=True)
def no_live_access(monkeypatch):
    from notelens_rag import assessment_trial, selection_trial
    def deny(*args, **kwargs): raise AssertionError('No real key, client or network in this suite.')
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(assessment_trial, '_client', deny)
    monkeypatch.setattr(assessment_trial, 'read_assessment_settings', deny)
    monkeypatch.setattr(selection_trial, 'read_assessment_settings', deny)


@pytest.fixture
def coverage(trial, previous_history):
    inputs = json.loads(trial[1]['CQ-02'].inputs_json)
    inputs['requirements'].append({'requirement_id': 'part-2', 'description': 'A second synthetic requested fact'})
    trial[1]['CQ-02'] = prepare_assessment(inputs['request'], inputs['candidates'], inputs['requirements'])
    create_single, original, retry, _, _, _ = previous_history()
    single = create_single(); approve_single(single); single.run(execute=True, budget_usd='0.02')
    paths = [original.folder/'usage.json', retry.folder/'usage.json', single.folder/'usage.json']
    before = [path.read_bytes() for path in paths]; latest = json.loads(before[2])
    cache = single.folder/'results/CQ-01.json'; prepared = {}
    for identifier in ('CQ-02', 'CQ-08'):
        source = json.loads(single.source_cases[identifier].inputs_json)
        prepared[identifier] = prepare_selection(source['request'], source['candidates'], source['requirements'])
    proposal = {'format_version': 'public-coverage-trial-v2', 'prepared_on': '2026-11-18',
        'execution_approved': False, 'approval': None, 'question_ids': ['CQ-02', 'CQ-08'],
        'max_new_attempts': 2, 'max_attempts_per_question': 1, 'cumulative_max_usd': '0.02',
        'prompt_version': PROMPT_VERSION, 'prompt_sha256': prepared['CQ-02'].prompt_sha256,
        'evidence_policy': EVIDENCE_POLICY,
        'requests': {identifier: {'context_sha256': p.context_sha256, 'selection_sha256': p.selection_sha256,
                                  'request_sha256': identity(assessment_request(p, single.parameters))}
                     for identifier, p in prepared.items()},
        'prior_trial': {'scope_sha256': single.scope_sha256, 'ledger_sha256': hashlib.sha256(before[2]).hexdigest(),
            'result_sha256': hashlib.sha256(cache.read_bytes()).hexdigest(),
            'original_ledger_sha256': hashlib.sha256(before[0]).hexdigest(),
            'retry_ledger_sha256': hashlib.sha256(before[1]).hexdigest(),
            'reserved_usd': latest['reserved_usd'], 'confirmed_usd': latest['confirmed_usd']}}
    events = []
    def create(*, fail=None, fail_question='CQ-02', before_generation=None, tokens=100):
        def client():
            def send(request):
                body = json.loads(request.content); data = json.loads(body['input'])
                identifier = 'CQ-02' if 'CQ-02' in data['question'] else 'CQ-08'
                active = fail if identifier == fail_question else None
                if request.url.path.endswith('/input_tokens'):
                    events.append(('count', identifier))
                    return httpx.Response(503 if active == 'count' else 200,
                        json={'object': 'response.input_tokens', 'input_tokens': tokens})
                events.append(('generate', identifier))
                if before_generation: before_generation(identifier)
                if active == 'provider': return httpx.Response(429, json={'error': {'message': 'PRIVATE_PROVIDER'}})
                parts = []
                for index, requirement in enumerate(data['requirements']):
                    supported = identifier == 'CQ-02' and index == 0
                    evidence = ['e1'] if supported else []
                    if active == 'id': supported, evidence = True, ['PRIVATE_ID']
                    parts.append({'requirement_id': requirement['requirement_id'],
                        'status': 'supported' if supported else 'not_supported', 'reason': 'Synthetic judgment only.',
                        'evidence_ids': evidence})
                assessment = {'format_version': 'rag-support-selection-v2', 'context_sha256': data['context_sha256'],
                              'selection_sha256': data['selection_sha256'], 'parts': parts}
                return httpx.Response(200, json={'object': 'response', 'model': 'gpt-6-luna', 'status': 'completed',
                    'error': None, 'incomplete_details': None, 'service_tier': 'default',
                    'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed', 'content': [
                        {'type': 'output_text', 'text': json.dumps({'requirements_cover_question': True, 'assessment': assessment})}]}],
                    'usage': {'input_tokens': tokens, 'output_tokens': 50, 'total_tokens': tokens+50}})
            return openai.OpenAI(api_key='fixture-key', base_url='https://api.openai.com/v1', max_retries=0, timeout=10,
                http_client=httpx.Client(transport=httpx.MockTransport(send)))
        return PublicCoverageTrial(single.plan, single.source_cases, original_folder=original.folder,
            retry_plan=retry.retry_plan, retry_folder=retry.folder, previous_proposal=single.proposal,
            previous_folder=single.folder, proposal=proposal, prepared=prepared, folder=original.folder/'coverage-v2',
            mode='mock', settings=original.settings, client_factory=client)
    return create, paths, before, cache, events, proposal


def test_preview_is_key_free_and_carries_the_latest_total_once(coverage):
    create, paths, before, _, events, _ = coverage; session = create(); session.settings = None
    value = session.preflight()
    assert value['execution_approved'] is False and value['provider_calls'] == 0
    assert value['question_ids'] == ['CQ-02', 'CQ-08'] and value['max_new_attempts'] == 2
    assert Decimal(value['carried_reserved_usd']) == Decimal(json.loads(before[2])['reserved_usd'])
    assert Decimal(value['carried_confirmed_usd']) == Decimal(json.loads(before[2])['confirmed_usd'])
    assert events == [] and not session.folder.exists() and [path.read_bytes() for path in paths] == before


@pytest.mark.parametrize('gate', ['pending', 'old_approval', 'execute', 'budget', 'activation', 'key'])
def test_separate_consent_and_all_activation_gates_are_required(coverage, gate):
    create, _, _, _, events, _ = coverage; session = create(); approve(session)
    execute, budget = True, '0.02'
    if gate == 'pending': session.proposal['execution_approved'] = False
    elif gate == 'old_approval': session.proposal['approval'] = deepcopy(session.previous_proposal['approval'])
    elif gate == 'execute': execute = False
    elif gate == 'budget': budget = '0.03'
    elif gate == 'activation': session.settings = AssessmentSettings(api_key='fixture', enabled=False)
    else: session.settings = AssessmentSettings(enabled=True)
    with pytest.raises(AssessmentError): session.run('CQ-02', execute=execute, budget_usd=budget)
    assert events == [] and not session.folder.exists()


def test_two_distinct_calls_return_partial_then_none_and_preserve_gaps(coverage):
    create, paths, before, _, events, _ = coverage; session = create(); approve(session)
    first = session.run('CQ-02', execute=True, budget_usd='0.02')['result']['decision']
    assert first['coverage'] == 'partial' and tuple(first['missing_requirement_ids']) == ('part-2',)
    assert events == [('count', 'CQ-02'), ('generate', 'CQ-02')]
    second = session.run('CQ-08', execute=True, budget_usd='0.02')['result']['decision']
    assert second['coverage'] == 'none' and not second['parts'][0]['evidence']
    assert events == [('count', 'CQ-02'), ('generate', 'CQ-02'), ('count', 'CQ-08'), ('generate', 'CQ-08')]
    ledger = json.loads((session.folder/'usage.json').read_text())
    assert ledger['format'] == 'coverage-trial-usage-v2' and len(ledger['attempts']) == 2
    assert Decimal(ledger['reserved_usd']) == Decimal(json.loads(before[2])['reserved_usd']) + sum(
        Decimal(attempt['reserved_usd']) for attempt in ledger['attempts'])
    session.settings = AssessmentSettings()
    assert session.run('CQ-02')['cache_hit'] is True and session.run('CQ-08')['cache_hit'] is True
    assert len(events) == 4 and [path.read_bytes() for path in paths] == before


@pytest.mark.parametrize('identifier', ['CQ-01', 'patient-question', 'CQ-08'])
def test_unlisted_questions_and_out_of_order_first_call_do_not_reach_provider(coverage, identifier):
    create, _, _, _, events, _ = coverage; session = create(); approve(session)
    with pytest.raises(AssessmentError): session.run(identifier, execute=True, budget_usd='0.02')
    assert events == []


@pytest.mark.parametrize('fail', ['count', 'provider', 'id'])
def test_first_failure_halts_both_new_cases_and_preserves_reservation(coverage, fail):
    create, paths, before, _, events, _ = coverage; session = create(fail=fail); approve(session)
    with pytest.raises(AssessmentError): session.run('CQ-02', execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'; saved = path.read_bytes(); ledger = json.loads(saved)
    assert ledger['halted'] is True and ledger['attempts'][0]['status'] == 'failed'
    count = len(events)
    for identifier in ('CQ-02', 'CQ-08'):
        with pytest.raises(AssessmentError): session.run(identifier, execute=True, budget_usd='0.02')
    assert len(events) == count and path.read_bytes() == saved and [p.read_bytes() for p in paths] == before
    assert b'PRIVATE_ID' not in saved and Decimal(ledger['reserved_usd']) >= Decimal(json.loads(before[2])['reserved_usd'])


def test_second_failure_keeps_first_result_readable_without_retrying_either(coverage):
    create, _, _, _, events, _ = coverage; session = create(fail='id', fail_question='CQ-08'); approve(session)
    session.run('CQ-02', execute=True, budget_usd='0.02')
    with pytest.raises(AssessmentError): session.run('CQ-08', execute=True, budget_usd='0.02')
    assert session.run('CQ-02')['cache_hit'] is True
    with pytest.raises(AssessmentError): session.run('CQ-08', execute=True, budget_usd='0.02')
    assert len(events) == 4


@pytest.mark.parametrize('target', [0, 1, 2, 'cache'])
def test_changed_ancestor_or_validated_result_is_rejected(coverage, target):
    create, paths, _, cache, events, _ = coverage
    path = cache if target == 'cache' else paths[target]; path.write_text('{}')
    with pytest.raises(AssessmentError):
        session = create(); approve(session); session.run('CQ-02', execute=True, budget_usd='0.02')
    assert events == []


@pytest.mark.parametrize('target', ['request', 'catalog', 'allowance', 'order'])
def test_request_scope_and_caps_cannot_drift(coverage, target):
    create, _, _, _, events, proposal = coverage
    if target == 'request': proposal['requests']['CQ-02']['request_sha256'] = 'changed'
    elif target == 'catalog': proposal['requests']['CQ-08']['selection_sha256'] = 'changed'
    elif target == 'allowance': proposal['cumulative_max_usd'] = '0.04'
    else: proposal['question_ids'].reverse()
    with pytest.raises(AssessmentError):
        session = create(); approve(session); session.run('CQ-02', execute=True, budget_usd='0.02')
    assert events == []


@pytest.mark.parametrize('index', [0, 1, 2, 3])
def test_every_history_and_current_lock_is_respected(coverage, index):
    create, paths, _, _, events, _ = coverage; session = create(); approve(session)
    folders = [path.parent for path in paths]+[session.folder]
    folder = folders[index]; folder.mkdir(exist_ok=True)
    lock = folder/'.build.lock'; lock.write_text('Owned test lock')
    with pytest.raises(AssessmentError): session.run('CQ-02', execute=True, budget_usd='0.02')
    assert events == [] and lock.read_text() == 'Owned test lock'


@pytest.mark.parametrize('tamper', ['cache', 'missing_ledger', 'carry', 'ancestor', 'order'])
def test_new_results_and_accounting_fail_closed_on_tampering(coverage, tamper):
    create, _, _, _, events, _ = coverage; session = create(); approve(session)
    for identifier in ('CQ-02', 'CQ-08'): session.run(identifier, execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'
    if tamper == 'cache': (session.folder/'results/CQ-02.json').write_text('{}')
    elif tamper == 'missing_ledger': path.unlink()
    else:
        ledger = json.loads(path.read_text())
        if tamper == 'carry': ledger['reserved_usd'] = ledger['attempts'][0]['reserved_usd']
        elif tamper == 'ancestor': ledger['prior_trial']['confirmed_usd'] = '0'
        else: ledger['attempts'].reverse()
        path.write_text(json.dumps(ledger))
    with pytest.raises(AssessmentError): session.run('CQ-02', execute=True, budget_usd='0.02')
    assert len(events) == 4


def test_input_limit_prevents_generation(coverage):
    create, _, _, _, events, _ = coverage; session = create(tokens=20001); approve(session)
    with pytest.raises(AssessmentError) as caught: session.run('CQ-02', execute=True, budget_usd='0.02')
    assert caught.value.code == 'input_limit_exceeded' and events == [('count', 'CQ-02')]


def test_reservation_and_four_locks_are_present_before_generation(coverage):
    create, paths, before, _, _, _ = coverage; observed = []; session = None
    def check(identifier):
        ledger = json.loads((session.folder/'usage.json').read_text())
        assert ledger['attempts'][-1]['question_id'] == identifier and ledger['attempts'][-1]['status'] == 'reserved'
        assert Decimal(ledger['reserved_usd']) > Decimal(json.loads(before[2])['reserved_usd'])
        assert all((folder/'.build.lock').exists() for folder in [p.parent for p in paths]+[session.folder])
        observed.append(identifier)
    session = create(before_generation=check); approve(session)
    session.run('CQ-02', execute=True, budget_usd='0.02')
    assert observed == ['CQ-02']


def test_cli_inspection_and_missing_question_never_load_a_key(coverage, monkeypatch, capsys):
    from notelens_rag import coverage_trial as command
    create, _, _, _, events, _ = coverage; session = create(); session.settings = None
    monkeypatch.setattr(command, 'load_coverage_trial', lambda: session)
    monkeypatch.setattr('sys.argv', ['coverage_trial'])
    assert command.main() == 0
    value = capsys.readouterr(); assert not value.err and json.loads(value.out)['provider_calls'] == 0
    monkeypatch.setattr('sys.argv', ['coverage_trial', '--execute', '--budget-usd', '0.02'])
    assert command.main() == 1
    value = capsys.readouterr(); assert json.loads(value.err)['code'] == 'coverage_question_required'
    assert events == [] and not session.folder.exists()


def test_incomplete_halt_write_still_blocks_both_questions(coverage, monkeypatch):
    from notelens_rag import assessment_trial
    create, paths, before, _, events, _ = coverage; session = create(fail='provider'); approve(session)
    original = assessment_trial.atomic_json
    def fail_write(path, value):
        if path == session.folder/'usage.json' and value.get('halted') is True:
            raise OSError('Synthetic halt write failure.')
        return original(path, value)
    monkeypatch.setattr(assessment_trial, 'atomic_json', fail_write)
    with pytest.raises(AssessmentError): session.run('CQ-02', execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'; saved = path.read_bytes()
    assert json.loads(saved)['attempts'][0]['status'] == 'reserved'
    for identifier in ('CQ-02', 'CQ-08'):
        with pytest.raises(AssessmentError): session.run(identifier, execute=True, budget_usd='0.02')
    assert events == [('count', 'CQ-02'), ('generate', 'CQ-02')]
    assert path.read_bytes() == saved and [path.read_bytes() for path in paths] == before
