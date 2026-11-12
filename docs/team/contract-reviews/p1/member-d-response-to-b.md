# Member D response to B's interface review

- **Prepared:** 2026-11-11
- **Workstream:** D — extraction, document-grounded generation and shared evaluation
- **Reviewer:** Coding agent assisting Milica (D); Milica confirmed the four principles
  listed below on 2026-11-11; detailed technical and team review remain pending
- **Audience:** B and the integration/CLI agent, with A and C for shared decisions
**Proposal P1:** Draft `contracts/v1/schema.json`, `contracts/v1/openapi.json` and
`contracts/v1/README.md` at commit `e7bc839c0632c3db4fd3bcf7c38838c6da16070d`,
using B's interface-review guide dated 2026-11-11. A's RAG response and C's response
and dependency report, supplied separately, were also considered.

The reviewer, date and proposal above apply to **every status below**. `agreed` means
the agent reviewer supports that specific behavior in P1; Milica's confirmation is
limited to the four principles recorded below, and does not represent B's or the
team's approval. `change requested` identifies a proposed change requiring
owner discussion. `still unresolved` identifies a decision that cannot be closed from
the current materials. No contract freeze, implementation or runtime result is implied.

## Principles confirmed by Milica

On 2026-11-11, Milica confirmed these four principles after reviewing the summary:

1. D uses the same prepared canonical text received from integration and provides
   exact source text as evidence.
2. Negated, suspected and family-history mentions must not be presented as confirmed
   diagnoses of the patient.
3. Ambiguous cases require discussion and an agreed rule rather than invented meaning.
4. Owner-created service scaffolds coordinated by B are supported as a **proposal**
   for the team; B and the affected owners still need to agree the responsibility split.

This confirmation does not adopt specific schema changes, HTTP mappings, matching
rules, budgets or every technical detail in this review. Those remain proposals until
the relevant owners review and record decisions.

## Overall assessment

The current fields are a workable starting point for D's stateless extraction and
document-question endpoints. They cover the prepared document, extracted items, cited
summary and answer, document identity on extraction results, and version labels. They
do **not yet fully specify** how to represent planned procedures, unknown assertion,
mention-level evaluation, incomplete extraction, answer correlation and some shared
failure/combination behavior. These need review before B freezes the shared contract.

No extra patient document is needed by A; no extraction output or inferred ICD is
required by C. B owns session access and document preparation. D owns extraction,
document-grounded summaries and answers, and evaluation coordination. This response
does not propose editing B's canonical files directly.

## R-01 — Prepared document, requests and identity

**Status: agreed.** D can consume P1's `ExtractionRequest` (`schema_version`,
`document`) and `DocumentQuestionRequest` (the same fields plus `question` and
optional `history`) as the basis for independent service calls.

- B prepares canonical text once using the proposed `nfc-lf-v1` rules. D does not
  trim, normalize, replace or truncate that text. Internal prompt construction or
  derived processing must not change the canonical source used for evidence.
- D verifies the digest of the exact canonical UTF-8 bytes and rejects a mismatched
  document rather than repairing it. `doc_id` and `text_sha256` are echoed in
  `ExtractionResult`. B compares them with the originating document and checks
  session ownership and expiry; neither value grants access by itself.
- Evidence uses zero-based, half-open Unicode code-point intervals `[start, end)`;
  the quote must equal the exact canonical text slice. B converts to UTF-16 indices
  when highlighting in the browser. Repeated passages must retain the intended
  occurrence instead of always matching the first instance.
- A valid `language: en` declaration is not proof of language compliance. The common
  input-language decision remains open under R-09.

Please include the existing synthetic emoji/repeated-passage example, a wrong digest,
an invalid slice and a UTF-16-as-code-point error in F-008's shared fixtures. This
agreement is a design assessment; no D HTTP or cross-language test has run.

## R-03 — Extraction items, evidence and summary

### Entity categories and context

**Status: agreed.** The proposed `diagnosis`, `symptom` and `procedure` types and
separate assertion, temporality and subject fields preserve essential distinctions.
A confirmed historical condition remains both `confirmed` and `historical`; a family
member's condition must not become a patient condition. Every returned item requires
at least one source evidence span. IDs must be unique within the result, and source
quotes must support the item's meaning, including negation, time and subject.

Optional ICD may only reproduce a code explicitly present in the document with exact
evidence; it must not be inferred from a diagnosis. Existence of the code text alone
does not establish that it belongs to the extracted item: the association also needs
review. ICD remains nonblocking for the MVP.

### Planned, ordered and hypothetical procedures

**Status: change requested.** P1 provides `current`, `historical`, and `unknown`
temporality, but does not define how to represent “Colonoscopy is planned for next
week” without suggesting that it occurred. Please agree on the meaning of planned,
ordered, performed, cancelled and hypothetical procedures before freeze. One option
is a separate procedure/event status; another is a reviewed rule for cases the current
schema cannot express. The exact fields and values are **not selected here**.

Until an agreed representation exists, D must not portray a planned procedure as
performed. Add cases for planned, completed, cancelled and ambiguous procedures to
the shared review/fixture backlog.

### Missing assertion context

**Status: still unresolved.** `assertion` is required and P1 permits only
`confirmed`, `suspected` and `negated`. Please decide how to handle a mention for
which the source does not justify any of these labels. An explicit `unknown` value is
one option; a documented omission/limitation rule is another. D should not invent
confirmation merely to satisfy an enum. This requires B/D agreement and fixtures.

### Repeated mentions and matching

**Status: change requested.** Define whether an `ExtractionItem` is an individual
mention or a grouped concept and when multiple spans can be grouped. P1 allows an
array of evidence spans, but does not settle how different assertions, time or
subjects interact with grouping. Contradictory mentions must remain distinguishable;
the synthetic first and second denials in B's guide must not be silently collapsed
into the wrong occurrence.

For evaluation, distinguish the **entity mention span** from a potentially wider
**evidence span** supporting its context. B's example uses `Chest pain` as the name
and the whole sentence `Chest pain is suspected.` as evidence. Please decide whether
P1 needs a separate exact mention span or whether the agreed evaluation representation
can provide it without changing the API. Define exact and relaxed matching, overlap,
repeated occurrences and one-to-one matching before calculating entity scores.
Do not treat a valid evidence quote as proof of semantic support.

### Empty and incomplete extraction

**Status: change requested.** `items: []` is valid in P1, but the extraction result
has no explicit overall extraction state. An empty completed result must not be
confused with a failure, an incomplete extraction or proof that the document has no
medical content. Please agree on the consumer-visible behavior for:

1. completed extraction with no supported items;
2. partial extraction where some supported items can be returned;
3. extraction that could not complete due to validation or provider failure; and
4. extraction success with an insufficient or failed summary.

Consider an extraction state and warnings, or use a non-2xx error for defined failed
cases. P1 currently requires `summary`; if independent extraction success and summary
failure are to be returned together, the representation needs an explicit decision.
Do not silently add fields or assume this proposal has been adopted.

### Summary text, claims and evidence

**Status: change requested.** P1's `Summary` has English text, claims, document
sources, evidence state and warnings. Its structural rules alone do not ensure that
every substantive displayed statement corresponds to supported claims, or that a
claim's source ID resolves to the correct document and digest.

Proposed behavior: all substantive summary statements are represented by claims
linked to supporting selected-document evidence. A limitation or evidence-gap notice
must be identifiable as such. For partial/insufficient outcomes, preserve supported
material and state the limitation without introducing an unsupported patient fact.
B/D should agree the representation and add positive and negative fixtures.

## Document answers — `DocumentQuestionRequest` and `AnswerResult`

### Source support and insufficient evidence

**Status: agreed.** D can use the prepared document and an English question to return
an `AnswerResult` with claims, document sources, evidence state, warnings, mode and
version labels. A document-fact claim must have support in the selected document;
general literature cannot establish a patient-specific fact. An absent fact should
yield an explicit evidence limitation instead of a fabricated answer.

An insufficient-evidence domain outcome is distinct from a timeout, unavailable
provider, malformed response or other operational failure. A valid quote is necessary
for source traceability but is not by itself a semantic-support judgment.

### Answer text and route semantics

**Status: change requested.** Agree how `AnswerResult.text`, `claims`, `sources`,
`warnings`, `route` and `evidence_state` correspond, including empty and partial
responses. P1 applies some structural conditions but cannot check semantic entailment
or the consistency of displayed text with every claim.

For a D-only supported response, the proposal is `route: document` with document
sources and document-fact claims. For an unanswered question with no claims or
sources, confirm whether D returns `route: none` or another documented route that
preserves attempted source context. B/A/D should use the same rule. B's mixed result
must retain independently supported content and explicit gaps.

### Generation versions

**Status: still unresolved.** P1 has `extractor_version` and `prompt_version` on
extraction results and `answer_version` and `prompt_version` on answers. Evaluation
needs to identify the model/provider and relevant configuration used in a run. Please
agree whether existing version values resolve through an immutable, versioned manifest
or whether additional structured fields are needed. A's proposal for retriever, index
and corpus provenance in literature answers should be resolved alongside this issue.
No provider, model, budget or numeric quality threshold is selected by this review.

## R-04 — Follow-up questions and history

**Status: still unresolved.** P1 gives D optional `history`; A's request has no
equivalent field. I support discussing A's stateless proposal: B may provide a
self-contained literature question or ask for clarification when a follow-up such as
“What causes it?” is ambiguous. It must not assume that a concept list always resolves
the question, and B must not generate new unsupported medical conclusions while
preparing or combining service calls.

B/A/D need to agree what D receives, how mixed follow-ups are routed, which history
is necessary, how it is bounded and how clarification is represented. History must
remain scoped to the authorized session and expire with document-bound content.
Numeric limits and the method for producing a self-contained question remain open.

## R-05 — Request correlation and stale answers

**Status: change requested.** `ExtractionResult` echoes document identity, but
`AnswerResult` has no top-level document ID/hash. In particular, an insufficient
answer can have no source from which to recover document identity. A response must
not be displayed against a different or expired document.

I support A's proposal for a server-generated request ID propagated and echoed in an
agreed HTTP header for successful and failed calls. P1's `ErrorEnvelope` already
contains `request_id`; consistent success/header behavior is not specified there.
B should bind the correlation to the originating session, question and selected
document ID/hash and check the active context again before accepting/displaying an
in-flight answer. B/A/D must agree header names, propagation and missing/mismatched
ID handling. This does not require putting patient-document fields in A's body.

## R-06 — Retrieval outcomes and independent document support

**Status: agreed.** D's supported document content should remain usable when A's
retrieval is insufficient or its service fails. Insufficient evidence is a domain
outcome, distinct from operational failure. A retrieval score is not clinical
confidence; P1 does not establish a substantive numeric threshold.

A proposes documenting that higher returned scores rank better, with meaning and
comparability explained by retriever/version. D supports making the score semantics
explicit for evaluation; the final convention is for A/B to agree. C's specialty is
an optional soft hint and must not force a default category, hard-filter literature
or suppress D's supported output.

## R-07 — Mixed composition, provenance and mode

**Status: change requested.** B's integration should preserve supported claim text,
namespace colliding claim/source identifiers and rewrite links consistently. It
should distinguish document facts from general literature, preserve missing-source
warnings and avoid inventing medical conclusions while combining responses.

P1's single `mode` cannot by itself describe a result containing both mock and live
components. B/A/D should agree how each contribution's mode and relevant answer,
prompt, retriever, index and corpus versions are retained, and how overall mode is
displayed. A combined result must not conceal mock contributions under a `live` label.
Whether this needs extra fields or an immutable associated record is unresolved.

## R-08 — Proposed HTTP and error behavior

**Status: change requested.** The following is a proposal for B and service owners,
not an implemented or agreed mapping. P1 lists 400 and 422 without distinguishing
their responsibilities; its OpenAPI already lists 502. Unexpected 500 is not listed
for D's operations and needs review.

| Condition | Proposed outcome | Boundary / clarification |
| --- | --- | --- |
| Malformed JSON | `400 / validation_failure` | D's HTTP boundary returns a safe envelope. |
| Invalid schema/version, invalid digest, empty canonical text or invalid question | `422 / validation_failure` | D validates the received request. Agree treatment of whitespace-only questions. |
| Canonical text exceeds the approved limit | `413 / validation_failure` | Reject; do not truncate. The PDF byte limit is checked by B at upload. |
| Missing or invalid service authentication where required | `401 / unauthorized` | D enforces the agreed exposed-service boundary. |
| Valid question with insufficient document evidence | `200 / AnswerResult` | Domain outcome with explicit limitation; no invented facts. |
| Provider rate limit | `429 / rate_limit` | Retryability and bounded behavior depend on the agreed policy. |
| Provider unavailable or required live configuration missing | `503 / provider_unavailable` or `configuration_required` | No silent mock fallback; use the actual cause. |
| Request deadline exceeded | `504 / timeout` | Agree which boundary creates the envelope and how cancellation works. |
| Malformed upstream result received by B | `502 / internal_error` proposed | B rejects the invalid service response; the canonical code needs agreement. |
| Unexpected internal service failure | `500 / internal_error` proposed | Add/document in OpenAPI if accepted; do not expose stack traces. |

The OpenAPI's listed codes do not prove these combinations are implemented or agreed.
The team should also reconcile A's retrieval `state: error` with non-2xx envelopes;
one proposed rule is non-2xx for operational failures and 200 for completed searches
with sufficient/insufficient evidence. D is not deciding A's interface unilaterally.

All error messages must be safe and English, with no submitted document body, secret,
stack trace or unsafe provider detail. Invalid input/configuration must not be retried
automatically. No retry count, timeout or rate limit is chosen here. B owns the safe
404 for missing, expired or other-session documents and the upload/PDF boundary.

## R-09 — Language, limits and privacy

**Status: still unresolved.** I support C's proposal that B coordinate a common
document-language check before dispatching the same prepared document to C and D.
The method and limitations require agreement; classifier confidence is not a language
detector. Also agree behavior for non-English questions and generated outputs, including
safe English error/limitation messages and no silent translation.

The existing approved limits are at most 2,097,152 bytes per PDF, 100,000 canonical
Unicode code points per document and 60 minutes of application server memory retention
from preparation. The PDF limit is B's upload concern; D receives prepared text. The
document cap is not automatically a question/history cap. Request, history, timeout,
retry, rate and concurrency controls are unresolved.

D processes submitted text transiently and must not place it in logs, disk caches,
training data or evaluation datasets. B removes document-bound content and history on
expiry or restart. Provider-side retention/data-use terms need separate review before
live activation; an application-side memory policy does not guarantee provider behavior.

## R-10 — Foundation scaffold ownership and CLI integration

**Status: change requested.** I support A/C's owner-created scaffold proposal: D
creates extraction-service files, local dependencies/lockfile, mock behavior, health
and local checks within `services/extraction/**`; A and C do the equivalent in their
paths. B coordinates F-004/F-011, shared contracts/bindings, root configuration,
startup and integration checks. B should record this arrangement with affected owners.

The D scaffold contribution is foundation work, not completed extraction business
logic. It must not depend on a later D task that itself requires F-004. The team should
agree the exact change to the foundation backlog rather than silently bypassing gates.
The D-owned evaluation package and its local lockfiles are separate from B's root
configuration; D does not edit the shared root lockfile.

Future mock startup must be key-free and report `mode: mock` truthfully. A real-mode
service without required configuration must fail safely instead of silently switching
to mock output. Actual startup commands, local ports, dependency compatibility,
health checks and process shutdown need verification after the scaffold exists;
this response does not invent commands or claim those checks passed.

## R-11 — Authentication and deployment

**Status: still unresolved.** The proposed server-to-server bearer boundary is a
reasonable starting point. The browser communicates with B; exposed internal services
must enforce the agreed authentication, with tokens kept server-side and out of logs.
Key-free mocks must remain loopback-only. Exact token provisioning, host, network
exposure, TLS, provider terms, budgets and deployment approval remain open.

## Shared evaluation and C's handoff

**Status: change requested.** Add an explicit subject-attribution measure alongside
entity precision/recall/F1, assertion and temporality. For example, a family member's
condition incorrectly attributed to the patient must be visible in the report. Define
the denominator and matching policy before measurement. Separate structural validity,
exact quote/offset validity and semantic support; a passing schema does not prove
correctness. Report actual counts, versions and limitations without fabricated results.

C reports C-001 as completed locally, with preliminary conflicting duplicate groups,
but its split manifests are not yet frozen. Those counts and tests are C's reported
evidence, not independently rerun by D. D cannot finalize D-002 selection or D-003
assignments until the required C-002 manifests exist. C's initial classifier training
does not depend on D's annotations; C-010 and its later final-task gate have their own
dependencies. Do not use preliminary inspection data as a frozen benchmark.

D-001 is the next ready D deliverable: an English annotation/evidence guide and
interface proposals covering entity boundaries, context, repeated mentions, exact
spans, review and adjudication. It is **not completed by this review**. After C's
group-disjoint manifests and the other stated prerequisites, D plans assignments of
ten primary documents per member and at least ten independent second reviews across
the team; these are targets, not completed assignments. C's pre-model-selection
assignments must be development-only, without final-reference feedback for model
selection. Agree a practical separation for D as both extractor developer and final
reference coordinator; record any unavoidable exposure as an evaluation limitation.

The planned approximately 80 QA cases, approximately 40 generated-answer reviews and
at least 20 entity-evidence reviews are separate activities and not existing results.
Human-reviewed references are not clinically validated without expert confirmation.
The team sets substantive thresholds after actual development measurements; final
examples must not be used to tune prompts or thresholds.

## Work dependencies and handoffs

The table reflects the committed task backlogs and C's supplied status report. The
local checkout is the initial documentation base; unpublished teammate work may be
newer and must be verified through their actual artifacts and checks. These are
dependency statements, not evidence that the named tasks have been completed.

| Work | Depends on | Handoff or consequence |
| --- | --- | --- |
| D-001 annotation/evidence guidance and interface proposals | No other task prerequisite. | D can prepare a draft now and send shared interface proposals to B. A separate local guide exists for later review; this interface-review contribution alone does not complete D-001. |
| F-008 fixtures and F-003 contract freeze | B coordinates fixtures and collects A/C/D review; F-003 depends on F-008. | B records actual owner agreement and checks; this document supplies D's proposals, not team acceptance. |
| F-009 bindings and F-004 shared mock scaffold | F-009 depends on F-003; F-004 depends on F-003 and F-009. | B coordinates the shared foundation. Owner-created service scaffolds remain a proposed responsibility split until agreed. |
| D-010 offline evaluation package | F-003 and F-004. | D prepares its own evaluation environment and mock adapters after those prerequisites. It does not wait for complete real A/C modules. |
| D-004 extraction implementation | D-001, F-003, F-004 and published foundation F-014. | D implements extraction after the listed gates; live provider use also needs its separate approved configuration and budget. |
| D-005 document answers and summaries | D-004. | D supplies supported document results and HTTP integration evidence to B; A retains literature generation. |
| C-009 and C-002 classification setup and splits | C-009 requires F-003 and F-004. C-002 requires C-001, C-009 and F-014. | C reports C-001 done locally, but that evidence was not independently rerun here. C publishes stable group-disjoint manifests through C-002. |
| D-002 selection and D-003 assignments | D-002 requires D-001 and C-002; D-003 requires D-002. | D selects feasible documents and assigns primary work and independent reviews. C's pre-selection primary and review assignments must use development material only. |
| D-013 adjudication | D-003, D's submissions and the listed A/B/C annotation tasks. | D preserves the independent submissions and records decisions separately. No human-reviewed reference is implied before this work. |
| D-006 evaluation runner and D-007 QA | D-006 requires D-010 and F-014; D-007 requires D-006 and A-002's corpus preparation. | A provides the actual corpus/passage context; D reviews QA relevance against it without putting evaluation questions into the index. |
| Development and final reports | D's evaluator, references and relevant A/C outputs and reviews; final reporting has the additional D-009 gates in the backlog. | Set substantive thresholds only after real development measurements and team review. Freeze configuration before final evaluation. |

C's D-003 annotation dependency does **not** block C-003 initial model training;
C-003 follows C-002. C's personal annotations are required for C-010 and the later
C-008 final-task gate. See the [D backlog](../../specs/004-extraction-evaluation/tasks.md),
[C backlog](../../specs/003-classification/tasks.md) and
[foundation backlog](../../specs/000-foundation/tasks.md) for complete task dependencies.

## Requested response from B and the integration agent

1. Record a decision for each issue above against P1, including reviewer, date,
   accepted behavior or remaining objection, and the reviewed proposal revision.
   Collect Milica's actual review and A/C input where applicable; do not infer consent.
2. Prioritize R-03 extraction representation, R-05 correlation, R-07 composition and
   R-08 errors for the contract freeze. Add representative positive/negative fixtures
   and semantic checks; resolve exact shared-field changes through B.
3. Record owner-created service scaffold responsibilities and the foundation/CLI
   dependency order, including D's contribution and the actual future checks.
4. Confirm what D must supply for F-008 and the agreed answer association/mode/version
   behavior. Coordinate D-001 with C's split handoff without treating assignments as
   ready before the manifest exists.
5. Keep live provider configuration, budgets, hosting and deployment as separate
   decisions; do not treat this technical review as authorization for those actions.

## Evidence and limitations

The reviewer read the supplied B guide, A response, C response and C dependency report,
and compared the D-related records with the local P1 schema, OpenAPI and contract README.
The local checkout inspected is the initial documentation commit identified above;
other members' described work is in their supplied reports and was not independently
executed or verified here. JSON examples in those documents are illustrations.

No D service, live provider, test suite, CLI scaffold, generated binding, benchmark,
annotation guide, team decision or contract freeze was created or verified by this
response. No shared schema, other owner's files or task checkboxes were changed.
