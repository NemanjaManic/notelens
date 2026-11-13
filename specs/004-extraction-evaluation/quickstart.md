# Quickstart Validation: Python Extraction and Shared Evaluation

**Status**: provisional local slice authorized 2026-11-11; frozen shared integration
and live generation remain pending. Run from the repository root. Full setup and
limits are in [integration](../../docs/extraction-eval/integration.md).

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

## Future: after foundation prerequisites

The later F-003/F-004/F-005 tasks must create frozen contracts/fixtures, dependency locks,
stubs and runnable commands. A command that names a missing file is not an executed pass.
After those prerequisites and the relevant implementation tasks create the listed checks:

```text
uv run --directory services/extraction python -m pytest tests/test_evidence.py tests/test_answers.py tests/test_contract.py
uv run --directory eval python -m notelens_eval.run --profile smoke
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

[Tasks](tasks.md) provide owner/path/dependency/acceptance details. All business work remains
unchecked. Do not declare the shared foundation ready until the runnable mock flow,
handoffs, separate-working-copy commands and checkpoint evidence have passed. The
checked local subtasks in the continuation do not satisfy those shared gates.
