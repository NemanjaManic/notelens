> **Historical context:** This historical P2 proposal is superseded by the accepted revision-3 canonical freeze in docs/decisions/contract-freeze.md. Live activation decisions remain gated; current consumers use contracts/v1 and the generated packages.

# P2 Contract Decision Proposal

**Prepared**: 2026-11-12. **Maintainer**: B. **Status**: proposal for affected-owner review.
**Basis**: P1 draft 1.0.0 at `e7bc839c0632c3db4fd3bcf7c38838c6da16070d` and the
[archived A/C/D responses](../team/contract-reviews/p1/README.md).
**Publication status**: local, uncommitted work on `member-b/task-f-003-p2-proposal`.

P2 means the second review proposal, not wire version 2.0.0. The canonical schema,
OpenAPI, fixtures, validators, and their proposed version remain unchanged. This document
does not implement or freeze anything, ratify the constitution, or complete F-003.
The delivery deadline remains **2026-11-24**.

## 1. Decision authority and review status

The user, acting as B, selected the six behavior positions in section 2 and approved
preparation of this package. Those selections are B's proposed position for team review;
they do not establish A/C/D acceptance of new fields, enums, or behavior.

Other recommendations below consolidate the responses. They remain recommendations,
not additional decisions silently attributed to B or the team. An owner accepting one
topic does not accept every other topic, a revised schema, spending, or deployment.

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| A's P1 response | Agent-assisted technical support and requested changes for A's interface. | Human/team approval of P2, working RAG endpoints, or acceptance on C/D's behalf. |
| C's P1 response | C's proposed document/classification/error/scaffold behavior and reported local audit. | Approval of the resulting P2 revisions or independent verification of the audit artifacts. |
| D's P1 response | Agent technical review and Milica's confirmation of four limited principles. | Milica's acceptance of every technical detail, shared schema changes, or other owners' decisions. |
| B's six selections | Proposed product behavior listed below. | Final field definitions, owner agreement, or a frozen version. |
| Existing F-008 record | 90 expected fixture outcomes and 29 tests passed against the local P1 draft. | Acceptance of P2, generic semantic support, actual HTTP behavior, or real module quality. |

The archive preserves dates and original statements. Any later review should identify
the exact proposal revision and, once produced, exact schema/fixture bytes. Do not create
`contracts/v1/freeze.json` or populate approval evidence from these proposals alone.

## 2. B's six selected positions

These selections were made in this session on 2026-11-12. All affected-owner responses
to P2 are **pending**. Candidate field names below are discussion aids, not valid P1 fields.

| ID | B's selected behavior | Contract impact to review | Affected owners |
| --- | --- | --- | --- |
| S-01 | Represent procedures explicitly as planned, ordered, performed, cancelled, or hypothetical instead of presenting every procedure as performed. | Propose a separate procedure-status field. D must confirm vocabulary, unknown/ambiguous cases, and interaction with assertion/temporality. | B/D; A for any concept-hint effects. |
| S-02 | Allow `unknown` assertion when the source cannot justify confirmed, suspected, or negated. | Add the enum value through the shared contract process; review UI language and downstream expectations. Do not invent confirmation to satisfy a schema. | B/D; shared consumers acknowledge the revised enum. |
| S-03 | Return one extraction item per mention. | Preserve each occurrence's evidence and context. Resolve an exact mention location separately from wider supporting evidence. Grouping for display must not collapse distinct underlying records. | B/D. |
| S-04 | Keep one analysis request, with separate extraction and summary states. | Preserve supported findings when summary generation fails. Define explicit partial/failed section outcomes instead of interpreting an empty item list as failure or medical absence. | B/D; D's evaluation consumers. |
| S-05 | Ask for clarification when a follow-up question is ambiguous. | Keep literature questions self-contained; do not add automatic question rewriting or unrestricted A history. Agree an explicit clarification outcome and detection/resolution boundary. | A/B/D. |
| S-06 | Include structured component/version and mock/live metadata in results. | Literature answers expose corpus/index/retriever provenance; generation identifies model/provider/configuration versions; combined answers preserve contribution origins. | A/B/D; C for classifier-version consistency. |

An explicit status does not make a planned procedure performed. An unknown assertion
does not mean a new diagnosis. One item per mention does not establish how many clinically
distinct conditions exist. Preserve these distinctions in the frontend and evaluation.

## 3. Complete issue register

Every item is pending affected-owner P2 agreement. The status column distinguishes B's
selected positions from recommended carry-forward behavior and still-open details.

| ID / P1 references | Proposed resolution | Status / reviewers | Contract and fixture impact |
| --- | --- | --- | --- |
| P2-01 / R-01 | Carry forward B's once-only canonical preparation, exact UTF-8 hash, opaque document identity, code-point evidence, and C/D verification without repair. A receives no document for corpus ingestion. | Recommendation; A/B/C/D. | Retain existing document/hash/non-BMP/repeated-span fixtures; keep access checks separate from hash possession. |
| P2-02 / D R-03 procedures | Apply S-01 with a separate procedure occurrence/status dimension; do not encode planned as performed or overload assertion. | B-selected behavior; B/D must settle representation. | Add planned/ordered/performed/cancelled/hypothetical/ambiguous examples and invalid combinations. |
| P2-03 / D R-03 missing assertion | Apply S-02; preserve unknown rather than forcing a label. | B-selected behavior; B/D and consumers. | Add unknown positives and negatives for falsely confirmed/suspected/negated references. |
| P2-04 / D R-03 repeated mentions and matching | Apply S-03. Recommend an exact mention span alongside the supporting evidence spans. | B-selected granularity; span and matching rules pending B/D. | Test both repeated occurrences, contradictory contexts, overlapping candidates, and mention/evidence distinction. |
| P2-05 / D R-03 empty/incomplete extraction | Apply S-04. Distinguish completed-empty, partial, failed, and extraction-success/summary-failure outcomes. | B-selected behavior; exact section states pending B/D. | Revise ExtractionResult/Summary representation and add cases for each outcome. |
| P2-06 / D summary and document-answer feedback | Every substantive displayed statement must correspond to supported claims; limitations remain identifiable. Empty/partial text and claims must be coherent. | Recommendation; B/D, with A for shared answer behavior. | Add unclaimed substantive text, stale document sources, false attribution, and explicit limitation fixtures/reviews. Structural checks cannot prove entailment. |
| P2-07 / R-02 | Adopt C's supported/uncertain/unsupported meanings, five computed scores for uncertain, and zero-or-five for unsupported according to whether classification ran. | Recommendation from C; B/C. | Retain labels; update score/cardinality/order rules and replace the P1 empty-score uncertain example as a real-service shape. |
| P2-08 / R-06 score/outcomes | Higher returned retrieval scores mean better ranking; explain metric/transformation and version-specific comparisons. Keep document support independent of retrieval outcomes. | Recommendation from A, supported in D's review; A/B/D. | Document score meaning without thresholds; check ordering/metadata and document-only support under weak/failed literature. |
| P2-09 / R-04 follow-ups | Apply S-05: request clarification rather than guess an ambiguous referent or silently rewrite. | B-selected behavior; triggering/representation pending A/B/D. | Clarification and self-contained-question fixtures; no automatic A history extension. |
| P2-10 / R-05 | Use a B-generated request ID propagated and echoed for successes and failures; B checks originating and active context. | Recommendation supported by A/D; A/B/C/D for shared HTTP convention. | Describe the header, its relationship to ErrorEnvelope.request_id, and missing/mismatched/stale handling; future HTTP tests. |
| P2-11 / R-07 and D generation versions | Apply S-06 with structured provenance and per-contribution mock/live origin. | B-selected metadata approach; exact records and overall mode pending A/B/D/C as applicable. | Extend affected result records and test missing versions, mixed origins, and no false live label. |
| P2-12 / R-07 composition and D answer routes | Preserve claim text, namespace colliding IDs and rewrite links together. Distinguish evidence route from execution origin. | Recommendation; A/B/D. | Test collisions, all evidence routes, supported partials, unavailable sources, and combined versions. |
| P2-13 / R-08 | Use the proposed error table below. Recommend non-2xx envelopes for operational failures, 200 for completed domain outcomes. | Recommendation; A/B/C/D. | Add 500, settle 400/422 and 502 codes, and reconcile/remove P1's successful retrieval-error channel only after agreement. |
| P2-14 / R-09 language/questions | B coordinates common input-language validation; confidence is not a detector. Reject whitespace-only questions and unsupported language explicitly in English. | Recommendation; A/B/C/D; method and limits remain open. | Input/question/output language and whitespace fixtures after the method is agreed; no silent translation. |
| P2-15 / R-10 scaffolds | Each service owner creates its own scaffold/dependencies/lock; B owns shared startup/configuration/contracts and integration checks. | Convergent proposal; A/B/C/D must record exact split. | Revise the foundation backlog under ownership review; do not depend on later consumer tasks that require that same scaffold. |
| P2-16 / D shared evaluation | Add subject-attribution reporting; define mention matching and its denominators separately from quote validity and semantic support. Preserve annotation and final-test dependencies. | Recommendation; D with B/A/C. | Evaluation design/fixtures belong to D; member-specific annotations stay separate; no invented results or thresholds. |
| P2-17 / R-09, R-11 activation | Keep operational limits, provider/account/budget/retention and hosting choices explicit at their dependent gates. Browser calls B; exposed services authenticate. | Deferred decisions; B with affected owners and user. | No configuration values or provider activation are created here; loopback mocks stay key-free and explicit. |

## 4. Extraction and answer details to confirm

### Procedures, assertion, and mention evidence

Candidate `procedure_status` vocabulary is `planned`, `ordered`, `performed`, `cancelled`,
`hypothetical`, plus an explicit unknown outcome if D considers it necessary. These are
proposed values, not a selected enum. D must define when each applies, how transitions
mentioned in a report are represented, whether it applies only to procedure items, and
how assertion and temporality interact. For example, an explicitly confirmed plan must
still display as planned rather than a confirmed performed procedure. The existing time
labels must not silently force future events into current/historical occurrence.

S-02 selects unknown assertion as a capability. Before changing the enum, agree the UI
wording and reference rules: missing context, contradictory evidence, and failed model
processing are different things. A processing failure is not an unknown assertion.

For S-03, recommend a required exact mention span using the existing start/end/quote
convention, separate from the wider evidence array. Keep `name` as a display label rather
than requiring it to equal a whole evidence sentence. D should confirm exact boundaries,
discontinuous mentions, overlap, evidence containment/context, and how one-to-one matching
handles multiple predictions/references. Different assertions, times, subjects, and
procedure statuses must not be collapsed because their display names match.

ICD remains optional and must be copied from the source with exact evidence. In addition
to checking the code string, D must review its association with the particular mention.
The current F-008 lexical code check does not establish that semantic association.

### Independent section outcomes within one request

S-04 does not add a separate summary endpoint or an extra user action. Recommend keeping
an extraction outcome and a summary outcome in the same structured result, each with
its own success/partial/failure information and safe warnings/error detail as applicable.
The exact state names, content nullability, and nested error shape require B/D agreement.

| Scenario | Proposed consumer-visible meaning |
| --- | --- |
| Completed extraction with zero supported items | Completed-empty, with no claim that the document contains no medical information. |
| Some validated findings survive incomplete processing | Partial extraction with supported items and an explicit limitation. |
| Findings succeed and summary generation fails | Keep findings and their evidence; show summary unavailability separately. |
| Summary processing completes but evidence is insufficient | A domain evidence outcome, not a provider failure; identify the gap. |
| No usable analysis can be produced because the request/service fails | Safe non-2xx ErrorEnvelope under the agreed mapping, not fake empty success or mock fallback. |

The error-channel decision must be consistent: a completed composite response may describe
a failed section when another supported section survives; a top-level operational failure
uses a non-2xx envelope. A's standalone completed-search/error convention is separate from
this composite D-result representation. D/B must settle the exact boundary before freeze.

For summaries and answers, recommend that substantive displayed statements are represented
in claims, and that limitations are displayed distinctly. Do not treat matching source IDs
and exact quotes as proof of support. Fixture expectations can test known synthetic cases;
arbitrary text-to-claim entailment requires separate review/evaluation. D-only supported
answers use document facts and document sources. Recommend `route: none` when no claims or
sources support an answer, while attempted-source context is preserved separately if
needed; A/B/D must agree the exact record instead of inferring it from absent sources.

## 5. Classification, retrieval, correlation, and composition

### Classification and retrieval scores

Recommend C's following state table without changing the five output labels:

| State | Category | Scores |
| --- | --- | --- |
| supported | Selected category under a development-selected acceptance policy. | All five, unique and in C's stated category order. |
| uncertain | null; completed classification did not satisfy that policy. | All five computed scores, retained for transparency. |
| unsupported | null; an agreed scope check identifies unsupported input. | Empty if classification was skipped; otherwise all five computed scores, with an explanation. |

Scores are finite. Probability scores remain within [0,1]; do not introduce a sum-to-one
test without an agreed tolerance. Decision scores may be signed and are not percentages.
Model/version/confidence explanations remain explicit. Low confidence is not proof of
unsupported input, a language detector, calibration, or clinical certainty. C owns model
selection, learned transformations, and development-only threshold selection.

For A, recommend higher-is-better returned scores, with metric/transformation and comparison
scope described in `score_note`. Scores from different retriever versions are not generally
comparable. No numeric threshold is proposed. C's category is only a soft hint; uncertain
classification must neither force a default category nor suppress A/D's supported output.

### Clarification and request association

S-05 keeps A's self-contained, stateless request boundary. When the referent of "What
causes it?" is ambiguous, ask the user to identify the topic rather than infer a condition.
No unrestricted history, automatic rewriting model, new diagnosis, or translation is
introduced. D's optional history field does not establish a history policy for A.
The owners must still agree how ambiguity is identified, where clarification is represented,
and how it differs from insufficient evidence and an operational error. No detection
algorithm or extra paid call is assumed by this document. B-owned conversation content
remains scoped to its session/document and expires with it; bounds remain open.

For R-05, propose `X-Request-ID` as the shared correlation header for owner review. B
generates an ID for each outgoing service call and associates it with the operation,
question, session, and selected document ID/hash when applicable. Services echo it on
successful and failed responses; ErrorEnvelope.request_id must agree with the correlated
ID. B rechecks the active context/expiry before accepting a response, including empty-source
answers and uncertain/unsupported classification results. The ID is not an access token.

Recommend treating missing/mismatched IDs as invalid upstream responses, and refusing
stale results without attaching them to a new document. A/B/C/D must confirm header
propagation, concurrent-call handling, safe failure behavior, and transport fixtures.
A's body does not need patient-document fields. Neither correlation nor a document hash
replaces server-side session authorization.

### Structured provenance and mixed origins

S-06 selects metadata in results rather than requiring manifest lookup to discover the
producing components. Recommend a structured per-contribution record that identifies:

- Service/component and actual mock/live origin.
- Answer/extractor and prompt versions as applicable.
- Model/provider and non-secret configuration version for generation; C's model version
  continues to identify its selected classification pipeline.
- A's corpus selection/preparation, index, and retriever versions for literature answers.

Exact field names, required/optional combinations, version identity rules, and no-result
configuration failures need owner agreement. Do not fabricate version identifiers for
an absent index/model. Never embed secret values, document bodies, credentials, or a full
sensitive prompt in provenance. Corpus snapshot date alone is not a preparation/index version.

Recommend per-component `mode` values remain mock/live, with an explicit overall mixed
origin indicator when both contributed. Whether this extends the top-level mode enum or
uses a separate summary field must be settled by A/B/D. It must not hide a mock contribution
under a live label. Evidence `route: mixed` and mixed execution origin are independent:
a fully mocked answer can combine document/literature evidence, and a document-only result
can still involve multiple execution components.

For composition, preserve supported claim text. Propose deterministic service-prefixed
IDs, rewriting both source definitions and claim references, and retaining contribution
versions/warnings. The precise namespace and combined-version format need A/B/D agreement.
Do not generate new medical conclusions in B. Keep document-supported content when
literature is insufficient/unavailable, and distinguish evidence gaps from outages.

## 6. Proposed HTTP and failure conventions

This table is a recommendation for all owners, not a new implemented mapping. The current
OpenAPI already lists 502. It does not list the proposed 500 response. Source reports
do not establish that any of these outcomes have been implemented by service endpoints.

| Condition | Proposed status / code | Responsible boundary |
| --- | --- | --- |
| Malformed JSON | 400 / validation_failure | Receiving HTTP service. |
| Invalid fields/version/digest, empty canonical text, invalid or whitespace-only question | 422 / validation_failure | Receiving validation boundary; preserve canonical text rather than repairing it. |
| Oversized document or PDF | 413 / validation_failure | B for PDF upload; receiving document consumer for the canonical code-point cap. |
| Unsupported upload format | 415 / unsupported_file | B's upload boundary; no OCR. |
| Explicitly rejected unsupported language | 422 / unsupported_language | Agreed common language-validation boundary; method and generated-output handling remain open. |
| Missing/invalid required service authentication | 401 / unauthorized | Exposed receiving service. |
| Unknown, expired, or other-session document | Identical safe 404 / document_unavailable | B; disclose no other-session content. |
| Completed classification, search, or answer, including uncertainty/insufficiency | 200 / domain result | Service truthfully reports the supported/uncertain/unsupported/evidence outcome. |
| Agreed rate limit reached | 429 / rate_limit | Actual limiting boundary; no numeric limit selected. |
| Malformed or mismatched upstream response | 502 / internal_error proposed | B rejects upstream data; preserve independent supported results. |
| Missing/incompatible model/index/configuration | 503 / configuration_required | Owning service; no invented readiness/version or silent mock fallback. |
| Provider unavailable / approved budget exhausted | 503 / provider_unavailable or budget_exceeded, as applicable | Owning service; use the actual cause. |
| Request deadline exceeded | 504 / timeout | Agree client/service ownership and cancellation behavior. |
| Unexpected internal exception | 500 / internal_error proposed | Failing boundary; safe English envelope without traces. |

Recommend non-2xx envelopes for A's operational retrieval failures and 200 for completed
sufficient/insufficient searches. A/B must agree how this replaces P1's `state: error`
result branch and update the schema, documentation, and existing fixtures consistently.
Do not simply add another ambiguous failure channel or silently remove a required outcome.

Validation/configuration failures are not automatically retried. Transient retryability,
cancellation, deadlines, retry counts, question/history limits, rate and concurrency
controls remain explicit decisions before dependent implementation/activation. Approved
document limits are not automatically question/history limits. Safe errors remain English
and omit submitted content, credentials, stack traces, and unsafe provider details.

## 7. Ownership, evaluation, and dependent work

### Owner-created foundation scaffolds

Recommend the responsibility split all three responses support as a proposal:

| Owner | Foundation contribution |
| --- | --- |
| A | RAG service scaffold, mock/health/readiness, local tests, Python dependencies/lock. |
| C | Classifier service scaffold, mock/health/readiness, local tests, Python dependencies/lock. |
| D | Extraction service scaffold, mock/health/readiness, local tests, Python dependencies/lock. |
| B | Web/root configuration, shared contracts/bindings, startup/shutdown, scope/CI and integration checks, foundation coordination. |

The affected owners must agree the exact change package/backlog split before execution.
B cannot grant itself service-path ownership. F-004 depends on F-003/F-009; service
scaffold contributions belong inside that foundation work, not behind A-010/C-009/D tasks
that themselves require F-004. F-011 coordinates the service health/failure contributions.
Later consumer tasks test the frozen records in the available scaffolds. Do not bypass
dependencies or mark business algorithms complete because a mock responds.

Explicit key-free mocks remain local to loopback. Real mode without a usable model/index
or required configuration fails safely rather than reporting readiness or substituting
mock results. D owns its separate evaluation manifests/locks; B owns root shared locks.
After agreement, B updates B-owned foundation tasks; owners update their own tasks/paths.

### Evaluation and annotation dependencies

Recommend a visible subject-attribution measure alongside entity, assertion, and time
measures. D must propose the matching population, denominator, handling of unknown labels,
false positives/negatives, exact/relaxed matching, overlap, and one-to-one assignment.
Do not choose metric formulas or thresholds just to make results pass. Distinguish
structure, exact quote/offset validity, and semantic support in evaluation reporting.

The dependency chain remains:

- D-001 annotation/evidence guidance and interface proposals can be prepared now; D's
  review response alone does not complete that guide or its review.
- C-009 requires F-003/F-004. C-002 requires C-001, C-009, and F-014 before frozen
  group-disjoint manifests. C-003 initial classifier training follows C-002, without
  waiting for D's annotation assignments.
- D-002 selection requires D-001 and C-002; D-003 assignments follow selection.
  Ten primary documents per member and at least ten independent second reviews across
  the team are targets, not current assignments or completed work.
- C's pre-model-selection annotations/reviews must use development material. Final
  references must not guide model/prompt/threshold selection. D as both developer and
  reference coordinator needs practical separation; unavoidable exposure is a limitation.
- D adjudicates separate submissions without editing members' source files. D-013 follows
  the required submissions; human review is not clinical validation without expert review.
- Approximately 80 QA cases, 40 generated-answer reviews, and at least 20 entity-evidence
  reviews are separate targets. D's evaluator need not wait for all real A/C modules once
  its own foundation prerequisites are satisfied. Evaluation QA stays out of A's index.

A reports 401 locally extracted topics and 19 XML-extraction tests. C reports 4,999 source
rows, 1,338 target rows, nine empty target rows removed, 1,329 remaining records, and 46
preliminary conflicting groups/92 rows, with eight audit tests and regeneration checks.
These are attributed reports, not independently rerun results. Neither the counts nor
the reviews establish frozen splits, ready retrieval/classification endpoints, or D's
assignments. Underlying audit/dependency/annotation artifacts were not supplied here.

The [foundation](../../specs/000-foundation/tasks.md), [A](../../specs/001-rag/tasks.md),
[C](../../specs/003-classification/tasks.md), and [D](../../specs/004-extraction-evaluation/tasks.md)
backlogs retain their gates. This proposal edits none of them. The F-014 publication gate
still refers to a later reviewed runnable foundation, not the documentation commit.

## 8. Decisions deferred to their dependent gates

The [open-decision register](../team/open-decisions.md) remains unchanged. Preserve the
approved 2,097,152-byte PDF limit, 100,000-code-point document limit, and maximum absolute
60-minute server-memory lifetime. Services process forwarded documents transiently;
that maximum is not permission for separate service stores, logs, training data, shared
caches, or evaluation artifacts. B clears related results/history on expiry/restart and
rechecks in-flight outcomes. Provider retention needs separate review.

Before dependent input/chat implementation, agree the common language-check method and
its limitations, non-English question/output behavior, clarification representation, and
applicable question/history/session controls. `language: en` is not proof of English;
classifier uncertainty is not a language detector. No silent translation is approved.

Before real integration/provider activation, approve actual operational controls,
accounts/providers/models, retention/data-use terms, spending cap, usage enforcement,
rate/concurrency/deadline/retry/cancellation policies. Before deployment, approve the host,
TLS, network exposure, service-token provisioning, public-corpus persistence, and rehearsal.
Server-to-server bearer authentication is a proposed boundary, not verified enforcement;
the browser calls B, and secrets stay server-side. Do not infer hosting capacity, paid
services, multi-instance memory behavior, or serverless persistence from the local plan.

Substantive quality thresholds follow actual development measurements and team decisions;
the existing target is 2026-11-14, not a fabricated result or a promise of capacity. Final
configuration is frozen before locked final measurement. Deadline, ownership, scope,
privacy, provider costs, and public publication are not changed by accepting this document.

## 9. Review requests and path to freeze

Reviewers should respond by P2 issue ID with acceptance, requested change, or unresolved
objection; give the actual reviewer/date and identify the reviewed P2 revision. Do not
copy a P1 `agreed` status into P2 without reviewing the new behavior.

| Reviewer | Requested review focus | Current P2 response |
| --- | --- | --- |
| A | P2-01, 08-14, 15, 17: stateless requests, clarification, correlation, score/provenance, mode/composition, failure channel, and scaffold contribution. | Pending |
| C | P2-01, 07, 10-11, 13-17: score/state policy, header/error behavior, common language boundary, scaffold, and data/annotation dependencies. | Pending |
| D | P2-01 through 06 and 08-17: procedure/assertion/mentions, section outcomes, claim/text consistency, clarification/provenance/composition, errors, scaffolds, and evaluation. | Pending |
| B | S-01 through S-06 are selected positions; the remaining recommendations and technical details require B's explicit review alongside affected owners. | Six positions selected; other P2 details pending |

The next sequence is:

1. Obtain responses on this proposal, resolve the remaining field/state/header/matching
   questions, and record actual agreement or objections per issue.
2. Prepare a separately approved canonical schema/OpenAPI/documentation/fixture change
   package. Choose the reviewed version deliberately; preserve the original source prompt
   and update governing/consumer requirements through their owners where necessary.
3. Rerun structural, exact-text, relationship, and fixture checks against the revised
   proposal. Planned P2 fixtures in this document do not already exist or pass.
4. Ask owners to review the actual resulting schema/fixtures, not just this behavioral
   proposal. Record the exact reviewed version, file digests, dates, approvals and exceptions.
5. Create the later freeze decision/record only from actual agreement and successful checks.
   F-003 stays open until its guard passes on that recorded version. F-009 bindings,
   coordinated scaffolds, and the reviewed runnable checkpoint follow their real gates.

No messages were sent by the agent. B can share the prepared package manually; this local
package does not authorize commits, merges, pushes, provider calls, or deployment.

## 10. Package verification and limitations

This package uses ordinary approved documentation preparation, not a Spec Kit generation,
clarification, or implementation workflow. It creates this proposal, a review-source index,
and three byte-identical source copies. It does not change schemas, fixtures, validators,
test files, task markers, or the earlier interface-review guide. Existing uncommitted
F-008/guide work is preserved; creating a new branch does not isolate uncommitted files.

Verification checks source/archive byte equality and hashes, proposal/index links and
anchors, coverage of R-01 through R-11 plus D's additional extraction/evaluation requests,
and the changed-file scope. Historical relative links inside source copies intentionally
retain author context and are explained in the archive index. The underlying linked
teammate artifacts are not treated as supplied or read.

No application/module/HTTP/benchmark/live tests were run for this documentation package.
The prior F-008 counts are historical P1 verification, not P2 acceptance or team sign-off.

Executed standard-library Python checks confirmed byte equality for all three source
copies and their indexed SHA256 values, all 15 authored-document local links, all six
selected positions and 17 issue IDs, and coverage of R-01 through R-11. Authored files
passed UTF-8/LF, final-newline, trailing-whitespace, and `git diff --no-index --check`
checks. Archived originals were checked for byte identity rather than reformatted.
A pre-package hash snapshot confirmed all 131 existing project files unchanged, including
the schemas, F-008 fixtures/tooling, task markers, source prompt, and review guide.
Git inspection confirmed exactly five new documentation files, no staged changes,
unchanged existing refs, and no real freeze record. These are documentation/integrity
checks, not agreement on P2 or new runtime verification.
