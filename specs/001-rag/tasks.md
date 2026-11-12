# Tasks: Python RAG

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contract references](contracts/README.md).
**Owner**: A. **Status**: A-001 source acquisition/provenance and A-002 offline corpus
preparation are complete. The corpus has 401 topics and 617 checked candidate
passages. A-010 and all service/retrieval/evaluation tasks remain unchecked.
**Tests**: Required where the source specifications explicitly require structural, semantic,
leakage, security or independent module checks. This is not blanket TDD for documentation.
**Organization**: Setup, foundational, story increments, polish. Every task has one owner
and a story reference; setup/foundation/polish use metadata instead of a story label.
Standard IDs stay sequential; global aliases preserve the source seed names.

**Documentation handoff update (2026-11-10)**: The user approved sharing documents/tasks
now and deferred runnable mocks/UI. The current initial commit is a documentation base,
not the later F-014 runnable-foundation publication. Inspection and owned proposals can
start now; business prerequisites and unchecked implementation tasks remain unchanged.

**Approved dependency correction (2026-11-11)**: Nemanja (A) approved separating
standalone local corpus preparation from service integration. A-002 now depends
only on A-001. A-010 and F-014 remain prerequisites of A-003, where the prepared
corpus enters the service/index implementation. This approval changes documentation
only; implementation of A-002 still requires a separate approved package.

## Format: `[ID] [P?] [Story] Description`

No task is marked [P]: dependencies or shared files make an unconditional parallel claim
unwarranted. Offline corpus preparation can progress independently of the shared
service base after its own approval; service integration still requires that base.
The initial documentation handoff checked only foundation F-001/F-002. On 2026-11-11,
A-001 was completed after actual authorized source acquisition and owner-local
acceptance checks. Writing plans/mocks does not close a business task.

## Path Conventions and Command Availability

All paths below are repository-relative and limited by the [ownership matrix](../../docs/team/allowed-paths.md).
Initial foundation scaffolding is the coordinator exception; afterward owners stay in scope.
Command availability is recorded per task: A-001 verification and A-002 extraction
checks exist now; later targets remain planned deliverables, not existing npm scripts
or claims of current execution. Each task's actual dependencies
and named test/CLI files must exist before its acceptance command is run. The A-002
offline command uses Python's standard library and does not require F-004; service
commands using `uv run --directory services/rag` require the service scaffold.
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

- [x] T001 A-001: Audit permitted corpus sources and prepare snapshot acquisition/provenance in `data/knowledge/**`, `docs/rag/sources.md`
  - **Owner / story**: A / US1.
  - **Dependencies**: None; may start after the approved specification, within this task's stated scope.
  - **Acceptance**: Review English Health Topic fields/reuse and attribution, then acquire only authorized content; record actual snapshot/checksums and measured topic counts. No outbound crawling.
  - **Verify**: `python -B -m json.tool data/knowledge/manifests/snapshot.json`.
  - **Completion (2026-11-11)**: Required JSON command and actual local archive/metadata checks passed after user approval. The [snapshot manifest](../../data/knowledge/manifests/snapshot.json) records the acquired release, checksums and 401 approved selected topic IDs. See the [acceptance evidence and limits](../../docs/rag/sources.md#a-001-acceptance-review). This completes acquisition/provenance only; corpus processing, chunking, indexing and retrieval remain later unchecked tasks. Paid-provider/deployment checks were not applicable and were not run.
  - **Coverage**: FR-001, FR-002, FR-003, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 2: Shared-service prerequisites

**Purpose**: Establish or verify the listed prerequisites without claiming unrelated module completion.

- [ ] T002 A-010: Review RAG boundary proposals and local mock consumer checks in `services/rag/tests/test_contract.py`, `docs/rag/interface-review.md`, `specs/001-rag/contracts/**`
  - **Owner / story**: A / US1.
  - **Dependencies**: 000-foundation/T004 (F-003); 000-foundation/T006 (F-004)
  - **Boundary**: Required before service integration, not before the owner-local A-002 corpus script. Read-only proposals may be prepared before freeze, but they do not complete this task or its consumer tests.
  - **Acceptance**: Propose any changes to B rather than edit contracts; consume frozen generated bindings and distinguish mode=mock/live and transport error from insufficient evidence.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_contract.py`.
  - **Coverage**: FR-006, FR-016, SC-001, SC-006.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

## Phase 3: User Story 1

**Goal**: Deliver the corresponding story's bounded increment from [spec.md](spec.md).
**Independent Test**: Run the tasks' owner-local verification against public/synthetic fixtures,
with unrelated real modules absent; inspect that story's acceptance scenarios.

- [x] T003 [US1] A-002: Prepare the standalone local English corpus and stable attributed passages in `data/knowledge/scripts/prepare_corpus.py`, `data/knowledge/tests/test_prepare_corpus.py`, `data/knowledge/.cache/corpus/**`, `data/knowledge/manifests/prepared-corpus.json`, `data/knowledge/manifests/cleaned-corpus.json`, `data/knowledge/manifests/passages.json`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T001 (A-001)
  - **Acceptance**: Use Python's standard library and the approved local snapshot/selection only. First extract the 401 selected English topic records with full summaries, IDs, titles, URLs, available synonyms, snapshot and attribution into a Git-ignored local artifact; reject missing/duplicate/extra IDs. In later separately approved increments, clean summary markup without fetching links and produce deterministic, versioned passages. Preserve source provenance, record actual counts and artifact checksums, and test stable output, non-BMP/repeated text and exclusion of site records, licensed/outbound content and evaluation QA. This task completes only when extraction, cleaning and passages all pass; extraction alone is a partial increment. Chunk settings require a documented proposal and approval before the passage-building increment.
  - **Boundary**: No HTTP service, frontend, shared schemas/bindings, service dependencies, embeddings, vector store or provider calls. A-010/F-003/F-004/F-014 are not dependencies of this standalone task. No root/shared files are changed; local artifact structure is A-owned and is not an API contract.
  - **Verify**: `python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"`. The script and test file exist; all 52 offline checks cover extraction, cleaning and passages. Actual stage commands have also been run against the approved snapshot.
  - **Partial progress (2026-11-11)**: User-approved extraction implemented and run with `python -B data/knowledge/scripts/prepare_corpus.py extract`. All 19 synthetic/offline tests passed on Python 3.14.2. Actual output contains exactly the approved 401 IDs; an independent comparison matched every summary and extracted metadata field to the acquired XML. See [extraction evidence](../../docs/rag/sources.md#a-002-extraction-increment) and the [prepared manifest](../../data/knowledge/manifests/prepared-corpus.json). Original snapshot/ZIP are unchanged. Cleaning, passage construction, embedding/indexing and service checks were not run; A-002 remains unchecked.
  - **Partial progress (2026-11-12)**: Separately approved cleaning implemented and run with `python -B data/knowledge/scripts/prepare_corpus.py clean`. All 35 offline tests passed on Python 3.14.2. All 401 topics were cleaned into a separate ignored artifact, with 14 tables preserved and four image tags omitted from topic 6681 as explicitly approved; two comments were also omitted. Independent checks confirmed unchanged original fields/inputs, digests and visible non-formatting character order (ignoring whitespace and formatting characters `-`/`|`, not a semantic check). See [cleaning evidence](../../docs/rag/sources.md#a-002-cleaning-increment) and the [cleaning manifest](../../data/knowledge/manifests/cleaned-corpus.json). No passages, providers or service checks; A-002 remains unchecked.
  - **Completion (2026-11-12)**: After the 2500/300 proposal and its heuristic basis were discussed, the user approved continuing with this initial candidate. `python -B data/knowledge/scripts/prepare_corpus.py chunk` produced 617 passages over all 401 selected topics. All 52 offline tests passed on Python 3.14.2; independent checks verified every passage's exact Unicode slice, stable ID, metadata, limits, forward coverage and unchanged inputs. All 14 tables and 4,947 rendered list lines stay whole; all 14 earlier review excerpts remain contained. Trailing NIH attribution stays with the preceding unit when it fits; zero passages contain only that attribution. See the [policy and measured evidence](../../docs/rag/chunking.md) and [passage manifest](../../data/knowledge/manifests/passages.json). This closes offline preparation only. The candidate has no measured retrieval optimum or tokenizer/model compatibility; service, live-provider and deployment checks were not applicable and were not run.
  - **Coverage**: FR-001, FR-002, FR-003, FR-004, SC-005.
  - **Done**: Mock = deterministic cases pass but do not close real behavior; module = the stated deliverable and owner-local/transport checks pass; live = separately authorized actual provider/deployment evidence, or explicitly unexecuted/not applicable when this task has no live-provider/deployment requirement.

- [ ] T004 [US1] A-003: Connect prepared corpus artifacts to service ingestion and implement embedding/store adapters and versioned indexing in `services/rag/src/notelens_rag/ingestion.py`, `services/rag/src/notelens_rag/adapters/**`, `services/rag/tests/test_corpus_adapter.py`, `services/rag/tests/test_index_version.py`, `data/knowledge/**`
  - **Owner / story**: A / US1.
  - **Dependencies**: 001-rag/T003 (A-002); 001-rag/T002 (A-010); 000-foundation/T014 (F-014)
  - **Acceptance**: After contract review, scaffold and published-foundation prerequisites pass, consume A-002 artifacts through a thin service adapter that verifies their manifest, checksums and stable topic/passage IDs; do not duplicate the offline parser or silently re-clean content. Batch/cache only permitted corpus data. Model/dimensions/preprocessing changes force a new index; mock tests never call providers; live indexing awaits approved model/budget. A-010 preserves F-003/F-004 requirements transitively.
  - **Verify**: `uv run --directory services/rag python -m pytest tests/test_corpus_adapter.py tests/test_index_version.py`.
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
before an actual foundation commit/push. The explicit 2026-11-11 correction permits
A-002 owner-local corpus preparation after A-001 without that service base. Phase 2
does not block this offline increment; task numbers remain stable and are not an
instruction to execute T002 before T003. It does block the later service path.

- A-001 (T001) <- no task prerequisite.
- A-010 (T002) <- F-003, F-004.
- A-002 (T003) <- A-001.
- A-003 (T004) <- A-002, A-010, F-014.
- A-004 (T005) <- A-003.
- A-009 (T006) <- A-004.
- A-006 (T007) <- A-004.
- A-005 (T008) <- A-006.
- A-007 (T009) <- A-002, C-002, D-003.
- A-008 (T010) <- A-005, A-007, A-009, D-007.
- A-011 (T011) <- A-008.

## Parallel Example and Story Order

Separate members may inspect corpus sources (A-001), audit dataset input (C-001) and draft
annotation rules (D-001) independently. After A-001 and a separate implementation
approval, A-002 can prepare the local corpus while B coordinates interfaces and
the service scaffold. A-002 and A-010 meet at A-003; neither must be serialized
behind completion of the other. After the foundation base, B's UI consumes mocks;
D's offline evaluator does not wait for real A/C. Within this feature use explicit edges:
work on independent story tasks only when their actual dependencies are complete.
For D, assignment publication (D-003) precedes member submissions; canonical adjudication
(D-013) follows them, preventing a review/annotation dependency cycle.

## Implementation Strategy

A-001 and A-002 are checked, including the approved initial passage candidate.
Next inspect A-010 and its actual F-003/F-004 prerequisites before service work;
A-003 additionally requires F-014. Preserve
the story's independent contract/mock scenario before service integration and replace its
own stub with real behavior and validate source support. Add measured improvements only
on development data. Optional reranking/extra data/ONNX/ICD must not block the core.
Do not run live or final checks merely to close checkboxes. Report actual mock/module/live
evidence separately, and seek approval before new scope, paid activation, deployment,
commits or publication.

## Workflow record for the dependency correction

On 2026-11-11, the `speckit-tasks` agent workflow was applied to this approved
dependency/path revision with explicit feature context `specs/001-rag` and
`SPECIFY_FEATURE_NO_PERSIST=1`. The official
`.specify/scripts/powershell/setup-tasks.ps1 -Json` resolver returned the existing
feature, available design documents and the resolved tasks-template content.
The existing phase/story structure, eleven task IDs, stable aliases and A-001
completion were retained. Only A-002's offline boundary and A-003's corresponding
service boundary/dependencies changed. This workflow did not execute implementation.
