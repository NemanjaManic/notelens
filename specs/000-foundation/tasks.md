# Tasks: Shared Foundation

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
Foundation F-001/F-002/F-008 and F-003/F-009 are checked, reflecting recorded
documentation/tooling, the user-confirmed contract freeze and generated-binding checks.
The runnable mock foundation and its publication remain incomplete. Writing plans/mocks does not close a business task.

## Path Conventions and Command Availability

All paths below are repository-relative and limited by the [ownership matrix](../../docs/team/allowed-paths.md).
Initial foundation scaffolding is the coordinator exception; afterward owners stay in scope.
Commands for unchecked tasks are **planned deliverables of the named tasks**, not existing
npm scripts or claims of current execution. F-008's contract command now exists in its own
B-owned tooling environment. Runtime commands remain unavailable until their prerequisites
create the dependencies and listed files; each command must actually pass before closure.
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

- [x] T001 F-001: Verify official integration and write the constitution draft in `.specify/**`, `.agents/skills/**`, `docs/team/preparation-status.md`
  - **Owner / story**: B / US1.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Spec Kit 1.3.3 provenance and actual resolver/check results recorded; constitution is explicitly unratified.
  - **Verify**: `uv --system-certs tool run --from 'git+https://github.com/github/spec-kit.git@v1.3.3' specify version`.
  - **Coverage**: FR-001, FR-019, FR-020.
  - **Done**: Executed tooling/documentation evidence exists; no human ratification or business implementation is implied.

- [x] T002 F-002: Record confirmed scope, ownership and five independent specifications in `AGENTS.md`, `docs/team/**`, `specs/**/spec.md`, `**/AGENTS.md`
  - **Owner / story**: B / US1.
  - **Dependencies**: 000-foundation/T001 (F-001)
  - **Acceptance**: English specs and most-specific ownership exceptions exist; 2026-11-24 deadline and Python boundaries preserved.
  - **Verify**: `python -B -c "from pathlib import Path; assert all((Path('specs')/p/'spec.md').is_file() for p in ['000-foundation','001-rag','002-platform','003-classification','004-extraction-evaluation'])"`.
  - **Coverage**: FR-002, FR-012, FR-019, FR-020.
  - **Done**: Executed tooling/documentation evidence exists; no human ratification or business implementation is implied.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [x] T003 F-008: Create representative positive/negative contract fixtures and validators in `contracts/v1/**`, `scripts/project/check_contracts.py`, `scripts/project/pyproject.toml`, `scripts/project/uv.lock`
  - **Owner / story**: B / US2.
  - **Dependencies**: 000-foundation/T002 (F-002)
  - **Acceptance**: Include invalid schema, wrong digest/quote, non-BMP UTF-16 mistakes, repeated spans, dangling citations, historical assertion/subject and source-only ICD negatives. Require 100% structural/span validity on the defined suite. The validator defines the later --require-freeze guard. Create a B-owned tooling environment with pinned validators; scripts resolve repo paths from their own file location.
  - **Verify**: `uv run --directory scripts/project python check_contracts.py`.
  - **Coverage**: FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-011, SC-003.
  - **Completion evidence (2026-11-11)**: [Tooling/workflow record](../../scripts/project/README.md): 90/90 fixture outcomes (38 positive, 52 negative), 29 regression tests passing, locked/offline execution. `--require-freeze` fails with FREEZE_PENDING as expected. No schema changes, owner agreement, HTTP/business-module checks, or live-provider/deployment requirement; F-003 and later tasks remain open.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [x] T004 F-003: Collect A/C/D feedback and record the reviewed contracts/v1 freeze in `contracts/v1/**`, `docs/decisions/contract-freeze.md`
  - **Owner / story**: B / US2.
  - **Dependencies**: 000-foundation/T003 (F-008)
  - **Acceptance**: B records all owner proposals/agreement, schema version, enums/canonicalization and fixture checks. Draft files alone do not satisfy this task.
  - **Verify**: `uv run --directory scripts/project python check_contracts.py --require-freeze`.
  - **Completion evidence (2026-11-13)**: [Owner freeze](../../docs/decisions/contract-freeze.md) records user-confirmed approvals for Nemanja (A), B, Sara (C), Milica (D) of p2-rc1 revision 3. Canonical metadata promotion preserves all approved definitions/operations. Actual checks: 155/155 fixture outcomes, 22/22 simulated exchanges and recorded digest/owner consistency. No runnable foundation or publication completion is implied.
  - **Coverage**: FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-016.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [x] T005 F-009: Generate shared Python and TypeScript bindings from the one schema in `contracts/generated/**`, `scripts/project/generate_contracts.py`, `contracts/v1/**`
  - **Owner / story**: B / US2.
  - **Dependencies**: 000-foundation/T004 (F-003)
  - **Acceptance**: Regeneration produces no diff; both languages validate the same fixtures; no competing handwritten schema.
  - **Verify**: `uv run --directory scripts/project python generate_contracts.py --check`.
  - **Completion evidence (2026-11-13)**: [Generated binding guide](../../contracts/generated/README.md): reproducible Python/TypeScript packages for all 29 definitions; each runtime passed the same 153/153 wire payloads and 22/22 correlation cases, native non-finite/strict-JSON checks; installed imports, TypeScript consumer compile and Python wheel build passed. Canonical suite: 57 tests. Two schema/API-tooling cases stay in the 155-case canonical checker. No HTTP/model/web-framework build or F-014 claim.
  - **Coverage**: FR-003, FR-004, FR-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T006 [US1] F-004: Scaffold the web workspace and three independent Python mock services in `apps/web/**`, `services/rag/**`, `services/classifier/**`, `services/extraction/**`, `package.json`, `package-lock.json`, `.env.example`, `scripts/project/check_scaffold.py`, `.gitignore`, `.gitattributes`
  - **Owner / story**: B / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T005 (F-009)
  - **Acceptance**: Create independent service pyproject/uv.lock and src/notelens_<service>/main.py, pytest dependencies, npm web workspace, lazy mock adapters and key-free configuration; verify actual installs/build compatibility. Ignore secrets/raw data/indexes/local state; define stable UTF-8/LF text handling without repository-wide reformatting.
  - **Verify**: `uv run --directory scripts/project python check_scaffold.py`.
  - **Coverage**: FR-010, FR-011, FR-017, SC-001.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T007 [US1] F-011: Add service health/readiness and safe mock failure records in `services/rag/**`, `services/classifier/**`, `services/extraction/**`, `scripts/project/check_health.py`
  - **Owner / story**: B / US1.
  - **Dependencies**: 000-foundation/T006 (F-004)
  - **Acceptance**: All three stubs expose health with explicit mode=mock and valid errors for timeout/rate/outage/validation; no model downloads or paid calls.
  - **Verify**: `uv run --directory scripts/project python check_health.py --mode mock`.
  - **Coverage**: FR-010, FR-011.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T008 [US2] F-012: Verify cross-language canonicalization and evidence examples in `contracts/v1/**`, `contracts/generated/**`, `apps/web/tests/canonical-text.test.ts`, `scripts/project/check_unicode.py`
  - **Owner / story**: B / US2.
  - **Dependencies**: 000-foundation/T006 (F-004); 000-foundation/T003 (F-008)
  - **Acceptance**: Executable Python/TypeScript examples cover exact UTF-8 hash, [start,end) code points, emoji and second repeated passage; invalid UTF-16 offsets fail.
  - **Verify**: `uv run --directory scripts/project python check_unicode.py`.
  - **Coverage**: FR-005, FR-006, FR-007, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T009 [US2] F-005: Create local startup and the English mock input-to-answer smoke path in `scripts/project/start_mock.py`, `scripts/project/smoke_mock.py`, `apps/web/**`
  - **Owner / story**: B / US2.
  - **Dependencies**: 000-foundation/T006 (F-004); 000-foundation/T007 (F-011); 000-foundation/T008 (F-012)
  - **Acceptance**: Actual documented startup launches only owned processes with clean shutdown; UI labels mock outputs and preserves document/literature/mixed/none provenance and insufficient states.
  - **Verify**: `uv run --directory scripts/project python smoke_mock.py`.
  - **Coverage**: FR-009, FR-010, FR-011, FR-017, SC-004.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T010 [US3] F-010: Prepare review routing, declared scope and key-free CI checks in `.github/**`, `scripts/project/check_scope.py`, `docs/team/**`
  - **Owner / story**: B / US3.
  - **Dependencies**: 000-foundation/T006 (F-004)
  - **Acceptance**: CODEOWNERS has no fictional handles and explains branch protection; scope checks honor member exceptions. Secret/dependency/contract/smoke checks exist; live CI disabled.
  - **Verify**: `uv run --directory scripts/project python check_scope.py --self-test`.
  - **Coverage**: FR-012, FR-020, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T011 [US3] F-006: Complete and verify five backlogs plus four handoffs/start prompts in `specs/**`, `docs/team/**`, `scripts/project/check_handoffs.py`
  - **Owner / story**: B / US3.
  - **Dependencies**: 000-foundation/T009 (F-005); 000-foundation/T010 (F-010)
  - **Acceptance**: Each owner has first-five task sequence, inputs/outputs, mock example, boundaries, actual startup/check commands and correct feature activation. Cross-feature aliases resolve; mocks do not close business tasks.
  - **Verify**: `uv run --directory scripts/project python check_handoffs.py`.
  - **Coverage**: FR-002, FR-013, FR-014, FR-015, FR-018, SC-001, SC-002.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T012 [US3] F-013: Review constitution and foundation acceptance without self-approval in `docs/decisions/**`, `docs/team/**`, `.specify/memory/constitution.md`, `scripts/project/check_handoffs.py`
  - **Owner / story**: B / US3.
  - **Dependencies**: 000-foundation/T011 (F-006)
  - **Acceptance**: Request and record actual user/team acceptance or exceptions; fill ratification only after review and remove temporary sync report before an authorized commit.
  - **Verify**: `uv run --directory scripts/project python check_handoffs.py --require-reviewed-foundation`.
  - **Coverage**: FR-016, FR-018, FR-020, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T013 [US3] F-007: Record the checked foundation inventory and isolated-working-copy procedure in `docs/team/foundation-checkpoint.md`, `docs/team/working-copies.md`, `scripts/project/check_checkpoint.py`
  - **Owner / story**: B / US3.
  - **Dependencies**: 000-foundation/T012 (F-013)
  - **Acceptance**: Bash/PowerShell commands use actual remote and explicit feature context. If no commit authorization exists, record prepared files and exact next command, never a fictional hash.
  - **Verify**: `uv run --directory scripts/project python check_checkpoint.py`.
  - **Coverage**: FR-013, FR-014, FR-018, SC-005, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T014 F-014: Publish the reviewed foundation base only after separate commit/push authorization in `docs/team/foundation-checkpoint.md`, `.git (authorized Git operations only)`
  - **Owner / story**: B / US3.
  - **Dependencies**: 000-foundation/T013 (F-007)
  - **Acceptance**: After explicit authorization, actual commit/push succeeds and the shared base is recorded. Until then remote cloning is not reported ready; no business module is committed as completed.
  - **Verify**: `git -c 'safe.directory=C:/Nemanja/AI Bootcamp 2026/notelens' log -1 --format=%H`.
  - **Coverage**: FR-013, FR-018, FR-020, SC-001, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- F-001 (T001) <- no task prerequisite.
- F-002 (T002) <- F-001.
- F-008 (T003) <- F-002.
- F-003 (T004) <- F-008.
- F-009 (T005) <- F-003.
- F-004 (T006) <- F-003, F-009.
- F-011 (T007) <- F-004.
- F-012 (T008) <- F-004, F-008.
- F-005 (T009) <- F-004, F-011, F-012.
- F-010 (T010) <- F-004.
- F-006 (T011) <- F-005, F-010.
- F-013 (T012) <- F-006.
- F-007 (T013) <- F-013.
- F-014 (T014) <- F-007.

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
