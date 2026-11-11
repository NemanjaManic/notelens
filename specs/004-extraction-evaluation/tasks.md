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
[start,end) interval with an exact canonical quote; assertion is confirmed|suspected|negated,
temporality is current|historical|unknown, subject is patient|family|other|unknown.
Approved PDF/text/retention limits are 2,097,152 bytes, 100,000 code points and at most
60 minutes. Model scores/retrieval scores are not clinical confidence.
Unapproved live budgets/models/timeouts/retry/history/rate settings disable live execution;
they are not silently assigned defaults.

## Phase 1: Setup

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T001 D-001: Draft annotation ontology, evidence rules and extraction interface proposals in `docs/extraction-eval/annotation-guide.md`, `specs/004-extraction-evaluation/contracts/**`
  - [x] Local draft guide, synthetic practice labels and interface proposals prepared; existing training command preserved and its eight negative cases made persistent tests.
  - [ ] Remaining: team resolution of the proposed annotation/matching representation and source-support rubric; no human acceptance is inferred.
  - **Owner / story**: D / US1.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Define diagnosis/symptom/procedure, confirmed|suspected|negated, current|historical|unknown, subject, exact/relaxed repeated-mention matching, code copying only and source-support rubrics. Submit shared changes to B.
  - **Verify local draft**: `python -B docs/extraction-eval/check_training_examples.py`; human/team decisions remain separate.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-017.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T002 D-010: Create D's independent offline evaluation packages, fixtures and mock adapters in `eval/pyproject.toml`, `eval/uv.lock`, `eval/package.json`, `eval/package-lock.json`, `eval/providers/**`, `eval/tests/test_offline_adapter.py`
  - [x] Local eval package/environment/locks, Promptfoo HTTP provider/config and synthetic smoke implemented and exercised without paid calls. Actual tests are in `eval/tests/test_slice.py`.
  - [ ] Remaining: reviewed frozen records/bindings and shared scaffold compatibility; this is a provisional adapter.
  - **Owner / story**: D / US4.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Own local eval locks without changing root lock; API adapters consume agreed records and never perform a paid call in offline/smoke mode.
  - **Verify local slice**: `./eval/.venv/Scripts/python.exe -m pytest eval/tests/test_slice.py`; Promptfoo command is documented in integration.md.
  - **Coverage**: FR-013, FR-025, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T003 [US1] D-004: Implement structured Python extraction and bounded semantic/span validation in `services/extraction/src/notelens_extraction/**`, `services/extraction/prompts/**`, `services/extraction/tests/test_evidence.py`, `services/extraction/tests/test_contract.py`
  - [x] Local request/schema/evidence validation, provider/config boundary, versioned prompts, bounded repair diagnostics, FastAPI/CLI and deterministic fake implemented. Checks live in `tests/test_service.py`, `tests/test_training_checker.py` and `tests/test_http_smoke.py`.
  - [ ] Remaining: B's freeze/bindings/foundation compatibility, approved live provider/model and evaluated semantic support beyond the narrow catalog guards.
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
  - [x] Local literal summaries, supported/partial/insufficient document answers, exact citation checks, source-free output guard and targeted injection case pass in mock mode; B handoff prepared.
  - [ ] Remaining: approved real-provider generation, general support/language evaluation and frozen integration. The literal mock is not a general medical QA model.
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

- [ ] T005 [US3] D-002: Select and freeze representative annotation assignment candidates in `eval/datasets/annotation-assignments.json`, `docs/extraction-eval/selection.md`
  - [x] Seeded selector and input validation tested on synthetic fixtures, including 40-group algorithm tests.
  - [ ] Blocked actual selection: C-002 permitted canonical document/group/split manifests and access policy are absent. No actual IDs or dev/final proportions are invented.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T001 (D-001); 003-classification/T003 (C-002)
  - **Acceptance**: Target 40 approximately balanced documents; dev/final document/group disjoint, align ML validation/test where feasible. Reserve C's pre-selection annotations to development; report infeasible targets for review.
  - **Verify**: `python -B -m json.tool eval/datasets/annotation-assignments.json`.
  - **Coverage**: FR-009, FR-010, FR-011, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T006 [US3] D-003: Publish ten primary assignments per member and independent-review workflow in `eval/datasets/annotation-assignments.json`, `docs/extraction-eval/review-workflow.md`
  - [x] Pending-only templates and distinct primary/reviewer allocation implemented under D-owned paths; C remains development-only in the demonstration.
  - [ ] Blocked actual assignments/publication: D-002, agreed source access and human review workflow. Synthetic allocation is not the real 40-document assignment.
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T005 (D-002)
  - **Acceptance**: Freeze each member's own submission paths and ten primary IDs; allocate distinct reviewers for at least ten documents. D must not edit A/B/C submissions. Canonical adjudication is D-013 after submissions arrive.
  - **Verify**: `python -B -m json.tool eval/datasets/annotation-assignments.json`.
  - **Coverage**: FR-009, FR-010, FR-011, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T007 [US3] D-012: Complete D's primary annotations and independent reviews in its own path in `eval/annotations/member-d/**`
  - **Owner / story**: D / US3.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003)
  - **Acceptance**: Use frozen IDs, separate primary/review files, correct subjects/status/spans and preserved adjudication input; do not edit A/B/C files.
  - **Verify**: `python -B -m json.tool eval/annotations/member-d/submission-manifest.json`.
  - **Coverage**: FR-011, FR-012.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T008 [US3] D-013: Adjudicate preserved primary/secondary submissions into canonical references in `eval/references/**`, `docs/extraction-eval/adjudication.md`, `eval/tests/test_annotation_integrity.py`
  - [x] Explicit-decision merge/pending workflow implemented and tested; preserves input-record provenance and never promotes synthetic decisions to human review.
  - [ ] Remaining: actual independent submissions and human adjudication. No completed A/B/C annotations were generated.
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

- [ ] T009 [US4] D-006: Implement shared Promptfoo API adapters and deterministic scorers in `eval/providers/**`, `eval/scorers/**`, `eval/profiles/**`, `eval/src/notelens_eval/run.py`, `eval/tests/test_metrics.py`
  - [x] Synthetic prediction-file runner, actual-service Promptfoo HTTP adapter, exact/relaxed one-to-one scoring, context-label accuracy and QA state/abstention counts implemented. Unsupported semantic/risk/English-quality metrics are explicitly unavailable.
  - [ ] Remaining: complete agreed A/C adapters, retrieval/coverage/risk metrics, frozen records and separately gated live profiles. Initial tests are in `eval/tests/test_slice.py`.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T002 (D-010); 000-foundation/T014 (F-014)
  - **Acceptance**: Offline/smoke/live profiles are separate. Unit fixtures verify schema/spans, exact/relaxed entity matching, assertion/temporality, unique-topic Recall@5/MRR/all-required, evidence coverage, error-versus-rejection and risk/coverage; real providers remain off.
  - **Verify local slice**: `./eval/.venv/Scripts/python.exe -m pytest eval/tests/test_slice.py -q`.
  - **Coverage**: FR-013, FR-016, FR-017, FR-018, FR-019, FR-020, FR-025, SC-001, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T010 [US4] D-007: Assemble source-reviewed development/final QA and relevance manifests in `eval/datasets/qa/**`, `eval/references/qa/**`, `eval/tests/test_qa_integrity.py`
  - [x] Initial versioned document-only synthetic case with three QA expectations exists separately from generated predictions; references never enter provider inputs.
  - [ ] Remaining: actual corpus-reviewed QA, development/final portions and the approximately 80-case cross-module benchmark with A/B.
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T009 (D-006); 001-rag/T003 (A-002)
  - **Acceptance**: Target ~80 QA including ~30 multi-source and ~10 lacking required-source answers plus out-of-scope. Publish exact counts/overlap, necessary topics/passages and answerability against actual corpus; flag >5 topics; no QA indexing.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_qa_integrity.py`.
  - **Coverage**: FR-014, FR-015, FR-019, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T011 [US4] D-008: Calibrate judge rubrics and coordinate separate generated-output human review in `eval/rubrics/**`, `eval/reviews/**`, `docs/extraction-eval/judge-calibration.md`, `eval/tests/test_review_integrity.py`
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T004 (D-005); 004-extraction-evaluation/T010 (D-007); 004-extraction-evaluation/T008 (D-013)
  - **Acceptance**: Calibrate on development examples, record judge versions/disagreements; plan ~40 answer reviews (10 each) and >=20 entity-evidence pairs separate from annotations. Final review is for reporting, not prompt tuning; live judges need budget approval.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_review_integrity.py`.
  - **Coverage**: FR-018, FR-021, FR-022, FR-025, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T012 [US4] D-011: Measure development quality and record named threshold decisions in `eval/config/acceptance.json`, `eval/reports/development/**`, `docs/extraction-eval/acceptance-process.md`, `eval/tests/test_acceptance_config.py`
  - **Owner / story**: D / US4.
  - **Dependencies**: 004-extraction-evaluation/T009 (D-006); 004-extraction-evaluation/T010 (D-007); 003-classification/T005 (C-003); 001-rag/T005 (A-004); 004-extraction-evaluation/T003 (D-004); 004-extraction-evaluation/T008 (D-013)
  - **Acceptance**: Keep substantive entries null/unset until first actual development measurement and team decision targeted 2026-11-14; structural/span targets remain 1.0; preserve sample/version/cost evidence and regression process.
  - **Verify**: `uv run --directory eval python -m pytest tests/test_acceptance_config.py`.
  - **Coverage**: FR-016, FR-017, FR-018, FR-019, FR-020, FR-023, FR-024, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 7: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T013 D-009: Freeze final evaluation configuration and produce the English measured report in `eval/reports/final/**`, `eval/config/**`, `docs/extraction-eval/final-report.md`, `eval/src/notelens_eval/run.py`
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
