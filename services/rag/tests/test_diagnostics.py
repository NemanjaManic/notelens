"""Locate rejected model evidence without retaining untrusted response text."""

from copy import deepcopy
import json

import pytest

from test_support import case as support_case
from test_assessor import case as model_case, provider
from test_assessment_trial import trial, session_for, approve
from notelens_rag.assessor import AssessmentError, prepare_assessment
from notelens_rag.support import SupportError, evaluate_support


@pytest.mark.parametrize('target,field,value,rule,path', [
    ('quote', 'quote', 'PRIVATE_QUOTE', 'quote_mismatch', '/parts/0/evidence/0/quote'),
    ('quote', 'quote', ' ', 'quote_empty', '/parts/0/evidence/0/quote'),
    ('quote', 'start', True, 'offset_type', '/parts/0/evidence/0/start'),
    ('quote', 'end', 12.0, 'offset_type', '/parts/0/evidence/0/end'),
    ('quote', 'start', -1, 'offset_bounds', '/parts/0/evidence/0'),
    ('quote', 'end', 999999, 'offset_bounds', '/parts/0/evidence/0'),
    ('quote', 'passage_id', 'PRIVATE_SOURCE', 'source_reference', '/parts/0/evidence/0/passage_id'),
    ('part', 'requirement_id', 'PRIVATE_REQUIREMENT', 'requirement_reference', '/parts/0/requirement_id'),
    ('part', 'reason', ' ', 'reason_empty', '/parts/0/reason'),
    ('part', 'status', 'PRIVATE_STATUS', 'part_status', '/parts/0/status'),
    ('part', 'evidence', [], 'evidence_policy', '/parts/0/evidence'),
    ('part', 'evidence', {}, 'evidence_shape', '/parts/0/evidence'),
    ('assessment', 'context_sha256', 'PRIVATE_HASH', 'assessment_binding', '/context_sha256'),
    ('assessment', 'parts', [], 'parts_count', '/parts'),
    ('assessment', 'parts', {}, 'parts_shape', '/parts'),
    ('assessment', 'format_version', 'PRIVATE_FORMAT', 'assessment_format', '/format_version'),
])
def test_rejection_identifies_rule_and_numeric_location(support_case, target, field, value, rule, path):
    assessment = support_case[3]
    item = {'quote': assessment['parts'][0]['evidence'][0],
            'part': assessment['parts'][0], 'assessment': assessment}[target]
    item[field] = value
    with pytest.raises(SupportError) as caught:
        evaluate_support(*support_case)
    assert caught.value.code == 'assessment_invalid'
    diagnostic = caught.value.diagnostic.as_dict()
    assert diagnostic == {'format_version': 'rag-validation-diagnostic-v1',
                          'stage': 'assessment', 'rule': rule, 'path': path}
    assert 'PRIVATE_' not in json.dumps(diagnostic) + str(caught.value) + repr(caught.value)


def test_duplicate_evidence_is_located_without_exposing_source_ids(support_case):
    evidence = support_case[3]['parts'][0]['evidence']
    evidence.append(deepcopy(evidence[0]))
    with pytest.raises(SupportError) as caught:
        evaluate_support(*support_case)
    assert caught.value.diagnostic.rule == 'duplicate_evidence'
    assert caught.value.diagnostic.path == '/parts/0/evidence/1'


def test_duplicate_requirement_is_separate_from_unknown_requirement(support_case):
    support_case[3]['parts'][1]['requirement_id'] = 'cause'
    with pytest.raises(SupportError) as caught:
        evaluate_support(*support_case)
    assert caught.value.diagnostic.rule == 'duplicate_requirement'
    assert caught.value.diagnostic.path == '/parts/1/requirement_id'


@pytest.mark.parametrize('level,rule,path', [
    ('assessment', 'assessment_shape', '/'),
    ('part', 'part_shape', '/parts/0'),
    ('quote', 'quote_shape', '/parts/0/evidence/0'),
])
def test_unknown_keys_never_appear_in_paths(support_case, level, rule, path):
    assessment = support_case[3]
    target = {'assessment': assessment, 'part': assessment['parts'][0],
              'quote': assessment['parts'][0]['evidence'][0]}[level]
    target['PRIVATE_FIELD_NAME'] = 'PRIVATE_VALUE'
    with pytest.raises(SupportError) as caught:
        evaluate_support(*support_case)
    diagnostic = caught.value.diagnostic.as_dict()
    assert diagnostic['rule'] == rule and diagnostic['path'] == path
    assert 'PRIVATE_' not in json.dumps(diagnostic)


@pytest.mark.parametrize('failure,rule,path', [
    ('request', 'context_request', '/request'),
    ('binding', 'context_binding', '/candidates/question_sha256'),
    ('passage', 'context_passage', '/candidates/passages/0'),
    ('requirements', 'context_requirements', '/requirements'),
])
def test_context_diagnostic_survives_preparation_without_contract_error_values(model_case, failure, rule, path):
    request, candidates, requirements = model_case
    if failure == 'request': request['PRIVATE_FIELD'] = 'PRIVATE_BODY'
    elif failure == 'binding': candidates['question_sha256'] = 'PRIVATE_HASH'
    elif failure == 'passage': candidates['passages'][0]['PRIVATE_FIELD'] = 'PRIVATE_BODY'
    else: requirements[0]['description'] = ' '
    with pytest.raises(AssessmentError) as caught:
        prepare_assessment(*model_case)
    diagnostic = caught.value.diagnostic.as_dict()
    assert caught.value.code == 'support_context_invalid'
    assert diagnostic['stage'] == 'context' and diagnostic['rule'] == rule and diagnostic['path'] == path
    assert 'PRIVATE_' not in json.dumps(diagnostic)


def test_sdk_adapter_preserves_quote_diagnostic_without_raw_model_text(model_case, provider):
    def alter(payload, body):
        output = payload['output'][0]['content'][0]
        answer = json.loads(output['text'])
        answer['assessment']['parts'][0]['reason'] = 'PRIVATE_REASON'
        answer['assessment']['parts'][0]['evidence'][0]['quote'] = 'PRIVATE_QUOTE'
        output['text'] = json.dumps(answer)
    assessor, calls = provider(alter)
    with pytest.raises(AssessmentError) as caught:
        assessor.assess(*model_case)
    diagnostic = caught.value.diagnostic.as_dict()
    assert caught.value.code == 'invalid_assessment' and len(calls) == 1
    assert diagnostic['rule'] == 'quote_mismatch'
    assert diagnostic['path'] == '/assessment/parts/0/evidence/0/quote'
    assert 'PRIVATE_' not in json.dumps(diagnostic) + str(caught.value)


@pytest.mark.parametrize('mutation,code,rule,path', [
    ('model', 'invalid_upstream', 'response_identity', '/response'),
    ('incomplete', 'assessment_incomplete', 'response_incomplete', '/response/status'),
    ('refusal', 'assessment_refused', 'response_refusal', '/response/output/0/content/0'),
    ('usage', 'invalid_upstream', 'usage_shape', '/response/usage'),
    ('usage_total', 'invalid_upstream', 'usage_total', '/response/usage/total_tokens'),
    ('usage_limit', 'invalid_upstream', 'usage_limit', '/response/usage/output_tokens'),
    ('wrapper', 'invalid_assessment', 'model_output_shape', '/'),
    ('flag_type', 'invalid_assessment', 'coverage_flag_type', '/requirements_cover_question'),
    ('flag_false', 'requirements_incomplete', 'requirements_incomplete', '/requirements_cover_question'),
    ('duplicate_json', 'invalid_upstream', 'json_duplicate_key', '/'),
    ('nonfinite_json', 'invalid_upstream', 'json_nonfinite', '/'),
    ('invalid_json', 'invalid_upstream', 'json_invalid', '/'),
])
def test_sdk_failures_have_safe_diagnostics(model_case, provider, mutation, code, rule, path):
    def alter(payload, body):
        output = payload['output'][0]['content'][0]
        if mutation == 'model': payload['model'] = 'PRIVATE_MODEL'
        elif mutation == 'incomplete': payload['status'] = 'incomplete'
        elif mutation == 'refusal': output.update(type='refusal', refusal='PRIVATE_REFUSAL')
        elif mutation == 'usage': payload['usage']['input_tokens'] = True
        elif mutation == 'usage_total': payload['usage']['total_tokens'] = 999
        elif mutation == 'usage_limit': payload['usage'].update(output_tokens=2049, total_tokens=2149)
        elif mutation == 'duplicate_json': output['text'] = '{"PRIVATE_KEY":1,"PRIVATE_KEY":2}'
        elif mutation == 'nonfinite_json': output['text'] = '{"PRIVATE_KEY":NaN}'
        elif mutation == 'invalid_json': output['text'] = 'PRIVATE_INVALID_JSON'
        else:
            answer = json.loads(output['text'])
            if mutation == 'wrapper': answer['PRIVATE_KEY'] = 'PRIVATE_BODY'
            else: answer['requirements_cover_question'] = 'PRIVATE_FLAG' if mutation == 'flag_type' else False
            output['text'] = json.dumps(answer)
    assessor, calls = provider(alter)
    with pytest.raises(AssessmentError) as caught:
        assessor.assess(*model_case)
    assert caught.value.code == code and len(calls) == 1
    diagnostic = caught.value.diagnostic.as_dict()
    assert diagnostic['stage'] == ('response' if mutation in
        ('model', 'incomplete', 'refusal', 'usage', 'usage_total', 'usage_limit') else 'assessment')
    assert diagnostic['rule'] == rule and diagnostic['path'] == path
    assert 'PRIVATE_' not in json.dumps(diagnostic)


def test_trial_persists_safe_failure_location_and_keeps_halt_and_reservation(trial):
    events = []
    session = session_for(trial, events, invalid_quote=True)
    approve(session)
    with pytest.raises(AssessmentError):
        session.run('CQ-01', execute=True, budget_usd='0.02')
    journal = (trial[2]/'usage.json').read_text()
    ledger = json.loads(journal)
    assert ledger['halted'] is True and ledger['attempts'][0]['status'] == 'failed'
    assert float(ledger['reserved_usd']) > 0 and ledger['confirmed_usd'] == '0'
    diagnostic = ledger['attempts'][0]['diagnostic']
    assert diagnostic['rule'] == 'quote_mismatch'
    assert diagnostic['path'] == '/assessment/parts/0/evidence/0/quote'
    assert 'Incorrect private text' not in journal and 'Public synthetic text' not in journal
    before = journal
    for identifier in ('CQ-01', 'CQ-02', 'CQ-08'):
        with pytest.raises(AssessmentError, match='completed safely') as caught:
            session.run(identifier, execute=True, budget_usd='0.02')
        assert caught.value.code == 'trial_retry_not_approved'
    assert events == ['count', 'generate'] and (trial[2]/'usage.json').read_text() == before


def test_diagnostic_rejects_dynamic_rule_stage_and_path_values():
    from notelens_rag.diagnostics import ValidationDiagnostic, safe_diagnostic
    for arguments in ({'rule': 'PRIVATE_RULE'}, {'stage': 'PRIVATE_STAGE'},
                      {'path': '/parts/PRIVATE_ID/quote'}, {'path': '/PRIVATE_FIELD'},
                      {'path': '/parts/999999999999/quote'}, {'path': []}, {'rule': []}):
        diagnostic = ValidationDiagnostic(**arguments)
        value = diagnostic.as_dict()
        assert 'PRIVATE_' not in json.dumps(value)
        assert value['path'] == '/' and value['rule'] == 'validation_failed'
    error = AssessmentError()
    error.diagnostic = 'PRIVATE_DIAGNOSTIC'
    assert safe_diagnostic(error)['rule'] == 'validation_failed'


def test_frozen_diagnostic_is_rechecked_at_serialization_boundary():
    from dataclasses import FrozenInstanceError
    from notelens_rag.diagnostics import ValidationDiagnostic, safe_diagnostic
    diagnostic = ValidationDiagnostic(stage='assessment', rule='quote_mismatch', path='/parts/0/evidence/0/quote')
    with pytest.raises(FrozenInstanceError):
        diagnostic.path = '/PRIVATE_VALUE'
    object.__setattr__(diagnostic, 'rule', 'PRIVATE_TAMPERED_RULE')
    error = AssessmentError(diagnostic=diagnostic)
    assert safe_diagnostic(error) == ValidationDiagnostic().as_dict()


def test_old_halted_ledger_without_diagnostics_is_preserved(trial):
    events = []
    session = session_for(trial, events, invalid_quote=True)
    approve(session)
    with pytest.raises(AssessmentError):
        session.run('CQ-01', execute=True, budget_usd='0.02')
    path = trial[2]/'usage.json'
    ledger = json.loads(path.read_text())
    del ledger['attempts'][0]['diagnostic']
    path.write_text(json.dumps(ledger))
    before = path.read_bytes()
    with pytest.raises(AssessmentError) as caught:
        session.run('CQ-02', execute=True, budget_usd='0.02')
    assert caught.value.code == 'trial_retry_not_approved'
    assert path.read_bytes() == before and events == ['count', 'generate']


def test_cli_renders_diagnostic_without_creating_provider(monkeypatch, capsys):
    from notelens_rag import assessment_trial as command
    from notelens_rag.diagnostics import ValidationDiagnostic
    def fail():
        raise AssessmentError('invalid_assessment', diagnostic=ValidationDiagnostic(
            stage='assessment', rule='quote_mismatch', path='/assessment/parts/0/evidence/0/quote'))
    monkeypatch.setattr(command, 'load_public_trial', fail)
    monkeypatch.setattr('sys.argv', ['assessment_trial'])
    assert command.main() == 1
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)['diagnostic']['rule'] == 'quote_mismatch'
