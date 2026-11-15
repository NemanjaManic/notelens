"""Embedding-only candidate ranking, separate from answer-support decisions."""

import hashlib
import math

from notelens_contracts.v1 import ContractValidationError, validate_record

from .embeddings import DIMENSIONS, MODEL, identity


class RetrievalError(ValueError):
    """A fixed diagnostic without question text, index contents or upstream bodies."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise RetrievalError(code, message)


class CandidateRetriever:
    """Internal ranking primitive; callers admit reviewed English development input."""

    def __init__(self, index, *, top_k=5):
        require(type(top_k) is int and 1 <= top_k <= 5, 'retrieval_configuration',
                'This development ranking accepts between one and five candidates.')
        self.index, self.top_k = index, top_k
        self.configuration = {'algorithm': 'chroma-embedding-only-v1', 'top_k': top_k,
            'query_policy': 'unchanged-self-contained-question-v1',
            'score': 'one-minus-cosine-distance-v1', 'signals': 'question-only',
            'tie_order': 'score-descending-then-passage-id-within-returned-pool',
            'answer_support': 'not-assessed', 'index_version': index.spec['index_version'],
            'embedding_space_version': index.spec['embedding_space_version']}
        self.retriever_version = identity(self.configuration)

    def _prepare(self, request, embedder):
        try:
            validate_record('RetrievalRequest', request)
            request['question'].encode('utf-8', errors='strict')
        except (ContractValidationError, UnicodeError):
            raise RetrievalError('validation_failure', 'The development query does not match the frozen request contract.') from None
        spec = self.index.spec
        require(spec['mode'] == embedder.mode and spec['model'] == MODEL
                and spec['dimensions'] == DIMENSIONS, 'configuration_required',
                'The query embedder and stored embedding space do not match.')
        try:
            self.index.verify()
            require(bool(self.index.corpus.passages), 'configuration_required', 'The verified index has no passages.')
        except RetrievalError:
            raise
        except Exception:
            raise RetrievalError('configuration_required', 'The public index is unavailable or has changed.') from None

    def retrieve(self, request, embedder):
        """Return internal candidates; never assert that related text proves an answer."""
        self._prepare(request, embedder)
        batch = embedder.embed([request['question']])
        require(batch.model == MODEL and len(batch.vectors) == 1, 'invalid_upstream',
                'The question embedding response has a different model or count.')
        vector = batch.vectors[0]
        require(len(vector) == DIMENSIONS and all(type(v) in (int, float) and math.isfinite(v) for v in vector)
                and any(v != 0 for v in vector), 'invalid_upstream', 'The question embedding vector is invalid.')
        count = min(self.top_k, len(self.index.corpus.passages))
        try:
            result = self.index.collection.query(query_embeddings=[list(vector)], n_results=count, include=['distances'])
            require(isinstance(result, dict) and len(result['ids']) == len(result['distances']) == 1,
                    'index_query_failure', 'The index returned malformed ranking data.')
            ids, distances = result['ids'][0], result['distances'][0]
            require(0 < len(ids) <= count and len(ids) == len(distances) and len(ids) == len(set(ids)),
                    'index_query_failure', 'The index returned an invalid candidate count or duplicate IDs.')
            passages = []
            for key, distance in zip(ids, distances, strict=True):
                require(key in self.index.corpus.by_id and type(distance) in (int, float)
                        and math.isfinite(distance) and -0.00001 <= distance <= 2.00001,
                        'index_query_failure', 'The index returned an unknown passage or invalid cosine distance.')
                source = self.index.corpus.by_id[key]
                passage = {'source_id': source.passage_id, 'kind': 'literature',
                    'topic_id': source.topic_id, 'passage_id': source.passage_id, 'title': source.title,
                    'url': source.url, 'text': source.text, 'snapshot_date': self.index.corpus.snapshot_date,
                    'score': 1.0 - float(distance)}
                validate_record('RetrievalPassage', passage)
                passages.append(passage)
            passages.sort(key=lambda row: (-row['score'], row['passage_id']))
        except RetrievalError:
            raise
        except Exception:
            raise RetrievalError('index_query_failure', 'The local index query failed safely.') from None
        return {'record_format_version': 'rag-candidate-ranking-v1', 'status': 'ranked_candidates',
                'mode': self.index.spec['mode'], 'answerability': 'not_assessed',
                'question_sha256': hashlib.sha256(request['question'].encode('utf-8')).hexdigest(),
                'passages': passages, 'top_k': self.top_k, 'signals_used': ['question'],
                'corpus_version': self.index.corpus.corpus_version,
                'index_version': self.index.spec['index_version'], 'retriever_version': self.retriever_version,
                'score_note': 'Score = 1 - Chroma cosine distance. Higher ranks better within this retriever/index version; '
                              'not clinical confidence or proof of answer support. Candidates are not assessed for answerability.'}
