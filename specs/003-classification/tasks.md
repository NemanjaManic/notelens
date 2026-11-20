# Tasks: Python Classification

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: C. **Status**: C-001 and C-009 complete locally; C-011 local F-004 scaffold contribution checked. F-014 is published. C-002 is complete and D received the permitted validation metadata.
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
[start,end) interval with an exact canonical quote; frozen assertion is confirmed|suspected|negated|unknown,
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

- [x] T002 C-009: Review classifier contracts and build standalone mock consumer checks in `services/classifier/tests/test_contract.py`, `docs/ml/interface-review.md`
  - **Owner / story**: C / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Verify category/null states, score kind/meaning and model version against generated bindings; propose changes through B, not shared edits.
  - **Review progress (2026-11-15)**: Shared candidate `8282a739727f3c696be8b63d5c1c13ea13ae81fc` reviewed in an isolated worktree. Python 3.13.7 installed; unchanged-source checks passed. First coordinated attempt passed contracts, 80 B tests and 319 RAG tests, then reported 50 classifier passes and a startup timeout; the focused transport retry passed. Second full attempt exceeded the shared unit-suite's 240-second deadline. No successful shared receipt exists. [F-004 review](../../docs/ml/member-c-f004-review.md) records supplementary 3.11 checks, both 3.13 attempts and remaining checks; C-009 is not complete.
  - **Review update (2026-11-16)**: The unchanged shared F-004 candidate passed the complete coordinated runner and current-checkout checker on Python 3.13.7: 80 project tests, 319/51/59 service tests and 30 HTTP cases; previous timeout history is retained in the [review](../../docs/ml/member-c-f004-review.md). B must record F-004 completion; C-009 remains open.
  - **Completion evidence (2026-11-16)**: B recorded F-004 technical completion in `f4173b8` on `member-b/task-f-004-web-workspace`; user authorized C-009. [Interface review](../../docs/ml/interface-review.md) records frozen contract behavior and limits. Python 3.13.7 locked offline checks: 24 contract tests, 61 classifier tests, 153 binding payload and 22 simulated exchange outcomes passed; no live provider or trained model involved.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_contract.py`.
  - **Coverage**: FR-012, FR-013, FR-014, FR-015, FR-016, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [X] T003 [US2] C-002: Group duplicates/conflicting labels and freeze seeded split manifests in `data/mtsamples/**`, `services/classifier/tests/test_splits.py`, `docs/ml/splits.md`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T001 (C-001); 003-classification/T002 (C-009); 000-foundation/T014 (F-014)
  - **Authorized draft (2026-11-16)**: Sara authorized C-002 preparation ahead of F-014, with final manifest freeze and downstream handoff deferred for review. [Draft evidence](../../docs/ml/splits.md) records screening and illustrative splits; thresholds, adjudication, canonical text/access and exposure controls remain unresolved. C-002 stays unchecked.
  - **Local update (2026-11-19)**: Audit and draft byte checks passed. Development loading rejects repeated source IDs across partitions. The approved group and split freeze is still pending.
  - **Review preparation (2026-11-19)**: [Local review queue and exposure ledger](../../docs/ml/splits.md#prepared-local-review-queue-2026-11-19) record three pending pairs and 1,045 development groups. Actual review and freeze remain pending.
  - **Review decision preview (2026-11-19)**: [Local reconciliation](../../docs/ml/splits.md#review-decision-preview-2026-11-19) validates the review records, propagates development exposure across confirmed duplicate components, and flags exposed or conflicting groups. The actual preview reconciled 860 training, 185 validation, 183 draft test and 101 unassigned documents with all three pair decisions pending.
  - **Review intake and handoffs (2026-11-19)**: The local commands record development reservations and reviewed pair decisions in new validated copies. [B's request](../../docs/ml/c002-handoff-to-b.md) covers access, canonical text and F-014. [D's note](../../docs/ml/c002-handoff-to-d.md) covers the future reviewed metadata handoff and development-only assignments.
  - **D confirmation (2026-11-19)**: The [handoff record](../../docs/ml/c002-handoff-to-d.md#ds-confirmation-2026-11-19) records agreed candidate metadata and review exposure requirements. Local intake records versioned reservations and actual access separately. The preview reports membership changes for confirmed merges. The submission ID mapping and access approvals are pending.
  - **B confirmation (2026-11-19)**: [B's response](../../docs/ml/c002-handoff-to-b.md#bs-confirmation-2026-11-19) confirms `nfc-lf-v1` and C's provenance ownership. All three pairs stay quarantined while access, reviewers, dataset preparation and restricted mapping storage are agreed. Verified `main` at `1ac8bfe` records F-011 complete and F-014 open.
  - **D-002 intake request (2026-11-19)**: D requested the reviewed, versioned manifest, explicit annotation permissions, quarantine and restriction flags, and the authorized route to canonical documents. The [handoff record](../../docs/ml/c002-handoff-to-d.md#d-002-intake-request-2026-11-19) separates this pending data handoff from the published D reconciliation branch.
  - **D identity and access confirmation (2026-11-20)**: D confirmed the stable dataset `doc_id` and needs the complete evaluation mapping. The [handoff convention](../../docs/ml/c002-handoff-to-d.md#assignment-identifiers-and-access-2026-11-20) specifies per-assignment access and delivery by a restricted link once the manifest and location are approved.
  - **B review authorization and preparation (2026-11-20)**: B approved Sara as sole reviewer of the three pairs in the checksum-verified C-001 copy. [Canonical preparation](../../docs/ml/splits.md#authorized-review-and-canonical-preparation) records the C-owned `nfc-lf-v1` entry point and seven passing F-012 preparation vectors from `1ac8bfe`. Pair decisions and F-014 remain pending.
  - **Published foundation baseline (2026-11-20)**: The `f-014-foundation` tag resolves to `7eb12e56f33240a428f916ba583b9e00077712df`. C-002 remains open pending the pair decisions, review sign-off and split freeze. [D handoff](../../docs/ml/c002-handoff-to-d.md#published-foundation-baseline-2026-11-20).
  - **Local freeze (2026-11-20)**: Sara confirmed two duplicate pairs and one unresolved pair reserved for quarantine. `c002-split-v1` has 864 training, 185 validation and 183 test documents. Prior test membership is preserved. Byte reproduction, group and document separation, and all five specialties per partition were verified.
  - **Restricted development handoff (2026-11-20)**: The permitted package `c002-d002-development-v1` contains 185 validation candidates. Manifest membership, checksum and the D selector at `97bf35a` were checked. Sara reported that Milica received the manifest and checksum. [D package status](../../docs/ml/c002-handoff-to-d.md#development-metadata-package-2026-11-20).
  - **Closure (2026-11-20)**: The temporary draft mapping was deleted and the explicit source-row column was removed from the generated C-001 inspection subset. The audited source checksum and frozen partition checksums were verified. [Cleanup and verification](../../docs/ml/splits.md#post-sign-off-mapping-cleanup-2026-11-20).
  - **Acceptance**: Document exact/near-duplicate criteria, audit-derived feasible proportions/seed and conflict exclusions before splitting; no group overlap. Publish stable IDs early for D.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_splits.py`.
  - **Coverage**: FR-005, FR-006, FR-007, FR-008, FR-017, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T004 [US2] C-010: Complete C's development-only primary annotations and independent reviews in `eval/annotations/member-c/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003)
  - **Local update (2026-11-19)**: [Assignment intake and exposure steps](../../docs/ml/integration.md#b-and-d-handoff) are ready for D-003. Actual assignments and submissions are pending.
  - **D confirmation (2026-11-19)**: D confirmed that C's primary and independent review assignments will be separate and development-only, with independent reviews of other annotators' work. Assignment selection waits for the reviewed manifest and approved access.
  - **Assignment convention (2026-11-20)**: Primary and independent review records share the dataset `doc_id`, D-issued `assignment_id` and canonical text digest. Each submission has a unique `submission_id`. D issues assignment IDs when assignments are frozen.
  - **Selector publication (2026-11-20)**: D published `97bf35a` with a synthetic-verified development-only independent review reservation when capacity permits. The [handoff record](../../docs/ml/c002-handoff-to-d.md#published-selector-and-evaluator-update-2026-11-20) records the candidate interface and pending real selection.
  - **Acceptance**: Before model selection C annotates development documents only; preserve separate submissions and leave final-reference decisions to D. Do not use annotation exposure as test-set feedback.
  - **Verify**: `python -B -m json.tool eval/annotations/member-c/submission-manifest.json`.
  - **Coverage**: FR-018.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [X] T005 [US2] C-003: Train majority and TF-IDF plus Logistic Regression baselines in `services/classifier/src/notelens_classifier/training/**`, `services/classifier/tests/test_training_leakage.py`, `docs/ml/experiments/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T003 (C-002)
  - **Exploratory run (2026-11-16)**: At Sara's explicit request, one local majority/TF-IDF Logistic Regression run used provisional draft train/validation groups before the C-002 freeze. [Development report](../../docs/ml/experiments/draft-baseline-v1.md) records actual results, hashes, safeguards and limitations. No test split was scored or model selected; C-003 remains unchecked pending its frozen C-002 prerequisite.
  - **Local update (2026-11-19)**: Majority and Logistic Regression were reproduced on the provisional 860/185 training and validation cohorts. [Updated validation report](../../docs/ml/validation-report.md) records the comparison and provenance.
  - **Local completion (2026-11-20)**: The frozen C-002 split supplied 864 training and 185 validation documents. Majority macro-F1 was 0.0917 and TF-IDF + Logistic Regression macro-F1 was 0.9285. All exported rows match the permitted C-002 validation handoff. [D-006 handoff report](../../docs/ml/c003-handoff-to-d.md) records the export and pending restricted delivery.
  - **Acceptance**: All fitted transformations use train only; no label-revealing metadata. Record real validation support/metrics and reproducibility, never final-test selection.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_training_leakage.py`.
  - **Coverage**: FR-008, FR-009, FR-010, FR-011, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [X] T006 [US2] C-004: Run a controlled XGBoost validation comparison in `services/classifier/src/notelens_classifier/training/**`, `services/classifier/tests/test_comparison.py`, `docs/ml/experiments/**`
  - **Owner / story**: C / US2.
  - **Dependencies**: 003-classification/T005 (C-003)
  - **Local update (2026-11-19)**: Same-feature CPU XGBoost comparison ran locally. Logistic Regression led by 0.0486 validation macro-F1 on the provisional split.
  - **Local completion (2026-11-20)**: Both estimators used the same train-fitted TF-IDF matrix on the frozen 864/185 cohort. Logistic Regression reproduced C-003 and led XGBoost 0.9285 to 0.8750 in validation macro-F1. The [comparison report](../../docs/ml/experiments/c004-frozen-comparison-v1.md) records class support, per-class metrics, confusion matrices and the selection for C-005. The final test remained locked.
  - **Acceptance**: Use the same split/features/comparison controls; retain better simpler baseline if appropriate. Optional embedding variants do not block core; no benchmark manipulation.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_comparison.py`.
  - **Coverage**: FR-009, FR-010, FR-011, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [X] T007 [US1] C-005: Select uncertainty policy and report model/error/confidence limits in `services/classifier/config/**`, `services/classifier/tests/test_uncertainty.py`, `docs/ml/validation-report.md`
  - **Owner / story**: C / US1.
  - **Dependencies**: 003-classification/T006 (C-004)
  - **Local update (2026-11-19)**: Provisional Logistic Regression threshold and refusal behavior were measured on validation. The [report](../../docs/ml/validation-report.md) records classwise rejection and false acceptance of unrelated synthetic inputs.
  - **Local improvement (2026-11-19)**: Balanced features and training-only short windows improved the local candidate. The [comparison](../../docs/ml/experiments/short-text-improvement-v1.md) records the rerun, fixed follow-up suite and remaining ambiguity limitation.
  - **Ambiguity policy (2026-11-19)**: The [local comparison](../../docs/ml/experiments/ambiguity-policy-v1.md) documents section disagreement, word evidence, fewer mixed-text acceptances and the clear-case coverage cost.
  - **Lexical evidence comparison (2026-11-19)**: [Local checks](../../docs/ml/experiments/lexical-evidence-v1.md) compared single-word, multiword and phrase evidence. The current policy stays selected after the fixed new-case comparison.
  - **Local completion (2026-11-20)**: Selected the two-word evidence policy for the C-004 Logistic Regression artifact on the frozen 185-document validation set and 128 synthetic development cases. The [C-005 report](../../docs/ml/validation-report.md#c-005-uncertainty-selection-on-the-frozen-split-2026-11-20) records abstention tradeoffs, the separate 50-case follow-up, calibration limits and pending promotion review. Final test remained locked.
  - **Acceptance**: Choose thresholds on validation, report macro/per-class metrics/confusion/support/errors and score calibration/OOD limits. Do not claim universal unsupported detection or clinical certainty.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_uncertainty.py`.
  - **Coverage**: FR-010, FR-011, FR-012, FR-014, FR-015, FR-020, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [X] T008 [US3] C-006: Package full deterministic inference and its FastAPI operation in `services/classifier/src/notelens_classifier/**`, `services/classifier/tests/test_inference.py`, `services/classifier/tests/test_contract.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T007 (C-005)
  - **Local update (2026-11-19)**: A trusted development artifact starts explicitly on authenticated loopback and returns frozen-contract performed classification. Both supported and uncertain outputs were verified.
  - **Local completion (2026-11-20)**: The separately installed classifier wheel loaded the pinned C-005 artifact, validated the fitted estimator and label mapping, and passed 11 real loopback HTTP probes and two rejected startup cases. The classifier and MTSamples suites passed 158 tests and 11 subtests. [Package verification](../../docs/ml/integration.md#c-006-package-verification).
  - **Acceptance**: POST /v1/classify uses frozen training-fitted preprocessing/label mapping/model version; result binds doc_id/hash, conforms to contracts and safely handles missing artifacts/errors. ONNX not required.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_inference.py tests/test_contract.py`.
  - **Coverage**: FR-013, FR-014, FR-015, FR-016, SC-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T009 [US3] C-007: Deliver actual startup and contract/smoke integration evidence to B/D in `docs/ml/integration.md`, `services/classifier/tests/test_http.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T008 (C-006)
  - **Local update (2026-11-19)**: [Startup instructions and owner-local HTTP evidence](../../docs/ml/integration.md) are ready. Coordinated integration with the reviewed artifact is pending.
  - **Acceptance**: B/D can run the independent service and validate HTTP payloads with permitted examples; mocks versus real-model outputs are distinguished.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_http.py tests/test_contract.py`.
  - **Coverage**: FR-013, FR-016, FR-017, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T010 C-008: Freeze the chosen model and run the locked final measurement/model card in `docs/ml/model-card.md`, `services/classifier/artifacts/manifests/**`, `services/classifier/tests/test_final_freeze.py`
  - **Owner / story**: C / US3.
  - **Dependencies**: 003-classification/T009 (C-007); 003-classification/T004 (C-010)
  - **Local update (2026-11-19)**: Final measurement guards and scoring were exercised on a synthetic held-out package. The [model card draft](../../docs/ml/model-card.md) records the required freeze and final evidence.
  - **Acceptance**: Record actual final results/versions/counts, baseline comparisons and limitations after selection freeze. A repeated final run requires new version/reason; supplementary distributions are reported separately.
  - **Verify**: `uv run --directory services/classifier python -m pytest tests/test_final_freeze.py`.
  - **Coverage**: FR-010, FR-011, FR-019, FR-020, FR-021, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Approved Foundation Contribution (2026-11-14)

The user authorized continuing from the published F-003/F-009 handoff. This bounded
owner contribution is appended to preserve the existing task IDs. It is part of shared
F-004, not a replacement for C-009 or permission to mark the whole foundation complete.

- [x] T011 C-011: Deliver C's local F-004 classifier mock scaffold in `services/classifier/**`, with owner evidence in `docs/ml/classifier-scaffold-handoff.md`
  - **Owner / story**: C / US1 and US3 scaffold contribution; B coordinates shared F-004.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T005 (F-009); published classifier brief and user authorization to continue within C's scope.
  - **Acceptance**: Independent manifest/lock and installed frozen TypedDict/validator package; supported/uncertain/unsupported deterministic mocks with actual input identity; five ordered finite scores or honest skipped metadata; strict JSON/document validation; safe errors and business request correlation; local-only key-free launcher and no document storage/logging. F-011 health remains behind the shared F-004 checkpoint.
  - **Verify**: `uv run --locked --offline --directory services/classifier python -B -m pytest -q`; see the service README for the verified local uv executable.
  - **Evidence (2026-11-14)**: 51 tests passed, including an actual loopback Uvicorn HTTP smoke and process cleanup. Installed Python contracts passed 153 payload/22 simulated exchange cases. [Handoff](../../docs/ml/classifier-scaffold-handoff.md) records versions, actual workflow, commands and limitations.
  - **Coverage**: FR-012, FR-014, FR-015, FR-016; scaffold support for SC-004/SC-005, not completion of real inference.
  - **Done**: Local mock contribution checked; shared integration and human/team acceptance remain pending. No trained model, live inference, F-004/F-011/C-009/F-014 completion or publication is implied.

- [x] T012 C-012: Contribute classifier health and mock failure behavior to shared F-011 in `services/classifier/**`, with owner handoff in `docs/ml/f011-classifier-handoff.md`
  - **Owner / story**: C / US1 and US3 scaffold contribution; B coordinates shared F-011.
  - **Dependencies**: F-004 technical completion and the frozen v1.0.0 contract; the failure seam and retryability require agreement with B before dependent shared probes.
  - **Progress (2026-11-17)**: Local liveness/readiness, not-ready and health authentication are implemented; 95 classifier tests and installed binding checks passed. Actual loopback tests cover both health states, authenticated denial and duplicate headers, business behavior and owned-process cleanup. See the [handoff](../../docs/ml/f011-classifier-handoff.md). This is not shared F-011 completion or publication.
  - **Interim publication (2026-11-19)**: The classifier subtree on `main` at `7aa6c32` matches C's published health commit `49c8418`. The [resume handoff](../../docs/ml/f011-classifier-handoff.md#resume-handoff-2026-11-19) records 77 passing snapshot tests and the binding results. B's shared checker still needs to exercise the available classifier not-ready trigger. The three business failure scenarios await agreement with B.
  - **Owner-local implementation (2026-11-19)**: Sara approved local C-012 work. All three mock failure profiles are implemented and verified over loopback HTTP. The [C-012 handoff](../../docs/ml/f011-classifier-handoff.md#c-012-local-candidate-2026-11-19) records the configuration, results and isolated review patch.
  - **B confirmation (2026-11-19)**: B confirmed the failure configuration and retryability in the reply supplied by Sara, reported adding the three authenticated probes and verified the readiness profile. B requested the published C commit SHA for the coordinated run.
  - **Publication (2026-11-19)**: Sara authorized the five-file contribution. The remote branch `member-c/checkpoint-classifier-mock-failures` was verified at `4080f9b3c41a0dba70238929e765d9ce535910eb`. The isolated preflight passed 84 classifier tests and the installed binding checks.
  - **Closure (2026-11-19)**: B's verification plan supplied by Sara records all four scenarios and all 63 classifier HTTP cases passing against the exact published C commit. That all-service run recorded 209 passes, zero failures and two blocked readiness cases for RAG and extraction. A subsequent published run closed F-011 on `main` at `1ac8bfe`. See the [closure record](../../docs/ml/f011-classifier-handoff.md#b-verification-and-c-012-closure-2026-11-19).
  - **Verify**: `uv run --directory services/classifier python -B -m pytest -q` with the documented locked environment; run the actual owner HTTP tests and installed binding checker.
  - **Done**: Mock = owner-local health and agreed failure scenarios pass; module = B imports the exact contribution and validates the coordinated matrix; live = not executed and no real classifier/provider is implied.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- C-001 (T001) <- no task prerequisite.
- C-011 (T011) <- F-003, F-009, published owner brief and authorized package; contributes to F-004.
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
