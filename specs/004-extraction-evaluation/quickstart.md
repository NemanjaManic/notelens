# Quickstart Validation: Python Extraction and Shared Evaluation

**Status**: D-owned key-free mock slice consumes frozen shared contracts/bindings v1.0.0.
The shared mock scaffold is [technically complete under F-004](../../docs/team/f-004-technical-completion.md).
F-014 foundation publication and live generation remain pending. Run from the repository
root. Full setup and limits are in [integration](../../docs/extraction-eval/integration.md).

## Available now: local mock service and evaluation

After the service/eval-local locked environments have been synced:

```powershell
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve
```

In another terminal:

```powershell
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli demo
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli demo --question "What does the document say about chest pain?"
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile smoke
./eval/.venv/Scripts/python.exe eval/smoke_http.py
./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests -q
./eval/.venv/Scripts/python.exe -m pytest eval/tests -q
```

These commands exercise synthetic/mock behavior. General real-model extraction,
human annotations and shared foundation acceptance are not claimed. Existing future
acceptance filenames below remain planned until parent tasks are actually completed.

## Available now: correct feature selection

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/004-extraction-evaluation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
```

Expected: FEATURE_DIR selects this feature regardless of Git branch. This checks paths,
not whether an application, plan/task tests or services execute successfully.
The installed script exists and has been verified; no feature-state file is overwritten.

## Shared scaffold verification and foundation work

F-003/F-009 are complete and their generated package is consumed by this service.
F-004 technical completion covers the shared mock scaffold and its HTTP checks.
B verified the reconciled D package on the [integration candidate](https://github.com/NemanjaManic/notelens/commit/4c8b9be7c5bddc0979376d13b254c05f6f30e86f),
which passed all 15 scaffold steps, including 30 shared HTTP cases. That candidate
awaits merge. B still coordinates F-005 startup and F-014 publication. Run these
commands for owner-local checks:

```powershell
./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests -q
./eval/.venv/Scripts/python.exe -m pytest eval/tests -q
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile smoke
./eval/.venv/Scripts/python.exe eval/smoke_http.py
```

These owner-local tests and smoke commands exist and are documented in [integration](../../docs/extraction-eval/integration.md). No root npm script is assumed; B owns shared startup and workspace commands.

## Independent scenarios

1. Start this workstream in key-free mock mode with other business modules absent.
2. Submit a valid synthetic/public example and verify shared structure plus evidence semantics.
3. Exercise empty/unsupported/insufficient, malformed upstream and provider-failure fixtures.
4. Include non-BMP/repeated-span cases, approved input caps and cross-session/expiry behavior
   where relevant. Use a controlled clock for expiry.
5. Report actual mock/module/live checks separately; business metrics and live checks remain
   unexecuted until their data, approvals and implementations exist.

## Exit and review

[Tasks](tasks.md) provide owner/path/dependency/acceptance details. Parent D tasks remain
open where real-model, real-data, cross-service, or human-review gates are unmet. Do not
declare the shared foundation ready until coordinated mock flow, handoffs,
separate-working-copy commands and checkpoint evidence have passed.
