# P2 RC1: Executable Contract Review Candidate

**Prepared:** 2026-11-12. **Owner:** B. **Candidate ID:** `p2-rc1`.
**Proposed wire version:** `1.0.0`. **Status:** awaiting actual owner review.
**Current revision:** 3, prepared 2026-11-13 in response to the supplied A/C/D reviews.

Start here for the final artifact review. The generated `schema.json`, `openapi.json`,
fixtures, and simulated correlation cases are concrete proposals. They are **not** a
second accepted contract: [P1](../../v1/README.md) remains unchanged and canonical.
No application/service should switch to this candidate until it is approved and promoted.
F-003, F-009, F-004 and F-014 remain open. No bindings, mock services, providers or
deployment are delivered by this package.

## Revision 3: preserve retrieval without generation

This revision supersedes commit `01e96ab6c6a676efb43073a2eca711e89e419030` and manifest
`2c5043aa375a5aef1b0fa3806e8204284218d7b671c48bd8474ac74330c8affa` as the review target.
A's sole technical blocker was missing search provenance after insufficient retrieval
without answer generation. AnswerResult now requires nullable retrieval_provenance:

```json
{
  "service": "rag",
  "mode": "mock",
  "state": "insufficient",
  "corpus_version": "fixture-corpus-version",
  "index_version": "fixture-index-version",
  "retriever_version": "fixture-retriever-version",
  "score_note": "Synthetic ranking scores; higher is better within this retriever version."
}
```

Copy actual values from the completed RetrievalResult. This record has no generator,
provider, model or prompt fields. For completed insufficient retrieval, keep the record
even with empty generation components and null prompt_version. For pre-search clarification
it is null; configuration/operational failures use the existing error channel and do not
fabricate a completed search. B retains a supported D answer plus the actual literature
gap or outage warning. A completed insufficient search and a failed search stay distinct.

Overall mode now includes both completed retrieval and generation. A mock document answer
plus live insufficient retrieval is mixed; a live retrieval-only response is live. These
fixture values illustrate the protocol only. Literature generation requires a sufficient
retrieval record with matching corpus/index/retriever versions.

Start with answer-literature-insufficient-no-generation,
answer-document-supported-literature-insufficient, answer-document-with-retrieval-unavailable,
and answer-clarification in fixtures/payloads.json. The shared suite rejects missing or
fabricated history, mismatched versions, generation after insufficient retrieval and
hidden execution modes. Classification, input, health, extraction/summary definitions
and the classifier scaffold brief are unchanged from revision 2. The answer-level
clarification condition additionally requires zero components and null retrieval history.

**Approval status:** [C provided human approval of revision 2](reviews/member-c-p2-rc1-revision-2-approval.md).
[A's revision-2 agent review](reviews/member-a-p2-revision-2-response.md) requested the
implemented retrieval-only fix and explicitly lacked Nemanja's human approval.
[D's supplied response](reviews/member-d-p2-proposal-review.md), identified by the user,
reviewed the older prose proposal and expressly excluded the executable revision.
Neither response completes current owner acceptance. C's exact revision-2 approval is
retained; approval of revision 3 is not inferred.

Read [B's resolution and exact remaining confirmations](reviews/revision-3-resolution.md)
and the [focused review request](../../../docs/team/p2-revision-3-review-request.md).
The proposed closure of D's language/clarification questions keeps the foundation on
known English fixtures and leaves live validation-method evaluation at B-001/B-003's
activation gates. D's confirmation of that separation remains required. No detector,
budget, provider, operational limit or reviewer acceptance has been invented.

Revision-3 executed verification is recorded in the resolution document. Older counts
below describe their respective historical revisions.

## Revision 2: C artifact-review corrections

This revision supersedes commit `4ad602712bb23df6077cb252e1dd18b8cf8b9288` and manifest
`45a74a22a2ccb3f581edc74acc212f0cc94f54f9de1590b6bdd541013b84f0b5` for further review.
The candidate ID and proposed wire version remain unchanged; revision and byte hashes
identify the new review target. The old commit preserves revision 1 exactly.

- Direct Python validation rejects NaN and both infinities with NUMBER_FINITE and the
  exact field path, before schema comparisons. The guard applies to all floating-point
  numbers, including standalone scores and nested results. Strict JSON parsing remains
  unchanged. Runtime checks in future F-009 bindings and C's service must preserve this
  rule before serialization; passing JSON-only fixtures is insufficient.
- Both health GETs declare 401 ErrorEnvelope, code unauthorized, retryable false,
  WWW-Authenticate: Bearer, and a fresh server-generated canonical UUID in both response
  X-Request-ID and body request_id. Incoming health IDs are optional and ignored, even
  when malformed/duplicated; they neither cause 400 nor get echoed. Health 200/503 bodies
  remain LivenessResult/HealthResult without required IDs. Business POST rules are unchanged.
- The outside-repository test uses its own temporary working directory and requires no
  pre-existing .cache directory.

Read the byte-preserved [C artifact review](reviews/member-c-p2-rc1-artifact-review.md)
and [B's point-by-point response](reviews/member-b-response-to-c-rc1.md). At that stage C's reviewer was
a coding agent and human confirmation was pending; C's later revision-2 approval is linked above. Support for revision 1 does
not approve these revised bytes. A/C/D must review the current revision before F-003.

### Revision-2 verification: 2026-11-13

Executed in PowerShell with the unchanged locked Python 3.13.7 environment, uv 0.13.7
and Node.js v24.22.1. The commands in the next section passed: regeneration check,
139/139 payload outcomes (63 positive/76 negative), 22/22 simulated correlation outcomes,
and 51 unittest tests. No HTTP server was called. The new native-number and health-auth
regression tests were first observed failing before the fixes.

The same 51-test suite also passed in a fresh temporary review copy containing the
manifest-listed files, with no .cache directory present at startup. It reused the locked
interpreter/dependencies; this was not a new installation. The incoming C review was
byte-compared with the supplied source. All P1 files, original tooling/tests/lock and
foundation task markers are unchanged. The scoped speckit-implement resolver selected
specs/000-foundation, its requirements checklist passed 16/16, and no extension hooks
were registered. These checks do not provide HTTP, generated-binding, live-model or
human-acceptance evidence. The earlier checkpoint below describes revision 1.

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
builder, tests, archived reviews and B's response. Give reviewers the candidate ID,
revision and
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

Health GETs do not require an incoming correlation header, so local process checks can run without
business request context; their contract explicitly says so. Exposed health/business
services use the agreed server-only authentication; key-free mock exceptions are limited
to loopback. Readiness describes configured mode; a live classifier needs a real usable
pipeline to report ready, while liveness only says that the process runs.
For authenticated health calls, 401 uses the diagnostic envelope/challenge/ID rules in
the revision-2 section. It does not use the business POST header-validation rules.

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
| A | Confirm the revision-3 retrieval-only provenance fix and preserve the previously reviewed score, stateless-request, error and composed-source behavior; record actual owner approval. |
| C | Confirm the revision-3 answer-metadata delta; classification/input/health definitions and scaffold requirements remain unchanged from the revision-2 human approval. |
| D | procedure_status, unknown assertion, mention/evidence boundaries, independent section states, deterministic claims/text, component provenance and semantic/evaluation limits. |
| B/user | Confirm candidate choices and any remaining product/scope concerns; authorize canonical promotion only after actual affected-owner agreement. |

Use the current revision-3 focused request above. Respond with candidate ID/revision plus manifest SHA256, actual reviewer/date, accepted issues or
specific objections, and human/agent distinction. Do not repeat the broad P2 questionnaire.
The [earlier C responses](reviews/member-c-response-to-b-p2-clarifications.md) provide detailed
agent recommendations; their pending-human status was superseded by C's exact revision-2
human approval linked above, not by inferred acceptance of revision 3.
The [earlier C response](reviews/member-c-p2-review-and-next-dependencies.md) accepts the
stated behavior and ownership split, not final schema bytes. [P1 responses](../../../docs/team/contract-reviews/p1/README.md)
and the [P2 proposal](../../../docs/decisions/contract-p2-proposal.md) remain historical context.

After agreement: apply the approved candidate to the single canonical contract, update
affected owner requirements/consumers, rerun checks, record the exact freeze, execute
F-009 generation/compatibility, and hand off scaffolds. No freeze.json or complete set
of current owner approvals exists. Publishing this review branch does not complete
F-014, generate bindings, activate a provider or authorize deployment.
