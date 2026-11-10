# Feature Specification: Evidence-Linked Extraction, Document Answers and Shared Evaluation

**Feature Branch**: Not created; feature selection is independent of Git branches.

**Feature Directory**: `specs/004-extraction-evaluation`

**Owner**: D

**Created**: 2026-11-10

**Status**: Draft for user review

**Input**: User description: "Extract source-supported diagnoses, symptoms and procedures, summarize and answer from the document in English, and coordinate human-reviewed annotations plus honest shared evaluation across all workstreams."

**Governing requirements**: [Constitution](../../.specify/memory/constitution.md) and
[source prompt](../../prompts/NoteLens_Codex_SpecKit_prompt_00.md). Implementation choices
belong to the later plan and must preserve the confirmed boundaries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a Faithful Document Summary and Extracted Items (Priority: P1)

As a user, I can inspect source-supported diagnoses, symptoms and procedures with their
assertion, temporality and subject, and read a short understandable English summary.

**Why this priority**: Extraction must preserve what the report actually says.

**Independent Test**: Use prepared document fixtures and draft shared records to inspect
extracted items, exact spans and summary support without real classification/RAG/frontend.

**Acceptance Scenarios**:

1. **Given** a historically confirmed condition, **When** it is extracted, **Then** its
   confirmed assertion and historical temporality remain separate.
2. **Given** negated, suspected and family-history mentions, **When** they are extracted,
   **Then** their statuses/subjects are not silently turned into current patient diagnoses.
3. **Given** repeated mentions and a non-BMP character, **When** evidence is returned,
   **Then** each selected occurrence's quote matches its exact canonical interval.
4. **Given** a source-present ICD code, **When** optional coding is returned, **Then** it
   copies that code; no code is inferred when none is present.

---

### User Story 2 - Ask a Document Question With Support (Priority: P1)

As a user, I can ask an English question about the selected document and receive a supported
answer or a clear evidence limitation.

**Why this priority**: Patient-specific statements require document evidence.

**Independent Test**: Ask answerable/unanswerable fixture questions and review each claim
against its cited canonical passages without a live literature module.

**Acceptance Scenarios**:

1. **Given** a passage supporting an answer, **When** I ask a document question,
   **Then** the English answer links the supporting claim to that passage.
2. **Given** the requested fact is absent, **When** I ask, **Then** absence of support is
   stated rather than filled using general literature or an invented diagnosis.
3. **Given** a mixed question, **When** D supplies the document-supported portion,
   **Then** its provenance can be preserved alongside A's independent literature portion.
4. **Given** a quote that exists but does not support the claim, **When** evidence is
   checked, **Then** quote validity alone does not mark that claim grounded.

---

### User Story 3 - Build Independent Human-Reviewed References (Priority: P1)

As an annotator, I can work on assigned documents in my own path, review different primary
work independently and let D adjudicate disagreements without file collisions.

**Why this priority**: Measured extraction quality depends on reliable reference creation.

**Independent Test**: Review a proposed 40-document assignment manifest against C's group/split
IDs, member paths and separate review/adjudication records.

**Acceptance Scenarios**:

1. **Given** 40 selected representative documents, **When** primary work is assigned,
   **Then** each member receives 10 documents under their own member path.
2. **Given** at least 10 independently second-reviewed documents, **When** disagreements
   occur, **Then** separate submissions are preserved and adjudication records a decision.
3. **Given** development and final documents, **When** references are frozen,
   **Then** no document/group crosses those portions and final references are not used
   to tune prompts.

---

### User Story 4 - Compare Quality With a Shared Honest Evaluation (Priority: P2)

As a team reviewer, I can evaluate versioned module results with deterministic measures,
calibrated human/LLM review, source-aware questions and explicit costs/limitations.

**Why this priority**: A reproducible shared report supports delivery and honest decisions.

**Independent Test**: Run a small key-free scoring suite from known fixture outputs, then
inspect separate development/final datasets and optional live-check controls.

**Acceptance Scenarios**:

1. **Given** several chunks of one relevant topic, **When** retrieval is scored,
   **Then** they count as one topic and cannot satisfy missing necessary topics.
2. **Given** an always-refusing system, **When** answerability is evaluated,
   **Then** poor answer coverage prevents passing on rejection alone.
3. **Given** LLM-judge disagreement with humans, **When** results are reported,
   **Then** calibration, disagreement and judge limits remain visible.
4. **Given** final answer reviews, **When** reporting is completed,
   **Then** those same final examples are not reused to tune the final prompt.

### Edge Cases

- Repeated mentions, overlapping entities, historical certainty, negation and family subjects.
- Exact quote validity with semantically unsupported claims or malformed generation.
- Missing document facts, non-English generation or embedded prompt instructions.
- No C split manifests yet, conflicting group assignments or insufficient class balance.
- A MedQuAD topic URL exists while its chosen corpus summary lacks the answer.
- Multi-source questions where not every diagnosis/topic is necessary, or more than five are.
- Optional silver summaries without span/status ground truth or nonclinical annotators.
- Rate limits/outages, unapproved paid judging or leakage between development/final portions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Define entities, assertion/temporality/subject rules, annotation instructions,
  matching rules, schema proposals and mocks before complete real ML/RAG implementations.
- **FR-002**: Extract diagnoses, symptoms and procedures with stable item identity,
  text/name, status, subject, version and supporting canonical evidence.
- **FR-003**: Keep assertion (including confirmed/suspected/negated) separate from
  temporality (current/historical/unknown); do not attribute family history to the patient.
- **FR-004**: Evidence MUST use exact canonical quotes and half-open code-point intervals.
  Cover non-BMP characters and repeated passages without altering prepared text.
- **FR-005**: Optional ICD output may only reproduce a source-present code; do not infer
  diagnoses, codes or treatment recommendations.
- **FR-006**: Generate short understandable English evidence-linked summaries and
  document-grounded answers within D's owned workstream.
- **FR-007**: Validate generated structure and spans with bounded repair/retry. Separately
  check whether evidence semantically supports extracted items, summary claims and answers.
- **FR-008**: Report unsupported/insufficient/error states explicitly in English.
  Literature MUST NOT fill absent patient-specific facts; retain provenance for mixed answers.
- **FR-009**: Select a planning target of 40 representative documents from C's published
  manifests, approximately balanced across specialties; freeze actual selection/assignment IDs.
- **FR-010**: Separate extraction development/final evaluation by document and duplicate
  group. Where feasible, align development with ML validation and final with ML test.
- **FR-011**: Assign 10 primary documents per member using separate member paths. Add
  independent secondary review for at least 10 documents without shared-file editing.
- **FR-012**: Preserve submissions, adjudicate disagreements and build canonical human-reviewed
  references. Do not call them clinically validated without expert confirmation.
- **FR-013**: Maintain the shared evaluation runner using adapters to agreed module results,
  versioned datasets, deterministic scorers and separate offline/smoke/live profiles.
  Module owners retain local tests and supply outputs; D does not edit A/C implementations.
- **FR-014**: Assemble approximately 80 QA cases with separate development/final portions,
  around 30 multi-source cases, around 10 lacking required-source answers and out-of-scope cases.
  Publish exact counts, category overlap definitions, versions and relevant topic/passage IDs.
- **FR-015**: Preserve original MedQuAD references; review questions against selected corpus
  evidence. Do not assume every diagnosis's topic is necessary to answer each question.
- **FR-016**: Measure classification macro-F1/per-class performance, confusion matrix,
  baseline comparison and leakage using C's outputs and recorded sample/version information.
- **FR-017**: Measure extraction structure, exact quote/offset validity, entity precision/
  recall/F1 under predefined exact/relaxed rules, assertion/temporality accuracy and
  unsupported-item rate. Define repeated-mention matching before scoring.
- **FR-018**: Measure source-relative correctness, groundedness, completeness, citation
  correctness and English compliance for summaries and answers.
- **FR-019**: Measure unique-topic Recall@5, MRR and all-required-topics@5 separately for
  single-/multi-source cases; report actual passage evidence coverage and flag more-than-five-
  necessary-topic questions. Do not double-count chunks or identical metric formulas.
- **FR-020**: Measure answer rate for answerable cases, correct rejection for unanswerable
  cases and error risk versus coverage. Always-refusing systems MUST not pass on abstention alone.
- **FR-021**: Define LLM-judge rubrics and calibrate on development examples with human
  review; record judge/model/prompt versions and disagreements. Judges are not the sole measure.
- **FR-022**: Plan approximately 40 generated-answer reviews, 10 per member, plus at least
  20 entity-evidence pair reviews, separate from initial document annotation. Final reviews
  inform reporting, not tuning against the same held-out examples.
- **FR-023**: Require 100% structural and quote/offset validity on the defined acceptance
  suite; leave substantive thresholds unset until first development measurements and team
  decisions targeted for 2026-11-14. Do not invent agreed numeric values.
- **FR-024**: Produce an English report of measured results, baseline comparisons, sample
  counts, costs, limitations, frozen configurations and accepted/rejected regressions.
  Never conceal a regression or alter a threshold merely to pass.
- **FR-025**: Routine checks MUST be deterministic/key-free; paid evaluation uses explicit
  triggering, caching, bounded calls and approved budget. Final runs use frozen versions
  and repeat only with a new version and documented reason.
- **FR-026**: Optional augmented notes remain nonblocking; generated silver summaries are
  not span/entity/status ground truth. Review provenance/licenses and report separately.
- **FR-027**: Integrate B's defined security and English review evidence into final reporting
  without claiming that finite checks prove universal safety.

### Key Entities *(include if feature involves data)*

- **Extracted item**: Identity, entity type/name, assertion, temporality, subject and evidence.
- **Document generation result**: Summary or answer with claim-linked canonical support,
  versions and explicit limitations.
- **Annotation assignment**: Document/group/split IDs, primary member and independent reviewer.
- **Reference set**: Preserved submissions, adjudication, versions and development/final designation.
- **QA relevance case**: Question, required source types/topics/passages, answerability and categories.
- **Evaluation run/review**: Frozen inputs/configurations, deterministic metrics, human/judge
  decisions, costs and limitations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All defined structural/quote-offset acceptance cases pass, including independent
  assertion/temporality/subject and non-BMP/repeated-passage cases.
- **SC-002**: The annotation manifest accounts for 40 primary documents, 10 per member,
  at least 10 independent secondary reviews, adjudication and no development/final group overlap.
- **SC-003**: QA reporting publishes actual counts around the approved targets, all required
  source/category/relevance definitions and separate development/final versions.
- **SC-004**: The key-free shared scoring suite reports the required extraction, answer,
  retrieval and rejection measures on known fixtures, with mock results explicitly labeled.
- **SC-005**: Human-review reporting accounts for approximately 40 generated answers and
  at least 20 entity-evidence pairs separately from document annotation and judge calibration.
- **SC-006**: Final reporting identifies actual sample/configuration versions, frozen-test
  handling, baseline comparisons, costs, limitations and team threshold/regression decisions.

## Assumptions

- Counts are approved planning targets, not evidence that documents/questions/reviews exist.
  Assignments depend on C's manifests and relevance review on A's chosen corpus.
- Shared record details depend on B's collection/freeze of proposals. D can draft guidelines,
  mocks and the evaluator before complete real modules exist.
- Budgets, operational limits and substantive quality thresholds remain
  [open decisions](../../docs/team/open-decisions.md); no numeric defaults are inferred.
- This specification creates no annotations, model calls, judge results, measured metrics
  or implementation.