# Key-free platform CI

The [required Windows check](../../.github/workflows/f010-key-free.yml) runs on
pull requests against `main`. It checks the scope declaration and commit
history with scripts from the target base, then installs the locked workspaces
on the candidate checkout. It runs the frozen contract and generated binding
checks, public dependency advisories, production build, and three mock smoke
scenarios. The B-006 step then runs the B-008 HTTP and process log audit plus
the deterministic web regressions. Every command must pass.

The workflow uses mock services on loopback, read-only workflow permissions,
and credential-free checkouts. The dependency audit uses public advisory
services. The [B-008 Chrome scenarios](security.md) are run separately with
isolated browser contexts.

## Reproduce locally on Windows

From the repository root after the locked setup, run these checks. Stop at the
first failure. For a PR, use its actual scope declaration and base and head SHAs
for the trusted scope and secret checks. For a local staged snapshot, use
`check_scope.py --staged --declaration <scope.json>` and
`check_ci.py --secrets --staged` from the project Python environment.

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:NOTELENS_MODE = 'mock'
$projectPython = './scripts/project/.venv/Scripts/python.exe'
& $projectPython -B scripts/project/check_scope.py --self-test
& $projectPython -B scripts/project/check_ci.py --self-test
& $projectPython -B scripts/project/check_ci.py --workflow
& $projectPython -B scripts/project/check_contracts.py --require-freeze
& $projectPython -B scripts/project/generate_contracts.py --check
& $projectPython -B scripts/project/check_ci.py --pr-dependencies
npm.cmd run build
& $projectPython -B scripts/project/smoke_mock.py
& $projectPython -B scripts/project/check_mock_security.py
node apps/web/scripts/check-contracts.mjs
node apps/web/scripts/check-preparation.mjs
node apps/web/scripts/check-sessions.mjs
node apps/web/scripts/check-report.mjs
& ./node_modules/.bin/tsc.cmd --noEmit --project apps/web/tests/tsconfig.routing.json
node --test apps/web/tests/routing.test.ts
```

## B-006 local verification

The B-006 branch passed on Windows with Python 3.13.7 and Node 24.22.1. The
staged-snapshot scope and secret checks, 25 scope tests, 34 CI policy tests,
frozen contracts, generated bindings, and public dependency audit passed.
The production build, all three mock smoke scenarios, the B-008 HTTP and
four-process log audit, and 369 web regressions also passed.

## B-006 hosted verification

The [first hosted run of PR #21](https://github.com/NemanjaManic/notelens/actions/runs/44786567870)
passed on `c14e3cd`. The required Windows job completed the trusted scope and
secret checks, locked installation, contracts, advisories, production build,
and mock smoke. The new mock security and platform regression step also passed.
