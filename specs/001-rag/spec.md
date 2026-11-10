# Feature Specification: Evidence-Grounded Medical Literature Retrieval and Answers

**Feature Branch**: Not created; feature selection is independent of Git branches.

**Feature Directory**: `specs/001-rag`

**Owner**: A

**Created**: 2026-11-10

**Status**: Draft for user review

**Input**: User description: "Let NoteLens answer English medical-concept questions from a small curated MedlinePlus corpus with traceable passages, measured retrieval quality and explicit evidence limitations."

**Governing requirements**: [Constitution](../../.specify/memory/constitution.md) and
[source prompt](../../prompts/NoteLens_Codex_SpecKit_prompt_00.md). Implementation choices
belong to the later plan and must preserve the confirmed boundaries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a Medical Concept With Sources (Priority: P1)

As a demo user, I can ask an English medical-concept question and receive an understandable
English answer supported by inspectable, attributable literature passages.

**Why this priority**: Literature explanations are RAG's core user value.

**Independent Test**: Ask answerable questions against a small permitted corpus fixture
through the RAG workstream's standalone interface; inspect source links and grounded claims
without a real classifier, extraction module or complete frontend.

**Acceptance Scenarios**:

1. **Given** a corpus passage containing the requested explanation, **When** a relevant
   concept question is asked, **Then** the answer cites supporting topic/passages and
   preserves title, URL and corpus/retriever versions.
2. **Given** no patient document evidence, **When** literature explains a condition,
   **Then** it does not claim that the user or a patient has that condition.
3. **Given** an extracted concept name, **When** it helps retrieval, **Then** it can be used
   without requiring an ICD code.

---

### User Story 2 - Find All Necessary Topics (Priority: P1)

As an evaluator, I can compare retrieval behavior on questions that require one or several
topics and inspect whether returned passages actually contain the needed evidence.

**Why this priority**: Finding related topics alone does not establish answerability.

**Independent Test**: Run fixed development questions against a versioned corpus and
human-reviewed relevant topic/passages; inspect unique-topic ranking and evidence coverage.

**Acceptance Scenarios**:

1. **Given** two required topics for a question, **When** retrieval returns repeated chunks
   of only one, **Then** evaluation does not count them as both topics or complete coverage.
2. **Given** an incorrect specialty prediction, **When** relevant sources are outside it,
   **Then** those sources remain eligible.
3. **Given** a question whose referenced topic URL exists but whose answer is absent from
   the selected summary, **When** answerability is reviewed, **Then** the case is not
   automatically marked answerable.

---

### User Story 3 - Receive an Honest Partial or Unavailable Outcome (Priority: P2)

As a user, I can understand when literature evidence is missing or the provider is unavailable
without losing separately supported document information.

**Why this priority**: Transparent limits prevent unsupported medical claims.

**Independent Test**: Use empty-corpus, insufficient-evidence, timeout, rate-limit and outage
fixtures and inspect RAG outputs independently of other real modules.

**Acceptance Scenarios**:

1. **Given** inadequate literature evidence, **When** an answer is requested, **Then**
   unsupported literature claims are withheld and the evidence gap is explicit in English.
2. **Given** document support handled elsewhere, **When** literature is insufficient,
   **Then** RAG's outcome does not instruct orchestration to suppress that document support.
3. **Given** an unavailable provider, **When** the request exceeds bounded recovery,
   **Then** a clear error is returned rather than fabricated passages or an unbounded retry.

### Edge Cases

- Empty or changed corpus, duplicate topics, missing metadata or broken provenance.
- Several chunks of one topic; a question requiring more than five topics.
- A specialty mistake, absent extracted concepts or no ICD codes.
- A low retrieval score, stale/mismatched index version or incompatible embedding space.
- Out-of-scope/non-English questions or instructions embedded in retrieved text.
- A provider rate limit, timeout, outage or unapproved budget.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Use a small inspectable English MedlinePlus Health Topic corpus restricted
  to relevant subjects; preserve snapshot date, topic ID, title, URL, synonyms and attribution.
- **FR-002**: Review reuse conditions before redistribution; do not automatically ingest
  outbound links, licensed encyclopedia content or drug monographs.
- **FR-003**: Publish measured topic/chunk counts and version/checksum provenance after
  acquisition; do not present source-plan estimates as measured results.
- **FR-004**: Preserve stable topic/passage identities and attributable source content
  throughout corpus preparation, retrieval, evaluation and answer generation.
- **FR-005**: Support concept names from questions and extraction without requiring ICD
  codes. Predicted specialty may be a soft signal and MUST NOT be a mandatory exclusion filter.
- **FR-006**: Return ranked passages with source identities, text, scores, versions and an
  explicit sufficient/insufficient/error outcome satisfying the agreed shared records.
- **FR-007**: Generate English literature-grounded answers with claim-linked citations
  inside A's owned workstream; do not transfer RAG business logic to platform integration.
- **FR-008**: Distinguish general medical information from patient-specific claims.
  Do not infer patient diagnoses, recommend treatment or invent clinical certainty.
- **FR-009**: Use retriever-specific evidence thresholds selected on development data.
  A retrieval score is not a probability of truth; low scores block unsupported literature
  claims without blocking document-supported answers from D.
- **FR-010**: Supply supported literature portions and explicit gaps for combination with
  document results; preserve provenance instead of filling unsupported mixed-answer claims.
- **FR-011**: Keep evaluation questions/reference answers out of the retrieval corpus.
  Check MedQuAD-derived cases against evidence actually present in the chosen snapshot.
- **FR-012**: Propose relevant single-/multi-source questions and references to D.
  Preserve original references and human-reviewed relevant topics/passages.
- **FR-013**: Measure unique-topic Recall@5, MRR and all-required-topics@5 separately for
  single-source/multi-source cases; do not inflate recall with repeated chunks or rename
  identical recall formulas as independent coverage measures.
- **FR-014**: Evaluate passage evidence coverage, answerability/rejection and empty/provider-
  failure behavior. Flag questions requiring more than five necessary topics.
- **FR-015**: Compare a retrieval baseline and a lexical/hybrid alternative on the same
  development questions; choose configurations by evidence, not final-test tuning.
  Reranking remains optional and depends on measured benefit, deadline and approved cost.
- **FR-016**: Maintain independent local mock checks and agreed-record validation.
  Deliver stable examples/start instructions to B and versioned evaluation outputs to D
  without editing their implementations.
- **FR-017**: Keep A's annotations/reviews under the explicit member-a path; D owns
  assignment and canonical-reference coordination.
- **FR-018**: Apply caching, timeouts, bounded retries, usage controls and explicit 429/
  outage outcomes. Provider activation needs approval; mocks MUST be key-free.
- **FR-019**: A changed embedding space MUST require reindexing and a new index version;
  never mix incompatible representations.
- **FR-020**: Treat retrieved text as untrusted evidence, not instructions. Unsupported
  input/language outcomes and all visible explanations MUST remain English.

### Key Entities *(include if feature involves data)*

- **Knowledge snapshot**: Permitted source version/date, checksums, attribution and counts.
- **Topic/passage**: Stable identity, readable content and original source metadata.
- **Retrieval request/result**: Question, optional concept/specialty signals, ranked evidence,
  versions and explicit evidence/error state.
- **Literature answer**: English claims linked to literature sources, limitations and warnings.
- **Relevance case**: Development/final designation, necessary unique topics/passages and
  evidence-based answerability.
- **Retrieval experiment**: Frozen candidate configuration, question versions, measurements
  and limitations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every passage/answer in the structural acceptance suite has valid shared
  structure, required source identities and versions, and English presentation.
- **SC-002**: Evaluation reports all three required ranking measurements, single-/multi-source
  counts, passage evidence coverage and rejection behavior on versioned inputs.
- **SC-003**: The same fixed development cases compare the baseline and alternative, and
  the chosen configuration/reason is recorded without using locked final questions.
- **SC-004**: Defined insufficient-evidence and outage fixtures return explicit outcomes,
  including a case where an independently supported document answer remains usable.
- **SC-005**: Acquired corpus reports actual unique-topic and passage counts and permitted
  provenance; every generated literature claim is reviewable against its cited evidence.
- **SC-006**: B and D can consume A's agreed example outputs without completed implementations
  of other modules. Semantic thresholds remain pending measured team acceptance.

## Assumptions

- Scope and sources are confirmed by the prompt; no corpus content, reuse permission,
  counts, provider budget or measured retrieval quality is assumed.
- Shared contract details depend on B's collection/freeze of proposals. A can inspect
  corpus sources and prepare proposals before that freeze.
- Exact snapshot/topics, supported provider configuration and acceptance thresholds remain
  recorded in [open decisions](../../docs/team/open-decisions.md).
- This is a specification; ingestion, retrieval, generation and evaluation are not implemented.