"""Owner-local service composition with explicit providers and no implicit activation."""

from collections.abc import Callable
from dataclasses import dataclass

from .answers import PARTIAL_POLICY, prepare_answer, retrieval_result, unsupported_answer
from .assessor import AssessmentError
from .contracts import Contracts
from .embeddings import EmbeddingError
from .ingestion import repository_directory, valid_hash
from .retrieval import CandidateRetriever, RetrievalError
from .support import assess_empty_candidates


class RagServiceError(ValueError):
    """Safe transport classification; never include question or provider bodies."""

    def __init__(self, code):
        self.code = code
        super().__init__('The RAG operation could not be completed safely.')


@dataclass(frozen=True)
class IndexedBackend:
    """Explicit startup inputs. Adapter construction and activation belong to the caller."""

    index_version: str
    model_version: str
    embedder: object
    admit: Callable
    requirements: Callable
    assessor: object
    generator: object
    partial_policy: str | None = None

    def bind(self, corpus, *, repository_root, mode):
        if (not valid_hash(self.index_version) or getattr(self.embedder, 'mode', None) != mode
                or not callable(getattr(self.embedder, 'embed', None))):
            raise RagServiceError('configuration_required')
        try:
            from .indexing import load_index

            index = load_index(corpus, repository_root=repository_directory(repository_root), mode=mode,
                               expected_index_version=self.index_version)
            retriever = CandidateRetriever(index)
        except Exception:
            # Startup errors can contain filesystem paths or vector-store internals.
            raise RagServiceError('configuration_required') from None

        return RagService(mode=mode, admit=self.admit, rank=lambda request: retriever.retrieve(request, self.embedder),
                          requirements=self.requirements, assessor=self.assessor, generator=self.generator,
                          health_check=lambda: index.collection.count() == corpus.passage_count,
                          model_version=self.model_version, partial_policy=self.partial_policy)


class RagService:
    """Bind admission, ranking, decomposition, assessment and generation explicitly.

    Nothing loads credentials, starts a client, writes content or assumes a live
    budget here. Production providers must supply their own authorized accounting
    and activation gates. The default application does not construct this service.
    """

    def __init__(self, *, mode, admit, rank, requirements, assessor, generator,
                 health_check, model_version, partial_policy=None):
        if (mode not in ('mock', 'live') or partial_policy not in (None, PARTIAL_POLICY)
                or not all(callable(value) for value in (admit, rank, requirements, health_check))
                or not callable(getattr(assessor, 'assess', None))
                or not callable(getattr(generator, 'generate', None))
                or not isinstance(model_version, str) or not model_version.strip()):
            raise RagServiceError('configuration_required')
        self.mode, self.model_version = mode, model_version
        self.admit, self.rank, self.requirements = admit, rank, requirements
        self.assessor, self.generator, self.health_check = assessor, generator, health_check
        self.partial_policy = partial_policy

    def is_ready(self):
        try:
            return self.health_check() is True
        except Exception:
            return False

    def _prepare(self, request):
        Contracts().validate('RetrievalRequest', request)
        if not self.is_ready():
            raise RagServiceError('configuration_required')
        if self.admit(request) is not True:
            raise RagServiceError('validation_failure')
        # Admission runs before ranking/decomposition: unsupported input cannot
        # trigger model calls through this composition layer.
        requirements = self.requirements(request)
        candidates = self.rank(request)
        if not isinstance(candidates, dict) or candidates.get('mode') != self.mode:
            raise RagServiceError('configuration_required')
        if candidates.get('passages') == []:
            decision = assess_empty_candidates(request, candidates, requirements)
            return prepare_answer(request, candidates, requirements, decision)
        assessment = self.assessor.assess(request, candidates, requirements)
        if assessment.mode != self.mode:
            raise RagServiceError('configuration_required')
        return prepare_answer(request, candidates, requirements, assessment.decision)

    def _operate(self, request, *, generate):
        try:
            prepared = self._prepare(request)
            if not generate:
                return retrieval_result(prepared, partial_policy=self.partial_policy)
            if prepared.coverage == 'none':
                return unsupported_answer(prepared).body
            result = self.generator.generate(prepared, partial_policy=self.partial_policy)
            body = result.body
            Contracts().validate('AnswerResult', body)
            if body['mode'] != self.mode:
                raise RagServiceError('configuration_required')
            return body
        except (AssessmentError, EmbeddingError, RetrievalError) as failure:
            known = {'timeout', 'rate_limit', 'provider_unavailable', 'budget_exceeded',
                     'configuration_required', 'validation_failure'}
            code = failure.code
            if isinstance(failure, AssessmentError) and code in (
                    'unsupported_language', 'needs_clarification', 'out_of_scope'):
                raise RagServiceError(code) from None
            if code in ('partial_policy_required', 'provider_authentication', 'embedding_configuration',
                        'tokenizer_unavailable'):
                code = 'configuration_required'
            if code == 'embedding_input_invalid':
                code = 'validation_failure'
            raise RagServiceError(code if code in known else 'internal_error') from None

    def retrieve(self, request):
        return self._operate(request, generate=False)

    def answer(self, request):
        return self._operate(request, generate=True)
