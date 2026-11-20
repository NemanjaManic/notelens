"""V2 trial preparation binds one request and preserves both stopped histories."""

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import socket

import httpx2 as httpx
import openai
import pytest

from test_assessment_trial import trial, session_for, approve as approve_original
from test_assessment_retry import approve as approve_retry
from notelens_rag.assessment_trial import AssessmentError, AssessmentSettings
from notelens_rag.assessment_retry import PublicAssessmentRetry
from notelens_rag.assessor import assessment_request
from notelens_rag.embeddings import identity
from notelens_rag.evidence_selection import prepare_selection, PROMPT_VERSION, EVIDENCE_POLICY
from notelens_rag.selection_trial import PublicSelectionTrial


@pytest.fixture(autouse=True)
def no_live_access(monkeypatch):
    from notelens_rag import assessment_trial, selection_trial
    def deny(*args, **kwargs): raise AssertionError('No real key, client or network is permitted.')
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(assessment_trial, '_client', deny)
    monkeypatch.setattr(assessment_trial, 'read_assessment_settings', deny)
    monkeypatch.setattr(selection_trial, 'read_assessment_settings', deny)


def approve(session):
    session.proposal['execution_approved'] = True
    session.proposal['approval'] = {'actor': 'Synthetic test approval', 'date': '2026-11-17',
                                   'scope_sha256': session.scope_sha256}


@pytest.fixture
def history(trial):
    def build(cap='0.02'):
        trial[0]['limits']['max_usd'] = cap
        old_events = []
        original = session_for(trial, old_events, invalid_quote=True); approve_original(original)
        with pytest.raises(AssessmentError): original.run('CQ-01', execute=True, budget_usd=cap)
        first_path = original.folder/'usage.json'; first = first_path.read_bytes()
        first_ledger = json.loads(first)
        retry_plan = {'format_version': 'public-luna-assessment-retry-v1', 'prepared_on': '2026-11-17',
            'execution_approved': False, 'approval': None, 'question_id': 'CQ-01',
            'max_new_attempts': 1, 'cumulative_max_usd': cap, 'prior_trial': {
                'scope_sha256': original.scope_sha256, 'ledger_sha256': hashlib.sha256(first).hexdigest(),
                'reserved_usd': first_ledger['reserved_usd'], 'confirmed_usd': first_ledger['confirmed_usd']}}
        from test_assessment_trial import factory
        retry = PublicAssessmentRetry(original.plan, original.cases, original.folder, retry_plan,
            original.folder/'retry', mode='mock', settings=original.settings,
            client_factory=factory(old_events, invalid_quote=True))
        approve_retry(retry)
        with pytest.raises(AssessmentError): retry.run('CQ-01', execute=True, budget_usd=cap)
        second_path = retry.folder/'usage.json'; second = second_path.read_bytes(); second_ledger = json.loads(second)
        inputs = json.loads(original.cases['CQ-01'].inputs_json)
        prepared = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
        proposal = {'format_version': 'public-selection-trial-v2', 'prepared_on': '2026-11-17',
            'execution_approved': False, 'approval': None, 'question_id': 'CQ-01', 'max_new_attempts': 1,
            'cumulative_max_usd': cap, 'prompt_version': PROMPT_VERSION, 'evidence_policy': EVIDENCE_POLICY,
            'prompt_sha256': prepared.prompt_sha256, 'selection_sha256': prepared.selection_sha256,
            'request_sha256': identity(assessment_request(prepared, original.parameters)),
            'prior_trial': {'scope_sha256': retry.scope_sha256,
                'ledger_sha256': hashlib.sha256(second).hexdigest(), 'original_ledger_sha256': hashlib.sha256(first).hexdigest(),
                'reserved_usd': second_ledger['reserved_usd'], 'confirmed_usd': second_ledger['confirmed_usd']}}
        events = []
        def create(*, fail=None, before_generation=None, tokens=100):
            def client():
                def send(request):
                    body = json.loads(request.content)
                    if request.url.path.endswith('/input_tokens'):
                        events.append('count')
                        return httpx.Response(503 if fail == 'count' else 200,
                            json={'object': 'response.input_tokens', 'input_tokens': tokens})
                    events.append('generate')
                    if before_generation: before_generation()
                    if fail == 'provider': return httpx.Response(429, json={'error': {'message': 'PRIVATE_PROVIDER'}})
                    supplied = json.loads(body['input'])
                    selected = {'format_version': 'rag-support-selection-v2',
                        'context_sha256': supplied['context_sha256'], 'selection_sha256': supplied['selection_sha256'],
                        'parts': [{'requirement_id': p['requirement_id'], 'status': 'supported',
                            'reason': 'Synthetic fixture judgment.', 'evidence_ids': ['PRIVATE_ID' if fail == 'id' else 'e1']}
                                  for p in supplied['requirements']]}
                    return httpx.Response(200, json={'object': 'response', 'model': 'gpt-6-luna',
                        'status': 'completed', 'error': None, 'incomplete_details': None, 'service_tier': 'default',
                        'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed', 'content': [
                            {'type': 'output_text', 'text': json.dumps({'requirements_cover_question': True,
                                                                      'assessment': selected})}]}],
                        'usage': {'input_tokens': tokens, 'output_tokens': 50, 'total_tokens': tokens+50}})
                return openai.OpenAI(api_key='fixture-key', base_url='https://api.openai.com/v1', max_retries=0,
                    timeout=10, http_client=httpx.Client(transport=httpx.MockTransport(send)))
            return PublicSelectionTrial(original.plan, original.cases, original_folder=original.folder,
                retry_plan=retry.retry_plan, retry_folder=retry.folder, proposal=proposal, prepared=prepared,
                folder=original.folder/'selection-v2', mode='mock', settings=original.settings, client_factory=client)
        return create, original, retry, (first, second), events, proposal
    return build


def test_preview_carries_latest_total_once_without_a_key_or_new_state(history):
    create, original, retry, saved, events, _ = history()
    session = create(); session.settings = None
    result = session.preflight()
    old_total = json.loads(saved[1])['reserved_usd']
    assert result['execution_approved'] is False and result['provider_calls'] == 0
    assert result['carried_reserved_usd'] == old_total
    assert result['question_id'] == 'CQ-01' and result['max_new_attempts'] == 1
    assert events == [] and not session.folder.exists()
    assert (original.folder/'usage.json').read_bytes() == saved[0]
    assert (retry.folder/'usage.json').read_bytes() == saved[1]


@pytest.mark.parametrize('gate', ['pending', 'original_approval', 'retry_approval', 'execute', 'budget', 'activation', 'key'])
def test_every_new_activation_gate_is_required(history, gate):
    create, original, retry, _, events, _ = history(); session = create(); approve(session)
    execute, budget = True, '0.02'
    if gate == 'pending': session.proposal['execution_approved'] = False
    elif gate == 'original_approval': session.proposal['approval'] = deepcopy(original.plan['approval'])
    elif gate == 'retry_approval': session.proposal['approval'] = deepcopy(retry.retry_plan['approval'])
    elif gate == 'execute': execute = False
    elif gate == 'budget': budget = '0.04'
    elif gate == 'activation': session.settings = AssessmentSettings(api_key='fixture', enabled=False)
    else: session.settings = AssessmentSettings(enabled=True)
    with pytest.raises(AssessmentError): session.run(execute=execute, budget_usd=budget)
    assert events == [] and not session.folder.exists()


@pytest.mark.parametrize('identifier', ['CQ-02', 'CQ-08', 'patient-question'])
def test_only_the_one_declared_public_question_is_admitted(history, identifier):
    create, _, _, _, events, _ = history(); session = create(); approve(session)
    with pytest.raises(AssessmentError): session.run(identifier, execute=True, budget_usd='0.02')
    assert events == [] and not session.folder.exists()


def test_mock_execution_counts_reserves_generates_v2_and_reuses_cache(history):
    create, original, retry, saved, events, _ = history(); session = create(); approve(session)
    result = session.run(execute=True, budget_usd='0.02')
    ledger = json.loads((session.folder/'usage.json').read_text())
    assert events == ['count', 'generate'] and len(ledger['attempts']) == 1
    assert ledger['format'] == 'selection-trial-usage-v2' and ledger['prior_trial'] == session.proposal['prior_trial']
    assert Decimal(ledger['reserved_usd']) == (Decimal(json.loads(saved[1])['reserved_usd'])
                                              + Decimal(ledger['attempts'][0]['reserved_usd']))
    value = result['result']
    assert value['mode'] == 'mock' and value['prompt_version'] == PROMPT_VERSION
    assert value['decision']['parts'][0]['evidence'][0]['quote'] == 'Public synthetic text.'
    assert value['decision']['parts'][0]['evidence'][0]['start'] == 0
    session.settings = AssessmentSettings()
    assert session.run()['cache_hit'] is True and events == ['count', 'generate']
    assert (original.folder/'usage.json').read_bytes() == saved[0] and (retry.folder/'usage.json').read_bytes() == saved[1]


@pytest.mark.parametrize('fail', ['count', 'provider', 'id'])
def test_failure_retains_both_old_reservations_and_stops_without_retry(history, fail):
    create, original, retry, saved, events, _ = history(); session = create(fail=fail); approve(session)
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'; before = path.read_bytes(); ledger = json.loads(before)
    assert ledger['halted'] is True and ledger['attempts'][0]['status'] == 'failed'
    assert Decimal(ledger['reserved_usd']) >= Decimal(json.loads(saved[1])['reserved_usd'])
    if fail == 'id':
        assert ledger['attempts'][0]['diagnostic']['rule'] == 'evidence_reference' and b'PRIVATE_ID' not in before
    count = len(events)
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    assert len(events) == count and path.read_bytes() == before
    assert (original.folder/'usage.json').read_bytes() == saved[0] and (retry.folder/'usage.json').read_bytes() == saved[1]


@pytest.mark.parametrize('target', ['original', 'retry', 'current'])
def test_all_three_locks_are_respected(history, target):
    create, original, retry, _, events, _ = history(); session = create(); approve(session)
    folders = {'original': original.folder, 'retry': retry.folder, 'current': session.folder}
    folder = folders[target]; folder.mkdir(exist_ok=True); lock = folder/'.build.lock'; lock.write_text('Owned test lock')
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    assert events == [] and lock.read_text() == 'Owned test lock'


@pytest.mark.parametrize('field', ['prompt_sha256', 'selection_sha256', 'request_sha256', 'cumulative_max_usd', 'max_new_attempts'])
def test_request_and_limits_cannot_silently_drift(history, field):
    create, _, _, _, events, proposal = history()
    proposal[field] = 2 if field == 'max_new_attempts' else ('0.04' if field == 'cumulative_max_usd' else 'PRIVATE_CHANGED')
    with pytest.raises(AssessmentError):
        session = create(); approve(session); session.run(execute=True, budget_usd='0.02')
    assert events == []


@pytest.mark.parametrize('target', ['original', 'retry'])
def test_changed_or_missing_old_state_cannot_reset_accounting(history, target):
    create, original, retry, _, events, _ = history()
    folder = original.folder if target == 'original' else retry.folder
    (folder/'usage.json').write_text('{}')
    with pytest.raises(AssessmentError):
        session = create(); approve(session); session.run(execute=True, budget_usd='0.02')
    assert events == []


def test_combined_allowance_rejects_request_that_would_fit_by_itself(history):
    create, _, _, saved, events, _ = history(cap='0.003'); session = create(); approve(session)
    with pytest.raises(AssessmentError) as caught: session.run(execute=True, budget_usd='0.003')
    assert caught.value.code == 'budget_exceeded' and events == ['count']
    ledger = json.loads((session.folder/'usage.json').read_text())
    assert ledger['reserved_usd'] == json.loads(saved[1])['reserved_usd'] and ledger['halted'] is True


def test_all_reservations_and_locks_exist_before_generation(history):
    create, original, retry, saved, _, _ = history(); observed = []; session = None
    def check():
        ledger = json.loads((session.folder/'usage.json').read_text())
        assert ledger['attempts'][0]['status'] == 'reserved'
        assert Decimal(ledger['reserved_usd']) > Decimal(json.loads(saved[1])['reserved_usd'])
        assert all((folder/'.build.lock').exists() for folder in (original.folder, retry.folder, session.folder))
        observed.append(True)
    session = create(before_generation=check); approve(session)
    session.run(execute=True, budget_usd='0.02'); assert observed == [True]


def test_input_count_above_cap_never_generates(history):
    create, _, _, _, events, _ = history(); session = create(tokens=20001); approve(session)
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    assert events == ['count']


@pytest.mark.parametrize('tamper', ['cache', 'missing_ledger', 'carry', 'ancestor', 'scope'])
def test_new_cache_and_accounting_cannot_silently_reset(history, tamper):
    create, _, _, _, events, _ = history(); session = create(); approve(session)
    session.run(execute=True, budget_usd='0.02'); path = session.folder/'usage.json'
    if tamper == 'cache': (session.folder/'results/CQ-01.json').write_text('{}')
    elif tamper == 'missing_ledger': path.unlink()
    elif tamper == 'scope': session.proposal['prepared_on'] = 'changed'
    else:
        ledger = json.loads(path.read_text())
        if tamper == 'carry': ledger['reserved_usd'] = ledger['attempts'][0]['reserved_usd']
        else: ledger['prior_trial']['reserved_usd'] = '0'
        path.write_text(json.dumps(ledger))
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    assert events == ['count', 'generate']


def test_preview_cli_is_key_free_and_metadata_only(history, monkeypatch, capsys):
    from notelens_rag import selection_trial as command
    create, _, _, _, events, _ = history(); session = create(); session.settings = None
    monkeypatch.setattr(command, 'load_selection_trial', lambda: session)
    monkeypatch.setattr('sys.argv', ['selection_trial'])
    assert command.main() == 0
    value = capsys.readouterr(); assert not value.err
    assert json.loads(value.out)['execution_approved'] is False and 'Public synthetic text' not in value.out
    assert events == [] and not session.folder.exists()


def test_execute_cli_is_blocked_by_pending_consent(history, monkeypatch, capsys):
    from notelens_rag import selection_trial as command
    create, _, _, _, events, _ = history(); session = create()
    monkeypatch.setattr(command, 'load_selection_trial', lambda: session)
    monkeypatch.setattr('sys.argv', ['selection_trial', '--execute', '--budget-usd', '0.02'])
    assert command.main() == 1
    value = capsys.readouterr(); assert not value.out
    assert json.loads(value.err)['code'] == 'selection_execution_not_approved'
    assert events == [] and not session.folder.exists()


def test_both_older_paths_stay_halted_after_a_successful_mock_v2_result(history):
    create, original, retry, saved, events, _ = history(); session = create(); approve(session)
    session.run(execute=True, budget_usd='0.02')
    for runner in (original, retry):
        for question in ('CQ-01', 'CQ-02', 'CQ-08'):
            with pytest.raises(AssessmentError): runner.run(question, execute=True, budget_usd='0.02')
    assert events == ['count', 'generate']
    assert (original.folder/'usage.json').read_bytes() == saved[0] and (retry.folder/'usage.json').read_bytes() == saved[1]


def test_changed_prepared_input_is_rejected_before_client_creation(history):
    from dataclasses import replace
    create, _, _, _, events, _ = history(); session = create(); approve(session)
    session.cases['CQ-01'] = replace(session.cases['CQ-01'], input_json='PRIVATE_FORGED_INPUT')
    with pytest.raises(AssessmentError): session.run(execute=True, budget_usd='0.02')
    assert events == []


def test_failed_halt_persistence_still_blocks_another_provider_call(history, monkeypatch):
    from notelens_rag import assessment_trial
    create, original, retry, saved, events, _ = history(); session = create(fail='provider'); approve(session)
    writer = assessment_trial.atomic_json
    def fail_halt_write(path, value):
        if path == session.folder/'usage.json' and value.get('halted') is True:
            raise OSError('Synthetic halt-write failure.')
        return writer(path, value)
    monkeypatch.setattr(assessment_trial, 'atomic_json', fail_halt_write)
    with pytest.raises(AssessmentError) as caught: session.run(execute=True, budget_usd='0.02')
    assert caught.value.code == 'trial_state_invalid'
    path = session.folder/'usage.json'; before = path.read_bytes(); ledger = json.loads(before)
    assert ledger['halted'] is False and ledger['attempts'][0]['status'] == 'reserved'
    with pytest.raises(AssessmentError) as caught: session.run(execute=True, budget_usd='0.02')
    assert caught.value.code == 'trial_retry_not_approved'
    assert events == ['count', 'generate'] and path.read_bytes() == before
    assert (original.folder/'usage.json').read_bytes() == saved[0] and (retry.folder/'usage.json').read_bytes() == saved[1]
