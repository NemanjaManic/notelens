# Member A: Python RAG

**Feature** `specs/001-rag`. `rag` is A’s published implementation branch. Preserve its local drafts and pending owner changes.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

## Recover your working copy

Read the [root instructions](../../../AGENTS.md), [constitution](../../../.specify/memory/constitution.md), [scope decisions](../open-decisions.md), [frozen contracts](../../../contracts/v1/README.md), and your [feature backlog](../../../specs/001-rag/tasks.md). Use the [working-copy guide](../working-copies.md) for isolation and reconciliation. Its initial documentation base is historical. Check your branch and drafts, fetch `origin/main`, verify the shared checkpoint, and compare overlapping files before reconciling. Preserve unpublished work.

PR #9 merged A's development work into the shared base. The shared backlog now records A-001, A-010 and standalone A-002 complete. A's indexed startup and development checks are recorded in the [RAG development handoff](../../rag/development-handoff.md).

From the repository root, select the feature without persisting local state.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

On Git Bash for Windows, export `SPECIFY_FEATURE_DIRECTORY=specs/001-rag` and `SPECIFY_FEATURE_NO_PERSIST=1`, then run `powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json`. Confirm the reported feature directory matches the selected path. Use actual Git branch output separately.

## Ownership and contracts

`services/rag/**`, `data/knowledge/**`, `docs/rag/**`, `specs/001-rag/**`, and `eval/annotations/member-a/**`. Follow the [allowed-path matrix](../allowed-paths.md) and seek review from the appropriate owner for shared changes.

A owns public corpus preparation, ingestion, embedding calls, vector-store access, retrieval, and literature-grounded answers. The frozen `RetrievalRequest` and `LiteratureAnswerRequest` carry an English question and any approved context. Specialty and concepts are soft retrieval signals.

Return `RetrievalResult` and literature `AnswerResult` with versioned retrieval provenance, claim-linked passage citations and explicit gaps. Literature supports general information. Preserve patient-specific evidence for the document route.

Use `answer-literature` in the frozen payload catalog for a supported synthetic literature answer. [Frozen fixture](../../../contracts/v1/fixtures/payloads.json)

## First five tasks

| Alias | Local ID | Deliverable | Status and next dependency |
| --- | --- | --- | --- |
| A-001 | T001 | Audit MedlinePlus provenance and reuse | Complete in the shared RAG backlog. |
| A-010 | T002 | Review frozen contracts and mock consumption | Complete on shared `main` through PR #5. |
| A-002 | T003 | Prepare the standalone English corpus and passages | Standalone corpus preparation is complete in the shared backlog. Shared integration is tracked in A-003. |
| A-003 | T004 | Connect corpus and implement versioned indexing | Indexed startup and development evidence are on the shared base. Full integration requires F-014. |
| A-004 | T005 | Deliver a retrieval baseline | Owner-local ranking and trial evidence exists. Full HTTP baseline depends on A-003. |

Resume A-003 from its owner-local evidence after F-014. Preserve the development/final split and keep evaluation questions and references outside the index. Leave live indexing and provider calls under their separate approval.

## Run the key-free mock

Use the Windows setup and build steps in the [mock startup runbook](../../platform/f-005-mock-startup.md). Run these commands separately from the repository root. For the interactive launcher, open the printed loopback URL, select the synthetic report and stop with Ctrl+C. The smoke command starts and stops its own processes.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

Run the focused check below after the same locked setup.

```powershell
uv run --locked --offline --directory services/rag python -B -m pytest tests/test_contract.py tests/test_http_smoke.py
```

Report mock, module and separately authorized live results with their actual scope. Use English and approved public or synthetic inputs. Keep document contents out of logs and raw datasets out of Git. Follow the approved memory-only 60-minute limit, 2 MiB PDF limit and 100,000-code-point limit where applicable. Obtain approval for a new change package and separate authorization for publishing or activating providers.

[Member A start prompt](../start-prompts/member-a.md)
