# Runnable foundation checkpoint

**Status** F-007 candidate verified locally. F-014 publication pending.
**Preparation base** `8ecd4d4621c0700d0e90f5f58200d51bb81ee80b`.

This branch starts from the F-013 acceptance record merged in
[PR #12](https://github.com/NemanjaManic/notelens/pull/12). The human
review covers the key-free mock foundation at `754f4bb`. See the
[acceptance record](../decisions/f-013-foundation-acceptance.md).

## Candidate inventory

[The scaffold inventory](../../scripts/project/scaffold_inputs.json) records
the frozen contracts, generated packages, lockfiles, A/C/D mock services,
the web demo, workflow, and review tooling. The F-007 check binds the actual
candidate bytes to the local scaffold and service-health receipts.
The merged A changes are checked against [PR #9](https://github.com/NemanjaManic/notelens/pull/9).
D's independently verified evaluation inventory is currently a separate
[PR #11](https://github.com/NemanjaManic/notelens/pull/11) candidate.

## Verify the candidate

Use the Windows locked setup in the
[mock startup runbook](../platform/f-005-mock-startup.md). Run these from the
repository root, in order, on the same source tree and installed runtimes.

```powershell
uv run --locked --offline --directory scripts/project python -B check_handoffs.py --require-reviewed-foundation
uv run --locked --offline --directory scripts/project python -B run_scaffold_checks.py
uv run --locked --offline --directory scripts/project python -B check_scaffold.py
uv run --locked --offline --directory scripts/project python -B check_health.py --mode mock
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
uv run --locked --offline --directory scripts/project python -B check_checkpoint.py
```

The checkpoint checker reads local receipts and compares source, runtime,
case, process cleanup and artifact evidence. Keep the reports under ignored
`.cache/` paths. Repeat the run if the candidate source changes.

## Local verification record

The candidate based on the merged F-013 tree passed the human acceptance
checker, all 15 scaffold steps, 30 shared HTTP cases, 213 service-health cases
and the F-005 mock smoke. The default test lane recorded 761 RAG, 84 classifier
and 60 extraction passes. Two RAG collections were skipped because the
optional indexing extra was absent. The PowerShell and Git Bash clone
rehearsals verified SHA and feature selection on the published preparation
base. The final F-014 SHA is still pending separate publication authorization.

## Share the reviewed base

Use the [separate Windows working-copy instructions](working-copies.md) for
the exact remote and feature directories. The candidate's final published
SHA will be recorded only after the reviewed commit is published under F-014.
Keep owner-local artifacts, raw data and credentials out of Git.
