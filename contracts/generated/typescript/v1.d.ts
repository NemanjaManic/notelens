// Generated; do not edit. Runtime validation is required.

export interface EvidenceSpan {
  start: number;
  end: number;
  quote: string;
}

export interface PreparedDocument {
  schema_version: "1.0.0";
  doc_id: string;
  text_sha256: string;
  text: string;
  canonicalization_version: "nfc-lf-v1";
  source: PreparedDocumentSource;
  language: "en";
  language_validation: LanguageValidation;
}

export interface ClassificationScore {
  category: "Cardiovascular / Pulmonary" | "Orthopedic" | "Gastroenterology" | "Neurology" | "Urology";
  score: number;
}

export interface ClassificationResult {
  schema_version: "1.0.0";
  mode: "mock" | "live";
  doc_id: string;
  text_sha256: string;
  status: "supported" | "uncertain" | "unsupported";
  category: ("Cardiovascular / Pulmonary" | "Orthopedic" | "Gastroenterology" | "Neurology" | "Urology" | null);
  scores: (ClassificationScore)[];
  score_kind: ("probability" | "decision_score" | null);
  confidence_note: string;
  model_version: (string | null);
  classification_execution: "skipped" | "performed";
  scope_policy_version: (string | null);
  scope_reason: (string | null);
}

export interface DocumentSource {
  source_id: string;
  kind: "document";
  doc_id: string;
  text_sha256: string;
  evidence: EvidenceSpan;
  component_id: string;
}

export interface LiteratureSource {
  source_id: string;
  kind: "literature";
  topic_id: string;
  passage_id: string;
  title: string;
  url: string;
  text: string;
  snapshot_date: string;
  component_id: string;
}

export type Source = (DocumentSource | LiteratureSource);

export interface Claim {
  claim_id: string;
  text: string;
  scope: "document_fact" | "general_information";
  source_ids: (string)[];
  component_id: string;
}

export interface Summary {
  language: "en";
  text: string;
  claims: (Claim)[];
  sources: (DocumentSource)[];
  evidence_state: "sufficient" | "partial" | "insufficient";
  warnings: (string)[];
  provenance: (ComponentProvenance | null);
}

export interface ExtractionItem {
  entity_id: string;
  type: "diagnosis" | "symptom" | "procedure";
  name: string;
  assertion: "confirmed" | "suspected" | "negated" | "unknown";
  temporality: "current" | "historical" | "unknown";
  subject: "patient" | "family" | "other" | "unknown";
  evidence: (EvidenceSpan)[];
  icd?: ExtractionItemIcd;
  mention: EvidenceSpan;
  component_id: string;
  procedure_status: null | "planned" | "ordered" | "performed" | "cancelled" | "hypothetical" | "unknown";
}

export interface ExtractionResult {
  schema_version: "1.0.0";
  mode: "mock" | "live" | "mixed";
  doc_id: string;
  text_sha256: string;
  items: (ExtractionItem)[];
  summary: SummaryOutcome;
  extractor_version: string;
  prompt_version: (string | null);
  extraction_status: "completed" | "partial" | "failed";
  extraction_error: (ErrorDetail | null);
  warnings: (string)[];
  extraction_provenance: (ComponentProvenance | null);
}

export interface RetrievalRequest {
  schema_version: "1.0.0";
  question: string;
  concepts?: (string)[];
  specialty_hint?: ("Cardiovascular / Pulmonary" | "Orthopedic" | "Gastroenterology" | "Neurology" | "Urology" | null);
}

export interface RetrievalPassage {
  source_id: string;
  kind: "literature";
  topic_id: string;
  passage_id: string;
  title: string;
  url: string;
  text: string;
  snapshot_date: string;
  score: number;
}

export interface RetrievalResult {
  schema_version: "1.0.0";
  mode: "mock" | "live";
  state: "sufficient" | "insufficient";
  passages: (RetrievalPassage)[];
  retriever_version: string;
  index_version: string;
  score_note: string;
  corpus_version: string;
}

export interface AnswerResult {
  schema_version: "1.0.0";
  mode: "mock" | "live" | "mixed";
  language: "en";
  text: string;
  claims: (Claim)[];
  sources: (Source)[];
  evidence_state: "sufficient" | "partial" | "insufficient";
  warnings: (string)[];
  route: "document" | "literature" | "mixed" | "none";
  answer_version: string;
  prompt_version: (string | null);
  components: (ComponentProvenance)[];
  attempted_routes: ("document" | "literature")[];
  clarification: (Clarification | null);
  retrieval_provenance: (RetrievalProvenance | null);
}

export interface ClassificationRequest {
  schema_version: "1.0.0";
  document: PreparedDocument;
}

export interface ExtractionRequest {
  schema_version: "1.0.0";
  document: PreparedDocument;
}

export interface DocumentQuestionRequest {
  schema_version: "1.0.0";
  document: PreparedDocument;
  question: string;
  history?: (DocumentQuestionRequestHistoryItem)[];
}

export type LiteratureAnswerRequest = RetrievalRequest;

export interface ErrorDetail {
  code: "unsupported_file" | "unsupported_language" | "validation_failure" | "timeout" | "rate_limit" | "provider_unavailable" | "insufficient_evidence" | "document_unavailable" | "unauthorized" | "configuration_required" | "budget_exceeded" | "internal_error";
  message: string;
  retryable: boolean;
}

export interface ErrorEnvelope {
  schema_version: "1.0.0";
  request_id: RequestId;
  error: ErrorDetail;
}

export interface HealthResult {
  schema_version: "1.0.0";
  service: "rag" | "classifier" | "extraction";
  status: "ok" | "not_ready";
  mode: "mock" | "live";
  version: string;
  model_version: (string | null);
  reason: (string | null);
}

export type RequestId = string;

export interface LanguageValidation {
  outcome: "accepted" | "rejected" | "inconclusive";
  language: ("en" | null);
  policy_version: string;
  reason: null | "unsupported_language" | "language_inconclusive";
}

export interface ComponentProvenance {
  component_id: string;
  service: "rag" | "extraction";
  operation: "extract" | "summarize" | "document-answer" | "literature-answer";
  mode: "mock" | "live";
  output_version: string;
  prompt_version: string;
  provider: string;
  model: string;
  configuration_version: string;
  corpus_version: (string | null);
  index_version: (string | null);
  retriever_version: (string | null);
}

export interface SummaryOutcome {
  status: "completed" | "failed";
  result: (Summary | null);
  error: (ErrorDetail | null);
}

export interface Clarification {
  code: "ambiguous_reference";
  message: string;
}

export interface RetrievalProvenance {
  service: "rag";
  mode: "mock" | "live";
  state: "sufficient" | "insufficient";
  corpus_version: string;
  index_version: string;
  retriever_version: string;
  score_note: string;
}

export interface LivenessResult {
  schema_version: "1.0.0";
  service: "rag" | "classifier" | "extraction";
  status: "alive";
  mode: "mock" | "live";
  version: string;
}

export interface PreparedDocumentSource {
  kind: "builtin_public" | "public_text" | "synthetic_text" | "text_pdf";
  name?: string;
}

export interface ExtractionItemIcd {
  code: string;
  evidence: EvidenceSpan;
}

export interface DocumentQuestionRequestHistoryItem {
  role: "user" | "assistant";
  text: string;
}

export interface Records {
  EvidenceSpan: EvidenceSpan;
  PreparedDocument: PreparedDocument;
  ClassificationScore: ClassificationScore;
  ClassificationResult: ClassificationResult;
  DocumentSource: DocumentSource;
  LiteratureSource: LiteratureSource;
  Source: Source;
  Claim: Claim;
  Summary: Summary;
  ExtractionItem: ExtractionItem;
  ExtractionResult: ExtractionResult;
  RetrievalRequest: RetrievalRequest;
  RetrievalPassage: RetrievalPassage;
  RetrievalResult: RetrievalResult;
  AnswerResult: AnswerResult;
  ClassificationRequest: ClassificationRequest;
  ExtractionRequest: ExtractionRequest;
  DocumentQuestionRequest: DocumentQuestionRequest;
  LiteratureAnswerRequest: LiteratureAnswerRequest;
  ErrorDetail: ErrorDetail;
  ErrorEnvelope: ErrorEnvelope;
  HealthResult: HealthResult;
  RequestId: RequestId;
  LanguageValidation: LanguageValidation;
  ComponentProvenance: ComponentProvenance;
  SummaryOutcome: SummaryOutcome;
  Clarification: Clarification;
  RetrievalProvenance: RetrievalProvenance;
  LivenessResult: LivenessResult;
}
export interface Issue { rule: string; path: string; }
export interface Context { document?: PreparedDocument; reference?: { attributes?: Record<string, unknown>; spans?: Record<string, unknown> }; }
export function validatePayload<K extends keyof Records>(definition: K, payload: unknown, context?: Context): Promise<Issue[]>;
export function validateRecord<K extends keyof Records>(definition: K, payload: unknown, context?: Context): Promise<Records[K]>;
export function validateJson<K extends keyof Records>(definition: K, text: string, context?: Context): Promise<Records[K]>;
export interface Exchange { request_headers: [string,string][]; response_headers: [string,string][]; status: number; body: unknown; path?: string; disposition: string; }
export function validateExchange(exchange: Exchange): Promise<string[]>;
export class ContractValidationError extends Error { issues: Issue[]; }
