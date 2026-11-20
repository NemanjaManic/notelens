# Member D: Extraction and Evaluation

**Feature** `specs/004-extraction-evaluation`. `member-d/reconcile-main-2026-11-19` contains D’s current reconciliation. Preserve `member-d/extraction-evaluation` and compare overlapping content before bringing owner work forward.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

## Recover your working copy

Read the [root instructions](../../../AGENTS.md), [constitution](../../../.specify/memory/constitution.md), [scope decisions](../open-decisions.md), [frozen contracts](../../../contracts/v1/README.md), and your [feature backlog](../../../specs/004-extraction-evaluation/tasks.md). Use the [working-copy guide](../working-copies.md) for isolation and reconciliation. Its initial documentation base is historical. Check your branch and drafts, fetch `origin/main`, verify the shared checkpoint, and compare overlapping files before reconciling. Preserve unpublished work.

The published D reconciliation tip `66ee547` records D-001 complete and owner-local progress on D-010, D-004, D-005 and D-002. The synthetic evaluator exercised all five mock business routes there. The shared mock service and readiness checks are already on `main`.

From the repository root, select the feature without persisting local state.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/004-extraction-evaluation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

On Git Bash for Windows, export `SPECIFY_FEATURE_DIRECTORY=specs/004-extraction-evaluation` and `SPECIFY_FEATURE_NO_PERSIST=1`, then run `powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json`. Confirm the reported feature directory matches the selected path. Use actual Git branch output separately.

## Ownership and contracts

`services/extraction/**`, `docs/extraction-eval/**`, `specs/004-extraction-evaluation/**`, and `eval/**` except A, B, and C’s member-specific annotation paths. Follow the [allowed-path matrix](../allowed-paths.md) and seek review from the appropriate owner for shared changes.

`ExtractionRequest` and `DocumentQuestionRequest` contain unchanged `PreparedDocument` records. Evaluation consumes versioned outputs and approved reference sets.

Return `ExtractionResult` with document-cited summaries and `AnswerResult` for document questions. Preserve exact offsets and quotes, plus separate assertion, temporality and subject. D coordinates annotation, adjudication and shared evaluation.

Use `extraction-valid` in the frozen payload catalog for a synthetic extraction with evidence and summary. [Frozen fixture](../../../contracts/v1/fixtures/payloads.json)

## First five tasks

| Alias | Local ID | Deliverable | Status and next dependency |
| --- | --- | --- | --- |
| D-001 | T001 | Prepare annotation ontology, evidence rules and proposals | Complete on D’s published reconciliation branch. |
| D-010 | T002 | Prepare offline evaluation packages, fixtures and mock adapters | Owner-local synthetic adapters and loopback checks exist. Parent task is open. |
| D-004 | T003 | Implement structured extraction and span validation | Owner-local mock slice exists. Full integration requires F-014. |
| D-005 | T004 | Generate evidence-linked summaries and document answers | Owner-local literal mock exists. Full implementation depends on D-004. |
| D-002 | T005 | Select and freeze annotation candidates | Synthetic selector checks exist. Real selection requires C-002 manifests and permitted source access. |

Verify the D-010 work in the owner checkout. Wait for permitted C-002 document/group IDs, split membership and canonical digests before D-002 selection. Keep D-003 assignments and independent reviews gated by actual selection. D-006 requires D-010 and F-014.

## Run the key-free mock

Use the Windows setup and build steps in the [mock startup runbook](../../platform/f-005-mock-startup.md). Run these commands separately from the repository root. For the interactive launcher, open the printed loopback URL, select the synthetic report and stop with Ctrl+C. The smoke command starts and stops its own processes.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

Run the focused check below after the same locked setup.

```powershell
uv run --locked --offline --directory services/extraction python -B -m pytest tests/test_http_smoke.py
```

Report mock, module and separately authorized live results with their actual scope. Use English and approved public or synthetic inputs. Keep document contents out of logs and raw datasets out of Git. Follow the approved memory-only 60-minute limit, 2 MiB PDF limit and 100,000-code-point limit where applicable. Obtain approval for a new change package and separate authorization for publishing or activating providers.

[Member D start prompt](../start-prompts/member-d.md)
