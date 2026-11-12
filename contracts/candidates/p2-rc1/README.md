# P2 RC1: Executable Contract Review Candidate

**Prepared:** 2026-11-12. **Owner:** B. **Candidate ID:** `p2-rc1`.
**Proposed wire version:** `1.0.0`. **Status:** awaiting actual owner review.

Start here for the final artifact review. The generated `schema.json`, `openapi.json`,
fixtures, and simulated correlation cases are concrete proposals. They are **not** a
second accepted contract: [P1](../../v1/README.md) remains unchanged and canonical.
No application/service should switch to this candidate until it is approved and promoted.
F-003, F-009, F-004 and F-014 remain open. No bindings, mock services, providers or
deployment are delivered by this package.

## Reproduce and check on Windows

From the repository root, using the already installed B-owned F-008 environment:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$contractUv = Join-Path (Get-Location).Path '.cache/tooling/Scripts/uv.exe'
& $contractUv run --locked --offline --directory scripts/project python build_candidate.py --check
& $contractUv run --locked --offline --directory scripts/project python check_candidate.py
& $contractUv run --locked --offline --directory scripts/project python -m unittest discover -s tests -v
```

Stop if any command fails. For a fresh environment follow [B's setup guide](../../../scripts/project/README.md).
No new dependencies, real keys, model artifacts or A's corpus/index are required.
The cross-language offset test also requires a local Node.js executable on PATH;
the checker itself only needs the locked Python environment.
The builder deterministically derives this candidate from P1 and the scoped changes in
`build_candidate.py`; it is the source for generated candidate assets. To regenerate
after an intentional revision, omit `--check`, then recheck and obtain review of the
new manifest hash. Do not edit generated JSON to make a test pass.

`candidate.json` fingerprints P1 inputs, generated assets, review documentation, checker,
builder, tests, and the two supplied C responses. Give reviewers the candidate ID and
SHA256 of that manifest. Approval of an older hash is not approval of revised bytes.
`check_candidate.py --require-freeze` must fail with `CANDIDATE_NOT_CANONICAL` even when
all checks pass. It cannot manufacture an F-003 freeze or owner consent.

## Review on GitHub

The review branch is `member-b/task-p2-contract-candidate` in the shared NoteLens
repository. Publish the candidate and its F-008 validation prerequisites there after
explicit commit/push authorization, then share the branch link and exact commit SHA.
Reviewers start with this README, inspect the schema/API and fixture changes, and use
a separate working copy if they want to execute the checks. Fresh setup needs package-
registry access; subsequent checks run offline. No ZIP transfer is required.

Record the reviewed commit SHA, candidate ID and printed manifest hash in each response.
Publishing a review branch does not approve the candidate or promote it over P1. Human
owner review, canonical promotion and any merge remain separate actions.

## Verified checkpoint: 2026-11-12

The three commands above were executed in PowerShell on B's Windows working copy
with Python 3.13.7, uv 0.13.7 and Node.js v24.22.1:

- Deterministic regeneration check: PASS.
- Candidate Draft 2020-12/OpenAPI 3.1.1 and payload checks: 139/139 expected outcomes,
  including 63 valid and 76 deliberately invalid cases.
- Simulated header/error correlation: 10/10 expected outcomes. No HTTP server called.
- Unittest discovery: 46 tests passed, including the unchanged 29 P1 checker tests,
  the original 90-case P1 fixture suite, freeze rejection, provenance/partial failures,
  and actual Node.js code-point-to-UTF-16 conversion on repeated/non-BMP text.

The scoped workflow was the repository's `speckit-implement` skill for F-003 preparation,
with explicit `specs/000-foundation` selection and the official PowerShell resolver:
`powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`.
Its requirements checklist had 16 checked items and zero unchecked. No extension hooks
were registered. No task completion marker was changed by this package.

At the executable-candidate checkpoint, P1 and all files that existed before that package
were preserved. Verification preceded any publication of the review branch. These results
do not establish generated-binding compatibility, runnable service behavior, cancellation/
retention behavior, retrieval quality or human owner acceptance.

## Exact RC1 decisions

These resolve proposal details into testable choices for one artifact review. They are
not assertions of A/C/D human approval. S-01 through S-06 were B's selected positions;
the additional field details below are candidate recommendations for affected owners.

| P2 issue | Concrete RC1 proposal |
| --- | --- |
| 01: canonical text | Preserve nfc-lf-v1, exact UTF-8 hashing, opaque document ID, and half-open code-point evidence. No source-text rewrites. |
| 02: procedures | Required `procedure_status` is planned/ordered/performed/cancelled/hypothetical/unknown for procedures, null for other types. It is independent of assertion and time; planned does not mean performed. |
| 03: assertion | Add `unknown`; a processing failure is not an unknown assertion. |
| 04: mentions | One item per contiguous mention; required exact `mention` span plus wider `evidence` spans. At least one evidence span covers the mention. Names remain display labels. Repeated occurrences retain distinct locations. |
| 05: partial analysis | One ExtractionResult with extraction_status completed/partial/failed, extraction_error, warnings, extraction_provenance, and a SummaryOutcome wrapper. Completed-empty is valid; partial needs supported items and warnings; failed extraction needs an error and no items. |
| 05: summary failure | SummaryOutcome has status completed/failed, result, and error. Completed processing may yield insufficient evidence; failure is operational. Keep successful findings or summary; if both sections fail, return an ErrorEnvelope rather than 200 fake success. |
| 06: text and claims | Summary/answer text with claims is exactly their text joined by two LF characters. Limitations stay in warnings/clarification. Empty responses use the fixed English notices below. This prevents unclaimed free prose; it does not prove semantic support. |
| 07: classifier | Retain `status` (not the fragment typo `state`). Add classification_execution performed/skipped; null model_version/score_kind when skipped. Performed results have exactly five unique, ordered scores. Supported/uncertain have no scope-policy fields; unsupported requires a policy version and safe reason ID. |
| 07: conservative scope | No automatic unsupported detector is claimed. Live unsupported outcomes are disabled until a separately approved/evaluated scope policy exists. Normal accepted English follows supported/uncertain. Unsupported mocks are explicit simulations only. Missing model configuration remains a 503 error. |
| 08: retrieval | Higher returned score ranks better within its retriever/version; score_note explains the metric/transformation. Add corpus_version beside index/retriever versions. No sufficiency threshold is invented. |
| 09: follow-ups | Clarification is explicit: AnswerResult.clarification has code ambiguous_reference and an English message; route none, insufficient evidence, no claims/sources. B asks the user to name the topic; no automatic rewriting/history expansion. |
| 10: correlation | Business POST operations require one canonical lowercase UUID X-Request-ID. B generates UUIDs; services echo valid IDs on success and failure. ErrorEnvelope.request_id matches the response header. Invalid/missing/duplicate request headers cause 400/validation_failure with a new safe diagnostic UUID. |
| 11: provenance | ComponentProvenance identifies component/service/operation, mode, output/prompt versions, provider/model/configuration versions, and A's corpus/index/retriever versions. Claim/source component_id links preserve origin. No guessed metadata for a generator that never ran. |
| 11: execution origin | Component modes remain mock/live. Overall AnswerResult/ExtractionResult mode is mock, live, or mixed as derived from the actual recorded components. With no executed component, mixed is invalid. Health mode describes the service, not a composed answer. |
| 12: answer composition | Preserve claim text and its links. B prefixes local component/source/claim IDs with a: or d: consistently when combining. Sources/claims must resolve to their producing component. Document facts come from D/document sources; general information from A/literature sources. |
| 12: routes | attempted_routes records document/literature targets even when route is none. A completed mixed answer retains both attempted routes; a partial answer may retain only supported sources plus warnings. Differentiate evidence gaps from outages. |
| 13: errors | Completed domain outcomes use 200. Operational errors use safe envelopes: 400 malformed JSON/header, 422 validation, 413 oversized document, 401 required auth, 429 rate, 500 internal_error, 502 invalid upstream, 503 configuration/provider/budget, 504 timeout. B retains its safe 404 and upload 415 boundaries. |
| 13: retrieval failure | Remove the 200 RetrievalResult.state:error branch. RetrievalResult is sufficient/insufficient; an operational failure is a non-2xx ErrorEnvelope. Update A's consumer task/docs only after approval. |
| 14: language | PreparedDocument now carries language_validation with accepted outcome, en, policy_version and null reason. Rejected/inconclusive LanguageValidation records are supported before preparation; neither becomes an admitted PreparedDocument. No live detector is selected by this schema. |
| 15: readiness | Shared GET /health/live returns LivenessResult. GET /health/ready returns HealthResult, 200 when ready, 503 when not ready. This 503 health payload is a documented health-specific exception to business ErrorEnvelope. Mock readiness never asserts a loaded real model. |
| 15: ownership | A/C/D build owned service scaffolds after their agreed handoff. B owns root/startup/contracts/bindings/integration; no service files are edited here. |
| 16/17: evaluation/activation | Keep subject-attribution and one-to-one mention evaluation with D; no formulas/thresholds invented. Provider activation, budget, numeric operational controls, deployment and publication stay separate gates. |

### Classification details

Exactly preserve this score order: Cardiovascular / Pulmonary, Orthopedic,
Gastroenterology, Neurology, Urology. Scores are finite JSON numbers. Probability scores
are within [0,1]; no unagreed sum-to-one tolerance. Decision scores are not percentages.
If classification is skipped, status is unsupported, scores are empty and model_version/
score_kind are null. An executed unsupported mock has all five scores and actual simulated
pipeline metadata. scope_policy_version/reason identify the separate simulated policy.
They never stand in for a missing classifier model. No hidden labels, extraction output,
keyword absence or low confidence establishes unsupported scope.

### Provenance and rendering

`components` belongs to AnswerResult; Summary has its own nullable provenance, while
ExtractionResult has extraction_provenance and the independent SummaryOutcome. A component
records an executed generation contribution, not configured-but-unused inventory. If a
static evidence-gap response needs no generator, provenance may be absent/null with no
claims. Output implementation versions can still identify the response-producing code.
For single-service answers, root answer_version/prompt_version match their component;
extraction root versions match extraction_provenance when that stage ran. Deterministic
mixed composition uses answer_version `notelens-compose-v1` and null prompt_version,
preserving actual generation versions in components. No-component static responses have
null prompt_version. This prevents a wrapper version from masquerading as an executed prompt.
When generation ran, record the actual provider/model/configuration and prompt versions;
do not include secrets, source text or sensitive prompts. A corpus version identifies
selection/preparation, not just snapshot date.

For text with claims, render `"\n\n".join(claim.text for claim in claims)`. Warnings are
separate limitation text and must not smuggle new medical claims. With no summary claims,
text is `The available document evidence does not support a summary.` With no answer
claims and no clarification, text is `The available sources do not support an answer.`
For clarification, text equals clarification.message. These rules constrain presentation;
source-relative medical support still requires D/A's validation and human evaluation.

Successful answer components are D document-answer or A literature-answer; summaries and
extraction identify their own D operations. Prefixing all IDs during composition is
deterministic, even if an original local ID already contains a colon. Rewrite every
reference together; do not concatenate unsupported medical prose or treat URL existence
as proof. Repeated mention matching and ICD-to-entity association remain semantic review
concerns beyond exact slices/token checks.

### Request IDs, errors, cancellation and health

Header names are case-insensitive; duplicates remain invalid even with the same UUID.
UUID spelling must be canonical lowercase with hyphens; B normally generates UUID4.
On invalid incoming IDs, generate a new UUID only for the error header/envelope. B treats
that response as a failed call, never a successful correlated classification. A changed
response ID for a valid incoming ID remains an upstream protocol failure. UUIDs do not
authorize access. B independently binds calls to session, question, doc_id/hash and expiry.

Health GETs do not require a correlation header, so local process checks can run without
business request context; their contract explicitly says so. Exposed health/business
services use the agreed server-only authentication; key-free mock exceptions are limited
to loopback. Readiness describes configured mode; a live classifier needs a real usable
pipeline to report ready, while liveness only says that the process runs.

B owns its outgoing deadline and late/stale rejection. C checks cancellation before work
and releases transient references when work ends; immediate interruption of synchronous
inference is not promised. Runtime bounds, maximum document lifetime across in-flight
processing, cancellation testing and operational controls must be resolved before real
integration. None of the error examples configures numeric limits or automatic retries.

### Language and clarification activation boundaries

The fixture policy ID is deliberately `fixture-language-policy-v0`. It labels synthetic
protocol data; it is not a language detector, measured policy, or approval to accept real
submissions. A live B-side language method still needs review/evaluation before B-001's
user-input behavior is enabled. Until then, the key-free foundation uses known English
public/synthetic fixtures. This preserves the MVP input requirement as unimplemented work;
it does not silently remove it. No translation is introduced.

Accepted maps to en/null reason; rejected maps to null language/unsupported_language;
inconclusive maps to null language/language_inconclusive. At the input boundary propose
422/unsupported_language for rejection and 422/validation_failure for inconclusive input,
with safe English guidance. C needs the accepted policy record, not detector probabilities,
session history or a confidence-based language guess. Short/mixed-language and terminology-
heavy examples need the later policy's own evaluation. Plain declarations are not proof.

Clarification records likewise specify a control outcome, not a claimed general ambiguity
detector. B asks users to supply an explicit topic rather than infer a patient condition.
No autonomous question rewriting, unrestricted A history, or extra paid call is enabled.
Question/history caps remain undecided and are not copied from document limits.

## Examples, executable checks and review boundary

`fixtures/manifest.json` lists positive/negative cases and exact expected diagnostics;
`payloads.json` holds complete examples. `documents.json` and `references.json` retain
synthetic evidence/gold contexts. Existing P1 cases are adapted rather than rewritten in
place. `transport-cases.json` simulates UUID header/error correlation; it starts no server.
Additional tests exercise strict text/claim rendering, section failures, component origin,
live unsupported reservation, deterministic regeneration and JavaScript UTF-16 conversion.

All cases are synthetic protocol illustrations, including entries whose mode is live or
mixed to test metadata rules. No model/provider/service actually ran. The examples are not
clinical ground truth, generated-binding compatibility, real HTTP tests or retrieval
quality measurements. Real patient reports, OCR, translation, accounts and treatment
recommendations remain outside the approved scope.

The builder rejects candidate drift under --check. The candidate checker fingerprints
its inputs, validates Draft 2020-12/OpenAPI 3.1.1, runs the cases, and prints case/rule
identifiers without payload bodies. It cannot approve itself or mark F-003 done.
The [classifier scaffold brief](../../../docs/team/classifier-scaffold-p2.md) is exact
about proposed behavior and file/import expectations, but its service commands are
explicitly planned, not verified runnable commands. C owns the future implementation.

## One final artifact review

| Reviewer | Review this exact candidate |
| --- | --- |
| A | Score direction, corpus/index/retriever metadata, stateless requests/clarification, request UUIDs, operational error channel, and composed provenance/IDs. |
| C | status/execution/scope fields, null unused-model metadata, ordered scores, UUID fallback, language-policy record and health/scaffold requirements. |
| D | procedure_status, unknown assertion, mention/evidence boundaries, independent section states, deterministic claims/text, component provenance and semantic/evaluation limits. |
| B/user | Confirm candidate choices and any remaining product/scope concerns; authorize canonical promotion only after actual affected-owner agreement. |

Respond with candidate ID plus manifest SHA256, actual reviewer/date, accepted issues or
specific objections, and human/agent distinction. Do not repeat the broad P2 questionnaire.
The [two C responses](reviews/member-c-response-to-b-p2-clarifications.md) provide detailed
agent recommendations; the latest explicitly says human confirmation is pending.
The [earlier C response](reviews/member-c-p2-review-and-next-dependencies.md) accepts the
stated behavior and ownership split, not final schema bytes. [P1 responses](../../../docs/team/contract-reviews/p1/README.md)
and the [P2 proposal](../../../docs/decisions/contract-p2-proposal.md) remain historical context.

After agreement: apply the approved candidate to the single canonical contract, update
affected owner requirements/consumers, rerun checks, record the exact freeze, execute
F-009 generation/compatibility, and hand off scaffolds. There is no freeze.json, final
human acceptance, published B commit/PR, paid activation, or F-014 checkpoint here.
