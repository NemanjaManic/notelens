# Tasks: Python RAG

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: A. **Status**: executable backlog proposal; no business task is complete.
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

- [ ] T001 A-001: Audit permitted corpus sources and prepare snapshot acquisition/provenance in `data/knowledge/**`, `docs/rag/sources.md`
  - **Owner / story**: A / US1.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Review English Health Topic fields/reuse and attribution, then acquire only authorized content; record actual snapshot/checksums and measured topic counts. No outbound crawling.
  - **Verify**: `python -B -m json.tool data/knowledge/manifests/snapshot.json`.
  - **Coverage**: FR-001, FR-002, FR-003, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Foundational prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T002 A-010: Review RAG boundary proposals and local mock consumer checks in `services/rag/tests/test_contract.py`, `docs/rag/interface-review.md`, `specs/001-rag/contracts/**`
  - **Owner / story**: A / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Acceptance**: Propose any changes to B rather than edit contracts; consume frozen generated bindings and distinguish mode=mock/live and transport error from insufficient evidence.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_contract.py`.
  - **Coverage**: FR-006, FR-016, SC-001, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T003 [US1] A-002: Implement English XML parsing, cleaning and stable attributed passages in `services/rag/src/notelens_rag/ingestion.py`, `services/rag/tests/test_ingestion.py`, `data/knowledge/**`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T001 (A-001); 001-rag/T002 (A-010); 000-foundation/T014 (F-014)
  - **Acceptance**: Select summaries/metadata only, preserve IDs/URLs/synonyms/snapshot, and test deterministic chunks plus excluded licensed/outbound content.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_ingestion.py`.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T004 [US1] A-003: Implement embedding/store adapters, versioned index ingestion and cache boundaries in `services/rag/src/notelens_rag/adapters/**`, `services/rag/tests/test_index_version.py`, `data/knowledge/**`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T003 (A-002)
  - **Acceptance**: Batch/cache only permitted corpus data. Model/dimensions/preprocessing changes force a new index; mock tests never call providers; live indexing awaits approved model/budget.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_index_version.py`.
  - **Coverage**: FR-004, FR-018, FR-019.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T005 [US1] A-004: Expose an embedding-only retrieval baseline with valid source records in `services/rag/src/notelens_rag/retrieval.py`, `services/rag/src/notelens_rag/main.py`, `services/rag/tests/test_retrieval.py`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T004 (A-003)
  - **Acceptance**: POST /v1/retrieve returns versioned ranked passages with sufficient/insufficient/error state and score limitations. Use development-selected thresholds; no hard specialty filter.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_retrieval.py tests/test_contract.py`.
  - **Coverage**: FR-005, FR-006, FR-009, SC-001.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T006 [US1] A-009: Generate literature-grounded English answers inside Python in `services/rag/src/notelens_rag/answers.py`, `services/rag/prompts/**`, `services/rag/tests/test_answers.py`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T005 (A-004)
  - **Acceptance**: POST /v1/literature-answer validates claims/citations and explicitly requests English; insufficient, injection and unsupported-language fixtures cannot fabricate patient facts or treatment. Live generation is separately gated.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_answers.py`.
  - **Coverage**: FR-007, FR-008, FR-009, FR-010, FR-020, SC-001, SC-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 4: User Story 2

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T007 [US2] A-006: Use question/extracted concepts and soft specialty hints in `services/rag/src/notelens_rag/query.py`, `services/rag/tests/test_query_signals.py`
  - **Owner / story**: A / US2.
  - **Dependencies**: 001-rag/T005 (A-004)
  - **Acceptance**: ICD absent and wrong specialty cases still retrieve relevant topics; concepts are optional and do not change canonical documents.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_query_signals.py`.
  - **Coverage**: FR-005, FR-008.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T008 [US2] A-005: Compare a lexical/hybrid variant with the fixed baseline in `services/rag/src/notelens_rag/hybrid.py`, `services/rag/tests/test_hybrid.py`, `docs/rag/experiments/**`
  - **Owner / story**: A / US2.
  - **Dependencies**: 001-rag/T007 (A-006)
  - **Acceptance**: Use the same versioned development questions and report actual unique-topic/evidence metrics, costs and selection reason; reranking optional, final questions untouched.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_hybrid.py`.
  - **Coverage**: FR-013, FR-014, FR-015, SC-003.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T009 [US2] A-007: Submit single-/multi-source relevance proposals and separate personal annotations in `docs/rag/qa-proposals.json`, `eval/annotations/member-a/**`
  - **Owner / story**: A / US2.
  - **Dependencies**: 001-rag/T003 (A-002); 003-classification/T003 (C-002); 004-extraction-evaluation/T006 (D-003)
  - **Acceptance**: Preserve original references and actual supporting passages; record necessary topics per question, answerability and separate independent reviews. D adjudicates; no QA enters index.
  - **Verify**: `python -B -m json.tool docs/rag/qa-proposals.json`.
  - **Coverage**: FR-011, FR-012, FR-017.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 5: User Story 3

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [ ] T010 [US3] A-008: Measure retrieval rejection and failure behavior, deliver integration evidence in `services/rag/tests/test_failures.py`, `docs/rag/evaluation/**`, `docs/rag/integration.md`
  - **Owner / story**: A / US3.
  - **Dependencies**: 001-rag/T008 (A-005); 001-rag/T009 (A-007); 001-rag/T006 (A-009); 004-extraction-evaluation/T010 (D-007)
  - **Acceptance**: Report Recall@5/MRR/all-required-topics@5 over unique topics, single/multi portions, passage evidence, >5-topic flags and risk/coverage; supply provider-failure fixtures with no document-suppression instruction; B verifies full routing behavior.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_failures.py tests/test_answers.py tests/test_contract.py`.
  - **Coverage**: FR-006, FR-009, FR-010, FR-011, FR-013, FR-014, FR-016, FR-018, FR-020, SC-002, SC-003, SC-004, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 6: Polish and cross-cutting concerns

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T011 A-011: Freeze the selected RAG configuration and hand actual outputs to B/D in `docs/rag/**`, `services/rag/config/**`, `data/knowledge/manifests/**`
  - **Owner / story**: A / US3.
  - **Dependencies**: 001-rag/T010 (A-008)
  - **Acceptance**: Record corpus/model/prompt/index/question versions, actual final-run reason and approved limits; no final-test prompt tuning. Document API startup and remaining live limitations.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_contract.py tests/test_index_version.py`.
  - **Coverage**: FR-003, FR-004, FR-015, FR-016, FR-018, FR-019, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Dependencies & Execution Order

Follow explicit dependency edges, not checkbox proximity. A story phase can start when
its listed prerequisites are satisfied; do not serialize every story behind other stories
or all of D behind completed A/C. Public-source audit/guideline tasks can start early.
F-003 freezes interfaces; F-004 creates independent scaffolds; F-014 is the authorized
published shared base for distributed business implementation. A remote clone is not ready
before an actual foundation commit/push.

- A-001 (T001) <- no task prerequisite.
- A-010 (T002) <- F-003, F-004.
- A-002 (T003) <- A-001, A-010, F-014.
- A-003 (T004) <- A-002.
- A-004 (T005) <- A-003.
- A-009 (T006) <- A-004.
- A-006 (T007) <- A-004.
- A-005 (T008) <- A-006.
- A-007 (T009) <- A-002, C-002, D-003.
- A-008 (T010) <- A-005, A-007, A-009, D-007.
- A-011 (T011) <- A-008.

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
