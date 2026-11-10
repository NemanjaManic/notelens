# Tasks: Complete Frontend and Integration

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: B. **Status**: executable backlog proposal; no business task is complete.
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
Only foundation F-001/F-002 are checked, because their actual documentation/tooling work
was completed and recorded. Writing plans/mocks does not close a business task.

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

- [ ] T001 B-010: Review shared-record proposals and establish the web mock consumer suite in `apps/web/tests/contracts.test.ts`, `docs/platform/interface-review.md`
  - **Owner / story**: B / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Consume generated bindings without reimplementing Python algorithms; malformed/mismatched results fail visibly; all test outputs are synthetic mocks.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/contracts.test.ts`.
  - **Coverage**: FR-014, FR-015.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T002 B-004: Implement approved memory lifetime, session ownership and guarded configuration in `apps/web/src/lib/sessions/**`, `apps/web/src/lib/config/**`, `apps/web/tests/session-isolation.test.ts`, `apps/web/tests/retention.test.ts`, `docs/platform/configuration.md`, `apps/web/tests/configuration.test.ts`
  - **Owner / story**: B / US3.
  - **Dependencies**: 002-platform/T001 (B-010); 000-foundation/T014 (F-014)
  - **Acceptance**: Document-bound content stays only in process memory for <=60 minutes, cleared on expiry/restart; fake-clock/two-session tests pass. Ask for remaining history/rate/retry/timeout limits; unconfigured live mode fails closed.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/session-isolation.test.ts tests/retention.test.ts tests/configuration.test.ts`.
  - **Coverage**: FR-011, FR-016, FR-017, FR-023, SC-002, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T003 [US1] B-001: Implement built-in/text/PDF input and canonical preparation in `apps/web/src/app/**`, `apps/web/src/lib/documents/**`, `apps/web/tests/canonical-text.test.ts`, `apps/web/tests/uploads.test.ts`
  - **Owner / story**: B / US1.
  - **Dependencies**: 002-platform/T001 (B-010); 000-foundation/T014 (F-014); 002-platform/T002 (B-004)
  - **Acceptance**: At most 2,097,152 PDF bytes and 100,000 code points; reject excess/scanned/unsupported language, never truncate. One nfc-lf-v1 preparation/hash; in-memory parsing only.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/canonical-text.test.ts tests/uploads.test.ts`.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, FR-012, SC-001, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T004 [US1] B-002: Build complete English report panels and exact evidence highlighting in `apps/web/src/components/**`, `apps/web/tests/report-view.test.tsx`
  - **Owner / story**: B / US1.
  - **Dependencies**: 002-platform/T001 (B-010); 000-foundation/T014 (F-014); 002-platform/T002 (B-004)
  - **Acceptance**: Document, specialty uncertainty, entities/assertion/temporality/subject, summary and sources work from mocks; emoji/repeated spans and all loading/empty/error states are covered.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/report-view.test.tsx`.
  - **Coverage**: FR-001, FR-005, FR-006, FR-007, FR-012, FR-013, SC-001, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T005 [US2] B-003: Implement thin service clients, source-preserving routing and bounded state in `apps/web/src/lib/clients/**`, `apps/web/src/lib/routing/**`, `apps/web/tests/routing.test.ts`
  - **Owner / story**: B / US2.
  - **Dependencies**: 002-platform/T003 (B-001); 002-platform/T004 (B-002)
  - **Acceptance**: Document/literature/mixed/none routes call D/A as agreed, namespace claim/source IDs, reject stale hashes and retain supported portions under partial failures; no TypeScript RAG or generation.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/routing.test.ts`.
  - **Coverage**: FR-008, FR-009, FR-010, FR-011, FR-014, FR-015, SC-001, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T006 [US3] B-011: Complete B's assigned primary annotations and independent reviews in `eval/annotations/member-b/**`
  - **Owner / story**: B / US3.
  - **Dependencies**: 004-extraction-evaluation/T006 (D-003)
  - **Acceptance**: Use frozen assignment IDs, separate files for review and primary work, exact spans/status/subject; D adjudicates. No clinically validated claim.
  - **Verify**: `python -B -m json.tool eval/annotations/member-b/submission-manifest.json`.
  - **Coverage**: Constitution VII; source prompt sections 7D and 8 (all-member annotation obligation)..
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T007 [US3] B-008: Test and harden injection, uploads, XSS, secrets/logs and abuse boundaries in `apps/web/tests/security/**`, `apps/web/src/lib/security/**`, `docs/platform/security.md`
  - **Owner / story**: B / US3.
  - **Dependencies**: 002-platform/T003 (B-001); 002-platform/T005 (B-003); 002-platform/T002 (B-004)
  - **Acceptance**: Finite defined suite covers source/retrieved instructions, unsafe markup, oversized bodies, other-session/expired IDs and no document/secret logging. No arbitrary browsing; approved fetching requires allowlist/SSRF protection.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/security`.
  - **Coverage**: FR-003, FR-011, FR-012, FR-016, FR-018, FR-019, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: User Story 4

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T008 [US4] B-006: Add deterministic integration CI and review/scope checks in `.github/**`, `scripts/project/**`, `docs/platform/ci.md`
  - **Owner / story**: B / US4.
  - **Dependencies**: 000-foundation/T010 (F-010); 002-platform/T007 (B-008)
  - **Acceptance**: Contracts, secrets/dependencies, declared path ownership and mock smoke checks run without keys; paid/live workflows are disabled unless explicitly triggered.
  - **Verify**: `uv run --directory scripts/project python check_scope.py --self-test`.
  - **Coverage**: FR-014, FR-017, FR-018, FR-021, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T009 [US4] B-005: Replace each module mock through separate contract-tested integrations in `apps/web/src/lib/clients/**`, `apps/web/tests/integration/**`, `docs/platform/integration-status.md`
  - **Owner / story**: B / US4.
  - **Dependencies**: 002-platform/T005 (B-003); 002-platform/T002 (B-004); 001-rag/T010 (A-008); 003-classification/T009 (C-007); 004-extraction-evaluation/T004 (D-005)
  - **Acceptance**: Three separate changes connect passing real module interfaces; remaining mocks stay labeled. Run actual transport checks, not just direct mocked objects.
  - **Verify**: `npm exec --workspace apps/web -- vitest run tests/integration`.
  - **Coverage**: FR-008, FR-009, FR-010, FR-014, FR-015, SC-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T010 [US4] B-007: Finalize an approved hosting/runbook arrangement and rehearse deployment in `infra/**`, `docs/platform/deployment.md`, `scripts/project/check_readiness.py`
  - **Owner / story**: B / US4.
  - **Dependencies**: 002-platform/T009 (B-005); 002-platform/T008 (B-006)
  - **Acceptance**: Obtain host/account/cost approval before deployment; verify TLS, service auth, readiness, public-corpus persistence and in-memory document behavior. Record real URLs only after deployment; no universal serverless persistence assumption.
  - **Verify**: `uv run --directory scripts/project python check_readiness.py`.
  - **Coverage**: FR-016, FR-017, FR-020, FR-022, FR-023, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 7: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T011 B-009: Finish English acceptance, attribution, notices and complete demo rehearsal in `apps/web/**`, `docs/platform/demo.md`
  - **Owner / story**: B / US4.
  - **Dependencies**: 002-platform/T009 (B-005); 002-platform/T007 (B-008)
  - **Acceptance**: Review every visible state and generation surface in English, source attribution and all three notices; full input-to-answer rehearsal passes. Deployment/live claims require actual evidence.
  - **Verify**: `npm exec --workspace apps/web -- playwright test`.
  - **Coverage**: FR-001, FR-005, FR-006, FR-007, FR-012, FR-013, FR-020, FR-024, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- B-010 (T001) <- F-003, F-004.
- B-004 (T002) <- B-010, F-014.
- B-001 (T003) <- B-010, F-014, B-004.
- B-002 (T004) <- B-010, F-014, B-004.
- B-003 (T005) <- B-001, B-002.
- B-011 (T006) <- D-003.
- B-008 (T007) <- B-001, B-003, B-004.
- B-006 (T008) <- F-010, B-008.
- B-005 (T009) <- B-003, B-004, A-008, C-007, D-005.
- B-007 (T010) <- B-005, B-006.
- B-009 (T011) <- B-005, B-008.

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
