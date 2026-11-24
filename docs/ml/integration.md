# C classifier local development handoff

**Updated** 2026-11-22. **Owner** Sara / C.

The development bundle originally verified for C-007 combines the Logistic
Regression pipeline fitted on the frozen C-002 split with the C-005 uncertainty policy. It runs
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
and 11 subtests.

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

## C-007 owner-local check, 2026-11-20

Verified the published C-006 commit
`7181a1abdf7831bb247510821c886b0e031d5de0` on `member-c/classification`.
All 14 classifier files in the installed wheel matched the clean
checkout's package files. The isolated Python 3.13.7 environment
ran the focused HTTP and frozen-contract suites with **60 passing tests**.

The installed launcher used the C-005 manifest SHA-256
`e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f`
and reported model version
`c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc`.
All seven authenticated loopback HTTP probes passed.

| Probe | Result |
| --- | --- |
| Readiness with the pinned bundle | HTTP 200 with the expected model version |
| Clear synthetic document, twice | HTTP 200 and repeatable `supported` with `Orthopedic` |
| Weak synthetic document, twice | HTTP 200 and repeatable `uncertain` with a null category |
| Readiness without a selected bundle | HTTP 503 and `not_ready` |
| Classification without a selected bundle | HTTP 503 and `configuration_required` |

The classifier returned the original `doc_id` and `text_sha256`,
five ordered scores, the admitted request ID in the response header,
and `Cache-Control: no-store`. Both local test processes stopped and
their ports closed. Captured service logs excluded the synthetic
document texts and temporary token.

## C-007 coordinated verification, 2026-11-21

Goran recorded B's verification of the classifier commit and C-005 bundle
pinned above. On platform baseline `f8bba16`, B's test adapter accepted
readiness with the model, `supported` with `Orthopedic`, and `uncertain`
with a null category. The adapter verified the document ID, canonical
SHA-256 and request ID. With no bundle, it reported `not-ready` for
readiness (`503`, `not_ready`) and `unavailable` for classification
(`503`, `configuration_required`). Six fitted-profile checks passed.

Milica confirmed D's independent authenticated replay on evaluator commit
`585ef0f`. The receipt matched the classifier commit, model version and
manifest SHA-256 from the B run. The model artifact matched the local
`model.joblib` SHA-256
`3bbf1c648c6ebd69036ee933c58b7e96cf1a0f5bf60975d1cafe7f59ec09fd6a`.
D validated the document ID, canonical SHA-256 and five scores in contract
order. Both fitted outcomes were repeatable, and D recorded `uncertain`
with a null category as an abstention. D distinguished mock and fitted
responses, rejected wrong fitted modes and model versions, and reported
16 passing targeted evaluator tests.

Receipt checksums for the local evidence:

| Receipt | SHA-256 |
| --- | --- |
| B adapter `b005-joint/receipt.json` | `5cf6ee2e1b465c7920860dece45c0022f44efc4da6e63814f3917ad831144607` |
| D evaluator `c007-owner-c005-transport-v1.json` | `bac46d0535a099daf67038b00b81bcf96496c0e7dd4619772133ee1886fa1155` |

C-007 is complete for authenticated local inference with synthetic inputs.
B-005 remains open for web integration. On the tested platform baseline,
the report consumer accepted mock responses and rejected fitted responses
under its `MOCK_MODE_REQUIRED` policy even though the classifier returned
HTTP 200. Both checks ran on loopback without provider calls.

## C-008 selected bundle, 2026-11-22

Sara selected the short-text model with the existing C-005 policy. The
classifier code is the same as in the C-007 checks. Use the Windows
environment and token setup above, then start the selected bundle with its
own manifest checksum:

```powershell
& $classifierPython -B -m notelens_classifier --port 8002 `
  --development-model .cache/c008-short-text-v1/matched-policy `
  --model-manifest-sha256 affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32
```

Owner-local HTTP verified readiness with authentication, `401` without
authentication, and `200` for `supported` with `Orthopedic` and `uncertain`
with a null category. Both classifications preserved document identity,
canonical digest and request ID. The separate frozen evaluation manifest
reproduced all 50 synthetic follow-up outputs. [Frozen model card](model-card.md)

## B and D handoff

- **B:** The [C-012 handoff](f011-classifier-handoff.md) has the scoped mock
  failure patch for the published checkpoint. Review that contribution
  separately from the development model. Shared readiness and failure probes
  remain in F-011.
- **D:** C verified the development groups and pinned canonical text digests
  before annotating. The private C-010 handoff contains 10 primary annotations
  and one independent review, with full-document confirmation and a checksum
  manifest. On 2026-11-22 Sara reported that Milica received this package and
  the separate revised independent review for D-013. D owns adjudication.
- **Final measurement:** The [model card](model-card.md#locked-final-results)
  records the frozen model and aggregate held-out results.
