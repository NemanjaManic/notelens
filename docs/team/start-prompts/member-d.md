# Member D Start Prompt

Copy the block into Codex opened in your own Member D working copy.

## BEGIN PROMPT

You are helping Member D with NoteLens Extraction and Evaluation. Keep work scoped to the selected approved task. Read `AGENTS.md`, `.specify/memory/constitution.md`, `docs/team/allowed-paths.md`, `docs/team/handoffs/member-d.md`, the feature spec/plan/tasks, and `contracts/v1/README.md`. Use the original source prompt as requirements context.

Shared mock base `c5c186c18b2ad74e825c030ad8c993918ea39599` on `origin/main` includes frozen v1.0.0 contracts, the F-005 mock demo, the F-011 health checks and the F-010 workflow. F-010 verification is recorded in the foundation backlog. F-014 publication is pending.

Check the local branch, changes and drafts, fetch the shared ref, then compare the owner branch with the shared tree before reconciling. `member-d/reconcile-main-2026-11-19` contains D’s current reconciliation. Preserve `member-d/extraction-evaluation` and compare overlapping content before bringing owner work forward.

Select the feature from the repository root.

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/004-extraction-evaluation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Confirm the reported feature path. Work in your own clone or worktree. Use the installed Spec Kit skill for the approved task when applicable.

### Current tasks

- D-001 Complete on D’s published reconciliation branch.
- D-010 Owner-local synthetic adapters and loopback checks exist. Parent task is open.
- D-004 Owner-local mock slice exists. Full integration requires F-014.
- D-005 Owner-local literal mock exists. Full implementation depends on D-004.
- D-002 Synthetic selector checks exist. Real selection requires C-002 manifests and permitted source access.

Verify the D-010 work in the owner checkout. Wait for permitted C-002 document/group IDs, split membership and canonical digests before D-002 selection. Keep D-003 assignments and independent reviews gated by actual selection. D-006 requires D-010 and F-014.

### Key-free mock check

Complete the setup and web build in `docs/platform/f-005-mock-startup.md`. Run the interactive launcher and the finite smoke separately from the repository root. Open the printed loopback URL to use the synthetic report and stop the launcher with Ctrl+C.

```powershell
uv run --locked --offline --directory scripts/project python -B start_mock.py
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

### Scope

Your owned paths are `services/extraction/**`, `docs/extraction-eval/**`, `specs/004-extraction-evaluation/**`, and `eval/**` except A, B, and C’s member-specific annotation paths. Preserve other owners’ changes and the frozen contracts. Keep canonical text unchanged downstream and use half-open Unicode code-point spans with exact quotes. Identify actual task evidence and blockers before changing checkboxes. Keep artifacts and application outputs in English. Use permitted public or synthetic inputs, keep report bodies out of logs, and keep final-test access restricted. Submitted documents are memory-only for at most 60 minutes. Limit PDFs to 2 MiB and documents to 100,000 Unicode code points. Keep credentials out of chat. Obtain explicit authorization before a new package, commit, push, provider call or deployment. Do not delegate or contact collaborators without authorization.

## END PROMPT
