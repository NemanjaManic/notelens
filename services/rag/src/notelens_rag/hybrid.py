"""Fuse lexical and vector ranks over the same prepared literature corpus."""

from collections import Counter, defaultdict
import math
from unicodedata import unidata_version

from .embeddings import identity
from .query import _word_sequence
from .retrieval import CandidateRetriever


VECTOR_DEPTH = 20
LEXICAL_DEPTH = 20
BM25_K1 = 1.2
BM25_B = 0.75
RRF_K = 60


class BM25Passages:
    """In-memory word postings over canonical passage text."""

    def __init__(self, passages):
        postings = defaultdict(list)
        lengths = {}
        for passage in passages:
            terms = Counter(_word_sequence(passage.text).split())
            if not terms:
                continue
            lengths[passage.passage_id] = sum(terms.values())
            for term, frequency in terms.items():
                postings[term].append((passage.passage_id, frequency))

        count = len(lengths)
        average = sum(lengths.values()) / count if count else 0.0
        self._normalization = {
            key: BM25_K1 * (1 - BM25_B + BM25_B * length / average)
            for key, length in lengths.items()
        }
        self._terms = {
            term: (math.log1p((count - len(rows) + 0.5) / (len(rows) + 0.5)), tuple(rows))
            for term, rows in postings.items()
        }

    def rank(self, question):
        scores = defaultdict(float)
        # Stable term order avoids differences in float accumulation across processes.
        for term in sorted(set(_word_sequence(question).split())):
            if term not in self._terms:
                continue
            idf, rows = self._terms[term]
            for key, frequency in rows:
                scores[key] += idf * frequency * (BM25_K1 + 1) / (frequency + self._normalization[key])
        return sorted(scores, key=lambda key: (-scores[key], key))[:LEXICAL_DEPTH]


class HybridRetriever(CandidateRetriever):
    """Use reciprocal rank fusion so lexical-only candidates can enter the result."""

    def __init__(self, index, *, top_k=5):
        super().__init__(index, top_k=top_k)
        self._lexical = BM25Passages(index.corpus.passages)
        self.configuration.update(algorithm='chroma-bm25-rrf-v1', score='equal-weight-rrf-v1',
            signals='question-vector-and-lexical-words',
            vector_depth=VECTOR_DEPTH, lexical_depth=LEXICAL_DEPTH, rrf_k=RRF_K,
            bm25_k1=BM25_K1, bm25_b=BM25_B,
            lexical_policy='nfkc-casefold-unique-query-words-canonical-passage-text-v1',
            unicode_data_version=unidata_version)
        self.retriever_version = identity(self.configuration)

    def _candidate_limit(self, request):
        return VECTOR_DEPTH

    def _rank_passages(self, request, passages):
        dense = sorted(passages, key=lambda row: (-row['score'], row['passage_id']))
        lexical = self._lexical.rank(request['question'])
        scores = defaultdict(float)
        for ranking in ([row['passage_id'] for row in dense], lexical):
            for rank, key in enumerate(ranking, start=1):
                scores[key] += 1 / (RRF_K + rank)
        signals = ['question', 'lexical_words'] if lexical else ['question']
        return [self._passage_record(key, score) for key, score in scores.items()], signals, (
            'Score sums reciprocal vector and lexical ranks within the configured candidate pools. '
            'Higher ranks better within this retriever/index version. Scores do not measure clinical '
            'confidence or proof of answer support. Candidates are not assessed for answerability.')
