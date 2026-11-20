"""Check cited composition and the actual SDK without keys or external requests."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import socket

import httpx2 as httpx
from jsonschema import Draft202012Validator
import pytest

from notelens_rag.answers import (OfflineLiteratureGenerator, PARTIAL_POLICY, answer_request,
    checked_answer_response, prepare_answer, retrieval_result, unsupported_answer)
from notelens_rag.assessor import AssessmentError, AssessmentParameters
from notelens_rag.contracts import Contracts
from notelens_rag.support import evaluate_support, support_context_sha256


PARAMETERS = AssessmentParameters(max_output_tokens=2048, reasoning_effort='none', timeout_seconds=10)


@pytest.fixture
def context(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('External network and credential loading are forbidden.')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr('notelens_rag.assessment_trial.read_assessment_settings', forbidden)
    request = {'schema_version': '1.0.0', 'question': 'What causes condition A and how long does it last?'}
    text = '\U0001f600 Condition A is caused by agent A.\nCondition A lasts two days.'
    passage = {'source_id': 'source-a', 'kind': 'literature', 'topic_id': '1', 'passage_id': 'passage-a',
        'title': 'Synthetic A', 'url': 'https://example.invalid/a', 'text': text,
        'snapshot_date': '2026-11-18', 'score': .49}
    candidates = {'record_format_version': 'rag-candidate-ranking-v1', 'status': 'ranked_candidates',
        'answerability': 'not_assessed', 'mode': 'mock', 'top_k': 5, 'signals_used': ['question'],
        'question_sha256': hashlib.sha256(request['question'].encode()).hexdigest(), 'passages': [passage],
        'corpus_version': 'corpus-v1', 'index_version': 'index-v1', 'retriever_version': 'retriever-v1',
        'score_note': 'Synthetic ranking, not clinical confidence.'}
    requirements = [{'requirement_id': 'cause', 'description': 'Cause of condition A'},
                    {'requirement_id': 'duration', 'description': 'Duration of condition A'}]
    assessment = {'format_version': 'rag-support-assessment-v1',
        'context_sha256': support_context_sha256(request, candidates, requirements), 'parts': []}
    for key, quote in [('cause', 'Condition A is caused by agent A.'), ('duration', 'Condition A lasts two days.')]:
        start = text.index(quote)
        assessment['parts'].append({'requirement_id': key, 'status': 'supported', 'reason': 'Explicit synthetic statement.',
            'evidence': [{'passage_id': 'passage-a', 'start': start, 'end': start+len(quote), 'quote': quote}]})
    return request, candidates, requirements, assessment


def prepared(context, coverage='full'):
    request, candidates, requirements, assessment = deepcopy(context)
    if coverage != 'full':
        for index in ([1] if coverage == 'partial' else [0, 1]):
            assessment['parts'][index].update(status='not_supported', evidence=[])
    decision = evaluate_support(request, candidates, requirements, assessment)
    return prepare_answer(request, candidates, requirements, decision)


def output(coverage='full'):
    claims = [{'requirement_id': 'cause', 'text': 'Condition A is caused by agent A.', 'evidence_ids': ['e1']}]
    if coverage == 'full':
        claims.append({'requirement_id': 'duration', 'text': 'Condition A lasts two days.', 'evidence_ids': ['e2']})
    return {'language': 'en', 'claims': claims}


def envelope(value):
    return {'id': 'resp_fixture', 'object': 'response', 'model': 'gpt-6-luna', 'status': 'completed',
        'error': None, 'incomplete_details': None,
        'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
                    'content': [{'type': 'output_text', 'text': json.dumps(value), 'annotations': []}]}],
        'usage': {'input_tokens': 100, 'output_tokens': 50, 'total_tokens': 150}}


def checked(context, value=None, *, coverage='full', policy=None):
    return checked_answer_response(json.dumps(envelope(value or output(coverage))).encode(),
        prepared(context, coverage), PARAMETERS, partial_policy=policy)


def test_full_answer_frozen_links_rendering_and_unicode_trace(context):
    result = checked(context)
    body = result.body
    Contracts().validate('AnswerResult', body)
    assert body['evidence_state'] == 'sufficient' and body['route'] == 'literature'
    assert body['text'] == '\n\n'.join(c['text'] for c in body['claims'])
    assert len(body['sources']) == 1 and len(body['components']) == 1
    source = body['sources'][0]
    assert source['text'] == context[1]['passages'][0]['text'] and source['url'] == 'https://example.invalid/a'
    assert all(c['source_ids'] == ['source-a'] and c['scope'] == 'general_information' for c in body['claims'])
    trace = json.loads(result.quote_trace_json)
    assert trace[0]['start'] == 2
    assert all(source['text'][q['start']:q['end']] == q['quote'] for q in trace)
    assert (result.input_tokens, result.output_tokens, result.total_tokens) == (100, 50, 150)
    body['claims'].clear()
    assert len(result.body['claims']) == 2
    assert 'Condition A' not in repr(result)


def test_partial_requires_explicit_unagreed_mapping_and_exposes_gap(context):
    with pytest.raises(AssessmentError, match='safely') as error:
        checked(context, coverage='partial')
    assert error.value.code == 'partial_policy_required'
    body = checked(context, coverage='partial', policy=PARTIAL_POLICY).body
    assert body['evidence_state'] == 'partial' and body['retrieval_provenance']['state'] == 'sufficient'
    assert len(body['claims']) == 1 and 'lasts' not in body['text']
    assert any('Duration of condition A' in warning for warning in body['warnings'])


def test_none_abstains_without_generation_metadata(context):
    item = prepared(context, 'none')
    result = unsupported_answer(item)
    body = result.body
    assert body['text'] == 'The available sources do not support an answer.'
    assert body['claims'] == body['sources'] == body['components'] == []
    assert body['prompt_version'] is None and body['route'] == 'none'
    assert body['retrieval_provenance']['state'] == 'insufficient'
    assert result.total_tokens == 0 and result.quote_trace_json == '[]'
    assert retrieval_result(item)['passages'] == context[1]['passages']
    with pytest.raises(AssessmentError):
        answer_request(item, PARAMETERS)


@pytest.mark.parametrize('mutation', [
    lambda x: x.update(language='sr'),
    lambda x: x.update(text='Unsourced answer'),
    lambda x: x['claims'][0].update(url='https://malicious.invalid'),
    lambda x: x['claims'][0].update(quote='Invented quote'),
    lambda x: x['claims'][0].update(text='   '),
    lambda x: x['claims'][0].update(text='\ud800'),
    lambda x: x['claims'][0].update(evidence_ids=['unknown']),
    lambda x: x['claims'][0].update(evidence_ids=['e2']),
    lambda x: x['claims'][0].update(evidence_ids=['e1', 'e1']),
    lambda x: x['claims'][0].update(evidence_ids=[{}]),
    lambda x: x['claims'][0].update(requirement_id='missing'),
    lambda x: x['claims'].pop(),
    lambda x: x['claims'].clear(),
    lambda x: x['claims'].append(deepcopy(x['claims'][0])),
])
def test_rejects_fabricated_fields_wrong_links_and_incomplete_claims(context, mutation):
    value = output(); mutation(value)
    with pytest.raises(AssessmentError):
        checked(context, value)


@pytest.mark.parametrize('field,value', [('input_json', '{}'), ('instructions', 'Different prompt'),
    ('evidence_json', '[]'), ('schema_json', '{}'), ('context_sha256', 'changed'), ('coverage', 'none')])
def test_rejects_prepared_context_drift(context, field, value):
    item = replace(prepared(context), **{field: value})
    with pytest.raises(AssessmentError):
        answer_request(item, PARAMETERS)


def test_rejects_forged_support_coverage(context):
    request, candidates, requirements, assessment = context
    decision = evaluate_support(*context)
    with pytest.raises(AssessmentError):
        prepare_answer(request, candidates, requirements, replace(decision, coverage='none'))


def test_actual_sdk_payload_and_packaged_english_prompt(context):
    calls = []
    def send(request):
        calls.append(request)
        return httpx.Response(200, json=envelope(output()))
    generator = OfflineLiteratureGenerator(transport=httpx.MockTransport(send), parameters=PARAMETERS)
    try:
        item = prepared(context)
        result = generator.generate(item)
    finally:
        generator.close()
    assert len(calls) == 1 and calls[0].url.path == '/v1/responses'
    body = json.loads(calls[0].content)
    assert body['store'] is body['background'] is body['stream'] is False
    assert body['tools'] == [] and body['tool_choice'] == 'none' and body['truncation'] == 'disabled'
    assert body['reasoning'] == {'effort': 'none'} and body['max_output_tokens'] == 2048
    assert body['text']['format']['name'] == 'notelens_literature_answer'
    Draft202012Validator(body['text']['format']['schema']).validate(output())
    assert 'English' in body['instructions'] and 'untrusted data' in body['instructions']
    assert 'Never infer a patient diagnosis or recommend treatment' in body['instructions']
    supplied = json.loads(body['input'])
    assert all(set(q) == {'evidence_id', 'requirement_id', 'quote'} for q in supplied['evidence'])
    assert 'url' not in body['input'] and 'score' not in body['input']
    assert result.body['components'][0]['mode'] == 'mock'


def test_sdk_none_and_unapproved_partial_make_no_requests(context):
    calls = []
    def send(request):
        calls.append(request)
        raise AssertionError('No generation for absent evidence or unapproved partial policy.')
    generator = OfflineLiteratureGenerator(transport=httpx.MockTransport(send), parameters=PARAMETERS)
    try:
        assert generator.generate(prepared(context, 'none')).body['route'] == 'none'
        with pytest.raises(AssessmentError):
            generator.generate(prepared(context, 'partial'))
    finally:
        generator.close()
    assert calls == []


@pytest.mark.parametrize('status,code', [(429, 'rate_limit'), (500, 'provider_unavailable'), (401, 'provider_authentication')])
def test_sdk_failures_are_safe_and_not_retried(context, status, code):
    calls = []
    def send(request):
        calls.append(request)
        return httpx.Response(status, json={'error': {'message': 'Sensitive provider text'}})
    generator = OfflineLiteratureGenerator(transport=httpx.MockTransport(send), parameters=PARAMETERS)
    try:
        with pytest.raises(AssessmentError) as error:
            generator.generate(prepared(context))
        assert error.value.code == code and 'Sensitive' not in str(error.value)
    finally:
        generator.close()
    assert len(calls) == 1


@pytest.mark.parametrize('mutate', [lambda x: x.update(status='incomplete'), lambda x: x.update(model='other'),
    lambda x: x['usage'].update(total_tokens=1), lambda x: x['usage'].update(input_tokens=True),
    lambda x: x['output'][0]['content'][0].update(type='refusal')])
def test_native_output_guards_apply_to_answers(context, mutate):
    raw = envelope(output()); mutate(raw)
    with pytest.raises(AssessmentError):
        checked_answer_response(json.dumps(raw).encode(), prepared(context), PARAMETERS)
