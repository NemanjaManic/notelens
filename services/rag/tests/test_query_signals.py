"""Exercise optional retrieval signals with frozen records and fixture vectors."""

from types import SimpleNamespace

from notelens_contracts.v1 import validate_record
import pytest

from notelens_rag.query import SignalAwareRetriever
from notelens_rag.retrieval import CandidateRetriever, RetrievalError

from test_retrieval import Embedder, REQUEST, index


def test_no_signals_returns_the_baseline_candidates(index):
    baseline = CandidateRetriever(index).retrieve(REQUEST, Embedder())
    request = {**REQUEST, 'concepts': [], 'specialty_hint': None}
    actual = SignalAwareRetriever(index).retrieve(request, Embedder())
    assert actual['retriever_version'] != baseline['retriever_version']
    assert {key: value for key, value in actual.items() if key != 'retriever_version'} == {
        key: value for key, value in baseline.items() if key != 'retriever_version'}
    assert index.collection.calls[0] == index.collection.calls[1]


def test_concept_changes_a_close_ranking_without_sending_concepts_to_embedder(index):
    index.collection.reply['distances'] = [[0.24, 0.20]]
    source = index.corpus.by_id['second']
    source.text = 'A \U0001f600 condition involving the Sciatic—Nerve.\nExact source text.'
    request = {**REQUEST, 'concepts': ['SCIATIC nerve', 'sciatic—nerve']}
    embedder = Embedder()
    ranked = SignalAwareRetriever(index).retrieve(request, embedder)
    assert embedder.calls == [(REQUEST['question'],)]
    assert [p['passage_id'] for p in ranked['passages']] == ['second', 'first']
    assert ranked['passages'][0]['text'] == source.text
    assert ranked['passages'][0]['score'] == pytest.approx(0.84)
    assert ranked['signals_used'] == ['question', 'concepts']
    assert ranked['answerability'] == 'not_assessed' and 'not clinical' in ranked['score_note']
    for passage in ranked['passages']:
        validate_record('RetrievalPassage', passage)


def test_concept_whole_word_boundaries_do_not_match_unrelated_substrings(index):
    index.corpus.by_id['second'].text = 'A primer in neurological terminology.'
    ranked = SignalAwareRetriever(index).retrieve({**REQUEST, 'concepts': ['neuro']}, Embedder())
    assert [p['score'] for p in ranked['passages']] == pytest.approx([0.80, 0.30])


@pytest.mark.parametrize('hint', [None, 'Urology'])
def test_relevant_topic_survives_missing_or_wrong_specialty_without_icd(index, hint):
    index.corpus.by_id['second'].specialties = ('Urology',)
    if hint is None:
        index.collection.reply = {'ids': [['first']], 'distances': [[0.20]]}
    request = {**REQUEST, 'specialty_hint': hint}
    ranked = SignalAwareRetriever(index, top_k=1).retrieve(request, Embedder())
    assert [p['passage_id'] for p in ranked['passages']] == ['first']
    assert 'where' not in index.collection.calls[0]


def test_specialty_can_break_a_close_ranking_in_the_unfiltered_pool(index):
    index.corpus.by_id['second'].specialties = ('Urology',)
    index.collection.reply['distances'] = [[0.21, 0.20]]
    ranks = SignalAwareRetriever(index).retrieve({**REQUEST, 'specialty_hint': 'Urology'}, Embedder())
    assert [p['passage_id'] for p in ranks['passages']] == ['second', 'first']
    assert ranks['passages'][0]['score'] == pytest.approx(0.81)
    assert ranks['signals_used'] == ['question', 'specialty_hint']


def test_bounded_pool_exposes_matching_candidate_outside_the_baseline_top_five(index):
    for position in range(18):
        key = f'extra-{position:02}'
        index.corpus.by_id[key] = SimpleNamespace(passage_id=key, topic_id=key, title='Fixture',
            url=f'https://example.invalid/{key}', text='The selected term.' if position == 17 else 'Other text.',
            specialties=('Urology',) if position == 17 else ('Neurology',))
    index.corpus.passages = tuple(index.corpus.by_id.values())
    index.collection.reply = {'ids': [list(index.corpus.by_id)], 'distances': [[.20] * 19 + [.26]]}
    ranked = SignalAwareRetriever(index).retrieve(
        {**REQUEST, 'concepts': ['selected term'], 'specialty_hint': 'Urology'}, Embedder())
    assert index.collection.calls[0]['n_results'] == 20
    assert len(ranked['passages']) == 5 and ranked['passages'][0]['passage_id'] == 'extra-17'
    assert ranked['passages'][0]['score'] == pytest.approx(.84)
    assert ranked['signals_used'] == ['question', 'concepts', 'specialty_hint']


def test_invalid_signal_is_rejected_before_embedding(index):
    embedder = Embedder()
    with pytest.raises(RetrievalError) as failure:
        SignalAwareRetriever(index).retrieve({**REQUEST, 'specialty_hint': 'made up'}, embedder)
    assert failure.value.code == 'validation_failure'
    assert embedder.calls == [] and index.collection.calls == []
