# B-005 classifier integration status

**Status, 2026-11-22.** B-005 remains open. The report can use the fitted classifier
through an opt-in local profile. The default application and hosted CI run in mock
mode. Literature, extraction and document answers use their existing mocks while A-008
and D-005 are open.

## Published classifier evidence

The branch starts from `origin/main` at `f8bba16`. Sara's published
`origin/member-c/classification` advanced to `9fc84e9`. Her branch marks C-006 complete and
records 60 focused HTTP and contract tests and seven loopback probes against the installed
classifier from `7181a1abdf7831bb247510821c886b0e031d5de0`. The probes covered readiness,
repeatable supported and uncertain results, and both no-model 503 responses. That published
snapshot predates the B verification recorded below.
[C-006 and C-007 evidence](https://github.com/NemanjaManic/notelens/blob/9fc84e9afc1ce7045dff653cb57bb9db1a29c300/docs/ml/integration.md#c-007-owner-local-check-2026-11-20)

Sara's recorded development candidate has manifest SHA-256
`e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f` and model version
`c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc`.
The bundle stays in Sara's environment. Use approved public or synthetic examples for
smoke runs. Preserve C-002's restricted access to reports and source mappings, and keep
the final test locked.

## Local fixture check

From the repository root with the locked Node workspaces installed:

```powershell
$env:NOTELENS_CLASSIFIER_TEST_PROFILE = 'fixture'
& ./node_modules/.bin/tsc.cmd --noEmit --project apps/web/tests/tsconfig.integration.json
node --test apps/web/tests/integration/classifier-http.test.ts
```

The fixture binds an ephemeral port on `127.0.0.1`, generates a temporary bearer token and
returns frozen v1 `mock` results for two synthetic documents. On Node 24.22.1, all 11
tests passed, including authenticated readiness, the readiness 503, repeatable supported
and uncertain outcomes with the expected category and five ordered scores, unique
business request IDs, and document ID and SHA-256 binding. Negative checks covered a
wrong bearer token, mismatched success and error correlation, wrong document ID and
digest, and rejection of mock results by the fitted profile. The suite closes the listener
after the run.

The local production build, default mock smoke and B-008 HTTP and log audit also passed.
The frozen contract and generated binding checks, CI workflow policy check, and 369
existing web regressions passed locally. Hosted CI was outside this local check.

## Joint fitted-model verification

Start the pinned classifier with the reviewed artifact using Sara's locked Windows
startup instructions. The runner connects only to
`127.0.0.1`. Use the same temporary local bearer token in the classifier process and
the Node test process through `NOTELENS_CLASSIFIER_SERVICE_TOKEN`. Keep the token
out of command arguments, files, chat and logs.

Prepare a local UTF-8 JSON file without a BOM from the approved English samples. It has
`supported` and `uncertain` objects. Each has `text` and `source_kind`, with source kind
`synthetic_text` or `public_text`. The supported example also has the expected v1
`category`. The runner prepares canonical text and computes each SHA-256 before sending
the classification request.

```powershell
$env:NOTELENS_CLASSIFIER_TEST_PROFILE = 'fitted'
$env:NOTELENS_CLASSIFIER_TEST_PORT = '<classifier loopback port>'
$env:NOTELENS_CLASSIFIER_TEST_MODEL_VERSION = '<reviewed model version>'
$env:NOTELENS_CLASSIFIER_TEST_EXAMPLES = '<path to approved examples JSON>'
node --test apps/web/tests/integration/classifier-http.test.ts
```

In this profile, wire mode `live` means fitted local inference. The fitted test suite
checks readiness and the pinned version, repeatable classifications, document identity
and request-ID correlation, and rejection of a wrong token and unexpected model version.

## B verification for C-007

B reviewed Sara's receipt on 2026-11-21. Sara ran the supplied B integration check on
her Windows machine using the `cd599d8` patch on `f8bba16`, the C-006 wheel verified
against `7181a1a`, Node `24.20.0`, and Python `3.13.7`. The receipt's patch and
runbook SHA-256 values match B's local copies, and its C-005 manifest digest and model
version match the pins above. The private receipt has SHA-256
`5cf6ee2e1b465c7920860dece45c0022f44efc4da6e63814f3917ad831144607`.

| Case | HTTP and wire outcome | B adapter outcome |
| --- | --- | --- |
| Fitted readiness | `200`, `ok` | `accepted` |
| Fitted supported classification | `200`, `supported`, `Orthopedic` | `accepted` |
| Fitted uncertain classification | `200`, `uncertain`, null category | `accepted` |
| Readiness without a bundle | `503`, `not_ready` | `not-ready` |
| Classification without a bundle | `503`, `configuration_required` | `unavailable` |

The receipt records six passing fitted-profile tests over two synthetic examples.
Document ID, canonical text SHA-256, request-ID correlation, repeatability, and
listener cleanup passed. The wrong-token and wrong-model-version cases were rejected.
B accepts these results as its C-007 adapter verification from Sara's run.

On 2026-11-22 Milica reported a passing D evaluator run at `585ef0f` against the same
C-005 bundle, with `supported / Orthopedic` and `uncertain / null`. Both calls reached the
web mock consumer over HTTP and returned 200 from the classifier. That consumer rejected
the fitted responses with `MOCK_MODE_REQUIRED`. The opt-in profile below is the report
path for those responses.

## Opt-in report profile

Start Sara's pinned classifier on loopback with the reviewed bundle and a temporary
service token. Build the web app from this checkout, then use a PowerShell session that
already holds the same server-side `NOTELENS_CLASSIFIER_SERVICE_TOKEN`. From the
repository root, use the model version above and the classifier's loopback port:

```powershell
$env:NEXT_TELEMETRY_DISABLED = '1'
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'The web build failed.' }
$env:NOTELENS_LOCAL_CLASSIFIER_PORT = '8002'
$env:NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION = 'c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc'
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/start_mock.py --fitted-classifier
```

Open the printed localhost URL. The report badge identifies the local classifier profile
and labels findings, summaries and answers as mocked. A classifier outage or missing
profile configuration leaves the specialty unavailable. The regular launcher without
the flag starts the all-mock workspace, independent of the classifier settings in the
parent shell.

The local report check uses the built app and real loopback HTTP with a test double
that supplies fitted-classifier response shapes. It verifies report HTTP 200 for
`supported / Orthopedic`, `uncertain` with no selected specialty, an unavailable
classifier, and rejection of a mismatched digest. It also checks session isolation,
request IDs, and that the service token stays server-side.

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_classifier_report.py
```

The fitted C-005 adapter evidence above came from Sara's run before the app wiring.
The fitted bundle is absent from this checkout. To verify the new report path against
that bundle, use one permitted English sample for each outcome that passes the app's
language admission and has a confirmed fitted response. The earlier short supported
sample and synthetic uncertain probe fail the app's language admission. The joint
fitted report replay and the remaining service integrations after A-008 and D-005
are still pending.
