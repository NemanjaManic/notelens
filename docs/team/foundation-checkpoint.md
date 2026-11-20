# Runnable foundation checkpoint

**Status** F-014 foundation published and verified.
**Preparation base** `8ecd4d4621c0700d0e90f5f58200d51bb81ee80b`.
**Published foundation** `7eb12e56f33240a428f916ba583b9e00077712df`.
**Publication tag** `f-014-foundation`.

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
base.

## Verified publication

On 2026-11-20, B merged [PR #13](https://github.com/NemanjaManic/notelens/pull/13)
after Nemanja approved the exact head and
[hosted CI passed](https://github.com/NemanjaManic/notelens/actions/runs/44722263169).
The published merge tree matched the approved PR tree
`f5e548d4ce09806782e7f6066d25da859648dd6b`.

An independent clone of the merged commit passed the human acceptance checker,
all 15 scaffold steps, 30 shared HTTP cases, 213 mock health cases and the F-005
mock smoke. All 19 health processes exited and closed their ports. The
checkpoint verifier matched source SHA-256
`3ceeaa80d09d7e872356b1b1e5a240ae0854dd6252a2546f1ea7b1bb35066dae`.
The official resolver selected the foundation and all four member contexts
without persisting local state.

| Local receipt | SHA-256 |
| --- | --- |
| Scaffold | `ab1018e1c29bb7eaba5c92baa7c65c64a66e848982b34b2789b4394ce526ba2e` |
| Service health | `dc2ca2e2184dffc895b08fa9903e1ec401258adffea7d286e6ce7968391ab901` |

The authorized public [tag](https://github.com/NemanjaManic/notelens/tree/f-014-foundation)
points to the same commit checked on `main`. Verify the tag and compare its
reported SHA with the published foundation above.

```powershell
git ls-remote --tags origin refs/tags/f-014-foundation
```

## Share the reviewed base

Use the [separate Windows working-copy instructions](working-copies.md), with
`NOTELENS_FOUNDATION_SHA` set to the published foundation above. Keep
owner-local artifacts, raw data and credentials out of Git.
