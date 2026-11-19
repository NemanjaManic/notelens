"""Exercise real local Chroma with synthetic vectors and no network."""

from decimal import Decimal
import json
from pathlib import Path
import socket
import tempfile
from types import SimpleNamespace

import pytest

pytest.importorskip("chromadb", reason="Index tests require the optional indexing extra.")

from notelens_rag.embeddings import EmbeddingBatch, EmbeddingError, plan_corpus
from notelens_rag.indexing import IndexBuildError, build_index, index_specification, load_index, PersistentTokenBudget


class Encoder:
    def encode(self,text,*,disallowed_special): return list(text.encode())


class FakeEmbedder:
    mode='mock'
    def __init__(self): self.calls=[]; self.budget=None
    def embed(self,texts):
        self.calls.append(tuple(texts));tokens=sum(len(t.encode()) for t in texts)
        self.budget.reserve(tokens)
        vectors=[]
        for text in texts:
            vector=[0.0]*1536;vector[0 if text.startswith('First') else 1]=1.0
            vectors.append(tuple(vector))
        return EmbeddingBatch(tuple(vectors),tokens)


@pytest.fixture
def prepared(monkeypatch):
    def deny(*args,**kwargs): raise AssertionError('Unexpected network in index tests.')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(socket,'create_connection',deny)
    parent=Path(__file__).resolve().parents[1]/'.cache/test-runs';parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent,ignore_cleanup_errors=True) as directory:
        passages=[]
        for n,text in enumerate(('First public paragraph.','Second public paragraph.')):
            passages.append(SimpleNamespace(passage_id=f'fixture-{n}',topic_id=str(n+1),
                title=f'Fixture {n}',url=f'https://example.invalid/{n}',language='en',
                date_created=None,synonyms=(),groups=(),source={'snapshot_date':'2026-11-10'},
                specialties=('Neurology',),topic_text_sha256='f'*64,cleaning_version='fixture-v1',
                start=0,end=len(text),overlap_code_points=0,text=text))
        corpus=SimpleNamespace(corpus_version='a'*64,manifest_sha256='b'*64,artifact_sha256='c'*64,
            topic_count=2,passages=tuple(passages),by_id={p.passage_id:p for p in passages})
        yield Path(directory),corpus,plan_corpus(corpus,encoder=Encoder())


def build(prepared,embedder=None,**kwargs):
    root,corpus,plan=prepared
    return build_index(corpus,repository_root=root,plan=plan,embedder=embedder or FakeEmbedder(),
                       max_usd=Decimal('0.10'),**kwargs)


def test_real_persistent_chroma_roundtrip_and_complete_reuse(prepared):
    root,corpus,plan=prepared;first=FakeEmbedder();result=build(prepared,first)
    assert result['status']=='complete' and result['passages']==2 and result['mode']=='mock'
    index=load_index(corpus,repository_root=root,plan=plan,mode='mock')
    assert index.verify()['passages']==2
    found=index.collection.query(query_embeddings=[[1.0]+[0.0]*1535],n_results=1)
    assert found['ids'][0]==['fixture-0'] and found['documents'][0]==[corpus.passages[0].text]
    assert index.collection.configuration_json['hnsw']['space']=='cosine'
    second=FakeEmbedder();build(prepared,second);assert second.calls==[]


def test_index_identity_binds_corpus_space_backend_and_mode(prepared):
    _,_,plan=prepared;before=index_specification(plan,mode='mock')['index_version']
    for key in ('embedding_plan_version','embedding_space_version','corpus_version'):
        changed=dict(plan);changed[key]='d'*64
        assert index_specification(changed,mode='mock')['index_version']!=before
    assert index_specification(plan,mode='live')['index_version']!=before


@pytest.mark.parametrize('kind',['manifest','text','vector','partial'])
def test_tampering_or_partial_build_cannot_report_readiness(prepared,kind):
    root,corpus,plan=prepared;summary=build(prepared)
    index=load_index(corpus,repository_root=root,plan=plan,mode='mock')
    if kind in ('manifest','partial'):
        path=root/'data/knowledge/indexes'/summary['index_version']/'manifest.json'
        data=json.loads(path.read_text());data['corpus_version' if kind=='manifest' else 'status']='wrong'
        path.write_text(json.dumps(data))
        with pytest.raises(IndexBuildError): load_index(corpus,repository_root=root,plan=plan,mode='mock')
    else:
        changes={'documents':['changed text'],'embeddings':[[1.0]+[0.0]*1535]} if kind=='text' else {'embeddings':[[0.0,1.0]+[0.0]*1534]}
        index.collection.update(ids=['fixture-0'],**changes)
        with pytest.raises(IndexBuildError): index.verify()


def test_failure_reservation_survives_and_resume_must_be_explicit(prepared):
    root,corpus,plan=prepared;first=FakeEmbedder()
    def fail(texts):
        first.budget.reserve(7);raise EmbeddingError('timeout','Fixture timeout.')
    first.embed=fail
    with pytest.raises(EmbeddingError): build(prepared,first)
    spec=index_specification(plan,mode='mock');folder=root/'data/knowledge/indexes'/spec['index_version']
    assert json.loads((folder/'usage.json').read_text())['reserved_tokens']==7
    with pytest.raises(IndexBuildError): build(prepared)
    assert build(prepared,resume=True)['status']=='complete'


def test_resume_reuses_saved_batches_without_duplicate_embedding(prepared):
    root,corpus,plan=prepared;result=build(prepared,batch_size=1)
    path=root/'data/knowledge/indexes'/result['index_version']/'manifest.json'
    data=json.loads(path.read_text());data['status']='building';path.write_text(json.dumps(data))
    again=FakeEmbedder();assert build(prepared,again,resume=True)['status']=='complete'
    assert again.calls==[]


def test_existing_lock_prevents_concurrent_build(prepared):
    root,_,plan=prepared;spec=index_specification(plan,mode='mock')
    folder=root/'data/knowledge/indexes'/spec['index_version'];folder.mkdir(parents=True)
    (folder/'.build.lock').write_text('fixture')
    with pytest.raises(IndexBuildError): build(prepared)


def test_persistent_budget_cannot_reset_reservations(prepared):
    root,_,_=prepared;path=root/'usage.json'
    ledger={'reserved_tokens':0,'max_usd':'0.00000006','price_per_million':'0.02'}
    path.write_text(json.dumps(ledger));one=PersistentTokenBudget(path,ledger);one.reserve(3)
    saved=json.loads(path.read_text());assert saved['reserved_tokens']==3
    with pytest.raises(EmbeddingError): PersistentTokenBudget(path,saved).reserve(1)


def test_decimal_vectors_survive_chroma_float32_storage(prepared):
    embedder=FakeEmbedder();original=embedder.embed
    def decimals(texts):
        result=original(texts)
        return EmbeddingBatch(tuple(tuple([0.1,0.2,0.3]+[0.0]*1533) for _ in texts),result.input_tokens)
    embedder.embed=decimals
    assert build(prepared,embedder)['status']=='complete'


def test_collection_identity_tampering_is_rejected(prepared):
    root,corpus,plan=prepared;build(prepared)
    index=load_index(corpus,repository_root=root,plan=plan,mode='mock')
    index.collection.modify(metadata={'corpus_version':'wrong'})
    with pytest.raises(IndexBuildError): index.verify()
