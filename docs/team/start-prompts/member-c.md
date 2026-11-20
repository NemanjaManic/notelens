# Member C Start Prompt

Copy the block into Codex opened in your own Member C working copy.

## BEGIN PROMPT

You are helping Member C with NoteLens Python Classification. Keep work scoped to the selected approved task. Read `AGENTS.md`, `.specify/memory/constitution.md`, `docs/team/allowed-paths.md`, `docs/team/handoffs/member-c.md`, the feature spec/plan/tasks, and `contracts/v1/README.md`. Use the original source prompt as requirements context.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

Check the local branch, changes and drafts, fetch the shared ref, then compare the owner branch with the shared tree before reconciling. `member-c/classification` is C’s published audit and consumer-review branch. Use a separate C-owned working branch for C-002.

Select the feature from the repository root.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-classification'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Confirm the reported feature path. Work in your own clone or worktree. Use the installed Spec Kit skill for the approved task when applicable.

### Current tasks

- C-001 Complete on C’s published branch at `50ee841`.
- C-009 Complete at `50ee841`.
- C-002 Approved early on `1ac8bfe`. Complete owner work and deliver permitted manifests before D-002.
- C-010 Depends on D-003 assignments.
- C-003 Depends on completed C-002. Keep final-test material and results restricted.

Resume C-002 in its approved scope using the checksum-matched audited copy. Keep raw and derived text and the source-row mapping local. Share only permitted metadata with D under the agreed access rules. Coordinate one Python nfc-lf-v1 preparation entry point against F-012 and hash the exact canonical UTF-8 bytes. The exception covers C-002 only.

### Key-free mock check

Complete the setup and web build in `docs/platform/f-005-mock-startup.md`. Run the interactive launcher and the finite smoke separately from the repository root. Open the printed loopback URL to use the synthetic report and stop the launcher with Ctrl+C.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

### Scope

Your owned paths are `services/classifier/**`, `data/mtsamples/**`, `docs/ml/**`, `specs/003-classification/**`, and `eval/annotations/member-c/**`. Preserve other owners’ changes and the frozen contracts. Keep canonical text unchanged downstream and use half-open Unicode code-point spans with exact quotes. Identify actual task evidence and blockers before changing checkboxes. Keep artifacts and application outputs in English. Use permitted public or synthetic inputs, keep report bodies out of logs, and keep final-test access restricted. Submitted documents are memory-only for at most 60 minutes. Limit PDFs to 2 MiB and documents to 100,000 Unicode code points. Keep credentials out of chat. Obtain explicit authorization before a new package, commit, push, provider call or deployment. Do not delegate or contact collaborators without authorization.

## END PROMPT
