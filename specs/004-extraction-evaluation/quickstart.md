# Quickstart Validation: Python Extraction and Shared Evaluation

**Status**: D-owned key-free mock slice consumes frozen shared contracts/bindings v1.0.0.
The shared mock scaffold is [technically complete under F-004](../../docs/team/f-004-technical-completion.md).
The reviewed [F-014 foundation is published](../../docs/team/foundation-checkpoint.md).
Run from the repository root. Live generation requires separate approval. Full setup and
verification evidence are in [integration](../../docs/extraction-eval/integration.md).

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
reference-based metrics and human annotations have separate acceptance criteria.

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
D-010 passed its offline and mock checks on the combined B-004 and current D candidate.
The [integration record](../../docs/extraction-eval/integration.md#d-010-verification-2026-11-20)
identifies the tested source and B's remaining checker inventory work. Run these
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
