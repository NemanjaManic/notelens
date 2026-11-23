# B-005 Windows classifier report replay

Run the C-005 bundle first and the C-008 bundle second on Sara’s Windows machine.
Use the same two approved synthetic examples from Milica’s private JSON file in both runs.

## Prepare the two working copies

- **Platform**. In a separate working copy, check out the B-005 branch at the commit
  that adds this runbook and the opt-in report profile. Record the full commit SHA
  in the replay receipt. The earlier C-007 evidence and adapter commits predate
  the report profile.
- **Classifier**. Use the reviewed C-007 classifier code from
  `7181a1abdf7831bb247510821c886b0e031d5de0` and its installed wheel in Sara’s locked
  Python 3.13.7 environment. Use the existing trusted local bundles in the classifier
  checkout. Each bundle directory contains its own `model.joblib` and `model-manifest.json`.
  The [pinned classifier instructions][classifier-pin] identify the C-005 and C-008
  startup manifests. The frozen evaluation manifest is separate from the C-008 startup
  manifest.
- **Inputs**. Keep Milica’s original JSON and the converted probe file outside the
  working copies. Use the exact two approved synthetic texts for both models.

From the platform root, use Python 3.13, Node 24, npm 11, and uv. The launcher needs the
three service-local environments even though the report uses an external classifier.

```powershell
$ErrorActionPreference = 'Stop'
$env:NEXT_TELEMETRY_DISABLED = '1'
foreach ($service in @('services/rag', 'services/classifier', 'services/extraction')) {
  uv sync --locked --directory $service --python 3.13 --no-dev
  if ($LASTEXITCODE -ne 0) { throw "Locked sync failed for $service." }
}
npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'Locked Node install failed.' }
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Platform build failed.' }
```

## Convert Milica’s JSON for the fitted probe

Milica’s original JSON has an `examples` array. The probe reads a UTF-8 file
without a BOM with top-level `supported` and `uncertain` objects. Passing the
original file directly fails before the first HTTP request.

In the parent PowerShell window, identify which row has the expected
`supported / Orthopedic` result and which has the expected `uncertain / null`
result. Set the zero-based indexes below to match your file. The example assumes
the supported input is first and reads each row’s `text` field. Keep the two
decoded text values exactly as supplied, including line breaks and whitespace.

```powershell
$originalExamplesPath = (Resolve-Path -LiteralPath 'C:\private\milica-examples.json').Path
$originalExamples = Get-Content -LiteralPath $originalExamplesPath -Raw -Encoding UTF8 |
  ConvertFrom-Json -ErrorAction Stop
$rows = @($originalExamples.examples)
$supportedIndex = 0
$uncertainIndex = 1
if ($rows.Count -ne 2 -or $supportedIndex -eq $uncertainIndex -or
    $supportedIndex -notin 0, 1 -or $uncertainIndex -notin 0, 1) {
  throw 'Select the two approved inputs from the examples array.'
}

$supportedText = $rows[$supportedIndex].text
$uncertainText = $rows[$uncertainIndex].text
if ($supportedText -isnot [string] -or [string]::IsNullOrWhiteSpace($supportedText) -or
    $uncertainText -isnot [string] -or [string]::IsNullOrWhiteSpace($uncertainText)) {
  throw 'The selected inputs must contain non-empty text strings.'
}

$probeExamples = [ordered]@{
  supported = @{ text = $supportedText; source_kind = 'synthetic_text'; category = 'Orthopedic' }
  uncertain = @{ text = $uncertainText; source_kind = 'synthetic_text'; category = $null }
}
$probeExamplesPath = Join-Path (Split-Path -Parent $originalExamplesPath) (
  [IO.Path]::GetFileNameWithoutExtension($originalExamplesPath) + '-fitted.json'
)
[IO.File]::WriteAllText($probeExamplesPath, ($probeExamples | ConvertTo-Json -Depth 4),
  [Text.UTF8Encoding]::new($false))
```

In the same parent window, enter the working-copy paths and open both shells.
They inherit the converted file path and the same temporary bearer token. Keep
the token in process environments.

```powershell
$platformRoot = 'C:\path\to\reviewed-platform'
$classifierRoot = 'C:\path\to\reviewed-classifier'
$env:NOTELENS_CLASSIFIER_TEST_EXAMPLES = $probeExamplesPath
$env:NOTELENS_CLASSIFIER_SERVICE_TOKEN = [Guid]::NewGuid().ToString('N')
Start-Process powershell.exe -ArgumentList '-NoProfile', '-NoExit' -WorkingDirectory $classifierRoot
Start-Process powershell.exe -ArgumentList '-NoProfile', '-NoExit' -WorkingDirectory $platformRoot
```

## 1. Run C-005

In the **classifier** window, start the fitted service on `127.0.0.1:8002`.
Set `$classifierPython` to the reviewed environment’s interpreter if it uses a different
local directory.

```powershell
$env:NOTELENS_CLASSIFIER_MODE = 'live'
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
& $classifierPython -B -m notelens_classifier --port 8002 `
  --development-model .cache/c005-frozen-uncertainty-v1 `
  --model-manifest-sha256 e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f
```

In the **platform** window, pin the C-005 version and run the transport and report
procedure below.

```powershell
$env:NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION = 'c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc'
```

### C-005 readiness troubleshooting

Keep the classifier in the foreground. If it exits, record the first redacted startup
error and the exit code before trying again. If port `8002` is already listening before
startup, use `Get-NetTCPConnection -LocalPort 8002 -State Listen` to identify the owner.
Stop a previous replay only if you own its process.

From the **platform** window, check readiness while the classifier is running. This uses
the token inherited by the platform window and prints only readiness metadata.

```powershell
if (-not $env:NOTELENS_CLASSIFIER_SERVICE_TOKEN) {
  throw 'The platform window did not inherit the classifier token.'
}
$headers = @{ Authorization = "Bearer $env:NOTELENS_CLASSIFIER_SERVICE_TOKEN" }
try {
  $ready = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8002/health/ready' `
    -Headers $headers -TimeoutSec 5 -MaximumRedirection 0 -ErrorAction Stop
} catch {
  $response = $_.Exception.Response
  if ($null -eq $response) {
    throw 'No readiness HTTP response. Check the classifier console and port 8002.'
  }
  throw "Classifier readiness returned HTTP $([int]$response.StatusCode)."
}
$health = $ready.Content | ConvertFrom-Json
if ($ready.StatusCode -ne 200 -or $health.service -cne 'classifier' -or
    $health.status -cne 'ok' -or $health.mode -cne 'live' -or
    $health.model_version -cne $env:NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION) {
  throw 'Readiness did not identify the pinned fitted C-005 model.'
}
[pscustomobject]@{
  HttpStatus   = $ready.StatusCode
  ModelVersion = $health.model_version
}
```

- **No HTTP response**. Check whether the process exited or whether the expected
  classifier is listening on loopback port `8002`.
- **HTTP 401**. Confirm both shells inherited the same temporary token. If needed,
  reopen both shells from the same parent after generating a fresh token.
- **HTTP 503 or a mismatched mode or version**. Check that the classifier used the
  reviewed interpreter and the C-005 bundle. Verify `model-manifest.json` against
  the C-005 pin above, `model.joblib` against the manifest’s `artifact_sha256`, and
  the installed package versions against its `packages` entries.

Continue with the fitted probe and both reports after authenticated HTTP `200` confirms
`live` mode and the pinned C-005 version. If readiness still fails, record the observed
status or redacted startup error and mark both downstream checks blocked.

## Transport and report procedure for each bundle

In the platform window, run the authenticated fitted HTTP probe and then launch the app.
Resolve and invoke an installed Python 3.13 executable explicitly so the launch
works when the shell’s default Python is 3.11.

```powershell
$env:NOTELENS_CLASSIFIER_TEST_PROFILE = 'fitted'
$env:NOTELENS_CLASSIFIER_TEST_PORT = '8002'
$env:NOTELENS_CLASSIFIER_TEST_MODEL_VERSION = $env:NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION
$env:NOTELENS_LOCAL_CLASSIFIER_PORT = '8002'
node --test apps/web/tests/integration/classifier-http.test.ts
if ($LASTEXITCODE -ne 0) { throw 'Fitted classifier transport check failed.' }
$platformPython = uv --offline python find --system 3.13
if ($LASTEXITCODE -ne 0 -or -not $platformPython) { throw 'Could not locate Python 3.13.' }
& $platformPython -B scripts/project/start_mock.py --fitted-classifier
```

If uv cannot find an existing managed Python 3.13 installation, set
`UV_PYTHON_INSTALL_DIR` in the platform window to the custom installation root
that contains the `cpython-3.13.*` directory. Then repeat the lookup and launch
commands above.

```powershell
$env:UV_PYTHON_INSTALL_DIR = 'C:\path\to\uv\python'
```

To select the interpreter directly, use its full path in the platform window
after the fitted probe has passed. Run this from the platform checkout root.

```powershell
$platformPython = (Resolve-Path -LiteralPath 'C:\path\to\Python313\python.exe').Path
& $platformPython -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 13))"
if ($LASTEXITCODE -ne 0) { throw 'Select a Python 3.13 executable.' }
& $platformPython -B scripts/project/start_mock.py --fitted-classifier
```

Open the printed `localhost` URL. On the demo page, submit each of Milica’s two
examples through the pasted-text form as synthetic input. Use the exact text from
the converted file and check both reports.

| Input | Classifier response expected | Report expected |
| --- | --- | --- |
| Supported | HTTP 200, `supported`, `Orthopedic` | **Orthopedic** with the pinned model version |
| Uncertain | HTTP 200, `uncertain`, null category | **Specialty uncertain**, with no assigned specialty and the pinned model version |

The page should identify the **Local classifier profile** and show that findings,
summaries and answers are mocked. Capture the submission HTTP status (expected `201`),
the document ID from the report URL, and the observed label and model version for each
row. Record the canonical SHA-256 from Milica’s admission receipt or compute it from the
exact submitted text using NFC normalization, LF newlines and UTF-8, preserving
whitespace. Keep the receipt to metadata rather than saving request bodies, bearer
tokens, browser cookies or a HAR capture.

Record the fitted probe result separately. It checks readiness, both repeatable
classifications, canonical digest and document-ID binding, request-ID correlation,
and rejection of a wrong token or model version. The probe creates its own document
and request IDs. The app validates the same bindings before showing the classifier
result, and its rendered report does not expose the raw classifier request ID.
If the troubleshooting steps do not resolve a failure, record it and stop that bundle’s replay.

After C-005, close the demo tab and stop the platform launcher with Ctrl+C, then stop
the classifier with Ctrl+C. Confirm port `8002` is free before starting C-008.

## 2. Run C-008

In the classifier window, start the selected C-008 bundle with its matching startup
manifest.

```powershell
& $classifierPython -B -m notelens_classifier --port 8002 `
  --development-model .cache/c008-short-text-v1/matched-policy `
  --model-manifest-sha256 affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32
```

In the platform window, switch the model version and repeat the same transport and
report procedure. The platform build can be reused. A fresh app process starts with
empty document sessions, so submit both examples again.

```powershell
$env:NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION = 'c008-short-text-matched-v1-ec4f77b94c735790aca7cf8a3eb8a83cdc4e263ce2ad56e599e477f219fe6e8d'
```

### C-008 fallback after HTTP 201

If the browser runner records HTTP `201` for `POST /api/documents/submit` but cannot read
the response body, let the app finish navigating in the same browser tab and session.
Use the `document` query parameter from the resulting report URL
(`http://localhost:<web-port>/demo?document=<id>`) as the document ID. In a runner,
wait for navigation, then read the query parameter from the current tab URL.
For a manual replay, read the ID from the address bar. If the report already opened,
use that report for the check.

Check the rendered specialty state, fitted-model version, and mock notices on the
report page. Repeat for the other example. Record the submission status, URL document
ID, canonical SHA-256, rendered specialty, and model version for each example. Keep
the fitted HTTP probe’s request-ID correlation result as a separate receipt entry.

If the app stays on the submission page or shows an error, record the HTTP status
and the redacted page notice or runner error. Treat that report as unverified.

After the run, close the demo tab, stop both launchers and close the two replay
shells. Clear the temporary token from the parent shell.

```powershell
Remove-Item Env:NOTELENS_CLASSIFIER_SERVICE_TOKEN
```

[classifier-pin]: https://github.com/NemanjaManic/notelens/blob/c67066743a505aa62920fada5689d7fbf2362c0c/docs/ml/integration.md#start-and-verify-the-development-model
