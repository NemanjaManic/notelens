"""Public-only admission, bounded paid attempts and verified vector-cache reuse."""

from decimal import Decimal
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

import pytest

from notelens_rag.embeddings import EmbeddingBatch, EmbeddingError
from notelens_rag.query_smoke import PublicQuerySession
from notelens_rag.retrieval import RetrievalError


class Encoder:
    def encode(self,text,*,disallowed_special): return list(text.encode())


class Ranking:
    index=SimpleNamespace(spec={'mode':'mock','embedding_space_version':'a'*64})
    def retrieve(self,payload,embedder):
        batch=embedder.embed([payload['question']])
        assert len(batch.vectors[0])==1536
        return {'status':'ranked_candidates','answerability':'not_assessed','passages':[]}


@pytest.fixture
def trial():
    parent=Path(__file__).resolve().parents[1]/'.cache/test-runs';parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as directory:
        calls=[]
        def factory(budget):
            class Provider:
                mode='mock'
                def embed(self,texts):
                    tokens=sum(len(t.encode()) for t in texts);budget.reserve(tokens)
                    calls.append(tuple(texts))
                    return EmbeddingBatch((tuple([1.0]+[0.0]*1535),),tokens)
                def close(self): pass
            return Provider()
        registry={'registry_version':'fixture-v1','language':'en','public_development_only':True,
                  'cases':[{'question_id':str(i),'question':f'Public topic {i}?'} for i in range(10)]}
        session=PublicQuerySession(retriever=Ranking(),registry=registry,cache_dir=Path(directory),
                                  encoder=Encoder(),provider_factory=factory)
        yield session,calls,registry,Path(directory),factory


def test_new_query_requires_explicit_activation_and_budget(trial):
    session,calls,_,_,_=trial
    with pytest.raises(RetrievalError): session.run('0')
    with pytest.raises(RetrievalError): session.run('0',execute=True)
    assert calls==[]


def test_public_query_is_cached_and_reused_without_another_paid_attempt(trial):
    session,calls,_,_,_=trial
    first=session.run('0',execute=True,budget_usd=Decimal('0.01'))
    second=session.run('0')
    assert len(calls)==1 and first['query_embedding']['cache_hit'] is False
    assert second['query_embedding']['cache_hit'] is True
    assert second['query_embedding']['provider_calls_this_run']==0
    assert first['query_run_budget']==second['query_run_budget']


def test_cached_vectors_work_in_a_new_process_like_session(trial):
    session,calls,registry,path,_=trial;session.run('0',execute=True,budget_usd=Decimal('0.01'))
    def forbidden(budget): raise AssertionError('No new provider is permitted.')
    again=PublicQuerySession(retriever=Ranking(),registry=registry,cache_dir=path,
                             encoder=Encoder(),provider_factory=forbidden)
    assert again.run('0')['query_embedding']['cache_hit'] is True
    assert len(calls)==1


def test_unregistered_question_cannot_be_sent_or_persisted(trial):
    session,calls,_,path,_=trial
    with pytest.raises(RetrievalError): session.run('PRIVATE_UNREGISTERED_QUESTION',execute=True,budget_usd=Decimal('0.01'))
    assert calls==[] and not (path/'usage.json').exists()


@pytest.mark.parametrize('cap',[Decimal('0'),Decimal('-1'),Decimal('0.02'),Decimal('NaN')])
def test_cap_stays_within_approved_query_allowance(trial,cap):
    session,calls,_,_,_=trial
    with pytest.raises(RetrievalError): session.run('0',execute=True,budget_usd=cap)
    assert calls==[]


def test_budget_exhaustion_stops_before_transmission(trial):
    session,calls,_,_,_=trial
    with pytest.raises(EmbeddingError): session.run('0',execute=True,budget_usd=Decimal('0.00000001'))
    assert calls==[]


def test_cache_tampering_is_not_a_reason_to_call_provider_again(trial):
    session,calls,_,path,_=trial;session.run('0',execute=True,budget_usd=Decimal('0.01'))
    cache=next((path/'queries').glob('*.json'));data=json.loads(cache.read_text());data['vector'][0]=0.5
    cache.write_text(json.dumps(data))
    with pytest.raises(RetrievalError): session.run('0',execute=True,budget_usd=Decimal('0.01'))
    assert len(calls)==1


def test_changed_question_registry_does_not_reset_the_same_budget(trial):
    session,_,registry,path,factory=trial;session.run('0',execute=True,budget_usd=Decimal('0.01'))
    registry['cases'][0]['question']='A different public question?'
    changed=PublicQuerySession(retriever=Ranking(),registry=registry,cache_dir=path,
                               encoder=Encoder(),provider_factory=factory)
    with pytest.raises(RetrievalError): changed.run('1',execute=True,budget_usd=Decimal('0.01'))


def test_ten_registered_queries_exhaust_attempt_slots_but_allow_free_reuse(trial):
    session,calls,_,_,_=trial
    for i in range(10): session.run(str(i),execute=True,budget_usd=Decimal('0.01'))
    assert len(calls)==10
    assert session.run('0')['query_run_budget']['attempts_total']==10
    assert len(calls)==10


def test_failed_attempt_is_reserved_and_not_automatically_retried(trial):
    _,calls,registry,path,_=trial
    def factory(budget):
        class FailingProvider:
            mode='mock'
            def embed(self,texts):
                budget.reserve(5);calls.append(tuple(texts))
                raise EmbeddingError('timeout','Synthetic timeout.')
            def close(self): pass
        return FailingProvider()
    session=PublicQuerySession(retriever=Ranking(),registry=registry,cache_dir=path,
                               encoder=Encoder(),provider_factory=factory)
    with pytest.raises(EmbeddingError): session.run('0',execute=True,budget_usd=Decimal('0.01'))
    ledger=json.loads((path/'usage.json').read_text())
    assert ledger['reserved_tokens']==5 and len(ledger['attempts'])==1
    with pytest.raises(RetrievalError): session.run('0',execute=True,budget_usd=Decimal('0.01'))
    assert len(calls)==1


@pytest.mark.parametrize('field,value',[('public_development_only',False),('language','sr')])
def test_non_public_or_non_english_registry_is_not_admitted(trial,field,value):
    _,calls,registry,path,factory=trial
    registry[field]=value
    with pytest.raises(RetrievalError):
        PublicQuerySession(retriever=Ranking(),registry=registry,cache_dir=path,
                           encoder=Encoder(),provider_factory=factory)
    assert calls==[]
