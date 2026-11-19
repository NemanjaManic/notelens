"""Check the published binding package inside A's actual service environment."""

from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from notelens_contracts.v1 import ContractValidationError, validate_record, validate_exchange
import pytest

from notelens_rag.main import DEMO_QUESTION, Settings, create_app
from notelens_rag.mock import result


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT/'contracts/v1/fixtures'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
PAYLOADS = read(FIXTURES/'payloads.json')
DOCUMENTS = read(FIXTURES/'documents.json')
REFERENCES = read(FIXTURES/'references.json')
CASES = [case for case in read(FIXTURES/'manifest.json')['cases'] if case['kind']=='payload']
EXCHANGES = read(FIXTURES/'transport-cases.json')['cases']


def test_installed_package_and_all_generated_bytes_match_published_manifest():
    assert version('notelens-contracts')=='1.0.0'
    manifest=read(ROOT/'contracts/generated/manifest.json')
    assert hashlib.sha256((ROOT/'contracts/v1/schema.json').read_bytes()).hexdigest()==manifest['schema_sha256']
    assert hashlib.sha256((ROOT/'contracts/v1/freeze.json').read_bytes()).hexdigest()==manifest['freeze_sha256']
    for path,digest in {**manifest['inputs_sha256'],**manifest['generated_files']}.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path


@pytest.mark.parametrize('case',CASES,ids=lambda case:case['id'])
def test_frozen_wire_fixture_in_service_interpreter(case):
    try:
        validate_record(case['definition'],deepcopy(PAYLOADS[case['id']]),
            document=DOCUMENTS.get(case.get('document')),reference=REFERENCES.get(case.get('reference')))
        issues=[]
    except ContractValidationError as failure:
        issues=[{'rule':issue.rule,'path':issue.path} for issue in failure.issues]
    assert sorted(issues,key=lambda v:(v['rule'],v['path']))==sorted(case['expected'],key=lambda v:(v['rule'],v['path']))


@pytest.mark.parametrize('case',EXCHANGES,ids=lambda case:case['id'])
def test_frozen_simulated_exchange_in_service_environment(case):
    assert validate_exchange(case)==case['expected']


@pytest.mark.parametrize('scenario',['sufficient','insufficient','clarification'])
def test_mock_answer_has_truthful_independent_retrieval_history(scenario):
    with TestClient(create_app(Settings(scenario=scenario)),client=('127.0.0.1',45000)) as client:
        reply=client.post('/v1/literature-answer',json={'schema_version':'1.0.0','question':DEMO_QUESTION},
                          headers={'X-Request-ID':str(uuid4())})
    assert reply.status_code==200
    body=reply.json();validate_record('AnswerResult',body)
    retrieval=body['retrieval_provenance']
    if scenario=='clarification':
        assert retrieval is None and body['components']==[]
    else:
        assert retrieval['mode']=='mock' and retrieval['state']==scenario
        assert 'provider' not in retrieval and 'model' not in retrieval and 'prompt_version' not in retrieval
        if scenario=='insufficient': assert body['components']==[] and body['prompt_version'] is None
        else:
            for key in ('corpus_version','index_version','retriever_version'):
                assert body['components'][0][key]==retrieval[key]


def test_duplicate_json_keys_are_rejected_before_schema_validation():
    raw=json.dumps({'schema_version':'1.0.0','question':DEMO_QUESTION})[:-1]+',"question":'+json.dumps(DEMO_QUESTION)+'}'
    with TestClient(create_app(Settings()),client=('127.0.0.1',45000)) as client:
        reply=client.post('/v1/retrieve',content=raw,headers={'X-Request-ID':str(uuid4()),'Content-Type':'application/json'})
    assert reply.status_code==400
    validate_record('ErrorEnvelope',reply.json())


def test_default_mock_needs_no_key_corpus_index_or_provider(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    def forbidden(*args,**kwargs): raise AssertionError('Mock must not use a corpus, index or provider.')
    monkeypatch.setattr('notelens_rag.main.load_corpus',forbidden)
    monkeypatch.setattr('openai.OpenAI',forbidden)
    original_import = __import__
    def mock_import(name, *args, **kwargs):
        if name == 'chromadb' or name.startswith('chromadb.'):
            raise AssertionError('The default mock must run without Chroma.')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr('builtins.__import__', mock_import)
    with TestClient(create_app(Settings()),client=('127.0.0.1',45000)) as client:
        assert client.get('/health/ready').status_code==200
        for path,definition in [('/v1/retrieve','RetrievalResult'),('/v1/literature-answer','AnswerResult')]:
            reply=client.post(path,json={'schema_version':'1.0.0','question':DEMO_QUESTION},
                              headers={'X-Request-ID':str(uuid4())})
            assert reply.status_code==200
            validate_record(definition,reply.json())


@pytest.mark.parametrize('mutation',[
    lambda body:body.pop('retrieval_provenance',None),
    lambda body:body['claims'][0].update(component_id='missing-component'),
    lambda body:body['components'][0].update(index_version='different-index'),
    lambda body:body['retrieval_provenance'].update(mode='live'),
])
def test_invalid_output_provenance_is_a_safe_internal_error(mutation):
    app=create_app(Settings())
    def invalid(operation,scenario):
        body=result(operation,scenario);mutation(body);return body
    app.state.mock_result=invalid
    with TestClient(app,client=('127.0.0.1',45000)) as client:
        reply=client.post('/v1/literature-answer',json={'schema_version':'1.0.0','question':DEMO_QUESTION},
                          headers={'X-Request-ID':str(uuid4())})
    assert reply.status_code==500 and reply.json()['error']['code']=='internal_error'
    validate_record('ErrorEnvelope',reply.json())


@pytest.mark.parametrize('path',['/health/live','/health/ready'])
@pytest.mark.parametrize('headers',[[],[('X-Request-ID','11111111-1111-4111-8111-111111111111')],
    [('X-Request-ID','bad')],[('X-Request-ID','bad'),('X-Request-ID','also-bad')]])
def test_actual_health_401_matches_frozen_transport_rules(path,headers):
    with TestClient(create_app(Settings(service_token='fixture-token')),client=('127.0.0.1',45000)) as client:
        reply=client.get(path,headers=headers)
    assert reply.status_code==401
    exchange={'path':path,'request_headers':headers,'response_headers':list(reply.headers.multi_items()),
              'status':401,'body':reply.json(),'disposition':'failed_call'}
    assert validate_exchange(exchange)==[]
