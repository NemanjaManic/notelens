# B-005 service integration status

**Status.** B-005 is closed for platform transport acceptance. Goran confirmed
Milica's agreement to use the fitted classifier, indexed RAG and D-005
saved-response evidence below. The default launcher and hosted CI use mocks.
Fresh provider-backed generation and D-009 final execution and scoring remain
separate work.

The platform reference for the consolidated key-free handoff is main at
`710706af0dfff60d00708e051a1c3b45fb39cc3d`. The checks below retain their
individual execution pins and service profiles.

| Integration | Evidence | Main merge |
| --- | --- | --- |
| Opt-in fitted classifier | C-005 and C-008 joint Windows replay at `9cdab928923056f31dd1f37ab4b569cc638999ab` | [PR #23](https://github.com/NemanjaManic/notelens/pull/23), `e4ffaae9d31726c7be25829ee7bbc74d970dea98` |
| Indexed RAG | Synthetic indexed service at `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4` | [PR #26](https://github.com/NemanjaManic/notelens/pull/26), `8352dbee32d40bab93393adbc264f56a5118bba3` |
| D-005 mock | Production app check at `00907a9c7ddb00f61fe2ad28c71000fc5564e1ad` against D handoff `e61140d3541e4b8b82a8cbd5e3d70e5b78ad0374` | [PR #28](https://github.com/NemanjaManic/notelens/pull/28), `aa25976956f46d1a6e419315be4ebc06dfb6dd30` |
| D-005 saved-response replay | Authenticated HTTP and app recheck against the reviewed `c7d0797` and `d41fa88` service pins | [PR #31](https://github.com/NemanjaManic/notelens/pull/31), `b8cfe3b072c5d9f7d6d262a69c72133821d43a8f`; [PR #32](https://github.com/NemanjaManic/notelens/pull/32), `229ecf9ba7b0a297bd8198564eef8c4d710f74b6` |

For locked Windows setup and the Python 3.13 interpreter selection, use the
[Windows readiness runbook](deployment.md). The commands below use
`$platformPython` from that setup.

## Published classifier evidence

The original classifier branch started from `origin/main` at `f8bba16`. Sara's published
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

## Joint Windows fitted report replay

Sara ran the pushed platform commit `9cdab928923056f31dd1f37ab4b569cc638999ab` on
Windows with classifier commit `7181a1abdf7831bb247510821c886b0e031d5de0`. She ran
C-005 first, then C-008 in a fresh app session, using the same two approved synthetic
examples. B checked the reported model versions and manifest pins against the
[Windows replay runbook](b-005-windows-replay.md).

| Bundle | Loaded model version | Startup manifest SHA-256 |
| --- | --- | --- |
| C-005 | `c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc` | `e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f` |
| C-008 | `c008-short-text-matched-v1-ec4f77b94c735790aca7cf8a3eb8a83cdc4e263ce2ad56e599e477f219fe6e8d` | `affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32` |

Both bundles returned authenticated HTTP `200` readiness on loopback port `8002` and
passed all six fitted HTTP checks each. Both classifications returned HTTP `200`
with the expected document identity, canonical SHA-256, and request-ID correlation.

All four form submissions returned HTTP `201`. Sara captured each document ID from
the report URL. Both bundles displayed **Orthopedic** for the supported example and
**Specialty uncertain** with no assigned specialty for the uncertain example. Each
report showed the pinned fitted model version and identified findings, summaries,
and answers as mocked. B verified that the four report IDs were distinct and that
each example's canonical digest matched across both bundles and the transport probe.
The receipt confirms port `8002` was released.

The private passing receipt has SHA-256
`a7a0412720b243c1aac4cb86e27ad5f64c861b985e60084f06d8502d5c2dda06`.

## Indexed RAG app verification

The [A-008 admission fix](https://github.com/NemanjaManic/notelens/pull/24) merged at
`5de01f17f04a2689ee728d218f50501cf1e7d6de`. The launcher integration and runtime
pin guard passed at PR #26 head `b4e19a9b4a69d746f3f19a798dadb07c5b106e01`.
Nemanja independently verified start and shutdown on Windows at
`14e4b9dfdfdd5832cae7f03d12e92cc5f9a00593`. The app check also passed on the
D-005 mock review snapshot `00907a9c7ddb00f61fe2ad28c71000fc5564e1ad`.

After locked setup and the production build, install the RAG indexing extra and
run the check from the platform checkout root.

```powershell
uv sync --locked --directory services/rag --python $platformPython --extra indexing --no-dev
if ($LASTEXITCODE -ne 0) { throw 'Indexed RAG setup failed.' }
& $platformPython -B scripts/project/check_rag_app.py
if ($LASTEXITCODE -ne 0) { throw 'Indexed RAG app check failed.' }
```

The partial literature question returned HTTP 200 with a citation for the
supported definition and an explicit missing start date. Both document claims
and citation highlights at `[7, 21)` and `[47, 61)` survived insufficient
literature and a stopped RAG listener. The UI displayed distinct notices, saved
a fresh answer after the outage, and all listeners closed. This profile uses
synthetic indexed RAG, mock extraction, and a mock classifier. The
[indexed RAG runbook](b-005-rag-app-check.md) describes the exact cases.

## Pinned D-005 mock app verification

Use a second clean checkout at Milica's mock handoff
`e61140d3541e4b8b82a8cbd5e3d70e5b78ad0374`. Set `$d005Checkout` to its full
path. From the platform checkout root after locked setup and the production
build, sync the pinned mock's extraction environment and run the checker.

```powershell
uv sync --locked --directory (Join-Path $d005Checkout 'services/extraction') --python $platformPython --no-dev
if ($LASTEXITCODE -ne 0) { throw 'Pinned extraction setup failed.' }
& $platformPython -B scripts/project/check_d005_app.py $d005Checkout
if ($LASTEXITCODE -ne 0) { throw 'Pinned D-005 mock app check failed.' }
```

The checker passed authenticated extraction and document-answer HTTP, request-ID
correlation, canonical document ID and digest, report isolation, and exact spans
for findings, summaries, and answers. The partial answer kept both citations
and explained that age was missing. Insufficient and out-of-scope answers
abstained and showed distinct states. All four listeners closed. The default
mock smoke, classifier report with a response double, and indexed RAG app check
also passed on the review snapshot. [PR #28 key-free CI](https://github.com/NemanjaManic/notelens/actions/runs/45161219377)

## Accepted D-005 saved-response evidence

The [historical replay](b-005-d-005-replay.md) used app revision
`0536cb56fdd1f99f9cc73110e28a90a22892cb01` and reviewed D service
`c7d0797a86061c643b0f23e6d56f8caa9e7a6813`. Milica accepted its evidence for
the saved sufficient cough answer. The pinned mock check above covers the
partial, insufficient and out-of-scope states in its own profile.

Milica also accepted B's reported key-free app recheck against D service
`d41fa880177a7855bb92e57d98673b0a7a77d36b`. The private v2 receipt records
10 extraction and six answer cases, document identity, citation highlights
and the partial-answer gap. It identifies the tested app patch at
`41b7b3433a55461eff28794745d28061df84209c`. Milica verified the receipt and
its pins. Her acceptance was based on the reported browser run.

Fresh provider-backed verification requires a separately authorized run. Record
the exact app and service revisions, model and prompt pins, document identity,
citation highlights, partial gaps, and insufficient and out-of-scope outcomes
with the execution receipt. B-007 deployment, B-009 demo acceptance and D-009
final evaluation each retain their own acceptance criteria.
