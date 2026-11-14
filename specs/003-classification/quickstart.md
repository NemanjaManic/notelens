# Quickstart Validation: Python Classification

**Status**: C-001 audit and C-011 local F-004 scaffold commands are available; commands labeled future remain gated.
Run from the repository root. C-001 is authorized; no command here authorizes paid calls
or bypasses the remaining task dependencies.

## Available now: correct feature selection

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-classification'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
```

Expected: FEATURE_DIR selects this feature regardless of Git branch. This checks paths,
not whether an application, plan/task tests or services execute successfully.
The installed script exists and has been verified; no feature-state file is overwritten.

## Available now: local dataset audit

The user-supplied CSV is in ignored `data/mtsamples/raw/mtsamples.csv`. With Python 3.11.9,
these commands passed on 2026-11-11; they need only the standard library:

```powershell
python -B data/mtsamples/audit.py --check
python -B -m unittest discover -s data/mtsamples/tests -v
python -B -m json.tool data/mtsamples/manifests/source.json
```

On a new working copy, supply the authorized CSV locally and run
`python -B data/mtsamples/audit.py` to generate the ignored nonempty target subset.
Review its checksum against the committed manifest before accepting a new source.
The subset is not ready for training: duplicate/conflict processing and grouped splits
remain C-002 work. See [the measured audit](../../docs/ml/data-audit.md).

## Available now: local classifier mock scaffold

Follow the [service setup/start/check commands](../../services/classifier/README.md).
The local uv executable is `.cache/classifier-tooling/Scripts/uv.exe` after setup.
F-003/F-009 are published; the scaffold consumes their installed frozen Python package.

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
& ./.cache/classifier-tooling/Scripts/uv.exe run --locked --offline --directory services/classifier python -B -m pytest -q
$env:NOTELENS_CLASSIFIER_MODE = 'mock'
$env:NOTELENS_CLASSIFIER_MOCK_SCENARIO = 'supported'
& ./.cache/classifier-tooling/Scripts/uv.exe run --locked --offline --directory services/classifier python -m notelens_classifier
```

The launcher is loopback-only at port 8002. Tests include real local HTTP and process
cleanup; health/readiness remains F-011 work after the shared F-004 checkpoint. The
local contribution does not complete the whole F-004 or C-009. See the [handoff](../../docs/ml/classifier-scaffold-handoff.md).

## Future: after foundation prerequisites

The later F-003/F-004/F-005 tasks must create frozen contracts/fixtures, dependency locks,
stubs and runnable commands. A command that names a missing file is not an executed pass.
After those prerequisites and the relevant implementation tasks create the listed checks:

```text
uv run --directory services/classifier python -m pytest tests/test_splits.py tests/test_training_leakage.py tests/test_contract.py
```

These are planned acceptance commands using real tool CLIs, not claims that package scripts
or test files exist today. The backlog names the task that creates each target.
No npm run script is assumed; B must document and verify actual package scripts later.

## Independent scenarios

1. Start this workstream in key-free mock mode with other business modules absent.
2. Submit a valid synthetic/public example and verify shared structure plus evidence semantics.
3. Exercise empty/unsupported/insufficient, malformed upstream and provider-failure fixtures.
4. Include non-BMP/repeated-span cases, approved input caps and cross-session/expiry behavior
   where relevant. Use a controlled clock for expiry.
5. Report actual mock/module/live checks separately; business metrics and live checks remain
   unexecuted until their data, approvals and implementations exist.

## Exit and review

[Tasks](tasks.md) provide owner/path/dependency/acceptance details. C-001 and the local
C-011 scaffold contribution are checked; C-009, C-002 and business tasks remain gated.
Do not declare the shared foundation ready until the runnable mock flow,
handoffs, separate-working-copy commands and checkpoint evidence have passed.
