# Quickstart Validation: Shared Foundation

**Status**: F-003/F-009 contract/binding checks are available; runtime commands labeled future remain unavailable.
Run from the repository root. No command here authorizes paid calls or business implementation.

## Available now: correct feature selection

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/000-foundation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
```

Expected: FEATURE_DIR selects this feature regardless of Git branch. This checks paths,
not whether an application, plan/task tests or services execute successfully.
The installed script exists and has been verified; no feature-state file is overwritten.

## Available now: canonical freeze and bindings

Use [the binding guide](../../contracts/generated/README.md) for exact locked Windows
setup and executed checks: check_contracts.py --require-freeze, generate_contracts.py
--check, Python/TypeScript consumer checks and type compilation. This does not provide
a runnable web/service foundation.

## Future: after runtime foundation prerequisites

F-003/F-009 now supply frozen contracts/fixtures and binding locks. F-004/F-005 must create runtime locks,
stubs and runnable commands. A command that names a missing file is not an executed pass.
After those prerequisites and the relevant implementation tasks create the listed checks:

```text
uv run --directory scripts/project python check_contracts.py
uv run --directory scripts/project python smoke_mock.py
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
handoffs, separate-working-copy commands and checkpoint evidence have passed.
