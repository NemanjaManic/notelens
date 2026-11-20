# C classifier local development handoff

**Updated** 2026-11-20. **Owner** Sara / C.

The current development bundle combines the Logistic Regression pipeline
fitted on the frozen C-002 split with the C-005 uncertainty policy. It runs
on authenticated loopback without providers. Use public and synthetic
examples in the local demo. The validation report records the observed
short-text limitations and mixed-text acceptance.
[C-005 evidence](validation-report.md#c-005-uncertainty-selection-on-the-frozen-split-2026-11-20)

## Reproduce the candidate on Windows

From the repository root with the authorized audited local inputs, use the
classifier lock and select a new ignored output directory:

```powershell
$classifierUv = Join-Path (Get-Location).Path '.cache/classifier-tooling/Scripts/uv.exe'
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$env:UV_LINK_MODE = 'copy'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:TEMP 'notelens-c-comparison-py313'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $classifierUv sync --locked --offline --directory services/classifier --group comparison
$classifierPython = Join-Path $env:UV_PROJECT_ENVIRONMENT 'Scripts/python.exe'
```

Initial setup needs the locked wheels in the uv cache. Use Python 3.13.7 for
the environment used in this check. Reproduce the frozen comparison
and then run the C-005 selection command against its pinned manifest.
The commands produce the model, manifest and aggregate metrics in ignored
local directories. Load only a trusted artifact and use the manifest checksum
from its run receipt.
[C-004 command](experiments/c004-frozen-comparison-v1.md#reproduce-locally) ·
[C-005 command](validation-report.md#score-meaning-and-reproducibility)

## Start and verify the development model

Use the explicit launcher for real local inference. Configure a private
local service token for both client and service. The example generates one
for this local session. Run the launcher from the repository root:

```powershell
$env:NOTELENS_CLASSIFIER_MODE = 'live'
$env:NOTELENS_CLASSIFIER_SERVICE_TOKEN = [Guid]::NewGuid().ToString('N')
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
& $classifierPython -B -m notelens_classifier --port 8002 `
  --development-model .cache/c005-frozen-uncertainty-v1 `
  --model-manifest-sha256 e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f
```

Authenticated `GET /health/ready` returns the model version. POST a frozen
`ClassificationRequest` with a canonical UUID in `X-Request-ID` and bearer
authentication. The result binds `doc_id` and `text_sha256` and returns five
probabilities in canonical category order. The wire mode `live` identifies
actual inference by a fitted local model. This artifact remains a development
candidate. Stop the local service with Ctrl+C. For the key-free fixture service,
use the [mock launcher](../../services/classifier/README.md#local-start-and-scenarios).

At startup the loader checks the supplied manifest digest, the package
versions and the artifact digest before deserialization. It checks the
fitted pipeline, estimator type and label mapping, then validates a
synthetic classification result before serving requests. An explicit
missing or mismatched artifact stops the launcher with a safe message.
With live mode and service authentication configured but no bundle
selected, readiness and valid classification requests return HTTP 503.

## C-006 package verification

The standalone wheel was built offline from `services/classifier` and
installed into a separate Python 3.13.7 environment with the locked
training dependencies. The executed wheel is
`.cache/c006-wheel/notelens_classifier-0.1.0-py3-none-any.whl` with SHA-256
`20282ac85a64ed39d84d567badff1f74b375af0f40be24f053e957a553bb966f`.
The wheel carries service code and fixtures. The trained bundle stays
in its ignored local directory and is selected explicitly at startup.

The installed launcher passed 11 real loopback HTTP probes. These
covered liveness and readiness, repeatable supported and uncertain
classifications, the document ID and canonical digest, all five ordered
scores, auth denial, a bad document digest and the live-without-bundle
configuration error. The missing-artifact and wrong-checksum launch
attempts exited before serving. Both test processes stopped, the test
ports closed, and service output omitted the synthetic bodies and
temporary token. The classifier and MTSamples suites passed 158 tests
and 11 subtests. Coordinated B/D verification remains in C-007.

Earlier owner verification on Python 3.13.7 passed 121 classifier tests and the
installed binding suite. The default locked mock environment passed 103 tests
with four test modules skipped because optional ML dependencies were absent.
Four targeted final measurement tests passed after strengthening the replay
reservation. The classifier suite ran with this command:

```powershell
& $classifierPython -B -m pytest services/classifier/tests -q -p no:cacheprovider -W error::starlette.exceptions.StarletteDeprecationWarning
```

A separate real Uvicorn loopback run against the
trained artifact passed authenticated readiness, unauthenticated denial,
two repeatable synthetic classification payloads (`supported` and `uncertain`),
and process and port cleanup. The test checked that the token and synthetic
body text did not appear in captured service logs.

## B and D handoff

- **B:** The [C-012 handoff](f011-classifier-handoff.md) has the scoped mock
  failure patch for the published checkpoint. Review that contribution
  separately from the development model. Shared readiness and failure probes
  remain in F-011. Coordinated real-inference integration remains in C-007.
- **D:** Assign development-only primary annotations and independent reviews
  for C through D-003 after the grouped split and canonical text/ID handoff.
  C will check each assigned document against the development group list and
  pinned canonical text digest before opening it. Record substantive review
  exposure by document and group so related cases remain in development.
  Keep C's primary and secondary files separate and route adjudication to D.
  Actual assignments and annotations are pending.
- **Final measurement:** See the [model card draft](model-card.md) for the
  evidence needed to freeze and measure the held-out evaluation.
