# Implementation Plan: Python RAG

**Branch**: rag | **Created**: 2026-11-10 | **Updated**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/001-rag/spec.md`.
**Owner**: A. **Status**: Draft local design and executable backlog proposal.
Constitution text remains a draft; confirmed source/user requirements are binding.
The plan alone does not authorize implementation, paid calls, publication or deployment.

**Approved dependency correction (2026-11-11)**: Nemanja (A) approved making local
corpus preparation independent of the shared service foundation. This package
updates documentation only. A-001 is complete, but A-002 implementation requires
its own approval. See the boundaries and dependency graph below.

**Approved extraction increment (2026-11-11)**: The user subsequently approved the
standalone script, tests and actual local extraction. That increment now exists
and extracted 401 source records with checked provenance.

**Approved cleaning increment (2026-11-12)**: The user approved plain-text summary
cleaning, tests and actual local processing, then explicitly approved preserving
table rows/cells and recording omitted image tags. All 401 topics are cleaned;
35 offline tests and the actual source-text/provenance comparisons passed on Python
3.14.2. See [cleaning evidence](../../docs/rag/sources.md#a-002-cleaning-increment).

**Approved passage increment (2026-11-12)**: After the 2500-code-point ceiling and
up-to-300 overlap were proposed and explained as an unmeasured candidate, the user
approved continuing. All 401 topics now produce 617 exact, attributable passages.
All 52 offline tests and actual coverage/offset/table checks passed; A-002 is
complete for offline preparation. See [policy and evidence](../../docs/rag/chunking.md).
This does not establish retrieval quality, a tokenizer budget or service readiness.

**Owner-local scaffold continuation (2026-11-13)**: The user explicitly requested
advancing A's work rather than waiting for another B response. This authorizes the
provisional local mock scaffold under `services/rag`, pinned to the reviewed P2 RC1
revision-2 bytes. It is a preparation exception before shared promotion, not a
contract freeze, generated-binding substitute or completion of A-010/F-004/F-014.
All 39 service tests and 52 corpus tests passed on Python 3.13.5. See
[the runnable service instructions](../../services/rag/README.md). No live provider,
real retrieval, shared file or root configuration is activated by this contribution.

**Owner-local reader continuation (2026-11-13)**: The user approved loading/checking
the real prepared corpus before indexing or provider calls. The service now has a
read-only ingestion adapter and optional server-controlled startup loading. All 75
service tests passed on Python 3.13.5, and actual loading verified 401 topics/617
passages. The adapter does not import preparation code or alter canonical content.
This extends local preparation, not the formal completion of A-003 or its shared
integration dependencies. See [reader commands](../../services/rag/README.md#verify-and-load-the-prepared-corpus).

## Summary

Inspect permitted Health Topics, parse/chunk with stable identifiers, establish embedding-only retrieval, compare lexical/hybrid on fixed development questions, and generate literature answers in Python with claim-linked evidence. Keep ranking, semantic support and abstention measurements separate.

## Technical Context

**Language/Version**: Python 3.13.5 verified for the provisional independent services/rag
project and uv.lock. Python 3.14.2 was used for earlier corpus preparation.
The standalone corpus-preparation script uses only Python's standard library and
does not require the service project, its lockfile or third-party installations.
**Primary Dependencies**: FastAPI/Uvicorn; narrow Google Gen AI, embedding and Chroma adapters; lexical/hybrid candidate; pytest. Real model IDs/prices remain activation decisions.
**Storage**: Versioned permitted English MedlinePlus metadata/manifests; ignored public corpus/index caches. No submitted documents enter this corpus or disk cache.
**Testing**: Contract/schema/semantic tests, deterministic fixtures and owner-local tests;
live and frozen final evaluation run only under separate approved gates.
**Target Platform**: Local Windows/PowerShell verified for workflow tooling; Node/Python
application execution and Bash/macOS/Linux runbooks must be verified during F-004/F-005.
**Project Type**: Monorepo workstream with explicit independent service/UI ownership.
**Performance Goals**: No latency/throughput SLO invented. Measure actual performance on
development data; bounded live policies require approval before activation.
**Constraints**: English only, key-free mocks, no submitted-document persistence,
approved 2 MiB PDFs/100,000 code points/60-minute maximum, delivery 2026-11-24.
**Scale/Scope**: Four members, five specialties, small inspectable literature corpus;
40-document annotation and approximately 80-QA targets, not measured datasets.

## Constitution Check

Gate evaluated before research and re-evaluated after this design:
| Principle | Pre-research / post-design assessment |
| --- | --- |
| English and educational MVP | PASS in design; source exclusions and notices preserved. |
| Ownership and independent work | PASS in design; one owner per path, member annotation exceptions, no business overlap. |
| Contract-first Python/TypeScript boundaries | PASS in design; schema/OAS are proposals, freeze required before real consumers. |
| Canonical text and evidence | PASS in design; one preparation step, code-point spans, semantic validation distinct. |
| Honest uncertainty | PASS in design; no clinical probabilities, partial mixed support, no hard specialty filtering. |
| Reproducibility and final-test protection | PASS in design; audit-driven manifests and development-only selection. |
| Measured acceptance | PASS in design; structural/span target 100%, substantive thresholds remain explicit team gates. |
| Security/privacy | PASS in design; memory-only policy and approved caps, isolation and redacted logs. |
| Key-free/cost controls | PASS for local design; paid activation and cloud freeze remain BLOCKED pending approval. |
| Real workflow/review | PASS for artifact preparation; no ratification, business implementation or deployment claimed. |

No unjustified constitutional exception is proposed. Pending external activation/contract
review gates are explicit; the cloud/provider portion is not frozen. Local planning can
proceed without selecting a paid service or fabricating runtime defaults.

## Project Structure

### Documentation (this feature)

```text
specs/001-rag/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/README.md
  quickstart.md
  tasks.md
  checklists/requirements.md
```

### Source Code (repository root)

Owned workstream paths. Offline extraction code now exists under data/knowledge;
service implementation remains a future deliverable:

```text
services/rag/**
data/knowledge/**
docs/rag/**
specs/001-rag/**
eval/annotations/member-a/**
```

**Structure Decision**: Keep the confirmed monorepo and one owner per path.
The shared [allowed-path matrix](../../docs/team/allowed-paths.md) controls exceptions.
Initial coordinator scaffolding across service paths is allowed only before the checkpoint.
Root configs/global Spec Kit files and canonical bindings remain B-owned.

### Offline corpus preparation and service integration

Keep A-002 as an owner-local data pipeline under `data/knowledge/**`:

- Implemented extraction/cleaning increments: `data/knowledge/scripts/prepare_corpus.py` and standard-library
  tests in `data/knowledge/tests/test_prepare_corpus.py`.
- Input: the acquired local MedlinePlus ZIP and approved 401-ID selection recorded
  in `data/knowledge/manifests/snapshot.json`.
- First separately approved increment, now executed: extract the selected English topic records,
  including summaries and attributable metadata, without cleaning/chunking or calls
  to the web, another service or a provider.
- Second separately approved increment, now executed: preserve original records and add
  plain-text summaries, with headings/paragraphs/lists and table rows/cells preserved.
  Decode HTML character references once; normalize whitespace; retain visible link text
  without URLs/attributes or fetching. Omit image tags/comments and record counts/affected
  topic IDs. Unknown, unbalanced or unsupported table markup fails before output.
- Third approved increment, now executed: pack exact canonical slices with a
  2500-code-point ceiling and optional whole-unit overlap up to 300. Keep tables
  and individual list items whole; split oversized paragraphs between words.
  Group a trailing NIH attribution with the previous unit when both fit, so
  attribution need not become a standalone passage. See [the full policy](../../docs/rag/chunking.md).
- Extraction output now exists: Git-ignored artifacts under `data/knowledge/.cache/corpus/**` and
  a small version/count/checksum manifest at `data/knowledge/manifests/prepared-corpus.json`.
  These are A-owned internal artifacts, not a competing shared API schema.
- Separate cleaned output: `data/knowledge/.cache/corpus/cleaned-topics.jsonl`, with
  `data/knowledge/manifests/cleaned-corpus.json` linking input identities and output checksum.
  Existing extraction inputs/manifests remain unchanged; original HTML is retained per record.
- Separate passage output: `data/knowledge/.cache/corpus/passages.jsonl`, with
  `data/knowledge/manifests/passages.json` recording stable IDs, configuration,
  corpus version, measured counts and checksums. Earlier artifacts remain unchanged.
- Available preparation checks: `python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"`.
  All 52 checks passed on Python 3.14.2; these do not establish clinical validity,
  retrieval quality, token budgets or service/Python 3.13 compatibility.

A-002 depends only on completed A-001 and the applicable user approval. Its
extraction CLI is `python -B data/knowledge/scripts/prepare_corpus.py extract`.
Its cleaning CLI is `python -B data/knowledge/scripts/prepare_corpus.py clean`.
Its passage CLI is `python -B data/knowledge/scripts/prepare_corpus.py chunk`.
The script refuses to overwrite existing outputs and makes no network calls. It does not
create HTTP routes, install the service scaffold, modify shared contracts or touch
root configuration. A-002 is complete after all three increments and actual checks;
the passage settings remain a candidate for later development measurements.

A-003 subsequently consumes the prepared artifacts through the service adapter
`services/rag/src/notelens_rag/ingestion.py`; parsing/cleaning is not independently
reimplemented there. A-003 requires A-002, A-010 and F-014. A-010 still requires
F-003/F-004, preserving contract, generated-binding and scaffold checks before
service integration. The shared runnable-foundation checkpoint remains pending.

## Research and Design Phases

### Phase 0: Research

[research.md](research.md) records choices, rationale and alternatives from the primary
[feasibility review](../../docs/decisions/technical-feasibility.md). No research agents were
spawned. Unknown data counts/configuration outcomes are assigned measured/approval tasks,
not substituted with claimed results or silent defaults.

### Phase 1: Data and interfaces

Use [data-model.md](data-model.md), [contract references](contracts/README.md) and the
single draft [canonical proposal](../../contracts/v1/README.md).
Canonicalization, enum and field proposals need owner review before freeze.
Generate bindings rather than diverging copies. Schema validation alone cannot verify
English, source support, span slices, SHA256 or citation foreign keys.

### Phase 2: Implementation handoff (future approval)

Generate an owner-specific [backlog](tasks.md) using the installed tasks workflow.
Follow its dependencies and distinct mock/module/live definitions of done.
Mock fixtures do not complete business tasks. Use [quickstart.md](quickstart.md) for
current safe checks versus planned commands after their named prerequisite creates files.

## Delivery Priorities and Dependencies

MUST: independent mocked interfaces, correct evidence/provenance, required baseline/evaluation,
English states, privacy/isolation and reproducible checks. SHOULD: measured improvements
within the deadline. COULD: reranking, extra datasets, embedding classifier variants,
ONNX/ICD extensions; these do not block the core.

Critical path: contract review/freeze -> shared mock scaffold -> independent baseline modules
and C's split manifests -> D's reviewed references/QA -> real integration -> human review ->
configuration freeze and locked final checks on 2026-11-22/23 -> delivery 2026-11-24.
A may inspect corpus sources, C audit data, D draft guidelines/evaluator and B prepare mocks
without waiting for complete real modules. First development measurement/threshold review
remains targeted for 2026-11-14. No available hours or velocity are assumed.

The offline branch of this dependency graph is now `A-001 -> A-002`; it can run
independently of B's shared service preparation after separate implementation
approval. Both branches meet at `A-003 <- A-002, A-010, F-014`, followed by A-004
retrieval and later generation/evaluation. All other task dependencies are preserved.

## Complexity Tracking

No constitutional violation requiring an exception. Three small Python services preserve
the confirmed ownership; they are not an invitation to add a distributed platform.
Any new paid service, scope/privacy change or cross-owner edit needs the applicable review.
