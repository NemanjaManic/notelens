"""Check ranking/provenance without model calls or unmeasured sufficiency claims."""

from copy import deepcopy
import math
from types import SimpleNamespace

from notelens_contracts.v1 import validate_record
import pytest

from notelens_rag.embeddings import DIMENSIONS, MODEL, EmbeddingBatch
from notelens_rag.retrieval import CandidateRetriever, RetrievalError


REQUEST={'schema_version':'1.0.0','question':'What is the synthetic medical topic?'}


class Collection:
    def __init__(self):
        self.reply={'ids':[['second','first']],'distances':[[0.7,0.2]]};self.calls=[]
    def query(self,**kwargs): self.calls.append(kwargs);return deepcopy(self.reply)


class Embedder:
    mode='mock'
    def __init__(self): self.calls=[];self.model=MODEL
    def embed(self,texts):
        self.calls.append(tuple(texts))
        return EmbeddingBatch((tuple([1.0]+[0.0]*(DIMENSIONS-1)),),5,model=self.model)


@pytest.fixture
def index():
    rows={key:SimpleNamespace(passage_id=key,topic_id=str(position+1),title=key.title(),
        url='https://example.invalid/'+key,text='Exact '+key+' 😀\nsource.',specialties=('Neurology',))
        for position,key in enumerate(('first','second'))}
    return SimpleNamespace(corpus=SimpleNamespace(by_id=rows,passages=tuple(rows.values()),
        corpus_version='a'*64,snapshot_date='2026-11-10'),
        spec={'mode':'mock','model':MODEL,'dimensions':DIMENSIONS,'embedding_space_version':'b'*64,
              'index_version':'c'*64,'corpus_version':'a'*64},
        collection=Collection(),verify=lambda:{'status':'complete'})


def test_ranked_sources_preserve_canonical_text_versions_and_score_direction(index):
    embedder=Embedder();result=CandidateRetriever(index).retrieve(REQUEST,embedder)
    assert embedder.calls==[(REQUEST['question'],)]
    assert [row['passage_id'] for row in result['passages']]==['first','second']
    assert [row['score'] for row in result['passages']]==pytest.approx([0.8,0.3])
    for row in result['passages']:
        validate_record('RetrievalPassage',row)
        assert row['text']==index.corpus.by_id[row['passage_id']].text
    assert result['answerability']=='not_assessed' and 'state' not in result
    assert result['index_version']==index.spec['index_version'] and result['corpus_version']=='a'*64
    assert 'not clinical' in result['score_note'].lower()
    assert index.collection.calls[0]['include']==['distances']
    assert 'where' not in index.collection.calls[0]


def test_hints_and_concepts_do_not_hard_filter_baseline(index):
    request={**REQUEST,'specialty_hint':'Urology','concepts':['unrelated concept']}
    result=CandidateRetriever(index).retrieve(request,Embedder())
    assert len(result['passages'])==2
    assert result['signals_used']==['question']


def test_question_unicode_and_whitespace_are_not_rewritten(index):
    request={**REQUEST,'question':'  What is the 😀 topic?\n'};embedder=Embedder()
    CandidateRetriever(index).retrieve(request,embedder)
    assert embedder.calls==[(request['question'],)]


@pytest.mark.parametrize('payload',[{}, {'schema_version':'1.0.0','question':'  '},
    {**REQUEST,'extra':'not allowed'}])
def test_invalid_request_never_calls_provider(index,payload):
    embedder=Embedder()
    with pytest.raises(RetrievalError): CandidateRetriever(index).retrieve(payload,embedder)
    assert embedder.calls==[]


def test_failed_index_verification_never_calls_provider(index):
    def fail(): raise ValueError('PRIVATE_INDEX_BODY')
    index.verify=fail;embedder=Embedder()
    with pytest.raises(RetrievalError) as failure: CandidateRetriever(index).retrieve(REQUEST,embedder)
    assert embedder.calls==[] and 'PRIVATE_INDEX_BODY' not in str(failure.value)


@pytest.mark.parametrize('field,value',[('mode','live'),('model','other-model'),('dimensions',1)])
def test_mismatched_embedding_space_is_rejected(index,field,value):
    index.spec[field]=value;embedder=Embedder()
    with pytest.raises(RetrievalError): CandidateRetriever(index).retrieve(REQUEST,embedder)
    assert embedder.calls==[]


@pytest.mark.parametrize('reply',[
    {'ids':[['unknown']],'distances':[[0.1]]},
    {'ids':[['first','first']],'distances':[[0.1,0.2]]},
    {'ids':[['first']],'distances':[[]]},
    {'ids':[['first']],'distances':[[math.nan]]},
    {'ids':[['first']],'distances':[[True]]},
    {'ids':[['first']],'distances':[[10.0]]},
    {'ids':[[]],'distances':[[]]},
])
def test_invalid_store_result_is_safe(index,reply):
    index.collection.reply=reply
    with pytest.raises(RetrievalError): CandidateRetriever(index).retrieve(REQUEST,Embedder())


def test_equal_scores_use_stable_passage_id_order(index):
    index.collection.reply['distances']=[[0.25,0.25]]
    assert [p['passage_id'] for p in CandidateRetriever(index).retrieve(REQUEST,Embedder())['passages']]==['first','second']


def test_retriever_version_is_stable_and_binds_configuration(index):
    a=CandidateRetriever(index).retrieve(REQUEST,Embedder())
    b=CandidateRetriever(index).retrieve(REQUEST,Embedder())
    index.collection.reply={'ids':[['first']],'distances':[[0.2]]}
    c=CandidateRetriever(index,top_k=1).retrieve(REQUEST,Embedder())
    assert a['retriever_version']==b['retriever_version']!=c['retriever_version']


@pytest.mark.parametrize('value',[0,6,True,1.5])
def test_top_k_stays_inside_approved_candidate_scope(index,value):
    with pytest.raises(RetrievalError): CandidateRetriever(index,top_k=value)


def test_provider_model_mismatch_is_not_used(index):
    embedder=Embedder();embedder.model='wrong'
    with pytest.raises(RetrievalError): CandidateRetriever(index).retrieve(REQUEST,embedder)
