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

## Remaining deployment acceptance

B-007 stays open. The local profile uses loopback HTTP and tests only the mock
stack. B-005 acceptance and team approval of the host, account, and costs are
required for a deployment rehearsal. On that approved target, verify TLS,
service authentication and readiness, public-corpus persistence across restart,
and memory-only document handling across expiry and restart. Record deployment
URLs after an actual deployment. The existing local session behavior is
documented in [B-004 configuration](configuration.md).
