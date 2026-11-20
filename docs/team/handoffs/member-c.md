# Member C: Python Classification

**Feature** `specs/003-classification`. `member-c/classification` is C’s published audit and consumer-review branch. Use a separate C-owned working branch for C-002.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

## Recover your working copy

Read the [root instructions](../../../AGENTS.md), [constitution](../../../.specify/memory/constitution.md), [scope decisions](../open-decisions.md), [frozen contracts](../../../contracts/v1/README.md), and your [feature backlog](../../../specs/003-classification/tasks.md). Use the [working-copy guide](../working-copies.md) for isolation and reconciliation. Its initial documentation base is historical. Check your branch and drafts, fetch `origin/main`, verify the shared checkpoint, and compare overlapping files before reconciling. Preserve unpublished work.

The published `member-c/classification` tip `50ee841` records C-001 and C-009 complete. F-011 classifier mock readiness and failure checks are on the shared base. C-002 is the only approved early-work exception in this sequence. Its approved base is `1ac8bfe9cf3ea9853c417ffe3f86ed7a1a15b6f8`.

From the repository root, select the feature without persisting local state.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-classification'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

On Git Bash for Windows, export `SPECIFY_FEATURE_DIRECTORY=specs/003-classification` and `SPECIFY_FEATURE_NO_PERSIST=1`, then run `powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json`. Confirm the reported feature directory matches the selected path. Use actual Git branch output separately.

## Ownership and contracts

`services/classifier/**`, `data/mtsamples/**`, `docs/ml/**`, `specs/003-classification/**`, and `eval/annotations/member-c/**`. Follow the [allowed-path matrix](../allowed-paths.md) and seek review from the appropriate owner for shared changes.

`ClassificationRequest` contains B’s unchanged `PreparedDocument`. C owns source provenance, the five-specialty mapping, duplicate grouping, splits, training and inference.

Return `ClassificationResult` with a supported specialty or an uncertain/unsupported state, versioned scores and an explanation of score limits. Specialty is a document label.

Use `classification-supported` in the frozen payload catalog to inspect the synthetic classification record. [Frozen fixture](../../../contracts/v1/fixtures/payloads.json)

## First five tasks

| Alias | Local ID | Deliverable | Status and next dependency |
| --- | --- | --- | --- |
| C-001 | T001 | Audit authorized MTSamples input and map labels | Complete on C’s published branch at `50ee841`. |
| C-009 | T002 | Review frozen classification contracts and mock consumer | Complete at `50ee841`. |
| C-002 | T003 | Group duplicates, exclude conflicts and prepare seeded splits | Approved early on `1ac8bfe`. Complete owner work and deliver permitted manifests before D-002. |
| C-010 | T004 | Complete development-only annotations and independent reviews | Depends on D-003 assignments. |
| C-003 | T005 | Train majority and TF-IDF plus Logistic Regression baselines | Depends on completed C-002. Keep final-test material and results restricted. |

Resume C-002 in its approved scope using the checksum-matched audited copy. Keep raw and derived text and the source-row mapping local. Share only permitted metadata with D under the agreed access rules. Coordinate one Python nfc-lf-v1 preparation entry point against F-012 and hash the exact canonical UTF-8 bytes. The exception covers C-002 only.

## Run the key-free mock

Use the Windows setup and build steps in the [mock startup runbook](../../platform/f-005-mock-startup.md). Run these commands separately from the repository root. For the interactive launcher, open the printed loopback URL, select the synthetic report and stop with Ctrl+C. The smoke command starts and stops its own processes.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

Run the focused check below after the same locked setup.

```powershell
uv run --locked --offline --directory services/classifier python -B -m pytest tests/test_contract.py tests/test_http.py
```

Report mock, module and separately authorized live results with their actual scope. Use English and approved public or synthetic inputs. Keep document contents out of logs and raw datasets out of Git. Follow the approved memory-only 60-minute limit, 2 MiB PDF limit and 100,000-code-point limit where applicable. Obtain approval for a new change package and separate authorization for publishing or activating providers.

[Member C start prompt](../start-prompts/member-c.md)
