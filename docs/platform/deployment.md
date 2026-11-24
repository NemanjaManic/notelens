# B-007 Windows readiness runbook

This rehearsal builds and starts the production web app with mock RAG, classifier,
and extraction services on Windows loopback. It uses synthetic fixtures and a
temporary service token created by the launcher. Provider credentials and
model or corpus downloads are unnecessary. Package installation may need access
to the dependency registries.

## Install and build

Use PowerShell from the repository root with Node 24, npm 11, Python 3.13, and uv.
If uv cannot find an existing Python 3.13 installation, set `$platformPython`
to the full path of its `python.exe` in the setup block. For a custom uv-managed
installation, set `UV_PYTHON_INSTALL_DIR` to the existing installation directory
before running discovery.

```powershell
$ErrorActionPreference = 'Stop'
$env:NEXT_TELEMETRY_DISABLED = '1'
$platformPython = uv --offline python find 3.13
if ($LASTEXITCODE -ne 0 -or -not $platformPython) {
    throw 'Could not locate Python 3.13.'
}

foreach ($project in @('scripts/project', 'services/rag', 'services/classifier', 'services/extraction')) {
    uv sync --locked --directory $project --python $platformPython --no-dev
    if ($LASTEXITCODE -ne 0) { throw "Locked setup failed for $project." }
}
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Web dependency setup failed.' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web production build failed.' }
```

## Run the finite readiness check

```powershell
uv run --locked --offline --directory scripts/project --python $platformPython --no-dev python -B check_readiness.py
if ($LASTEXITCODE -ne 0) { throw 'Local key-free readiness check failed.' }
```

The checker starts its own four processes on independent loopback ports. It
requires HTTP 200 from `/demo/health` and `/demo` in mock mode. For each Python
service, it verifies authenticated HTTP 200 from `/health/live` and
`/health/ready`, the expected service identity and mock status, and HTTP 401
without the token. It checks that all four owned listeners close before
reporting success. Output gives the failing component or probe without logging
response bodies or the service token.

If setup or startup fails, check the Python and Node versions, rerun the locked
setup for the named component, and rebuild the web workspace before trying
again. Use a fresh checkout for source verification and leave other running
processes alone. Each invocation chooses its own ports.

For an interactive demo, run the launcher below, open the printed loopback URL,
and press Ctrl+C in the launcher terminal when finished. Use the
[key-free Chrome rehearsal](demo.md) for the input-to-answer checks.

```powershell
uv run --locked --offline --directory scripts/project --python $platformPython --no-dev python -B start_mock.py
```

## Local verification

Verified on Windows from main at `aa25976956f46d1a6e419315be4ebc06dfb6dd30`
with Python 3.13.7, Node 24.22.1, npm 11.19.1, and uv 0.13.7. The locked
setup, production build, and readiness command passed. Both web endpoints
returned HTTP 200. All six service endpoints returned HTTP 200 with the
temporary token and HTTP 401 without it. All four processes stopped and
their loopback ports closed.

## Railway deployment evidence

The [Railway web app](https://notelens-live-production.up.railway.app/demo)
returned HTTP 200 over HTTPS. Its [health endpoint](https://notelens-live-production.up.railway.app/demo/health)
returned HTTP 200 with mode `public-live` and startup ID
`4295a1ba-4247-48d4-a6c3-c04af4673233`. The web health endpoint reports the
configured profile. It does not probe the three Python services.

The `live-deploy` candidate is
[`559184067e14c698cd85548fea958fd79438fa89`](https://github.com/NemanjaManic/notelens/commit/559184067e14c698cd85548fea958fd79438fa89).
Its page title matches the deployed page and differs from the preceding
revision. The exact deployed SHA was unverified at closure.
[PR #50](https://github.com/NemanjaManic/notelens/pull/50)
records the Railway implementation merged to `main` and the PR author's live
extraction and document, literature, and mixed answer checks.

| Check | Evidence |
| --- | --- |
| HTTPS and web readiness | `/demo` and `/demo/health` returned 200 with certificate validation enabled. |
| Origin, document ownership, and session deletion | The session route rejected a foreign origin with 403. A synthetic text submission returned 201 with a `Secure`, `HttpOnly`, `SameSite=Strict` cookie. Clearing the fresh document's empty question history returned 404 without the cookie and 204 with the owning cookie. Ending the session returned 204, and the old cookie then received 404. These requests used preparation and session routes and made no provider calls. |
| Private service readiness and authentication | The candidate Railway launcher binds RAG, extraction, and the fitted classifier to loopback. It requires authenticated HTTP 200 with `mode: live` from each service before it starts the web process. Deployment log evidence and unauthenticated rejection checks for the running image are pending. |
| Public corpus and in-memory documents after restart | The candidate Docker image includes the prepared RAG corpus and index. The candidate web code stores submitted documents in the Node process with a 60-minute upper limit, as documented in [B-004 configuration](configuration.md). Hosted corpus availability after restart and loss of a pre-restart synthetic document have not been exercised. Hosted expiry has not been exercised. |

## B-007 closure

Goran relayed the project administrator's approval to close B-007 on the
available Railway evidence. This decision waived further evidence collection
for closure, including the exact deployment SHA, separate confirmation of
hosting account and cost, direct private service checks, and hosted restart and
expiry checks. Those checks remain outside the verified results above.
