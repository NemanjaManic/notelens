# Feature Specification: Complete English Demo Interface and Safe Module Integration

**Feature Branch**: Not created; feature selection is independent of Git branches.

**Feature Directory**: `specs/002-platform`

**Owner**: B

**Created**: 2026-11-10

**Status**: Draft for user review

**Input**: User description: "Provide the complete English NoteLens demo experience for public/synthetic medical documents, integrate the three independent workstreams and preserve safe access, evidence and deployment controls."

**Governing requirements**: [Constitution](../../.specify/memory/constitution.md) and
[source prompt](../../prompts/NoteLens_Codex_SpecKit_prompt_00.md). Implementation choices
belong to the later plan and must preserve the confirmed boundaries.

## Clarifications

### Session 2026-11-10

- Q: May submitted demo documents be kept only in server memory for at most 60 minutes,
  deleted on expiry or restart? -> A: Yes; memory only, at most 60 minutes. Built-in public
  examples may remain versioned in the repository.
- Q: May the MVP limit PDFs to 2 MiB and documents to 100,000 Unicode code points?
  -> A: Yes; 2 MiB per PDF and 100,000 code points per document.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explore an Evidence-Linked Medical Report (Priority: P1)

As a demo user, I can select a built-in public example or supply permitted English text/a
text-based PDF and inspect the document, specialty, extracted items and short summary.

**Why this priority**: This is the primary end-to-end demonstration.

**Independent Test**: Use representative mocks for all three services and exercise input,
document view, specialty state, extracted entities, summary and source highlights.

**Acceptance Scenarios**:

1. **Given** a permitted example, **When** processing succeeds, **Then** I see canonical
   text, a supported specialty or uncertain/unsupported outcome, evidence-linked extracted
   items and an understandable English summary.
2. **Given** a repeated passage after an emoji, **When** I select an extracted item,
   **Then** highlighting identifies its exact canonical evidence occurrence.
3. **Given** a scanned or unsupported/oversized file, **When** I submit it, **Then** an
   English validation outcome explains the supported input and processing does not proceed.
4. **Given** mock mode, **When** results are shown, **Then** their mock origin is visible.

---

### User Story 2 - Ask Questions Without Losing Source Meaning (Priority: P1)

As a user, I can ask document questions, general medical-concept questions or questions
requiring both and inspect what supports each claim.

**Why this priority**: Mixed answers must not confuse patient evidence and general knowledge.

**Independent Test**: Exercise document/literature/mixed/unsupported fixtures with mocked
module responses and inspect source links, routing and partial answers.

**Acceptance Scenarios**:

1. **Given** support only in the document, **When** literature is insufficient,
   **Then** the document-supported answer remains available.
2. **Given** support in both sources, **When** a mixed answer is displayed, **Then**
   each claim retains its document/literature provenance.
3. **Given** no required evidence or an out-of-scope request, **When** I ask,
   **Then** the application clearly communicates the limit without inventing a diagnosis.
4. **Given** a non-English input, **When** it is identified as unsupported,
   **Then** I receive English guidance rather than an apparently compliant translated result.

---

### User Story 3 - Use an Isolated and Understandable Demo (Priority: P1)

As a user, I can understand processing states and privacy notices while my document is
unavailable to another session and untrusted text cannot control the application's behavior.

**Why this priority**: Isolation and clear states are prerequisites for permitted input.

**Independent Test**: Use two isolated mock sessions and the defined upload/injection/error
suite; inspect responses, rendered text, logs and visible notices.

**Acceptance Scenarios**:

1. **Given** two sessions, **When** one uses the other's document ID, **Then** access is
   denied and the other document is not disclosed.
2. **Given** instructions or markup embedded in source text, **When** it is processed/
   displayed, **Then** it cannot override source rules or execute untrusted markup.
3. **Given** a timeout, rate limit or provider outage, **When** a request fails,
   **Then** the application shows a readable English state with bounded recovery.
4. **Given** the landing/input flow, **When** I review its notices, **Then** I understand
   that this is a demo, not a doctor, and real personal medical reports must not be uploaded.

---

### User Story 4 - Run and Rehearse the Complete System (Priority: P2)

As a team member, I can start the mock foundation, replace one passing mock at a time with
real modules, and rehearse an approved deployment using documented checks.

**Why this priority**: Integration must progress without waiting for every real module.

**Independent Test**: Follow documented local startup with mock services, then connect one
agreed-record-compliant module while the others remain mocked.

**Acceptance Scenarios**:

1. **Given** one ready real module, **When** its integration checks pass, **Then** it can
   replace its mock through a small change without waiting for the other modules.
2. **Given** no paid-call/deployment approval, **When** routine checks execute,
   **Then** they remain key-free and do not activate paid infrastructure.
3. **Given** an approved hosting arrangement, **When** deployment is rehearsed,
   **Then** service readiness, persistence and authentication have actual evidence.

### Edge Cases

- Empty input, unsupported language, no extractable PDF text, unsupported/oversized uploads.
- A specialty mistake, uncertain/unsupported classification or no extracted entities.
- Digest mismatch, non-BMP characters, repeated passages or invalid source spans.
- Partial module failure, provider rate limit/outage or incomplete mixed evidence.
- A leaked/expired/unknown document ID or stale state/history from another document/session.
- Source prompt injection, unsafe markup, accidental document logging or oversized requests.
- Missing secrets, unapproved spending, missing persistence or unreachable service readiness.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Own the complete frontend and application integration, including all English
  navigation, input, document, specialty, entity, summary, chat and source interfaces.
- **FR-002**: Prioritize built-in public examples; additionally accept permitted English
  public/synthetic text and text-based PDFs. Limit each PDF to 2 MiB (2,097,152 bytes)
  and each canonical document to 100,000 Unicode code points. Reject oversized input
  with an English explanation; do not silently truncate it.
- **FR-003**: Validate type/size and unsupported input; explain scanned PDFs without
  introducing OCR, translation or unsupported processing.
- **FR-004**: Prepare canonical text once, recording document identity, digest and source
  metadata. Downstream consumers MUST not alter it.
- **FR-005**: Display classification as a document specialty with scores/version/limitations
  and uncertain/unsupported states; do not present it as a diagnosis.
- **FR-006**: Display diagnoses/symptoms/procedures with assertion, temporality, subject and
  exact passage highlighting, including non-BMP and repeated-passage cases.
- **FR-007**: Display short English summaries and source-linked claims; source existence
  alone MUST not be represented as semantic support.
- **FR-008**: Support document, literature, mixed and unsupported/no-source question routes.
  Preserve each claim's source kind and identity when combining supported portions.
- **FR-009**: Route document-grounded answering to D and literature-grounded answering to A.
  Do not implement RAG algorithms or document-generation business logic in integration.
- **FR-010**: Retain document-supported answers when literature is weak/unavailable;
  provide supported portions and explicit gaps rather than fabricated mixed answers.
- **FR-011**: Keep chat history/document state bounded and scoped to its session and selected
  document. Possession of another session's document ID MUST not grant access. Submitted
  documents MUST remain only in server memory, for at most 60 minutes from preparation,
  and MUST be deleted on expiry or restart. Built-in public examples may remain versioned.
  An expired or lost document MUST require re-submission rather than silently recovering
  its content from disk or shared caches.
- **FR-012**: Include explicit English loading, empty, validation, error, unsupported and
  insufficient-evidence states; do not silently present non-English generation as compliant.
- **FR-013**: Display demo, not-a-doctor and no-real-personal-medical-report notices, privacy
  information and source attribution. Mock results MUST be visibly labeled.
- **FR-014**: Coordinate canonical shared-record collection/freeze and validate mocks/real
  payloads against the same version. Proposals/consumers retain their own ownership.
- **FR-015**: Begin UI work with mocks; connect actual modules through separate small
  changes after their agreed-record checks pass.
- **FR-016**: Provide server-side secrets, redacted logs, configuration, caching, usage
  accounting, timeouts, bounded retries and explicit provider-limit/outage outcomes.
- **FR-017**: Spending controls MUST be configured from an approved cap; no amount or paid
  provider activation may be assumed. Routine checks remain key-free; live checks are opt-in.
- **FR-018**: Test source/retrieved-text injection, XSS, oversized inputs, unauthorized IDs,
  document-log leakage and abuse/rate limits. Passing the finite suite is not universal security.
- **FR-019**: Do not introduce arbitrary browsing. If approved URL fetching exists,
  restrict it to an allowlist with SSRF protection.
- **FR-020**: Provide local/cloud runbooks and service readiness, persistence and
  authentication decisions verified before deployment; publish real URLs only after deployment.
- **FR-021**: Maintain shared/root configuration, contributor guidance, scope/review checks,
  secret/dependency checks and agreed integration checks without repository-wide formatting
  of other members' files.
- **FR-022**: Review official hosting/runtime constraints and propose the smallest viable
  arrangement. Do not assume persistent serverless files or all services share one web host.
- **FR-023**: Seek approval for remaining session/input/history/usage limits,
  provider budget and hosting before dependent implementation or deployment.
- **FR-024**: Finish attribution, readable errors, English review and demo rehearsal before
  final delivery on 2026-11-24; optional features MUST not block the core flow.

### Key Entities *(include if feature involves data)*

- **Prepared document**: Canonical content, digest, identity, permitted source and session scope.
- **Session/history**: Controlled access and question context for the selected document.
- **Analysis view**: Specialty, extracted items, summary, evidence, versions and status.
- **Answer view**: Supported claims, document/literature provenance and explicit evidence gaps.
- **Operational configuration**: Approved limits, provider mode, spending and hosting choices.
- **Integration checkpoint**: Mock/real module versions, readiness and executed checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can complete example selection, report inspection and each of the
  four question-route outcomes using mocks without real service implementations or keys.
- **SC-002**: All defined structural/span fixtures highlight the exact canonical evidence;
  all visible/generated states in the English acceptance suite are English.
- **SC-003**: All defined cross-session access cases deny unauthorized documents, and the
  complete defined injection/upload/secrets/logging/isolation suite records actual results.
- **SC-004**: Every displayed claim's source kind and citation links survive integration;
  partial mixed support and document answers with weak literature remain inspectable.
- **SC-005**: Each of the three real modules can replace its mock independently after its
  checks pass; integration status records which outputs remain mocked.
- **SC-006**: Local and approved cloud runbooks contain actual runnable commands and
  deployment evidence, with live paid checks disabled by default.

## Assumptions

- No user accounts or real personal medical-report use is approved. Session isolation is
  required independently of any account system.
- Submitted-document retention is approved as memory-only with an absolute 60-minute maximum;
  loss on restart or earlier process termination is permitted and must be explained.
- Remaining limits/session behavior, provider activation, code license and hosting
  are [open decisions](../../docs/team/open-decisions.md), not implicit defaults.
- Complete real modules are not prerequisites for mock UI development.
- This is a draft specification; UI, contracts, startup scripts, CI and deployment are not
  implemented or approved for publication by writing it.
