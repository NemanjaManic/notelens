# B-005 key-free RAG app check

The app uses the reviewed A-008 prompt admission fix. The check runs the
[portable indexed RAG service](../rag/evaluation/serve_indexed_demo.py) from commit
`d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4`. It checks that the local RAG and contract
source trees match that revision. Classifier and extraction use the local mocks.
The indexed service uses only synthetic data and requires no provider credentials.

Use Windows, Python 3.13, Node 24, npm 11 and uv. From the repository root,
install the locked dependencies, build the web app, and run the check.

```powershell
$ErrorActionPreference = 'Stop'
$env:NEXT_TELEMETRY_DISABLED = '1'
uv sync --locked --directory services/rag --python 3.13 --extra indexing --no-dev
if ($LASTEXITCODE -ne 0) { throw 'Indexed RAG setup failed.' }
foreach ($service in @('classifier', 'extraction')) {
  uv sync --locked --directory "services/$service" --python 3.13 --no-dev
  if ($LASTEXITCODE -ne 0) { throw "Mock setup failed for $service." }
}
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Web dependency setup failed.' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
$platformPython = uv --offline python find --system 3.13
if ($LASTEXITCODE -ne 0 -or -not $platformPython) { throw 'Could not locate Python 3.13.' }
& $platformPython -B scripts/project/check_rag_app.py
if ($LASTEXITCODE -ne 0) { throw 'The key-free RAG app check failed.' }
```

The runner starts a production web process and three services on independent
loopback ports with a temporary service token. It prepares the built-in
synthetic document over HTTP and opens the rendered answer and citation pages.

| Case | Required app result |
| --- | --- |
| Document-only baseline | Both occurrences of the supported document claim are cited. |
| “What is the synthetic demo topic, and when did it begin?” | HTTP 200, partial literature answer, a linked citation for the supported definition and an explicit start-date gap. |
| Mixed question with RAG running and insufficient literature | The answer keeps both supported document claims and citations. It shows the insufficient-evidence notice. |
| Same mixed question with RAG stopped | The answer keeps both supported document claims and citations. It shows the unavailable notice and saves a new turn. |

Each document citation keeps the same document and answer identifiers and
highlights the correct repeated quote at `[7, 21)` or `[47, 61)` in Unicode
code points. The runner stops only its indexed RAG process tree for the outage
case, verifies the RAG port refuses connections, then checks shutdown of all
four listeners. It never opens the synthetic literature URL.

This checks B’s app and transport behavior against the pinned key-free service.
Provider-backed behavior and overall B-005 acceptance remain pending.

## Local verification

The production build, the pinned service’s standalone TCP smoke, the app check
above, and the default mock smoke passed on Windows. The app check returned
HTTP 200 for the partial question and verified both citation highlights in
each mixed fallback. All four listeners stopped.
