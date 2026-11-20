# Member B Start Prompt

Copy the block into Codex opened in your own Member B working copy.

## BEGIN PROMPT

You are helping Member B with NoteLens Frontend and Integration. Keep work scoped to the selected approved task. Read `AGENTS.md`, `.specify/memory/constitution.md`, `docs/team/allowed-paths.md`, `docs/team/handoffs/member-b.md`, the feature spec/plan/tasks, and `contracts/v1/README.md`. Use the original source prompt as requirements context.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

Check the local branch, changes and drafts, fetch the shared ref, then compare the owner branch with the shared tree before reconciling. Use a B-owned branch for the approved package. Select `specs/000-foundation` when the task belongs to the shared foundation.

Select the feature from the repository root.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/002-platform'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Confirm the reported feature path. Work in your own clone or worktree. Use the installed Spec Kit skill for the approved task when applicable.

### Current tasks

- B-010 Complete in the shared platform backlog.
- B-004 Approved early memory/config core verified. Full transport and acceptance depend on F-014.
- B-001 Approved built-in core verified. Full input flow depends on F-014 and B-004.
- B-002 Approved fixture workspace verified. Full acceptance depends on F-014 and B-004.
- B-003 Depends on B-001 and B-002. F-005 exercises the preset mock flow.

After F-006 review, proceed through F-013 human acceptance and F-007 checkpoint verification. F-014 publication requires separate authorization.

### Key-free mock check

Complete the setup and web build in `docs/platform/f-005-mock-startup.md`. Run the interactive launcher and the finite smoke separately from the repository root. Open the printed loopback URL to use the synthetic report and stop the launcher with Ctrl+C.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

### Scope

Your owned paths are `apps/web/**`, `contracts/**`, `infra/**`, `.github/**`, `scripts/project/**`, `docs/platform/**`, `docs/team/**`, `docs/decisions/**`, `specs/000-foundation/**`, `specs/002-platform/**`, owned root/shared configuration, and `eval/annotations/member-b/**`. Preserve other owners’ changes and the frozen contracts. Keep canonical text unchanged downstream and use half-open Unicode code-point spans with exact quotes. Identify actual task evidence and blockers before changing checkboxes. Keep artifacts and application outputs in English. Use permitted public or synthetic inputs, keep report bodies out of logs, and keep final-test access restricted. Submitted documents are memory-only for at most 60 minutes. Limit PDFs to 2 MiB and documents to 100,000 Unicode code points. Keep credentials out of chat. Obtain explicit authorization before a new package, commit, push, provider call or deployment. Do not delegate or contact collaborators without authorization.

## END PROMPT
