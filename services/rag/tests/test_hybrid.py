"""Check independent lexical admission, fused ranking and unique-topic measurement."""

from types import SimpleNamespace

from notelens_contracts.v1 import validate_record
import pytest

from notelens_rag.hybrid import BM25Passages, HybridRetriever
from notelens_rag.hybrid_smoke import _observations, topic_metrics
from notelens_rag.retrieval import CandidateRetriever

from test_retrieval import Embedder, REQUEST, index


def test_hybrid_admits_lexical_only_passage_with_exact_source_and_one_embedding(index):
    text = 'The \U0001f600 Sciatic—Nerve carries signals.\nCanonical text.'
    source = SimpleNamespace(passage_id='lexical-only', topic_id='ref-3', title='Example source',
                             url='https://example.invalid/lexical-only', text=text)
    index.corpus.by_id[source.passage_id] = source
    index.corpus.passages += (source,)
    request = {**REQUEST, 'question': 'SCIATIC nerve?'}
    embedder = Embedder()
    result = HybridRetriever(index).retrieve(request, embedder)
    assert [p['passage_id'] for p in result['passages']] == ['first', 'lexical-only', 'second']
    assert embedder.calls == [('SCIATIC nerve?',)]
    assert 'where' not in index.collection.calls[0]
    validate_record('RetrievalPassage', result['passages'][1])
    assert result['passages'][1]['text'] == text
    assert result['answerability'] == 'not_assessed'
    assert result['signals_used'] == ['question', 'lexical_words']
    assert result['retriever_version'] != CandidateRetriever(index).retriever_version


def test_passage_found_by_both_rankers_gets_both_contributions(index):
    index.corpus.by_id['second'].text = 'Sciatic nerve.'
    result = HybridRetriever(index, top_k=1).retrieve({**REQUEST, 'question': 'Sciatic nerve'}, Embedder())
    row, = result['passages']
    assert row['passage_id'] == 'second'
    assert row['score'] == pytest.approx(1 / 62 + 1 / 61)


def test_no_lexical_match_preserves_vector_order(index):
    result = HybridRetriever(index).retrieve({**REQUEST, 'question': 'zzzunknownword'}, Embedder())
    assert result['signals_used'] == ['question']
    assert [p['passage_id'] for p in result['passages']] == ['first', 'second']


def test_lexical_words_respect_boundaries_and_resolve_ties_by_passage_id():
    passages = [SimpleNamespace(passage_id=key, text=text) for key, text in (
        ('z', 'nerve'), ('a', 'ｎｅｒｖｅ'), ('b', 'nerves'), ('c', '???'))]
    lexical = BM25Passages(passages)
    assert lexical.rank('Nerve nerve') == ['a', 'z']
    assert lexical.rank('!?') == []
    assert BM25Passages([]).rank('nerve') == []


def test_metrics_deduplicate_topics_and_keep_the_passage_cutoff():
    topics = [{'topic_id': topic} for topic in ('off', 'off', 'a', 'a', 'b', 'c')]
    assert topic_metrics(topics, ['a', 'b', 'c']) == {'recall_at_5': 2 / 3,
        'reciprocal_rank_at_5': 0.5, 'all_required_topics_at_5': False}
    assert topic_metrics(topics, ['a', 'b'])['all_required_topics_at_5'] is True
    assert topic_metrics(topics, ['c'])['reciprocal_rank_at_5'] == 0.0


def test_unreviewed_passages_do_not_inherit_support_from_the_same_topic():
    passages = [{'passage_id': key, 'topic_id': 'a'} for key in ('reviewed', 'new')]
    report = _observations(passages, ['a'], {'reviewed': 'partially_supports_question'})
    assert report['known_partial_evidence'] == 1 and report['known_full_evidence'] == 0
    assert report['unreviewed_passages'] == 1 and report['known_related_without_support'] == 0
