"""Retry preparation must preserve history, carry cost and require fresh consent."""

from copy import deepcopy
from decimal import Decimal
import hashlib
import json

import pytest

from test_assessment_trial import trial, session_for, approve as approve_trial, factory
from notelens_rag.assessor import AssessmentError
from notelens_rag.assessment_trial import AssessmentSettings
from notelens_rag.assessment_retry import PublicAssessmentRetry


@pytest.fixture(autouse=True)
def forbid_live_configuration_and_transport(monkeypatch):
    import socket
    from notelens_rag import assessment_retry, assessment_trial
    def forbidden(*args, **kwargs):
        raise AssertionError('No real credentials, live client or network may be used here.')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(assessment_trial, '_client', forbidden)
    monkeypatch.setattr(assessment_retry, 'read_assessment_settings', forbidden)


def approve(session):
    session.retry_plan['execution_approved'] = True
    session.retry_plan['approval'] = {'actor': 'Synthetic test approval', 'date': '2026-11-17',
                                    'scope_sha256': session.scope_sha256}


@pytest.fixture
def retry(trial):
    events = []
    original = session_for(trial, events, invalid_quote=True)
    approve_trial(original)
    with pytest.raises(AssessmentError):
        original.run('CQ-01', execute=True, budget_usd='0.02')
    path = original.folder/'usage.json'
    before = path.read_bytes()
    ledger = json.loads(before)
    proposal = {'format_version': 'public-luna-assessment-retry-v1', 'prepared_on': '2026-11-17',
        'execution_approved': False, 'approval': None, 'question_id': 'CQ-01',
        'max_new_attempts': 1, 'cumulative_max_usd': '0.02', 'prior_trial': {
            'scope_sha256': original.scope_sha256, 'ledger_sha256': hashlib.sha256(before).hexdigest(),
            'reserved_usd': ledger['reserved_usd'], 'confirmed_usd': ledger['confirmed_usd']}}
    events.clear()
    def create(**kwargs):
        return PublicAssessmentRetry(original.plan, original.cases, original.folder, proposal,
            original.folder/'retry-cq01', mode='mock',
            settings=AssessmentSettings(api_key='fixture-key', enabled=True),
            client_factory=factory(events, **kwargs))
    return create, original, before, events, proposal


def test_preflight_is_key_free_and_counts_old_reservation(retry):
    create, original, before, events, _ = retry
    session = create()
    session.settings = None
    report = session.preflight()
    assert report['execution_approved'] is False and report['provider_calls'] == 0
    assert report['question_id'] == 'CQ-01' and report['max_new_attempts'] == 1
    assert Decimal(report['carried_reserved_usd']) > 0
    assert Decimal(report['maximum_combined_reservation_usd']) == (
        Decimal(report['carried_reserved_usd']) + Decimal(report['maximum_new_reservation_usd']))
    assert events == [] and not session.folder.exists()
    assert (original.folder/'usage.json').read_bytes() == before


@pytest.mark.parametrize('gate', ['unapproved', 'old_approval', 'scope', 'execute', 'budget', 'activation', 'key'])
def test_fresh_approval_and_every_execution_gate_are_required(retry, gate):
    create, original, before, events, _ = retry
    session = create()
    approve(session)
    execute, budget = True, '0.02'
    if gate == 'unapproved': session.retry_plan['execution_approved'] = False
    elif gate == 'old_approval': session.retry_plan['approval'] = deepcopy(original.plan['approval'])
    elif gate == 'scope': session.retry_plan['approval']['scope_sha256'] = 'stale'
    elif gate == 'execute': execute = False
    elif gate == 'budget': budget = '0.03'
    elif gate == 'activation': session.settings = AssessmentSettings(api_key='fixture', enabled=False)
    else: session.settings = AssessmentSettings(enabled=True)
    with pytest.raises(AssessmentError):
        session.run('CQ-01', execute=execute, budget_usd=budget)
    assert events == [] and not session.folder.exists()
    assert (original.folder/'usage.json').read_bytes() == before


@pytest.mark.parametrize('identifier', ['CQ-02', 'CQ-08', 'patient-question'])
def test_only_first_public_question_can_be_retried(retry, identifier):
    create, _, _, events, _ = retry
    session = create(); approve(session)
    with pytest.raises(AssessmentError):
        session.run(identifier, execute=True, budget_usd='0.02')
    assert events == [] and not session.folder.exists()


def test_one_mock_retry_carries_prior_usage_and_cache_never_calls_again(retry):
    create, original, before, events, _ = retry
    session = create(); approve(session)
    result = session.run('CQ-01', execute=True, budget_usd='0.02')
    ledger = json.loads((session.folder/'usage.json').read_text())
    old = json.loads(before)
    assert ledger['format'] == 'assessment-retry-usage-v1'
    assert ledger['prior_trial'] == session.retry_plan['prior_trial']
    assert events == ['count', 'generate'] and len(ledger['attempts']) == 1
    assert result['result']['mode'] == 'mock' and result['result']['decision']['coverage'] == 'full'
    assert Decimal(ledger['reserved_usd']) == (
        Decimal(old['reserved_usd']) + Decimal(ledger['attempts'][0]['reserved_usd']))
    assert Decimal(ledger['confirmed_usd']) == (
        Decimal(old['confirmed_usd']) + Decimal(ledger['attempts'][0]['confirmed_usd']))
    session.settings = AssessmentSettings()
    assert session.run('CQ-01')['cache_hit'] is True
    assert session.run('CQ-01')['cache_hit'] is True and events == ['count', 'generate']
    assert (original.folder/'usage.json').read_bytes() == before


@pytest.mark.parametrize('failure', ['count', 'generation', 'quote'])
def test_failure_retains_combined_cost_and_cannot_be_repeated(retry, failure):
    create, original, before, events, _ = retry
    session = create(fail_count=failure == 'count', fail_generation=failure == 'generation',
                     invalid_quote=failure == 'quote')
    approve(session)
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'; saved = path.read_bytes(); ledger = json.loads(saved)
    assert ledger['halted'] is True and ledger['attempts'][0]['status'] == 'failed'
    assert 'diagnostic' in ledger['attempts'][0]
    carried = Decimal(json.loads(before)['reserved_usd'])
    assert Decimal(ledger['reserved_usd']) == carried + Decimal(ledger['attempts'][0]['reserved_usd'])
    if failure != 'count': assert Decimal(ledger['reserved_usd']) > carried
    if failure == 'quote':
        assert ledger['attempts'][0]['diagnostic']['rule'] == 'quote_mismatch'
        assert b'Incorrect private text' not in saved
    count = len(events)
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    assert len(events) == count and path.read_bytes() == saved
    assert (original.folder/'usage.json').read_bytes() == before


@pytest.mark.parametrize('tamper', ['missing_history', 'changed_history', 'wrong_scope', 'carry', 'cap', 'attempts'])
def test_history_and_proposal_cannot_reset_or_expand_the_scope(retry, tamper):
    create, original, before, events, proposal = retry
    if tamper == 'missing_history': (original.folder/'usage.json').unlink()
    elif tamper == 'changed_history': (original.folder/'usage.json').write_bytes(before+b' ')
    elif tamper == 'wrong_scope': proposal['prior_trial']['scope_sha256'] = 'changed'
    elif tamper == 'carry': proposal['prior_trial']['reserved_usd'] = '0'
    elif tamper == 'cap': proposal['cumulative_max_usd'] = '0.04'
    else: proposal['max_new_attempts'] = 2
    with pytest.raises(AssessmentError):
        session = create(); approve(session)
        session.run('CQ-01', execute=True, budget_usd='0.02')
    assert events == []


def test_old_trial_stays_halted_even_after_successful_mock_retry(retry):
    create, original, before, events, _ = retry
    session = create(); approve(session)
    session.run('CQ-01', execute=True, budget_usd='0.02')
    for identifier in ('CQ-01', 'CQ-02', 'CQ-08'):
        with pytest.raises(AssessmentError) as caught:
            original.run(identifier, execute=True, budget_usd='0.02')
        assert caught.value.code == 'trial_retry_not_approved'
    assert events == ['count', 'generate'] and (original.folder/'usage.json').read_bytes() == before


def test_old_trial_lock_blocks_retry_without_being_removed(retry):
    create, original, _, events, _ = retry
    lock = original.folder/'.build.lock'; lock.write_text('Owned test lock')
    session = create(); approve(session)
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    assert events == [] and lock.read_text() == 'Owned test lock'


def test_retry_lock_blocks_duplicate_process(retry):
    create, original, before, events, _ = retry
    session = create(); approve(session)
    session.folder.mkdir(); lock = session.folder/'.build.lock'; lock.write_text('Owned test lock')
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    assert events == [] and lock.exists() and not (original.folder/'.build.lock').exists()
    assert (original.folder/'usage.json').read_bytes() == before


def test_reservation_is_persisted_before_retry_generation(retry):
    create, original, before, _, _ = retry
    observed = []
    session = None
    def check():
        ledger = json.loads((session.folder/'usage.json').read_text())
        assert ledger['attempts'][0]['status'] == 'reserved'
        assert Decimal(ledger['reserved_usd']) > Decimal(json.loads(before)['reserved_usd'])
        assert (original.folder/'.build.lock').exists() and (session.folder/'.build.lock').exists()
        observed.append(True)
    session = create(before_generation=check); approve(session)
    session.run('CQ-01', execute=True, budget_usd='0.02')
    assert observed == [True]


def test_combined_budget_can_reject_a_retry_that_would_fit_alone(retry):
    create, original, _, events, proposal = retry
    # A smaller synthetic allowance makes the carry-forward decisive.
    original.plan['limits']['max_usd'] = '0.0015'
    path = original.folder/'usage.json'
    history = json.loads(path.read_text())
    history.update(scope_sha256=original.scope_sha256, max_usd='0.0015')
    path.write_text(json.dumps(history))
    before = path.read_bytes()
    proposal['cumulative_max_usd'] = '0.0015'
    proposal['prior_trial'].update(scope_sha256=original.scope_sha256,
        ledger_sha256=hashlib.sha256(before).hexdigest())
    session = create(); approve(session)
    with pytest.raises(AssessmentError) as caught:
        session.run('CQ-01', execute=True, budget_usd='0.0015')
    assert caught.value.code == 'budget_exceeded' and events == ['count']
    assert path.read_bytes() == before
    ledger = json.loads((session.folder/'usage.json').read_text())
    assert ledger['halted'] is True and ledger['reserved_usd'] == history['reserved_usd']


@pytest.mark.parametrize('tamper', ['drop_carry', 'missing_ledger', 'cache', 'scope', 'ancestor'])
def test_saved_retry_cannot_lose_accounting_or_silently_change_scope(retry, tamper):
    create, original, before, events, _ = retry
    session = create(); approve(session)
    session.run('CQ-01', execute=True, budget_usd='0.02')
    path = session.folder/'usage.json'
    if tamper == 'drop_carry':
        ledger = json.loads(path.read_text())
        ledger['reserved_usd'] = ledger['attempts'][0]['reserved_usd']
        path.write_text(json.dumps(ledger))
    elif tamper == 'missing_ledger': path.unlink()
    elif tamper == 'cache': (session.folder/'results/CQ-01.json').write_text('{}')
    elif tamper == 'ancestor':
        ledger = json.loads(path.read_text())
        ledger['prior_trial']['reserved_usd'] = '0'
        path.write_text(json.dumps(ledger))
    else: session.plan['parameters']['max_output_tokens'] = 2047
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    assert events == ['count', 'generate'] and (original.folder/'usage.json').read_bytes() == before


def test_cli_default_only_inspects_without_reading_a_key(retry, monkeypatch, capsys):
    from notelens_rag import assessment_retry as command
    create, _, _, events, _ = retry
    session = create(); session.settings = None
    monkeypatch.setattr(command, 'load_public_retry', lambda: session)
    monkeypatch.setattr('sys.argv', ['assessment_retry'])
    assert command.main() == 0
    output = capsys.readouterr()
    assert not output.err and json.loads(output.out)['execution_approved'] is False
    assert events == [] and not session.folder.exists()


def test_cli_execute_without_new_consent_is_blocked(retry, monkeypatch, capsys):
    from notelens_rag import assessment_retry as command
    create, original, before, events, _ = retry
    session = create()
    monkeypatch.setattr(command, 'load_public_retry', lambda: session)
    monkeypatch.setattr('sys.argv', ['assessment_retry', '--execute', '--budget-usd', '0.02'])
    assert command.main() == 1
    output = capsys.readouterr()
    assert not output.out and json.loads(output.err)['code'] == 'retry_execution_not_approved'
    assert events == [] and not session.folder.exists()
    assert (original.folder/'usage.json').read_bytes() == before
