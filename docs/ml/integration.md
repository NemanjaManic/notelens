# C classifier local development handoff

**Date:** 2026-11-19. **Owner:** Sara / C.

The [current development candidate](experiments/ambiguity-policy-v1.md)
was trained on the provisional split. It runs
without providers and accepts only authenticated loopback requests. Use
public and synthetic examples in the local demo. The [validation report](validation-report.md)
records the candidate's results and its observed false acceptance of unrelated
text. This package is ready for owner-local checks with a trusted local build.

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
& $classifierPython -B -m notelens_classifier.training.development --output .cache/c-development-new-run
```

Initial setup needs the locked wheels in the uv cache. Use Python 3.13.7 for
the environment used in this check. The run prints the model manifest checksum
and saves the model, manifest and aggregate metrics under the chosen ignored
directory. The verified original comparison is under
`.cache/c-development-comparison-v1-verified`. The current candidate
builds on that pinned reference. See the
[short-text training command](experiments/short-text-improvement-v1.md#reproduction-and-receipts)
and the [ambiguity policy command](experiments/ambiguity-policy-v1.md#reproduction-and-evidence).
Load only a trusted artifact created locally. A checksum identifies bytes and
must come from the trusted training receipt. [Model persistence guidance](https://scikit-learn.org/stable/model_persistence.html)

## Start and verify the development model

Use the explicit launcher for real local inference. Configure a private
local service token for both client and service. The example generates one
for this local session. Run the launcher from the repository root:

```powershell
$env:NOTELENS_CLASSIFIER_MODE = 'live'
$env:NOTELENS_CLASSIFIER_SERVICE_TOKEN = [Guid]::NewGuid().ToString('N')
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
& $classifierPython -B -m notelens_classifier --port 8002 `
  --development-model .cache/c-ambiguity-policy-v1-selected `
  --model-manifest-sha256 e0674f10f2adb1c81ffdac1d157d10947662d0fff913fd37352d973fdf7c61a2
```

Authenticated `GET /health/ready` returns the model version. POST a frozen
`ClassificationRequest` with a canonical UUID in `X-Request-ID` and bearer
authentication. The result binds `doc_id` and `text_sha256` and returns five
probabilities in canonical category order. The wire mode `live` identifies
actual inference by a fitted local model. This artifact remains a development
candidate. Stop the local service with Ctrl+C. For the key-free fixture service,
use the [mock launcher](../../services/classifier/README.md#local-start-and-scenarios).

Owner verification on Python 3.13.7 passed 121 classifier tests and the
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
