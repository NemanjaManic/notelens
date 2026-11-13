# Generated; do not edit. Runtime validation is required.
from __future__ import annotations
from typing import TypedDict, NotRequired, Literal, Union, TypeAlias

class EvidenceSpan(TypedDict):
    start: int
    end: int
    quote: str

class PreparedDocument(TypedDict):
    schema_version: Literal['1.0.0']
    doc_id: str
    text_sha256: str
    text: str
    canonicalization_version: Literal['nfc-lf-v1']
    source: PreparedDocumentSource
    language: Literal['en']
    language_validation: LanguageValidation

class ClassificationScore(TypedDict):
    category: Literal['Cardiovascular / Pulmonary', 'Orthopedic', 'Gastroenterology', 'Neurology', 'Urology']
    score: float

class ClassificationResult(TypedDict):
    schema_version: Literal['1.0.0']
    mode: Literal['mock', 'live']
    doc_id: str
    text_sha256: str
    status: Literal['supported', 'uncertain', 'unsupported']
    category: Union[Literal['Cardiovascular / Pulmonary', 'Orthopedic', 'Gastroenterology', 'Neurology', 'Urology'], None]
    scores: list[ClassificationScore]
    score_kind: Union[Literal['probability', 'decision_score'], None]
    confidence_note: str
    model_version: Union[str, None]
    classification_execution: Literal['skipped', 'performed']
    scope_policy_version: Union[str, None]
    scope_reason: Union[str, None]

class DocumentSource(TypedDict):
    source_id: str
    kind: Literal['document']
    doc_id: str
    text_sha256: str
    evidence: EvidenceSpan
    component_id: str

class LiteratureSource(TypedDict):
    source_id: str
    kind: Literal['literature']
    topic_id: str
    passage_id: str
    title: str
    url: str
    text: str
    snapshot_date: str
    component_id: str

class Claim(TypedDict):
    claim_id: str
    text: str
    scope: Literal['document_fact', 'general_information']
    source_ids: list[str]
    component_id: str

class Summary(TypedDict):
    language: Literal['en']
    text: str
    claims: list[Claim]
    sources: list[DocumentSource]
    evidence_state: Literal['sufficient', 'partial', 'insufficient']
    warnings: list[str]
    provenance: Union[ComponentProvenance, None]

class ExtractionItemRequired(TypedDict):
    entity_id: str
    type: Literal['diagnosis', 'symptom', 'procedure']
    name: str
    assertion: Literal['confirmed', 'suspected', 'negated', 'unknown']
    temporality: Literal['current', 'historical', 'unknown']
    subject: Literal['patient', 'family', 'other', 'unknown']
    evidence: list[EvidenceSpan]
    mention: EvidenceSpan
    component_id: str
    procedure_status: Literal[None, 'planned', 'ordered', 'performed', 'cancelled', 'hypothetical', 'unknown']

class ExtractionItem(ExtractionItemRequired, total=False):
    icd: NotRequired[ExtractionItemIcd]

class ExtractionResult(TypedDict):
    schema_version: Literal['1.0.0']
    mode: Literal['mock', 'live', 'mixed']
    doc_id: str
    text_sha256: str
    items: list[ExtractionItem]
    summary: SummaryOutcome
    extractor_version: str
    prompt_version: Union[str, None]
    extraction_status: Literal['completed', 'partial', 'failed']
    extraction_error: Union[ErrorDetail, None]
    warnings: list[str]
    extraction_provenance: Union[ComponentProvenance, None]

class RetrievalRequestRequired(TypedDict):
    schema_version: Literal['1.0.0']
    question: str

class RetrievalRequest(RetrievalRequestRequired, total=False):
    concepts: NotRequired[list[str]]
    specialty_hint: NotRequired[Union[Literal['Cardiovascular / Pulmonary', 'Orthopedic', 'Gastroenterology', 'Neurology', 'Urology'], None]]

class RetrievalPassage(TypedDict):
    source_id: str
    kind: Literal['literature']
    topic_id: str
    passage_id: str
    title: str
    url: str
    text: str
    snapshot_date: str
    score: float

class RetrievalResult(TypedDict):
    schema_version: Literal['1.0.0']
    mode: Literal['mock', 'live']
    state: Literal['sufficient', 'insufficient']
    passages: list[RetrievalPassage]
    retriever_version: str
    index_version: str
    score_note: str
    corpus_version: str

class AnswerResult(TypedDict):
    schema_version: Literal['1.0.0']
    mode: Literal['mock', 'live', 'mixed']
    language: Literal['en']
    text: str
    claims: list[Claim]
    sources: list[Source]
    evidence_state: Literal['sufficient', 'partial', 'insufficient']
    warnings: list[str]
    route: Literal['document', 'literature', 'mixed', 'none']
    answer_version: str
    prompt_version: Union[str, None]
    components: list[ComponentProvenance]
    attempted_routes: list[Literal['document', 'literature']]
    clarification: Union[Clarification, None]
    retrieval_provenance: Union[RetrievalProvenance, None]

class ClassificationRequest(TypedDict):
    schema_version: Literal['1.0.0']
    document: PreparedDocument

class ExtractionRequest(TypedDict):
    schema_version: Literal['1.0.0']
    document: PreparedDocument

class DocumentQuestionRequestRequired(TypedDict):
    schema_version: Literal['1.0.0']
    document: PreparedDocument
    question: str

class DocumentQuestionRequest(DocumentQuestionRequestRequired, total=False):
    history: NotRequired[list[DocumentQuestionRequestHistoryItem]]

class ErrorDetail(TypedDict):
    code: Literal['unsupported_file', 'unsupported_language', 'validation_failure', 'timeout', 'rate_limit', 'provider_unavailable', 'insufficient_evidence', 'document_unavailable', 'unauthorized', 'configuration_required', 'budget_exceeded', 'internal_error']
    message: str
    retryable: bool

class ErrorEnvelope(TypedDict):
    schema_version: Literal['1.0.0']
    request_id: RequestId
    error: ErrorDetail

class HealthResult(TypedDict):
    schema_version: Literal['1.0.0']
    service: Literal['rag', 'classifier', 'extraction']
    status: Literal['ok', 'not_ready']
    mode: Literal['mock', 'live']
    version: str
    model_version: Union[str, None]
    reason: Union[str, None]

class LanguageValidation(TypedDict):
    outcome: Literal['accepted', 'rejected', 'inconclusive']
    language: Union[Literal['en'], None]
    policy_version: str
    reason: Literal[None, 'unsupported_language', 'language_inconclusive']

class ComponentProvenance(TypedDict):
    component_id: str
    service: Literal['rag', 'extraction']
    operation: Literal['extract', 'summarize', 'document-answer', 'literature-answer']
    mode: Literal['mock', 'live']
    output_version: str
    prompt_version: str
    provider: str
    model: str
    configuration_version: str
    corpus_version: Union[str, None]
    index_version: Union[str, None]
    retriever_version: Union[str, None]

class SummaryOutcome(TypedDict):
    status: Literal['completed', 'failed']
    result: Union[Summary, None]
    error: Union[ErrorDetail, None]

class Clarification(TypedDict):
    code: Literal['ambiguous_reference']
    message: str

class RetrievalProvenance(TypedDict):
    service: Literal['rag']
    mode: Literal['mock', 'live']
    state: Literal['sufficient', 'insufficient']
    corpus_version: str
    index_version: str
    retriever_version: str
    score_note: str

class LivenessResult(TypedDict):
    schema_version: Literal['1.0.0']
    service: Literal['rag', 'classifier', 'extraction']
    status: Literal['alive']
    mode: Literal['mock', 'live']
    version: str

class PreparedDocumentSourceRequired(TypedDict):
    kind: Literal['builtin_public', 'public_text', 'synthetic_text', 'text_pdf']

class PreparedDocumentSource(PreparedDocumentSourceRequired, total=False):
    name: NotRequired[str]

class ExtractionItemIcd(TypedDict):
    code: str
    evidence: EvidenceSpan

class DocumentQuestionRequestHistoryItem(TypedDict):
    role: Literal['user', 'assistant']
    text: str

Source: TypeAlias = Union['DocumentSource', 'LiteratureSource']

LiteratureAnswerRequest: TypeAlias = RetrievalRequest

RequestId: TypeAlias = str

from .runtime import validate_record, validate_json, validate_exchange, ContractValidationError, Issue
