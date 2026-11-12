# Tasks: Python Classification

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: C. **Status**: C-001 local data audit complete (2026-11-11); remaining tasks blocked by their listed prerequisites.
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
Foundation F-001/F-002 have recorded documentation/tooling completion. This feature now
also records C-001's actual local data audit. Writing plans/mocks does not close later tasks.

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

- [x] T001 C-001: Audit authorized MTSamples input, provenance and measured class mapping in `data/mtsamples/**`, `docs/ml/data-audit.md`
  - **Owner / story**: C / US2.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Support local CSV; review release/upstream reuse before redistribution; measure before/after counts for exact five targets, remove empties, reject broad-label merging. Never request credentials in chat.
  - **Verify**: `python -B -m json.tool data/mtsamples/manifests/source.json`.
  - **Evidence (2026-11-11)**: [Data audit](../../docs/ml/data-audit.md): 4,999 source rows; 1,338 target rows, 9 target empties removed, 1,329 retained. Eight synthetic audit tests and actual-source byte-for-byte regeneration passed. Raw/derived text stays ignored; no redistribution or live-provider check. Exact-conflict inventory is preliminary, not C-002 completion.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, SC-001.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T002 C-009: Review classifier contracts and build standalone mock consumer checks in `services/classifier/tests/test_contract.py`, `docs/ml/interface-review.md`
  - **Owner / story**: C / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Verify category/null states, score kind/meaning and model version against generated bindings; propose changes through B, not shared edits.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_contract.py`.
  - **Coverage**: FR-012, FR-013, FR-014, FR-015, FR-016, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T003 [US2] C-002: Group duplicates/conflicting labels and freeze seeded split manifests in `data/mtsamples/**`, `services/classifier/tests/test_splits.py`, `docs/ml/splits.md`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T001 (C-001); 003-classification/T002 (C-009); 000-foundation/T014 (F-014)
  - **Acceptance**: Document exact/near-duplicate criteria, audit-derived feasible proportions/seed and conflict exclusions before splitting; no group overlap. Publish stable IDs early for D.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_splits.py`.
  - **Coverage**: FR-005, FR-006, FR-007, FR-008, FR-017, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T004 [US2] C-010: Complete C's development-only primary annotations and independent reviews in `eval/annotations/member-c/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003)
  - **Acceptance**: Before model selection C annotates development documents only; preserve separate submissions and leave final-reference decisions to D. Do not use annotation exposure as test-set feedback.
  - **Verify**: `python -B -m json.tool eval/annotations/member-c/submission-manifest.json`.
  - **Coverage**: FR-018.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T005 [US2] C-003: Train majority and TF-IDF plus Logistic Regression baselines in `services/classifier/src/notelens_classifier/training/**`, `services/classifier/tests/test_training_leakage.py`, `docs/ml/experiments/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T003 (C-002)
  - **Acceptance**: All fitted transformations use train only; no label-revealing metadata. Record real validation support/metrics and reproducibility, never final-test selection.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_training_leakage.py`.
  - **Coverage**: FR-008, FR-009, FR-010, FR-011, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T006 [US2] C-004: Run a controlled XGBoost validation comparison in `services/classifier/src/notelens_classifier/training/**`, `services/classifier/tests/test_comparison.py`, `docs/ml/experiments/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T005 (C-003)
  - **Acceptance**: Use the same split/features/comparison controls; retain better simpler baseline if appropriate. Optional embedding variants do not block core; no benchmark manipulation.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_comparison.py`.
  - **Coverage**: FR-009, FR-010, FR-011, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T007 [US1] C-005: Select uncertainty policy and report model/error/confidence limits in `services/classifier/config/**`, `services/classifier/tests/test_uncertainty.py`, `docs/ml/validation-report.md`
  - **Owner / story**: C / US1.
  - **Dependencies**: 003-classification/T006 (C-004)
  - **Acceptance**: Choose thresholds on validation, report macro/per-class metrics/confusion/support/errors and score calibration/OOD limits. Do not claim universal unsupported detection or clinical certainty.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_uncertainty.py`.
  - **Coverage**: FR-010, FR-011, FR-012, FR-014, FR-015, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T008 [US3] C-006: Package full deterministic inference and its FastAPI operation in `services/classifier/src/notelens_classifier/**`, `services/classifier/tests/test_inference.py`, `services/classifier/tests/test_contract.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T007 (C-005)
  - **Acceptance**: POST /v1/classify uses frozen training-fitted preprocessing/label mapping/model version; result binds doc_id/hash, conforms to contracts and safely handles missing artifacts/errors. ONNX not required.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_inference.py tests/test_contract.py`.
  - **Coverage**: FR-013, FR-014, FR-015, FR-016, SC-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T009 [US3] C-007: Deliver actual startup and contract/smoke integration evidence to B/D in `docs/ml/integration.md`, `services/classifier/tests/test_http.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T008 (C-006)
  - **Acceptance**: B/D can run the independent service and validate HTTP payloads with permitted examples; mocks versus real-model outputs are distinguished.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_http.py tests/test_contract.py`.
  - **Coverage**: FR-013, FR-016, FR-017, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T010 C-008: Freeze the chosen model and run the locked final measurement/model card in `docs/ml/model-card.md`, `services/classifier/artifacts/manifests/**`, `services/classifier/tests/test_final_freeze.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T009 (C-007); 003-classification/T004 (C-010)
  - **Acceptance**: Record actual final results/versions/counts, baseline comparisons and limitations after selection freeze. A repeated final run requires new version/reason; supplementary distributions are reported separately.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_final_freeze.py`.
  - **Coverage**: FR-010, FR-011, FR-019, FR-020, FR-021, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- C-001 (T001) <- no task prerequisite.
- C-009 (T002) <- F-003, F-004.
- C-002 (T003) <- C-001, C-009, F-014.
- C-010 (T004) <- D-003.
- C-003 (T005) <- C-002.
- C-004 (T006) <- C-003.
- C-005 (T007) <- C-004.
- C-006 (T008) <- C-005.
- C-007 (T009) <- C-006.
- C-008 (T010) <- C-007, C-010.

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
