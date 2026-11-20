# Member A Start Prompt

Copy the block into Codex opened in your own Member A working copy.

## BEGIN PROMPT

You are helping Member A with NoteLens Python RAG. Keep work scoped to the selected approved task. Read `AGENTS.md`, `.specify/memory/constitution.md`, `docs/team/allowed-paths.md`, `docs/team/handoffs/member-a.md`, the feature spec/plan/tasks, and `contracts/v1/README.md`. Use the original source prompt as requirements context.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

Check the local branch, changes and drafts, fetch the shared ref, then compare the owner branch with the shared tree before reconciling. `rag` is A’s published implementation branch. Preserve its local drafts and pending owner changes.

Select the feature from the repository root.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Confirm the reported feature path. Work in your own clone or worktree. Use the installed Spec Kit skill for the approved task when applicable.

### Current tasks

- A-001 Complete in the shared RAG backlog.
- A-010 Complete on shared `main` through PR #5.
- A-002 Standalone corpus preparation is complete in the shared backlog. Shared integration is tracked in A-003.
- A-003 Indexed startup and development evidence are on the shared base. Full integration requires F-014.
- A-004 Owner-local ranking and trial evidence exists. Full HTTP baseline depends on A-003.

Resume A-003 from its owner-local evidence after F-014. Preserve the development/final split and keep evaluation questions and references outside the index. Leave live indexing and provider calls under their separate approval.

### Key-free mock check

Complete the setup and web build in `docs/platform/f-005-mock-startup.md`. Run the interactive launcher and the finite smoke separately from the repository root. Open the printed loopback URL to use the synthetic report and stop the launcher with Ctrl+C.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

### Scope

Your owned paths are `services/rag/**`, `data/knowledge/**`, `docs/rag/**`, `specs/001-rag/**`, and `eval/annotations/member-a/**`. Preserve other owners’ changes and the frozen contracts. Keep canonical text unchanged downstream and use half-open Unicode code-point spans with exact quotes. Identify actual task evidence and blockers before changing checkboxes. Keep artifacts and application outputs in English. Use permitted public or synthetic inputs, keep report bodies out of logs, and keep final-test access restricted. Submitted documents are memory-only for at most 60 minutes. Limit PDFs to 2 MiB and documents to 100,000 Unicode code points. Keep credentials out of chat. Obtain explicit authorization before a new package, commit, push, provider call or deployment. Do not delegate or contact collaborators without authorization.

## END PROMPT
