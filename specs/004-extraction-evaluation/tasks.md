# Tasks: Python Extraction and Shared Evaluation

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: D. **Status**: executable backlog proposal; no business task is complete.

**Authorized continuation (2026-11-11):** The user explicitly requested the runnable
D-owned local slice despite missing shared gates. Completed local subtasks below do
not close their parent task's frozen-contract, real-model, real-data or human-review
requirements. No A/B/C task or shared prerequisite is self-approved by D. Actual
commands/results: [integration](../../docs/extraction-eval/integration.md).
**Tests**: Required where the source specifications explicitly require structural, semantic,
leakage, security or independent module checks. This is not blanket TDD for documentation.
**Organization**: Setup, foundational, story increments, polish. Every task has one owner
and a story reference; setup/foundation/polish use metadata instead of a story label.
Standard IDs stay sequential; global aliases preserve the source seed names.

**Documentation handoff update (2026-11-10)**: The user approved sharing documents/tasks
now and deferred runnable mocks/UI. The current initial commit is a documentation base,
not the later F-014 runnable-foundation publication. Inspection and owned proposals can
start now; business prerequisites and unchecked implementation tasks remain unchanged.

## Frozen D local evidence (2026-11-13)

- [x] D-001: practice records/linter use frozen assertion and independent procedure
  status values; exact code-point spans remain checked. Team adoption remains open.
- [x] D-004/D-005: generated frozen binding, independent extraction/summary outcomes,
  literal supported/partial/insufficient answers and safe transport implemented locally.
- [x] D-006: locked installed contracts dependency, language-validation fixtures,
  canonical UUID HTTP adapters and authenticated health readiness checks updated.
- [x] D-008 preparation: read-only review validator, separate blank/incomplete/U/error
  reporting and blank form prepared. No real human review or calibration performed.

See [verification and remaining gates](../../docs/extraction-eval/d-local-completion-2026-11-13.md).
F-003/F-009 are complete upstream. No parent D checkbox, F-004/F-014 completion,
live activation or human acceptance follows from these local mock checks.

## Format: `[ID] [P?] [Story] Description`

No task is marked [P]: dependencies or shared files make an unconditional parallel claim
unwarranted. Different workstreams can progress independently after the shared base.
Only foundation F-001/F-002 were checked at the original handoff. The local continuation
adds subtask checkboxes with explicit limits; no D parent task is closed from mocks.

## Path Conventions and Command Availability

All paths below are repository-relative and limited by the [ownership matrix](../../docs/team/allowed-paths.md).
Initial foundation scaffolding is the coordinator exception; afterward owners stay in scope.
The command targets named below are **planned deliverables of the named tasks**, not
existing npm scripts or claims of current execution. After F-004 dependencies and the task's
listed test/CLI file exist, its command must actually pass before closing it.
`uv run --directory` intentionally changes the working directory to the service/eval
project; do not replace it with --project while leaving relative test paths at the repo root.

Contract constraints apply verbatim: evidence is a half-open Unicode code-point
[start,end) interval with an exact canonical quote; assertion is confirmed|suspected|negated|unknown,
temporality is current|historical|unknown, subject is patient|family|other|unknown.
Approved PDF/text/retention limits are 2,097,152 bytes, 100,000 code points and at most
60 minutes. Model scores/retrieval scores are not clinical confidence.
Unapproved live budgets/models/timeouts/retry/history/rate settings disable live execution;
they are not silently assigned defaults.

## Phase 1: Setup

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [x] T001 D-001: Draft annotation ontology, evidence rules and extraction interface proposals in `docs/extraction-eval/annotation-guide.md`, `specs/004-extraction-evaluation/contracts/**`
  - [x] Local draft guide, synthetic practice labels and interface proposals prepared; existing training command preserved and its eight negative cases made persistent tests.
  - [x] Draft submission lint reports malformed entity labels as field-level corrections. Tested arrays and objects in type, assertion, temporality, subject and procedure status.
  - [x] D reported team agreement on 2026-11-19 on separate occurrences, distinct nested or overlapping concepts, one-to-one exact and relaxed matching, and the source-support rule. Recorded in the annotation guide and answer-review rubric.
  - **Owner / story**: D / US1.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Define diagnosis/symptom/procedure, confirmed|suspected|negated, current|historical|unknown, subject, exact/relaxed repeated-mention matching, code copying only and source-support rubrics. Submit shared changes to B.
  - **Verify local draft**: `python -B docs/extraction-eval/check_training_examples.py`; human/team decisions remain separate.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-017.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [x] T002 D-010: Create D's independent offline evaluation packages, fixtures and mock adapters in `eval/pyproject.toml`, `eval/uv.lock`, `eval/package.json`, `eval/package-lock.json`, `eval/providers/**`, `eval/tests/test_offline_adapter.py`
  - [x] Local eval package/environment/locks, Promptfoo HTTP provider/config and synthetic smoke implemented and exercised without paid calls. Actual tests are in `eval/tests/test_slice.py`.
  - [x] The D Promptfoo adapter uses the frozen correlation validator, checks no-store and rejects non-200, non-object and non-mock responses. Loopback tests cover malformed transport and redirect responses in `eval/tests/test_offline_adapter.py`.
  - [x] The evaluator consumes all five accepted mock business routes over loopback. The synthetic smoke checks document identity, partial answers, and literature provenance in `eval/src/notelens_eval/cross_service_smoke.py`.
  - [x] F-003 and F-004 are complete and F-014 is published. On 2026-11-20 the combined B/D inventory candidate and B-004 main passed all 97 evaluator tests, three Promptfoo cases and the five-route D evaluator smoke. The [integration record](../../docs/extraction-eval/integration.md#d-010-verification-2026-11-20) identifies the tested source and the remaining platform inventory work. Real reference-backed A/C evaluation is tracked in D-006 and later tasks.
  - **Owner / story**: D / US4.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Own local eval locks without changing root lock; API adapters consume agreed records and never perform a paid call in offline/smoke mode.
  - **Verify**: `./eval/.venv/Scripts/python.exe -B -m pytest eval/tests -q`, `./eval/.venv/Scripts/python.exe -B eval/smoke_http.py`, and the [three-service evaluator smoke](../../docs/extraction-eval/integration.md#three-service-evaluator-smoke).
  - **Coverage**: FR-013, FR-025, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T003 [US1] D-004: Implement structured Python extraction and bounded semantic/span validation in `services/extraction/src/notelens_extraction/**`, `services/extraction/prompts/**`, `services/extraction/tests/test_evidence.py`, `services/extraction/tests/test_contract.py`
  - [x] The 2026-11-21 synthetic HTTP rerun returned 24 structurally valid extractions. The deterministic catalog matched 14 of 29 reference mentions. See the [rerun](../../docs/extraction-eval/synthetic-failure-review-v2.md) for the separate transport and fixture findings.
  - [x] Strict generated JSON validation, single-attempt live orchestration and offline OpenAI Responses adapter/HTTPS transport implemented in commits 7ccb1ba, 948bde6, 273b9ed and 3fbb67f. Trial reserves at most USD 0.10 across at most three approved requests. Extraction suite passed 83 tests after transport integration.
  - [x] 2026-11-20: User reports Nemanja approved one synthetic development smoke. Published `gpt-6-luna` standard rates and per-request conservative input bounds are recorded in `docs/extraction-eval/d-004-live-trial-2026-11-20.json`; the two-call reservation is USD 0.0028227 under the USD 0.10 cap.
  - [x] Added a one-command runner restricted to the two approved synthetic requests; it verifies exact payload hashes before sending and claims a single-use receipt. Invocation and credential setup are documented in `services/extraction/README.md`.
  - [x] Local request/schema/evidence validation, provider/config boundary, versioned prompts, bounded repair diagnostics, FastAPI/CLI and deterministic fake implemented. Checks live in `tests/test_service.py`, `tests/test_training_checker.py` and `tests/test_http_smoke.py`.
  - [x] Generated extraction and document-answer records use the frozen strict JSON validator. Duplicate keys and nonfinite numbers trigger bounded repair before evidence scoring.
  - [x] Live orchestration makes one provider attempt per request. Regression tests exercise invalid extraction and answer output without making a paid call.
  - [x] F-003, F-004 and F-014 integration is available on the published foundation. The combined B/D inventory candidate and mock integration checks are recorded under D-010 in the [integration record](../../docs/extraction-eval/integration.md#d-010-verification-2026-11-20).
  - [x] Nemanja's 2026-11-21 handoff records approval for one fresh attempt with the same two synthetic requests, zero retries and the existing cumulative USD 0.10 limit. D verified both prepared request hashes offline against the pinned scope and the handoff.
  - [ ] Remaining: keep the fresh attempt paused as requested by B until the authorized operator confirms the setup route, approved model access and remaining balance under the cumulative cap. Record the fresh attempt separately from the original single-use receipt. Verify the output schema, spans and semantic support.
  - **Owner / story**: D / US1.
  - **Dependencies**: 004-extraction-evaluation/T001 (D-001); 000-foundation/T004 (F-003); 000-foundation/T006 (F-004); 000-foundation/T014 (F-014)
  - **Acceptance**: POST /v1/extract preserves canonical text/status/subject and validates exact offsets/quotes, unsupported items and source-only ICD. Bounded repair; no inferred diagnoses. Live activation requires approved provider policy.
  - **Verify local slice**: `./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests -q`.
  - **Coverage**: FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, SC-001.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T004 [US2] D-005: Generate English summaries and document answers with supported claims in `services/extraction/src/notelens_extraction/answers.py`, `services/extraction/prompts/**`, `services/extraction/tests/test_answers.py`, `docs/extraction-eval/integration.md`
  - [x] Reran the 24-document/48-answer synthetic HTTP suite on 2026-11-21. All 72 records passed transport and structural checks. The [failure review](../../docs/extraction-eval/synthetic-failure-review-v2.md) documents all 14 incomplete answers and their exact fixture causes.
  - [x] Multi-part document mock answers preserve supported parts and explicit gaps (09b0573). Synthetic HTTP run returned 72/72 HTTP 200 responses with matching request IDs; literal completeness was 34/48. Responses trial supports the fixed synthetic document question.
  - [x] Local literal summaries, supported/partial/insufficient document answers, exact citation checks, source-free output guard and targeted injection case pass in mock mode; B handoff prepared.
  - [x] Mock document answers cover explicit catalog topics independently, retain cited supported parts, and disclose gaps. The 72-request synthetic HTTP run preserved the contract and recorded 34 of 48 complete literal answers and 25 of 26 expected gap mentions.
  - [ ] Remaining: after D-004, verify the provider-generated summary and document answer for source support, completeness, citations and English. Supply the reviewed service evidence to B for the integration check.
  - **Owner / story**: D / US2.
  - **Dependencies**: 004-extraction-evaluation/T003 (D-004)
  - **Acceptance**: POST /v1/document-answer and extraction summary explicitly request English, link claims to selected-document evidence and reject unsupported/injected/non-English output; literature cannot fill patient facts. Deliver HTTP checks/startup to B.
  - **Verify local slice**: `./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests/test_service.py -q`.
  - **Coverage**: FR-006, FR-007, FR-008, SC-001.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [x] T005 [US3] D-002: Select and freeze representative annotation assignment candidates in `eval/datasets/annotation-assignments.json`, `docs/extraction-eval/selection.md`
  - [x] Seeded selector and input validation tested on synthetic fixtures, including 40-group algorithm tests.
  - [x] Selector requires explicit boolean annotation permission and rejects identical canonical text placed in different duplicate groups. Both checks are covered by synthetic regressions.
  - [x] The synthetic proposal checks C's development-only review capacity and reserves an independent review when feasible. Infeasible capacity is reported for team review before freeze.
  - [x] Read-only manifest preflight verifies the pinned version and SHA-256, reuses candidate validation and reports aggregate allocation capacity. Selection can recheck the same immutable inputs before writing a proposal.
  - [x] Received C's restricted `c002-d002-development-v1` manifest and matching SHA-256 on 2026-11-20. D preflight found 185 unique permitted groups, all in validation/development, with sufficient allocation capacity. A deterministic seed-20261120 selection contains 40 groups, eight per specialty, and records 10 primary assignments per member plus 10 separate reviews in `eval/datasets/annotation-assignments.json`.
  - [x] The user accepted and froze the D-002 selection on 2026-11-20. The handoff manifest contains metadata and text hashes but no canonical text; source-row delivery remains pending the approved access route.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T001 (D-001); 003-classification/T003 (C-002)
  - **Acceptance**: Target 40 approximately balanced documents; dev/final document/group disjoint, align ML validation/test where feasible. Reserve C's pre-selection annotations to development; report infeasible targets for review.
  - **Verify**: `python -B -m json.tool eval/datasets/annotation-assignments.json`.
  - **Coverage**: FR-009, FR-010, FR-011, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [x] T006 [US3] D-003: Publish ten primary assignments per member and independent-review workflow in `eval/datasets/annotation-assignments.json`, `docs/extraction-eval/review-workflow.md`
  - [x] Pending-only templates and distinct primary/reviewer allocation implemented under D-owned paths; C remains development-only in the demonstration.
  - [x] Synthetic rehearsal verifies separate submissions linked to the same document and assignment. The linter preserves open questions from both current and earlier templates.
  - [x] Generated a real-metadata assignment proposal from the received C-002 manifest: 10 primary assignments per member, 10 distinct secondary assignments, all in development. Saved 50 pending templates and a D-owned workflow proposal. After user acceptance, the manifest is frozen; row-level source access remains pending.
  - [x] The user accepted and froze the assignment allocation and workflow paths on 2026-11-20. The manifest is published locally in the D branch. Row-level delivery remains pending the approved canonical-text access route; no member receipt or annotation is claimed.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T005 (D-002)
  - **Acceptance**: Freeze each member's own submission paths and ten primary IDs; allocate distinct reviewers for at least ten documents. D must not edit A/B/C submissions. Canonical adjudication is D-013 after submissions arrive.
  - **Verify**: `python -B -m json.tool eval/datasets/annotation-assignments.json`.
  - **Coverage**: FR-009, FR-010, FR-011, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [x] T007 [US3] D-012: Complete D's primary annotations and independent reviews in its own path in `eval/annotations/member-d/**`
  - [x] Verified Sara's Milica-only development packet against D-003 and C-002. All 13 canonical text hashes matched. Separate local draft forms are ready for 10 primary annotations and 3 independent reviews. See the [verification receipt](../../eval/reports/development/d012-member-d-packet-verification-v1.json).
  - [x] Milica confirmed full-document review of assignments 002, 005 and 008. All three reviewed secondary records are packaged locally, with one source gap retained for assignment 005.
  - [x] Milica confirmed the full read of assignment 033 and approved all ten revised primary drafts in review workspace v3. The ten human-reviewed records are packaged for private submission. D verified 293 mention spans and 301 evidence spans against the frozen canonical texts. All ten records passed structural validation.
  - [x] Verified the combined private submission folder with separate `primary` and `reviews` subfolders and a top-level `submission-manifest.json` for Milica's 13 records.
  - [x] Nemanja confirmed receipt and verified Milica's private ZIP, and Goran confirmed readability and all nine listed file hashes. D verified the [submission receipt](../../eval/reports/development/d012-private-submission-receipt-v1.json). The single open question on 005 carries into D-013.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003)
  - **Acceptance**: Use frozen IDs, separate primary/review files, correct subjects/status/spans and preserved adjudication input; do not edit A/B/C files.
  - **Verify**: `python -B -m json.tool eval/annotations/member-d/submission-manifest.json`.
  - **Coverage**: FR-011, FR-012.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T008 [US3] D-013: Adjudicate preserved primary/secondary submissions into canonical references in `eval/references/**`, `docs/extraction-eval/adjudication.md`, `eval/tests/test_annotation_integrity.py`
  - [x] Received A's 10 primary and 3 independent submissions. Verified all package digests and frozen assignment identities. The [intake receipt](../../eval/reports/development/d013-member-a-intake-v1.json) records A's 27 open questions. Nemanja confirmed access and canonical digests for his own 13 assigned texts.
  - [x] Explicit-decision merge/pending workflow implemented and tested; preserves input-record provenance and never promotes synthetic decisions to human review.
  - [x] Verified C's updated 11-draft package against the frozen allocation and canonical texts. Verified 278 mention and 307 evidence spans. Replaced the preliminary comparison inputs with the new C drafts for 000, 003, 006 and 010, and checked three C/D pairs for 002, 005 and 008.
  - [x] Sara confirmed full-document review for all 11 C-010 assignments and reported a private finalized package of ten primaries and one independent review. The locally accessible package is the earlier draft. Intake and checksum verification of the finalized records remain pending.
  - [x] Sara confirmed Goran's authorized B-011 packet and direct access instructions. The primary labels for 001, 004 and 007 remain held until he submits those reviews.
  - [x] Prepared a restricted adjudication queue with proposed guidance and a source check for each of A's 27 open questions. The queue separates 12 attribute differences, 50 evidence-only differences and 56 groups of non-exact mentions for review. Final decisions await approved canonical-text verification and human adjudication.
  - [x] Prepared feedback on C's 14 questions. A's complete private packet verified against the frozen allocation and all 13 canonical text hashes. D checked A's 271 mention spans and 393 evidence spans and prepared source-grounded proposals for all 27 open questions.
  - [x] Sara confirmed Milica's access to A's canonical texts. D reopened and reverified all 13 local canonical files against the frozen allocation and reverified Nemanja's existing reviewed ZIP. Sara approved Nemanja's direct private chat with Milica for revisions, with an updated manifest and SHA-256 checksums. The team-wide submission route remains pending. Nemanja still needs to confirm the pinned passages retrieval location.
  - [x] Milica reported team confirmation of Goran for 034, Sara for 036 and Nemanja for 038. Prepared and verified separate private canonical-text and metadata packets for all three D-013 reviews.
  - [x] Recorded the three assignments in a [supplemental allocation](../../eval/datasets/annotation-review-allocation-addendum-v1.json) pinned to the frozen D-003 manifest. Sara returned her review. Goran's availability and return date for 034 await individual confirmation.
  - [x] Verified Sara's reviewed 036 v2 against the canonical text and its superseded v1 record. Paired it with Milica's reviewed primary record. The comparison has 13 exact type-and-offset matches and the three clarified procedure mentions appear in v2.
  - [x] Verified Nemanja's reviewed 038 v2, including all ten package checksums and 24 mention and 24 evidence spans. Paired it with Milica's primary submission and queued the four questions. Recorded it as a non-blinded secondary review with zero independent-review credit because Nemanja had seen the primary labels. Nemanja reconfirmed submission and has no outstanding 038 handoff.
  - [x] Received Milica's verified D-012 submission. Its one source-gap question on 005 remains in D-013 adjudication.
  - [x] Prepared a restricted review workspace for Milica to inspect canonical evidence and record decisions on A's 27 questions, with input hashes pinned to the reviewed records.
  - [ ] Remaining: collect outstanding human-reviewed submissions, resolve the open questions and paired disagreements, and record human decisions before preparing references.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003); 004-extraction-evaluation/T007 (D-012); 001-rag/T009 (A-007); 002-platform/T006 (B-011); 003-classification/T004 (C-010)
  - **Acceptance**: Keep all submissions immutable; adjudicate disagreements with provenance and >=10 independent secondary reviews; confirm group-separated development/final references. Call references human-reviewed, not clinically validated.
  - **Verify local tooling**: `./eval/.venv/Scripts/python.exe -m pytest eval/tests/test_slice.py -k merge`; actual adjudication needs human submissions.
  - **Coverage**: FR-009, FR-010, FR-011, FR-012, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: User Story 4

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [x] T009 [US4] D-006: Implement shared Promptfoo API adapters and deterministic scorers in `eval/providers/**`, `eval/profiles/**`, `eval/src/notelens_eval/**` and `eval/tests/**`
  - [x] Verified C-003's prediction checksum and replayed all 185 validation documents against C-002. Recorded the confusion matrix, five per-class metrics rows, coverage, descriptive baseline, and group/hash integrity. Accuracy was 174/185 and macro-F1 was 0.9285. The [classification report](../../docs/extraction-eval/classification-scoring.md) records the cross-split leakage and training-baseline evidence limits.
  - [x] Replayed the two actual A development answers in the v2 packet against agent-reviewed labels. Both answers met the pilot's source-relative correctness rule. The [pilot record](../../docs/extraction-eval/answer-risk-scoring.md#saved-a-development-pilot-2026-11-20) gives sample and review limits.
  - [x] Verified separate offline and HTTP mock paths. Passed all 104 evaluator tests, the three Promptfoo document cases, the shared Promptfoo case covering five routes, and the 72-request synthetic HTTP suite. Live and final entry points rejected execution. See the [verification record](../../docs/extraction-eval/integration.md#d-006-verification-2026-11-20).
  - [x] Offline retrieval profile measures unique-topic Recall@5, MRR, all-required topics and independent passage evidence coverage, grouped by single/multi source (269012d).
  - [x] Replayed A's saved vector, hybrid and BM25 rankings against eight proposed public development references on 2026-11-20. Vector and BM25 retrieved every proposed topic and cited passage in the top five. Hybrid retrieved all proposed topics in 7/8 cases and all cited passages in 7/8; A-QA-03 has no proposed reference topic and was excluded. The [report records that the source passage artifact was absent and proposal labels await review](../../docs/extraction-eval/retrieval-scoring.md#a-public-development-replay).
  - [x] Reconciled A's saved development-evaluation counts. It includes three single-topic rankings and one no-reference case; the retrieved five-passage source slices are not present locally. No new ranking or independent source review is claimed.
  - [x] Recorded D's evidence review of the supplied A-QA-02/A-QA-03 passages and the retained A-QA-02 partial answer. All ten supplied passage hashes and the answer citation-slice hash match. The review is agent-authored, non-blinded and limited to these cases. It is not a human review or calibrated risk result. See [the review record](../../docs/extraction-eval/a-qa-02-03-evidence-review.md).
  - [x] Offline answer-risk profile measures independently judged answer errors, coverage, answerability and rejection rates, technical errors and optional confidence threshold curves (1d48f2e).
  - [x] Synthetic prediction-file runner, actual-service Promptfoo HTTP adapter, exact/relaxed one-to-one scoring, context-label accuracy and QA state/abstention counts implemented. Unsupported semantic/risk/English-quality metrics are explicitly unavailable.
  - [x] Full 24-document/48-question loopback HTTP runner added in `eval/src/notelens_eval/http_suite.py`; local run: 72 HTTP 200 responses, 0 technical failures, all request IDs matched, and 72 schema-valid outputs. Mock scorer misses are recorded separately; local outputs are ignored under `eval/reports/local/http-suite/`.
  - [x] The synthetic HTTP runner distinguishes transport and record validity from quality. Broken HTTP 200 responses fail the run, and the expected gap denominator remains fixed when records cannot be scored.
  - [x] Authorized 2026-11-12 extension: 24 synthetic documents / 48 questions, six groups, validated references, grouped and per-case failure reporting, required literal QA support checks, and reproducible generation/rescoring CLI. See `docs/extraction-eval/synthetic-evaluation-v1.md` and `eval/tests/test_synthetic_suite.py`. Mock provider unchanged; this does not close the parent task.
  - [x] Follow-up answer-completeness evaluation: versioned per-question required facts and expected gaps; detects missing required evidence, extra source quotes, and undisclosed gaps. Latest synthetic run is recorded in `docs/extraction-eval/synthetic-failure-review-v1.md`; evaluation-only labels never enter provider requests.
  - [x] Five additional D-local increments prepared 2026-11-12: full synthetic HTTP suite; annotation draft linter; independent submission comparison; human answer-review rubric/form draft; and reference coverage profile. See `docs/extraction-eval/independent-d-work-2026-11-12.md`. Parent remains open for A/C integration, human review and frozen records.
  - [x] Authorized 2026-11-12 local integration readiness tool checks D's draft contract bindings, demo fixtures, loopback HTTP schemas/evidence/errors/headers and reports missing cross-service gates; see `docs/extraction-eval/readiness-v1.md`.
  - [x] Follow-up negative boundary suite covers malformed JSON, invalid/oversized/non-English requests, authentication, independent document IDs versus text digests, no-source claims and document-text log/response leakage. Per-case fake misses are summarized in `docs/extraction-eval/synthetic-failure-review-v1.md`; no real-model interpretation is claimed.
  - D-007 tracks the pinned passage artifact and source-reviewed QA reference freeze. D-008 tracks calibrated human review. D-011 tracks threshold decisions and D-009 tracks the final freeze and measured report.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T002 (D-010); 000-foundation/T014 (F-014)
  - **Acceptance**: Offline/smoke/live profiles are separate. Unit fixtures verify schema/spans, exact/relaxed entity matching, assertion/temporality, unique-topic Recall@5/MRR/all-required, evidence coverage, error-versus-rejection and risk/coverage; real providers remain off.
  - **Verify**: `./eval/.venv/Scripts/python.exe -m pytest eval/tests -q` and `./eval/.venv/Scripts/python.exe eval/smoke_http.py --cross-service`.
  - **Coverage**: FR-013, FR-016, FR-017, FR-018, FR-019, FR-020, FR-025, SC-001, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T010 [US4] D-007: Assemble source-reviewed development/final QA and relevance manifests in `eval/datasets/qa/**`, `eval/references/qa/**`, `eval/tests/test_qa_integrity.py`
  - [x] Versioned a nine-case development manifest with overlap grouping and scoped excerpt review. Nine of twelve citations matched at the excerpt-only checkpoint. See the [inventory](../../docs/extraction-eval/qa-development-inventory.md#development-manifest-and-available-excerpts).
  - [x] Public A proposal inventory validates nine development candidates, twelve evidence references, label counts and shared-passage overlap (68cad50). Optional artifact verification checks pinned SHA-256 and exact source slices.
  - [x] A supplied the pinned passage JSONL and SHA-256. D verified both pins, checked 12/12 exact citation slices, and reviewed all 13 requested parts against the available source material. Eleven parts are supported and two remain gaps in the pinned snapshot. The [source review](../../docs/extraction-eval/qa-development-inventory.md#pinned-source-review-after-as-handoff) records the gap search and alternate supporting passages.
  - [x] Initial versioned document-only synthetic case with three QA expectations exists separately from generated predictions; references never enter provider inputs.
  - [x] Built a 66-case development candidate inventory with ten new mixed requests. Deduplicated one identical document question, preserved cross-case source groups and validated all 12 original literature citations. See the [cross-module candidate inventory](../../docs/extraction-eval/qa-development-inventory.md#cross-module-development-candidates).
  - [x] Expanded the development inventory to 74 candidates and 21 multi-source requests. The [v2 coverage record](../../eval/reports/development/d007-development-coverage-v2.json) tracks source overlap, 12 verified original citation slices and four proposed additional reference slices.
  - [x] Prepared a [benchmark selection proposal](../../eval/reports/development/d007-benchmark-selection-proposal-v1.json) with 54 development cases and 26 unseen cases to source for the held-out partition. The proposal keeps the nine A cases and all 21 development multi-source cases. It omits 20 repetitive age-only probes from this proposed selection.
  - [x] [Reconciled the suggested 66/14 split](../../eval/reports/development/d007-benchmark-reconciliation-v1.json) with 74 current candidates. The existing inventory can reach 66 by restoring 12 repetitive age probes. The alternative uses 12 new, reviewed development cases. Recorded the nine A cases in development and verified the four proposed additional reference slices, including A-QA-09 part 2 at `[0,105)`.
  - [x] Recorded [joint A/D technical confirmation](../../eval/references/qa/d007-a008-development-qa-manifest-v1.json) of all nine development ratings and the four reference decisions. Reconciled the 75 source rows as 54 proposed development selections, 20 development reserves and one exact duplicate, `D-DOC/limited-04/absent`, represented by `D-DOC/negation-01/absent`.
  - [x] Prepared a [named staffing proposal](../../eval/reports/development/d007-final-author-review-plan-v1.json) for all 26 proposed final cases. Each slot has separate authorship and independent review. The proposal retains nine multi-source and three insufficient-evidence slots in supported routes. It contains planning metadata only.
  - [x] Recorded [Nemanja's staffing proposal](../../eval/reports/development/d007-final-author-review-plan-v2.json). Sara and Goran would each author 13 cases and independently review 13. The 26 slots meet the proposed route and evidence coverage targets. Sara accepted her assignments and the custodian role. She supplied the restricted folder and confirmed herself as owner and Goran as editor. Goran's availability awaits confirmation.
  - [x] Recorded [B's confirmation of the proposed coverage and rebuilt the development source baseline](../../docs/extraction-eval/qa-development-inventory.md#bs-coverage-check-and-final-source-separation). The check covers all 74 unique development candidates across 14 groups, including the nine reviewed cases and 20 reserves. Final source separation awaits candidate metadata in the approved restricted workflow.
  - [x] Prepared the pinned [development exclusion list](../../eval/reports/development/d007-development-source-exclusions-v1.json) for the pre-authoring source comparison. It includes all 74 unique candidates, their 14 source groups, and the excluded duplicate.
  - [x] Recorded A's verification of the v2 development package and the [pinned A-008 RAG handoff](../../docs/extraction-eval/qa-development-inventory.md#a-008-pinned-rag-handoff). D independently reverified the package, the duplicate and the nine reviewed references. B's app-routing acceptance and the shared benchmark freeze remain pending.
  - [x] Prepared the [source-planning guide](../../docs/extraction-eval/d007-final-source-intake.md) and the blank 26-slot intake template. Sara confirmed receipt of the exclusion list and reported zero slots checked. The exact v2 plan, exclusion list, guide and template are staged for the authoring team.
  - [x] Sara confirmed all packet checksums and all 26 intake-slot mappings. D reverified the pinned A passage ZIP for the literature slots. Nemanja's handoff to the authors, Goran's acceptance and the planned source list remain pending.
  - [ ] Obtain B and team confirmation of 54 development and 26 unseen final cases and Goran's assignments. Verify separation against the planned source list before authoring. Recheck the completed inventory and freeze the manifest and configuration before A/D evaluation access or measurement.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T009 (D-006); 001-rag/T003 (A-002)
  - **Acceptance**: Target ~80 QA including ~30 multi-source and ~10 lacking required-source answers plus out-of-scope. Publish exact counts/overlap, necessary topics/passages and answerability against actual corpus; flag >5 topics; no QA indexing.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_qa_integrity.py`.
  - **Coverage**: FR-014, FR-015, FR-019, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T011 [US4] D-008: Calibrate judge rubrics and coordinate separate generated-output human review in `eval/rubrics/**`, `eval/reviews/**`, `docs/extraction-eval/judge-calibration.md`, `eval/tests/test_review_integrity.py`
  - [x] Applied the draft rubric to seven retained synthetic answers and one injected HTTP 503. Recorded the agent ratings, proposed scoring anchors and severity question. The [practice check](../../docs/extraction-eval/judge-calibration.md#synthetic-rubric-practice-2026-11-21) confirmed zero completed human reviews and no quality scores for the operational failure.
  - [x] Prepared a separate human calibration packet with seven exact retained mock answers, their synthetic inputs, the rubric and blank rating forms. The packet supports independent scoring of identical responses.
  - [x] Independent review comparison reports per-dimension agreement and adjudication pairs for identical pinned outputs (d72bec9). Exact retained response artifact verification added (6c7c7d5). Full eval suite passed 95 tests.
  - [ ] Collect independent human reviews of answers and entity evidence, adjudicate disagreements and record rubric calibration decisions.
  - [x] Draft seven-dimension answer rubric and blank independent-review form prepared in `docs/extraction-eval/answer-review-rubric.md` and `eval/fixtures/answer-review-template-v1.json`; calibration, reviewers and human records remain pending.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T004 (D-005); 004-extraction-evaluation/T010 (D-007); 004-extraction-evaluation/T008 (D-013)
  - **Acceptance**: Calibrate on development examples, record judge versions/disagreements; plan ~40 answer reviews (10 each) and >=20 entity-evidence pairs separate from annotations. Final review is for reporting, not prompt tuning; live judges need budget approval.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_review_integrity.py`.
  - **Coverage**: FR-018, FR-021, FR-022, FR-025, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T012 [US4] D-011: Measure development quality and record named threshold decisions in `eval/config/acceptance.json`, `eval/reports/development/**`, `docs/extraction-eval/acceptance-process.md`, `eval/tests/test_acceptance_config.py`
  - [x] Consolidated the 185-document classification validation, eight-case retrieval replay, two-answer agent pilot and 72 synthetic HTTP records with pinned inputs and denominators. The [development record](../../docs/extraction-eval/acceptance-process.md#development-measurements-recorded-on-2026-11-21) leaves substantive thresholds unset.
  - [x] Acceptance proposal and read-only evaluator added. Structural targets remain 1.0; quality thresholds stay null. Missing decisions/measurements remain pending, violations fail, and numeric quality decisions require a named decision record. Full eval suite passed 97 tests; targeted acceptance tests passed after integer sample validation.
  - [ ] Remaining: measure provider-backed extraction and answers against reviewed development references, record named quality-threshold decisions, and review regressions against the recorded baselines.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T009 (D-006); 004-extraction-evaluation/T010 (D-007); 003-classification/T005 (C-003); 001-rag/T005 (A-004); 004-extraction-evaluation/T003 (D-004); 004-extraction-evaluation/T008 (D-013)
  - **Acceptance**: Keep substantive entries null/unset until first actual development measurement and team decision targeted 2026-11-14; structural/span targets remain 1.0; preserve sample/version/cost evidence and regression process.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_acceptance_config.py`.
  - **Coverage**: FR-016, FR-017, FR-018, FR-019, FR-020, FR-023, FR-024, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 7: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T013 D-009: Freeze final evaluation configuration and produce the English measured report in `eval/reports/final/**`, `eval/config/**`, `docs/extraction-eval/final-report.md`, `eval/src/notelens_eval/run.py`
  - [x] Verified Sara's C-008 aggregate results against the pinned model card and recorded the [classification evidence](../../eval/reports/final/c008-owner-classification-evidence-v1.json). The locked run covered 183 documents in 183 groups. Forced-choice accuracy was 176/183 and macro-F1 was 0.9582. Selective coverage was 174/183 and accuracy among assigned labels was 169/174. Bind the selected classifier artifact explicitly in the D-009 system freeze because the C-008 artifact differs from the C-005 B-005 rehearsal artifact.
  - [x] Verified Sara's exact C-008 startup manifest and repeated the authenticated C-005 transport check with the two admitted synthetic examples. The [joint preflight receipt](../../eval/reports/development/b005-c005-c008-joint-preflight-v1.json) records the model pins and the outstanding B-005 rendered report check for both models.
  - [ ] Resolve the listed dependencies, record the approved freeze, run the final evaluation and publish the measured report.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T011 (D-008); 004-extraction-evaluation/T012 (D-011); 004-extraction-evaluation/T007 (D-012); 001-rag/T010 (A-008); 003-classification/T010 (C-008); 002-platform/T007 (B-008); 002-platform/T011 (B-009); 004-extraction-evaluation/T008 (D-013)
  - **Acceptance**: Run frozen final versions only after approved gates; report counts/versions, baseline comparisons, costs, limits, security/English suite and accepted regressions. Optional silver data separately; no hidden threshold reduction or universal security claim.
  - **Verify**: `uv run --directory eval python -m notelens_eval.run --profile final --require-freeze`.
  - **Coverage**: FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- D-001 (T001) <- no task prerequisite.
- D-010 (T002) <- F-003, F-004.
- D-004 (T003) <- D-001, F-003, F-004, F-014.
- D-005 (T004) <- D-004.
- D-002 (T005) <- D-001, C-002.
- D-003 (T006) <- D-002.
- D-012 (T007) <- D-003.
- D-013 (T008) <- D-003, D-012, A-007, B-011, C-010.
- D-006 (T009) <- D-010, F-014.
- D-007 (T010) <- D-006, A-002.
- D-008 (T011) <- D-005, D-007, D-013.
- D-011 (T012) <- D-006, D-007, C-003, A-004, D-004, D-013.
- D-009 (T013) <- D-008, D-011, D-012, A-008, C-008, B-008, B-009, D-013.

## Parallel Example and Story Order

Separate members may inspect corpus sources (A-001), audit dataset input (C-001) and draft
annotation rules (D-001) independently. After the foundation base, B's UI consumes mocks;
D's offline evaluator does not wait for real A/C. Within this feature use explicit edges:
work on independent story tasks only when their actual dependencies are complete.
For D, assignment publication (D-003) precedes member submissions; canonical adjudication
(D-013) follows them, preventing a review/annotation dependency cycle.

## Implementation Strategy

MVP first: preserve the story's independent contract/mock scenario, then replace its
own stub with real behavior and validate source support. Add measured improvements only
on development data. Optional reranking/extra data/ONNX/ICD must not block the core.
Do not run live or final checks merely to close checkboxes. Report actual mock/module/live
evidence separately, and seek approval before new scope, paid activation, deployment,
commits or publication.
