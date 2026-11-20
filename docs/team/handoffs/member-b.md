# Member B: Frontend and Integration

**Feature** `specs/002-platform`. Use a B-owned branch for the approved package. Select `specs/000-foundation` when the task belongs to the shared foundation.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

## Recover your working copy

Read the [root instructions](../../../AGENTS.md), [constitution](../../../.specify/memory/constitution.md), [scope decisions](../open-decisions.md), [frozen contracts](../../../contracts/v1/README.md), and your [feature backlog](../../../specs/002-platform/tasks.md). Use the [working-copy guide](../working-copies.md) for isolation and reconciliation. Its initial documentation base is historical. Check your branch and drafts, fetch `origin/main`, verify the shared checkpoint, and compare overlapping files before reconciling. Preserve unpublished work.

F-005, F-011 and F-012 have shared evidence. PR #8 added key-free CI and CODEOWNERS. Protected main, review routing and the hosted check were verified with PR #9.

From the repository root, select the feature without persisting local state.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/002-platform'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

On Git Bash for Windows, export `SPECIFY_FEATURE_DIRECTORY=specs/002-platform` and `SPECIFY_FEATURE_NO_PERSIST=1`, then run `powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json`. Confirm the reported feature directory matches the selected path. Use actual Git branch output separately.

## Ownership and contracts

`apps/web/**`, `contracts/**`, `infra/**`, `.github/**`, `scripts/project/**`, `docs/platform/**`, `docs/team/**`, `docs/decisions/**`, `specs/000-foundation/**`, `specs/002-platform/**`, owned root/shared configuration, and `eval/annotations/member-b/**`. Follow the [allowed-path matrix](../allowed-paths.md) and seek review from the appropriate owner for shared changes.

Consume prepared documents and validated classifier, extraction, retrieval and answer records. B prepares canonical text once, owns session isolation, and uses thin clients for A, C, and D.

Produce `PreparedDocument` and the English report and chat experience. Preserve claim origins when combining results. Keep document-supported claims visible when literature is insufficient or unavailable.

Use `offset` in the frozen document catalog to inspect the canonical digest and repeated passages. [Frozen fixture](../../../contracts/v1/fixtures/documents.json)

## First five tasks

| Alias | Local ID | Deliverable | Status and next dependency |
| --- | --- | --- | --- |
| B-010 | T001 | Review the frozen records and web mock consumer | Complete in the shared platform backlog. |
| B-004 | T002 | Implement bounded sessions and configuration | Approved early memory/config core verified. Full transport and acceptance depend on F-014. |
| B-001 | T003 | Prepare built-in, text and PDF inputs | Approved built-in core verified. Full input flow depends on F-014 and B-004. |
| B-002 | T004 | Render reports and exact evidence highlights | Approved fixture workspace verified. Full acceptance depends on F-014 and B-004. |
| B-003 | T005 | Implement service clients and source-preserving routing | Depends on B-001 and B-002. F-005 exercises the preset mock flow. |

After F-006 review, proceed through F-013 human acceptance and F-007 checkpoint verification. F-014 publication requires separate authorization.

## Run the key-free mock

Use the Windows setup and build steps in the [mock startup runbook](../../platform/f-005-mock-startup.md). Run these commands separately from the repository root. For the interactive launcher, open the printed loopback URL, select the synthetic report and stop with Ctrl+C. The smoke command starts and stops its own processes.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

Run the focused check below after the same locked setup.

```powershell
node apps/web/scripts/check-contracts.mjs
```

Report mock, module and separately authorized live results with their actual scope. Use English and approved public or synthetic inputs. Keep document contents out of logs and raw datasets out of Git. Follow the approved memory-only 60-minute limit, 2 MiB PDF limit and 100,000-code-point limit where applicable. Obtain approval for a new change package and separate authorization for publishing or activating providers.

[Member B start prompt](../start-prompts/member-b.md)
