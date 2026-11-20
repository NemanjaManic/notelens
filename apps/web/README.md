# NoteLens Web Scaffold — B's F-004 Contribution

**Verified:** 2026-11-14 on Windows/PowerShell, Node v24.22.1, npm 11.19.1,
Python 3.13.7 and repository-local uv 0.13.7.
**Branch:** `member-b/task-f-004-web-workspace`, based on
`fd1197bd380de9ba9037ea0b73b42031dc1d4bb2`. No commit or push is authorized.

This is the B-owned contribution to foundation T006 / F-004. It provides a minimal
English mock shell with the three required notices, root npm workspaces/lock,
generated-package integration and scoped checks. It accepts no submitted documents
and has no upload, report-analysis, session or chat functionality. It does not complete
shared F-004, F-014 or any platform business task.

## Setup and run

Run from the repository root in PowerShell. Node 24 and npm 11 are the tested toolchain.
The root lock owns the web and generated TypeScript workspace install. Preserve the
generated package's existing standalone lock and the independent tooling consumer locks.
No Python service installation or API key is needed.

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
$env:NOTELENS_MODE = 'mock'
npm.cmd ci --cache .cache/npm --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Workspace install failed.' }
npm.cmd run typecheck --workspace apps/web
if ($LASTEXITCODE -ne 0) { throw 'Typecheck failed.' }
npm.cmd run build --workspace apps/web
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
npm.cmd run start --workspace apps/web
```

Open `http://127.0.0.1:3000`; stop this foreground web process with Ctrl+C.
For development, use `npm.cmd run dev --workspace apps/web` instead of production start.
The root `dev`, `build`, `start` and `typecheck` scripts forward to the web workspace.
`typecheck` generates Next route types before invoking TypeScript, including on a fresh
checkout. The loopback hostname is explicit; this is not a deployment command.

`.env.example` records the only scaffold setting. Unset `NOTELENS_MODE` selects the
key-free mock scaffold; any explicit value other than `mock` fails. Runtime validation
occurs per request, with dynamic rendering, so changing the process to `live` cannot
silently serve cached mock output. There is no live adapter or provider import.
The expected production failure is HTTP 500; only developer-run scaffold configuration
is tested here, not the later application's user-facing error system.

The server lazily imports `@notelens/contracts/v1` and validates the existing versioned
synthetic `offset` fixture. No alternate schema or generated file is maintained here.
No submitted input, filesystem document store, document logging, shared document cache,
remote fonts or remote assets are introduced.

## Verification

After installation/build, run from the root:

```powershell
npm.cmd ls --workspace apps/web @notelens/contracts next react react-dom typescript
node apps/web/scripts/check-bindings.mjs
node apps/web/scripts/check-config.mjs
python -B apps/web/scripts/check-render.py

$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$contractUv = Join-Path (Get-Location).Path '.cache/tooling/Scripts/uv.exe'
& $contractUv run --locked --offline --directory scripts/project python check_scaffold.py --web-only
& $contractUv run --locked --offline --directory scripts/project python check_scaffold.py
```

Stop on unexpected nonzero exits. The **last command intentionally exits 1** while
shared service scaffolds/verification remain absent. `--web-only` exits 0 for the checked
B contribution and explicitly excludes shared F-004. Both modes resolve repository paths
from their own file. The checker runs local type/runtime probes and checks a current build
artifact; it does not install, launch services or execute A/C/D environments. It separately
reports missing manifests/locks/entrypoints or outstanding owner runtime verification.
Default mode remains an incomplete inventory until that owner evidence is integrated;
mere file presence can never close the shared task.

The render script starts only its own production web processes on temporary loopback
ports, checks mock HTTP 200, required English notices, built assets and absence of input
controls, then verifies explicit live mode returns HTTP 500. It terminates the processes
it starts. Its startup/request deadlines are verification limits, not application
timeout/retry/session/rate defaults. No browser is launched, so visual layout and browser
interaction acceptance are not claimed.

## Actual results

- Clean root `npm ci`: passed; npm resolved the local frozen workspace package.
- Typecheck and Next production build: passed with Next 16.4.6, React/React DOM 19.3.1,
  TypeScript 7.0.2, `@types/node` 24.19.2 and React/React DOM types 19.3.0.
- Installed local package resolution and async fixture validation: passed.
- Mock configuration probe: passed; live/empty/unknown values rejected.
- Production HTTP render and built asset checks: passed; mock 200 and live 500.
- B-only scaffold check: passed. Shared checker: expected incomplete, exit 1, all three
  Python scaffolds absent from this checkout.
- B tooling unittest suite: **61 tests passed**, including four new negative scaffold
  tests for missing services, unverified service presence, wrong workspace/registry
  substitution and missing/malformed metadata.
- Frozen contract guard: **155/155 outcomes**, 69 positive/86 negative, and **22 simulated
  correlation outcomes**. Generated-binding drift guard: passed. Those exchanges did
  not call an HTTP service; the production shell checks above did call the local web.

An initial binding probe was accidentally overlapped with `npm ci` and failed during
dependency replacement. It passed when rerun after installation. No source/package override
or contract edit was needed. The existing Python tooling manifest/lock and generated
package sources/manifests/locks remain unchanged.

## Workflow, sources and remaining work

Executed the installed [speckit-implement skill](../../.agents/skills/speckit-implement/SKILL.md)
with explicit user approval limited to B's part of foundation T006. The official
PowerShell prerequisite resolver selected `specs/000-foundation` using
`SPECIFY_FEATURE_DIRECTORY` and `SPECIFY_FEATURE_NO_PERSIST=1`, with `-Json -RequireTasks
-IncludeTasks`. The built-in checklist contained 16 checked items and no unchecked items;
this is an agent requirements review, not new human acceptance. Pre/post extension hooks
are absent. No templates, feature state, constitution or feature plans were regenerated.
The integration remains pinned to Spec Kit 1.3.3; its CLI version command was not rerun.

Dependency metadata was checked using npm registry queries before installation. Reviewed
[official installation guidance](https://nextjs.org/docs/app/getting-started/installation),
the [November security release](https://nextjs.org/blog/november-2026-security-release),
and installed Next documentation under `node_modules/next/dist/docs/01-app/`.
Next 16.4.6 follows the security release's 16.4.5 fixes. These sources informed dependency
selection; actual local install/build checks provide the compatibility evidence.

See the [scoped plan](../../docs/platform/f-004-web-workspace-plan.md) for ownership and
dependencies. A/C/D retain their service files/manifests/locks. F-011/F-012/F-005 and
B-010/B-004/B-001/B-002/B-003 are not implemented here. No provider/model call, paid
activation, deployment, browser acceptance, clinical-quality evaluation or shared runnable
foundation pass is claimed. Delivery remains 2026-11-24.
