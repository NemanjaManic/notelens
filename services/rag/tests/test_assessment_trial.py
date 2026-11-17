"""Verify explicit approval, pre-counting and durable reservations without models."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile

import httpx2 as httpx
import openai
import pytest

from notelens_rag.assessor import AssessmentError, prepare_assessment
from notelens_rag.assessment_trial import (
    AssessmentSettings, PublicAssessmentTrial, count_public_inputs, read_assessment_settings,
)


@pytest.fixture
def trial():
    root = Path(__file__).resolve().parents[3]
    plan = json.loads((root/'docs/rag/assessment-trial-proposal.json').read_text())
    # Tests control approval independently of the real owner's execution record.
    plan['execution_approved'] = False
    plan['approval'] = None
    cases = {}
    for identifier in plan['question_ids']:
        question = f'What does the public synthetic example {identifier} say?'
        request = {'schema_version': '1.0.0', 'question': question}
        candidates = {'record_format_version': 'rag-candidate-ranking-v1',
            'status': 'ranked_candidates', 'answerability': 'not_assessed', 'mode': 'mock',
            'question_sha256': hashlib.sha256(question.encode()).hexdigest(), 'top_k': 5,
            'corpus_version': 'corpus', 'index_version': 'index', 'retriever_version': 'retriever',
            'score_note': 'Synthetic score.', 'passages': [{'source_id': 'one', 'passage_id': 'one',
                'kind': 'literature', 'topic_id': '1', 'title': 'Public fixture',
                'url': 'https://example.invalid/public', 'text': 'Public synthetic text.',
                'snapshot_date': '2026-11-10', 'score': 0.5}]}
        cases[identifier] = prepare_assessment(request, candidates,
            [{'requirement_id': 'part-1', 'description': 'The public example statement'}])
    parent = root/'services/rag/.cache/test-runs'; parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as directory:
        yield plan, cases, Path(directory)


def approve(session):
    session.plan['execution_approved'] = True
    session.plan['approval'] = {'actor': 'Synthetic test approval', 'date': '2026-11-16',
                                'scope_sha256': session.scope_sha256}


def factory(events, *, tokens=100, fail_generation=False, fail_count=False, invalid_quote=False,
            before_generation=None):
    def create():
        def send(request):
            body = json.loads(request.content)
            if request.url.path.endswith('/input_tokens'):
                events.append('count')
                return httpx.Response(503 if fail_count else 200,
                    json={'object': 'response.input_tokens', 'input_tokens': tokens})
            events.append('generate')
            if before_generation is not None:
                before_generation()
            if fail_generation:
                return httpx.Response(429, json={'error': {'message': 'PRIVATE_PROVIDER_DETAIL'}})
            context = json.loads(body['input'])
            assessment = {'requirements_cover_question': True, 'assessment': {
                'format_version': 'rag-support-assessment-v1', 'context_sha256': context['context_sha256'],
                'parts': [{'requirement_id': 'part-1', 'status': 'supported', 'reason': 'The fixture states this.',
                    'evidence': [{'passage_id': 'one', 'start': 0, 'end': 22,
                                 'quote': 'Incorrect private text' if invalid_quote else 'Public synthetic text.'}]}]}}
            return httpx.Response(200, json={'object': 'response', 'model': 'gpt-6-luna',
                'status': 'completed', 'error': None, 'incomplete_details': None, 'service_tier': 'default',
                'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
                    'content': [{'type': 'output_text', 'text': json.dumps(assessment)}]}],
                'usage': {'input_tokens': tokens, 'output_tokens': 50, 'total_tokens': tokens+50}})
        return openai.OpenAI(api_key='fixture-key', base_url='https://api.openai.com/v1',
            max_retries=0, timeout=10, http_client=httpx.Client(transport=httpx.MockTransport(send)))
    return create


def session_for(trial, events, **kwargs):
    plan, cases, folder = trial
    return PublicAssessmentTrial(plan, cases, folder, mode='mock',
        settings=AssessmentSettings(api_key='fixture-key', enabled=True),
        client_factory=factory(events, **kwargs))


def test_proposal_rejects_execution_before_provider_or_ledger_creation(trial):
    events=[];session=session_for(trial, events)
    with pytest.raises(AssessmentError): session.run('CQ-01', execute=True, budget_usd='0.02')
    assert events==[] and not (trial[2]/'usage.json').exists()


@pytest.mark.parametrize('gate', ['execute', 'enabled', 'budget', 'approval_scope', 'unknown_question'])
def test_every_activation_gate_is_required(trial, gate):
    events=[];session=session_for(trial,events);approve(session)
    execute=True;budget='0.02';identifier='CQ-01'
    if gate=='execute': execute=False
    elif gate=='enabled': session.settings=AssessmentSettings(api_key='fixture-key',enabled=False)
    elif gate=='budget': budget='0.03'
    elif gate=='approval_scope': session.plan['approval']['scope_sha256']='wrong'
    else: identifier='patient-question'
    with pytest.raises(AssessmentError): session.run(identifier, execute=execute, budget_usd=budget)
    assert events==[]


def test_precount_reserve_generate_and_reuse_cache_without_new_calls(trial):
    events=[];session=session_for(trial,events);approve(session)
    result=session.run('CQ-01',execute=True,budget_usd='0.02')
    assert events==['count','generate'] and result['result']['mode']=='mock'
    ledger=json.loads((trial[2]/'usage.json').read_text())
    assert ledger['attempts'][0]['status']=='confirmed'
    assert float(ledger['reserved_usd'])>float(ledger['confirmed_usd'])>0
    before=(trial[2]/'usage.json').read_bytes()
    assert session.run('CQ-01')['cache_hit'] is True
    assert events==['count','generate'] and (trial[2]/'usage.json').read_bytes()==before


def test_three_registered_cases_each_have_only_one_attempt(trial):
    events=[];session=session_for(trial,events);approve(session)
    for identifier in ('CQ-01','CQ-02','CQ-08'):
        session.run(identifier,execute=True,budget_usd='0.02')
    assert events==['count','generate']*3
    assert len(json.loads((trial[2]/'usage.json').read_text())['attempts'])==3


@pytest.mark.parametrize('failure', ['generation','count','quote'])
def test_failure_halts_later_cases_and_never_retries(trial, failure):
    events=[];session=session_for(trial,events,fail_generation=failure=='generation',
        fail_count=failure=='count',invalid_quote=failure=='quote');approve(session)
    with pytest.raises(AssessmentError) as caught:session.run('CQ-01',execute=True,budget_usd='0.02')
    assert caught.value.code == {'generation':'rate_limit', 'count':'provider_unavailable',
                                 'quote':'invalid_assessment'}[failure]
    count=len(events)
    for identifier in ('CQ-01','CQ-02'):
        with pytest.raises(AssessmentError):session.run(identifier,execute=True,budget_usd='0.02')
    assert len(events)==count
    ledger=json.loads((trial[2]/'usage.json').read_text())
    assert ledger['halted'] is True and ledger['attempts'][0]['status']=='failed'
    if failure!='count': assert float(ledger['reserved_usd'])>0


def test_input_limit_is_checked_before_generation(trial):
    events=[];session=session_for(trial,events,tokens=20001);approve(session)
    with pytest.raises(AssessmentError):session.run('CQ-01',execute=True,budget_usd='0.02')
    assert events==['count']


def test_budget_is_reserved_before_a_generation_can_happen(trial):
    plan,cases,folder=trial;plan['limits']['max_usd']='0.000001'
    events=[];session=session_for(trial,events);approve(session)
    with pytest.raises(AssessmentError):session.run('CQ-01',execute=True,budget_usd='0.000001')
    assert events==['count']


def test_reservation_is_already_on_disk_when_the_model_request_starts(trial):
    observed=[]
    def inspect_reservation():
        ledger=json.loads((trial[2]/'usage.json').read_text())
        observed.append(ledger['attempts'][0]['status'])
        assert float(ledger['reserved_usd'])>0
        assert not (trial[2]/'results/CQ-01.json').exists()
    events=[];session=session_for(trial,events,before_generation=inspect_reservation);approve(session)
    session.run('CQ-01',execute=True,budget_usd='0.02')
    assert observed==['reserved']


def test_missing_key_fails_before_consuming_an_attempt(trial):
    events=[];session=session_for(trial,events);approve(session)
    session.settings=AssessmentSettings(enabled=True)
    with pytest.raises(AssessmentError):session.run('CQ-01',execute=True,budget_usd='0.02')
    assert events==[] and not (trial[2]/'usage.json').exists()


def test_mock_mode_requires_an_explicit_fake_client(trial):
    plan,cases,folder=trial
    with pytest.raises(AssessmentError):PublicAssessmentTrial(plan,cases,folder,mode='mock')
    with pytest.raises(AssessmentError):count_public_inputs(plan,cases,mode='mock')


@pytest.mark.parametrize('tamper', ['cache','ledger','missing_ledger','other_context'])
def test_saved_scope_and_state_cannot_silently_reset_allowance(trial,tamper):
    events=[];session=session_for(trial,events);approve(session)
    session.run('CQ-01',execute=True,budget_usd='0.02');count=len(events)
    if tamper=='cache': (trial[2]/'results/CQ-01.json').write_text('{}')
    elif tamper=='missing_ledger': (trial[2]/'usage.json').unlink()
    elif tamper=='ledger':
        ledger=json.loads((trial[2]/'usage.json').read_text());ledger['reserved_usd']='0'
        (trial[2]/'usage.json').write_text(json.dumps(ledger))
    else: session.plan['limits']['max_input_tokens']=19999
    with pytest.raises(AssessmentError):session.run('CQ-01',execute=True,budget_usd='0.02')
    assert len(events)==count


def test_stale_lock_is_not_removed_or_bypassed(trial):
    (trial[2]/'.build.lock').write_text('Owned test lock')
    events=[];session=session_for(trial,events);approve(session)
    with pytest.raises(AssessmentError):session.run('CQ-01',execute=True,budget_usd='0.02')
    assert events==[] and (trial[2]/'.build.lock').exists()


def test_count_only_is_available_without_paid_activation_and_cannot_generate(trial):
    plan,cases,_=trial;events=[]
    report=count_public_inputs(plan,cases,client_factory=factory(events),mode='mock')
    assert events==['count']*3 and report['generation_calls']==0
    assert report['total_input_tokens']==300
    assert report['execution_approved'] is False


def test_assessment_activation_is_separate_from_embedding_activation(trial,monkeypatch):
    env_file=trial[2]/'.env';env_file.write_text('OPENAI_API_KEY=fixture-secret\nNOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=true\n')
    monkeypatch.delenv('NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS',raising=False)
    settings=read_assessment_settings(env_file)
    assert settings.enabled is False and 'fixture-secret' not in repr(settings)
