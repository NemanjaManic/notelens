"""Exercise safe configuration, unchanged inputs and fail-closed paid execution."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

import httpx2 as httpx
import pytest

from notelens_rag.embeddings import (
    EmbeddingError, EmbeddingSettings, OpenAIEmbedder, TokenBudget,
    count_tokens, local_tokenizer, plan_corpus, read_settings,
)


class Encoder:
    def encode(self, text, *, disallowed_special):
        assert disallowed_special == ()
        return list(text.encode('utf-8'))


def corpus():
    return SimpleNamespace(corpus_version='a' * 64, manifest_sha256='b' * 64,
        artifact_sha256='c' * 64, topic_count=1, passages=(
            SimpleNamespace(passage_id='one', text='A😀\nA'),
            SimpleNamespace(passage_id='two', text='  B  '),
        ))


def response(dimensions=1536):
    vector = [1.0] + [0.0] * (dimensions - 1)
    return {'object': 'list', 'model': 'text-embedding-3-small',
            'data': [{'object': 'embedding', 'index': 0, 'embedding': vector}],
            'usage': {'prompt_tokens': 3, 'total_tokens': 3}}


@pytest.fixture
def tmp_path():
    parent=Path(__file__).resolve().parents[1]/'.cache/test-runs'
    parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as directory:
        yield Path(directory)


@pytest.fixture
def make_embedder():
    clients = []
    def create(payload=None, *, status=200, budget=None, enabled=True, fail=None):
        calls = []
        def send(request):
            calls.append(request)
            if fail: raise fail(request)
            return httpx.Response(status, content=json.dumps(payload if payload is not None else response()).encode(),
                                  headers={'Content-Type':'application/json'})
        client = httpx.Client(transport=httpx.MockTransport(send))
        clients.append(client)
        instance = OpenAIEmbedder(api_key='fixture-key', enabled=enabled, timeout_seconds=10,
            budget=budget or TokenBudget(Decimal('0.10'), Decimal('0.02')),
            encoder=Encoder(), http_client=client)
        return instance, calls
    yield create
    for client in clients: client.close()


def test_dotenv_values_remain_secret_and_do_not_interpolate(tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    path=tmp_path/'.env'
    path.write_text('OPENAI_API_KEY=fixture-${HOME}-secret\nNOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=false\n')
    settings=read_settings(path)
    assert settings.api_key=='fixture-${HOME}-secret'
    assert settings.enabled is False
    assert 'fixture-' not in repr(settings)
    assert 'fixture-' not in json.dumps(settings.public_summary())


def test_environment_can_override_dotenv_without_printing_key(tmp_path, monkeypatch):
    path=tmp_path/'.env'; path.write_text('OPENAI_API_KEY=file-fixture\n')
    monkeypatch.setenv('OPENAI_API_KEY','process-fixture')
    assert read_settings(path).api_key=='process-fixture'


def test_missing_dotenv_is_key_free_and_disabled(tmp_path, monkeypatch):
    for key in ('OPENAI_API_KEY','NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS'):
        monkeypatch.delenv(key,raising=False)
    settings=read_settings(tmp_path/'absent.env')
    assert settings.api_key is None and not settings.enabled


@pytest.mark.parametrize('content',[
    'NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=maybe',
    'NOTELENS_RAG_EMBEDDING_MODEL=gpt-6-luna',
    'NOTELENS_RAG_EMBEDDING_DIMENSIONS=3072',
])
def test_configuration_does_not_silently_change_approved_space(tmp_path, content):
    path=tmp_path/'.env'; path.write_text(content)
    with pytest.raises(EmbeddingError): read_settings(path)


def test_plan_preserves_inputs_and_identity_and_never_needs_a_key():
    source=corpus(); before=[p.text for p in source.passages]
    plan=plan_corpus(source,encoder=Encoder())
    assert plan['passages']==2 and plan['topics']==1
    assert plan['input_tokens']==12 and plan['max_passage_tokens']==7
    assert plan['estimated_usd']=='0.00000024'
    assert plan['model']=='text-embedding-3-small' and plan['dimensions']==1536
    assert plan['corpus_version']==source.corpus_version
    assert before==[p.text for p in source.passages]
    assert plan['embedding_space_version']==plan_corpus(source,encoder=Encoder())['embedding_space_version']
    source.corpus_version='d'*64
    assert plan['embedding_plan_version']!=plan_corpus(source,encoder=Encoder())['embedding_plan_version']


def test_literal_special_tokens_and_non_bmp_are_not_rewritten():
    assert count_tokens('<|endoftext|>😀', Encoder())==len('<|endoftext|>😀'.encode())


@pytest.mark.parametrize('text',['', ' \n\t ', 'x'*8193, '\ud800'])
def test_invalid_input_fails_before_network(make_embedder,text):
    embedder,calls=make_embedder()
    with pytest.raises(EmbeddingError): embedder.embed([text])
    assert calls==[]


def test_unapproved_live_activation_fails_before_network(make_embedder):
    embedder,calls=make_embedder(enabled=False)
    with pytest.raises(EmbeddingError,match='disabled'): embedder.embed(['abc'])
    assert calls==[]


def test_paid_call_preserves_text_and_targets_only_official_endpoint(make_embedder):
    embedder,calls=make_embedder()
    result=embedder.embed(['abc'])
    body=json.loads(calls[0].content)
    assert body=={'input':['abc'],'model':'text-embedding-3-small','dimensions':1536,'encoding_format':'float'}
    assert str(calls[0].url)=='https://api.openai.com/v1/embeddings'
    assert len(result.vectors[0])==1536 and result.input_tokens==3


def test_response_indices_restore_request_order(make_embedder):
    payload=response(); second=deepcopy(payload['data'][0]);second['index']=1
    second['embedding']=[0.0,1.0]+[0.0]*1534
    payload['data']=[second,payload['data'][0]]
    payload['usage']={'prompt_tokens':6,'total_tokens':6}
    embedder,_=make_embedder(payload)
    result=embedder.embed(['abc','def'])
    assert result.vectors[0][0]==1 and result.vectors[1][1]==1


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(model='different-model'),
    lambda p:p.update(data=[]),
    lambda p:p['data'][0].update(index=1),
    lambda p:p['data'].append(deepcopy(p['data'][0])),
    lambda p:p['data'][0].update(embedding=[1.0]),
    lambda p:p['data'][0].update(embedding=[0.0]*1536),
    lambda p:p['data'][0]['embedding'].__setitem__(0,float('nan')),
    lambda p:p['data'][0]['embedding'].__setitem__(0,True),
    lambda p:p['usage'].update(prompt_tokens=4,total_tokens=4),
])
def test_malformed_upstream_data_is_rejected_without_payload_leak(make_embedder,mutation):
    payload=response();mutation(payload)
    embedder,calls=make_embedder(payload)
    with pytest.raises(EmbeddingError) as failure: embedder.embed(['abc'])
    assert 'abc' not in str(failure.value) and 'fixture-key' not in str(failure.value)
    assert len(calls)==1 and embedder.budget.reserved_tokens==3


@pytest.mark.parametrize('status,code',[(401,'provider_authentication'),(429,'rate_limit'),(500,'provider_unavailable')])
def test_provider_failure_has_no_hidden_retry(make_embedder,status,code):
    embedder,calls=make_embedder({'error':{'message':'private-body','type':'error'}},status=status)
    with pytest.raises(EmbeddingError) as failure: embedder.embed(['abc'])
    assert failure.value.code==code and 'private-body' not in str(failure.value)
    assert len(calls)==1 and embedder.budget.reserved_tokens==3


def test_timeout_reserves_possible_charge_and_does_not_retry(make_embedder):
    embedder,calls=make_embedder(fail=lambda request:httpx.ReadTimeout('private-body',request=request))
    with pytest.raises(EmbeddingError) as failure: embedder.embed(['abc'])
    assert failure.value.code=='timeout' and len(calls)==1
    assert embedder.budget.reserved_tokens==3


def test_budget_counts_attempts_and_blocks_before_second_call(make_embedder):
    budget=TokenBudget(Decimal('0.00000006'),Decimal('0.02'))
    embedder,calls=make_embedder(budget=budget)
    embedder.embed(['abc'])
    with pytest.raises(EmbeddingError) as failure: embedder.embed(['abc'])
    assert failure.value.code=='budget_exceeded' and len(calls)==1


@pytest.mark.parametrize('cap,price',[('0','0.02'),('-1','0.02'),('NaN','0.02'),('1','0'),('1','Infinity')])
def test_invalid_budget_or_price_cannot_enable_spending(cap,price):
    with pytest.raises(EmbeddingError): TokenBudget(Decimal(cap),Decimal(price))


@pytest.mark.parametrize('tokens',[0,-1,True,1.5])
def test_invalid_reservation_cannot_reduce_budget(tokens):
    budget=TokenBudget(Decimal('1'),Decimal('0.02'))
    with pytest.raises(EmbeddingError): budget.reserve(tokens)
    assert budget.reserved_tokens==0


def test_missing_tokenizer_never_triggers_implicit_network(tmp_path,monkeypatch):
    monkeypatch.setenv('TIKTOKEN_CACHE_DIR',str(tmp_path/'empty-cache'))
    with patch('notelens_rag.embeddings.tiktoken.get_encoding') as load:
        with pytest.raises(EmbeddingError) as failure: local_tokenizer()
        assert failure.value.code=='tokenizer_unavailable'
        load.assert_not_called()
