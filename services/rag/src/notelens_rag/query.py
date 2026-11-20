"""Rank vector candidates with optional local concept and specialty signals."""

import re
import unicodedata

from .embeddings import identity
from .retrieval import CandidateRetriever


CANDIDATE_POOL_SIZE = 20
CONCEPT_BONUS = 0.08
SPECIALTY_BONUS = 0.02
WORD = re.compile(r"[^\W_]+")


def _word_sequence(text):
    return ' '.join(WORD.findall(unicodedata.normalize('NFKC', text).casefold()))


def _concept_phrases(request):
    return {_with_boundaries(sequence) for concept in request.get('concepts', ())
            if (sequence := _word_sequence(concept))}


def _with_boundaries(sequence):
    return f' {sequence} '


class SignalAwareRetriever(CandidateRetriever):
    """Use positive, bounded bonuses in an unfiltered vector candidate pool."""

    def __init__(self, index, *, top_k=5):
        super().__init__(index, top_k=top_k)
        self.configuration.update(algorithm='chroma-soft-signals-v1',
            score='cosine-similarity-plus-local-bonuses-v1',
            signals='question-optional-concept-phrases-and-specialty',
            signal_candidate_pool=CANDIDATE_POOL_SIZE,
            concept_bonus=CONCEPT_BONUS, specialty_bonus=SPECIALTY_BONUS,
            concept_policy='casefold-nfkc-contiguous-whole-words-title-or-passage-v1')
        self.retriever_version = identity(self.configuration)

    def _candidate_limit(self, request):
        if request.get('specialty_hint') is not None or _concept_phrases(request):
            return CANDIDATE_POOL_SIZE
        return super()._candidate_limit(request)

    def _rank_passages(self, request, passages):
        concepts = _concept_phrases(request)
        specialty = request.get('specialty_hint')
        if not concepts and specialty is None:
            return super()._rank_passages(request, passages)

        signals = ['question']
        if concepts:
            signals.append('concepts')
        if specialty is not None:
            signals.append('specialty_hint')

        ranked = []
        for passage in passages:
            concept_bonus = 0.0
            if concepts:
                title = _with_boundaries(_word_sequence(passage['title']))
                text = _with_boundaries(_word_sequence(passage['text']))
                matched_concepts = sum(phrase in title or phrase in text for phrase in concepts)
                concept_bonus = CONCEPT_BONUS * matched_concepts / len(concepts)
            source = self.index.corpus.by_id[passage['passage_id']]
            specialty_bonus = SPECIALTY_BONUS if specialty in source.specialties else 0.0
            ranked.append({**passage, 'score': passage['score'] + concept_bonus + specialty_bonus})

        note = ('Score = 1 - Chroma cosine distance plus bounded concept and specialty bonuses. '
                'Higher ranks better within this retriever/index version. This score is not clinical '
                'confidence or proof of answer support. Candidates are not assessed for answerability.')
        return ranked, signals, note
