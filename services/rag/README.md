# NoteLens RAG Local Development

Owner: Nemanja (A). Verified on Windows with Python 3.13.5 and uv 0.12.5.

This is a runnable, owner-local mock service using B's frozen v1.0.0 bindings.
It is not a production RAG implementation or the shared-foundation checkpoint. The prepared
401-topic/617-passage corpus is unchanged. A read-only adapter can now load it for future
indexing; the synthetic HTTP routes still return their explicit mock examples.

The 2026-11-14 local continuation adds an OpenAI embedding adapter and a key-free
token/cost preflight. See [embedding configuration and evidence](../../docs/rag/embeddings.md).
Store the server-side key only in the ignored `services/rag/.env`, using the empty
`.env.example` template. An API key alone does not activate paid calls.

The [local Chroma index CLI](../../docs/rag/indexing.md) now provides versioned public
data persistence, integrity verification and explicit interrupted-run handling.
Index activation is separate from these still-synthetic HTTP endpoints.

On 2026-11-15 the explicitly resumed live embedding run completed: all 617 prepared
passages now have real text-embedding-3-small vectors in the local Chroma index.
Readback and zero-call reuse passed. See [the live-run record](../../docs/rag/indexing.md#successful-explicit-resume-2026-11-15).
The HTTP routes remain mock; question retrieval and generation are later increments.

Educational demo. Not a doctor. Do not submit real personal medical reports.

The 2026-11-17 [safe diagnostics increment](../../docs/rag/assessment-trial.md#safe-validation-diagnostics-2026-11-17)
locates rejected model output by rule and numeric field path without retaining raw
responses. At that checkpoint, all 506 local tests passed without new provider
requests. The original trial remains halted and its original cause is unknown.

The [single CQ-01 retry](../../docs/rag/assessment-retry.md) was separately approved
and attempted on 2026-11-17 after all 539 offline tests passed again. Its response
failed exact-quote validation (quote_mismatch). The retry is halted, the cumulative
reference-price reservation is USD 0.0027622 and the activation flag is false.
See [actual results](../../docs/rag/assessment-retry-results.json). No further
provider attempt is approved; default inspection remains key-free.

The [v2 evidence-selection increment](../../docs/rag/evidence-selection.md) is now
checked locally: the model selects offered evidence IDs, and Python supplies exact
canonical quotes/offsets. All 585 tests pass. Retrieval and mock HTTP routes are
unchanged. Its first separately approved actual public probe is recorded below.

The [single v2 trial](../../docs/rag/selection-trial.md) was approved and run once
on 2026-11-18 after all 623 offline tests passed again. CQ-01 produced a validated
full-coverage assessment: 11,029 input tokens, 204 output tokens and four exact
evidence references. A key-free cache replay made zero provider calls. The old
histories are unchanged and activation is false again. See [actual results](../../docs/rag/selection-trial-results.json).
No other case, additional generation, final literature answer or shared HTTP
integration is approved/completed by this one probe.

The subsequent [two-case coverage trial](../../docs/rag/coverage-trial.md) completed
on 2026-11-18 after all 659 offline checks passed. CQ-02 correctly retained the
supported COVID-19 cause and identified missing contagiousness duration; CQ-08
found no evidence for the requested Serbia 2025 incidence rate. Both actual
results replayed without a key or provider request, with four ledgers unchanged.
The three public v2 probes now cover full/partial/none examples; they are not a
general quality benchmark. Cumulative reserved reference cost is USD 0.0087813
within the USD 0.02 allowance; actual billing is unverified. The approved attempts
are consumed and activation is disabled.

The 2026-11-18 owner-local pipeline adds question decomposition, v2 evidence
selection and cited answer composition through the existing HTTP contract. The
local tests inject the pipeline via `create_app(settings, backend=service)` and
simulate the SDK responses. Question decomposition sees only the exact question.
It checks returned anchors and assigns part IDs before evidence selection. The
original question also goes to the assessor for its coverage check. Exact anchors
alone cannot establish whether the model captured all the requested facts.
Unclear, non-English and out-of-scope fixture questions return a fixed English
422 response before ranking. All 727 RAG tests passed. The default app uses its
mock backend. Live question decomposition, answer evaluation and team integration
remain open.

## Install and verify

From the repository root in PowerShell, with Python 3.13 already installed:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
uv --system-certs sync --locked --directory services/rag --python 3.13 --dev
uv run --locked --offline --directory services/rag python -m pytest
```

First installation requires package-registry access. Subsequent checks use the locked
local environment offline. This service owns its pyproject.toml, uv.lock and .venv;
root/shared package files are not changed by this service installation. Its local
notelens-contracts dependency comes from ../../contracts/generated/python, imported
through B's published dependency commit. Python 3.14 service execution is unverified.

The default locked install runs the key-free checkpoint mock and core RAG tests.
Use the optional `indexing` extra to open Chroma and run the persistent-index
and indexed-startup checks.

```powershell
uv --system-certs sync --locked --directory services/rag --python 3.13 --dev --extra indexing
uv run --locked --offline --directory services/rag --extra indexing python -m pytest
```

The indexing extra retains the checkpoint's Chroma version and its open advisory
finding. See the [integration handoff](../../docs/rag/development-handoff.md#configured-index-startup)
for the pinned assets and explicit backend setup.

## Run locally

For the separate candidate-ranking CLI over registered public development questions,
see [retrieval commands, allowance and limitations](../../docs/rag/retrieval.md#public-development-cli-and-separate-query-allowance).
It does not change the frozen-contract mock HTTP routes documented below.

The approved 2026-11-15 public trial has completed ten real searches, each returning
five sources. All ten can now be repeated locally without API calls using their
cached query vectors. For example, from this checkout with its existing local index:

```powershell
uv run --locked --offline --directory services/rag --extra indexing python -m notelens_rag.query_smoke --question-id CQ-01
```

This prints exact public passage text and sources. It does not generate an answer
or assert answerability. Fresh clones do not include the ignored index/query cache;
the default mock remains independent of those artifacts.

```powershell
$env:NOTELENS_RAG_MODE = 'mock'
$env:NOTELENS_RAG_MOCK_SCENARIO = 'sufficient'
uv run --locked --offline --directory services/rag uvicorn notelens_rag.main:app --host 127.0.0.1 --port 8001 --no-proxy-headers --no-access-log
```

Use a separate terminal for requests. Ctrl+C stops the process started in that terminal.
The automated smoke test starts and stops its own process on an ephemeral loopback port;
it does not leave a server running.

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8001/health/live'
Invoke-RestMethod -Uri 'http://127.0.0.1:8001/health/ready'

$ragHeaders = @{ 'X-Request-ID' = [guid]::NewGuid().ToString() }
$ragBody = @{ schema_version = '1.0.0'; question = 'What is the synthetic demo topic?' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/v1/retrieve' -Headers $ragHeaders -ContentType 'application/json' -Body $ragBody

$ragHeaders = @{ 'X-Request-ID' = [guid]::NewGuid().ToString() }
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/v1/literature-answer' -Headers $ragHeaders -ContentType 'application/json' -Body $ragBody
```

Only that exact synthetic question is admitted in mock mode. Other questions receive
422/validation_failure with an English fixture-only explanation. This is not a language
detector or real input-policy implementation. Concepts/specialty hints are schema-checked
but do not run a classifier or affect a real search.

## Implemented behavior

- GET /health/live returns a truthful process/mode record.
- GET /health/ready reports ready by default in mock mode. To exercise F-011's
  key-free unavailable case, start the service with `NOTELENS_RAG_MODE=mock`
  and `NOTELENS_RAG_MOCK_READY=false`. Readiness returns HTTP 503 with
  `status=not_ready`, `mode=mock` and a reason. Liveness still returns HTTP 200
  with `status=alive`. Omit the flag or set it to `true` for normal mock
  readiness. Unconfigured live mode reports HTTP 503.
- POST /v1/retrieve and /v1/literature-answer return explicit synthetic mock examples.
- Business POSTs require one canonical lowercase UUID X-Request-ID. Valid IDs are echoed
  on successes/errors. Bad or duplicate IDs produce 400 with a fresh diagnostic UUID.
- Health GETs ignore incoming correlation IDs. Health authentication errors use a fresh
  diagnostic ID and WWW-Authenticate: Bearer, as required by the frozen contract.
- JSON Schema validates requests/responses. Malformed/non-finite JSON is rejected, and
  native non-finite values cannot pass the validator. No request values or exception
  strings are included in diagnostics or application logs.
- A configured NOTELENS_RAG_SERVICE_TOKEN is enforced even on loopback. With no token,
  key-free access is restricted to direct loopback mock requests; forwarded headers do
  not grant access. This local exception is not an exposure/deployment authorization.
- Valid authenticated business calls in live mode return 503/configuration_required;
  no provider call, index access or silent mock fallback occurs.

Server-selected mock scenarios are sufficient, insufficient, clarification, timeout,
rate_limit, provider_unavailable and internal_error. Select one through
NOTELENS_RAG_MOCK_SCENARIO before startup. They simulate protocol outcomes; they do not
implement an ambiguity detector, rate limiter, provider retry policy or live timeout.
All simulated errors are non-retryable in this scaffold. There are no automatic retries.

The synthetic source uses example.invalid and mock-prefixed versions. It is not part
of the MedlinePlus corpus. Static insufficient/clarification examples have no generator
components. They do not resolve the retrieval-only provenance proposal in
[the review](../../docs/rag/p2-rc1-review.md).

## Verify and load the prepared corpus

From the repository root, after the installation above:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.ingestion
```

The current dataset reports status verified, 401 topics and 617 passages, with its
corpus version and artifact/manifest hashes. No topic bodies or filesystem paths are
printed. Errors use a safe English JSON diagnostic on stderr and exit code 1.

To load the corpus into the service's memory at startup, set this before the same
Uvicorn command documented above, then restart your own server:

```powershell
$env:NOTELENS_RAG_CORPUS_MANIFEST = 'data/knowledge/manifests/passages.json'
```

Paths are resolved against the nearest checkout ancestor containing the snapshot
manifest. An explicit server-only NOTELENS_RAG_REPOSITORY_ROOT or CLI --repository-root
can select the checkout when running elsewhere. An optional
NOTELENS_RAG_EXPECTED_CORPUS_VERSION or CLI --expected-corpus-version pins the intended
corpus version. Input requests cannot choose paths or versions.

The adapter reads the passage manifest, cleaning manifest, snapshot manifest and two
prepared JSONL artifacts. It verifies hashes/sizes, approved topic membership, exact
Unicode slices, source metadata, stable IDs, counts, policy, coverage and corpus-version
identity. It preserves the snapshot's explicit specialty assignments, including overrides.
PreparedCorpus/PreparedPassage records and their lookup maps are immutable. They contain
the unchanged passage text and metadata for a later indexing adapter.

It never imports the preparation script, re-cleans/re-chunks content, fetches links,
loads a model or writes corpus files. Raw ZIP/XML and extraction-stage files are not
needed at runtime. Fresh clones need the locally prepared artifacts, which remain
Git-ignored; the default synthetic mock does not require them.

With an explicitly configured invalid/missing corpus, the process remains alive but
readiness and valid business requests return 503; business errors use
configuration_required. A valid loaded corpus does not make live retrieval/generation
ready. No new fields are added to the shared health schema.

Verification occurs on each explicit load or service startup, not through a filesystem
watcher. The loaded in-memory snapshot stays unchanged if disk files are edited; restart
to validate a replacement. Checks establish consistency with trusted manifests, not a
new upstream authenticity/clinical review. Question/reference QA files are not inputs.

The reader reports these safe internal diagnostics: corpus_file_missing,
corpus_file_unreadable, corpus_path_invalid, corpus_format_invalid,
corpus_integrity_failure and corpus_version_mismatch. These are CLI/internal codes;
the shared HTTP error enum is unchanged.

## Contract boundary

The owner-local [support assessment processor](../../docs/rag/support-assessment.md)
validates supplied per-question-part judgments and exact passage quotes without
an API key or provider. It does not yet assess new questions semantically or
activate a real HTTP route. Its 39 new checks and the full 397-test service suite
passed on Python 3.13.5; the earlier checkpoint results below remain historical.

The [GPT-6 Luna adapter checkpoint](../../docs/rag/luna-assessor.md) adds a versioned
English assessment prompt and actual Responses SDK wiring through mandatory
MockTransport. All 43 new checks and the full 440-test suite passed. There is no
real-key loading or live switch; provider calls and semantic quality measurement
remain separately gated. The prompt is included and load-tested in the wheel.

The separate [bounded public trial](../../docs/rag/assessment-trial.md) was approved
on 2026-11-17 and halted after its first invalid assessment. The default inspection
command remains key-free and makes no API calls:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.assessment_trial
```

All 23 trial checks and the full 463-test suite passed again before execution.
The prior free preflight measured 9,508 input tokens across CQ-01/CQ-02/CQ-08.
The approved run attempted only CQ-01, failed with invalid_assessment and retained
a USD 0.0013811 reference-price reservation; no validated assessment was produced.
CQ-02/CQ-08 were not attempted. Actual billing is unverified. The ledger is halted,
the flag is disabled again and the real .env is unchanged. Do not reset the ledger
or repeat/continue the test without separate approval. See the
[actual run record](../../docs/rag/assessment-trial-results.json).

The installed notelens-contracts 1.0.0 package exports notelens_contracts.v1 TypedDicts
and validate_json/validate_record. The service uses these runtime validators for
requests and responses, with fixed safe error messages. The installed schema is
pinned to SHA-256 707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78.
B's dependency source is fd1197bd380de9ba9037ea0b73b42031dc1d4bb2.

The old RAG-owned revision-2 schema/API copies were removed. The service neither
maintains a second schema nor publishes FastAPI-generated API documentation as a
competing contract. Strict JSON parsing rejects duplicate keys and non-finite numbers
with 400; schema/field violations use 422. Invalid output semantics produce safe 500
envelopes. Completed mock retrieval retains independent retrieval_provenance, including
insufficient answers without generation; pre-search clarification keeps it null.

All 319 service tests passed on Python 3.13.5. See the [adaptation handoff](../../docs/rag/frozen-contracts-adaptation.md).
This completes A's local mock adaptation, not global F-004/F-014 or A-010's unmet
shared prerequisites. B's imported files were not manually modified by A.

## Evidence and limits

The scoped speckit-implement workflow used the official PowerShell prerequisite resolver
for specs/001-rag with non-persistent feature selection. The specification checklist had
16 checked and zero unchecked items; no extension hooks were configured. The user
authorized this local scaffold contribution on 2026-11-13 before shared promotion.

- 75 service tests passed: 39 scaffold/transport checks and 36 prepared-reader checks,
  including a real owned Uvicorn loopback HTTP process.
- The actual 401-topic/617-passage dataset passed reader validation and was loaded into
  an app instance; readiness remained truthfully mock with no model/index claim.
- The 52 existing corpus-preparation tests previously passed on Python 3.13.5.
- Tests cover schema shapes, claim/source/component links, correlation/concurrency,
  invalid/native numbers, synthetic-only input, health/authentication, simulated failures,
  redaction, pin drift, live-mode unavailability and process cleanup. Reader checks cover
  Unicode/repeated text, immutable records, source overrides, tampering, missing files,
  paths, counts, version/policy/ID errors, incomplete coverage and safe CLI/startup failures.
- Test-created directories stay under the ignored services/rag/.cache/test-runs path.

Those earlier reader-checkpoint results were local mock/module transport checks; they
did not then verify frozen generated-binding compatibility or live retrieval/generation.
The 2026-11-15 adaptation below adds actual installed-binding compatibility checks.
Clinical support, performance, deployment, provider retention and general operational
policies remain unverified. The reader is an
explicit 2026-11-13 owner-local preparation increment; A-003 remains open for its later
integration, embedding/store and index work. Submitted document endpoints, model SDKs,
generation and a vector store were absent at that reader checkpoint. The separate
2026-11-14 embedding increment now provides the SDK adapter and offline planning;
it does not enable live HTTP answers or close A-003.

Embedding-increment verification, 2026-11-14: all 114 service tests passed, including
39 new configuration/embedding checks. Provider requests were simulated through the
real SDK with fixture credentials and local HTTP transport. Actual offline planning
counted 207,790 corpus tokens; no paid request was made for that checkpoint.

The later full suite passed all 126 tests on 2026-11-14, including 12 real-local-Chroma
tests with synthetic vectors. The unchanged source was not retested for the 2026-11-15
data-only resume; actual provider execution, full-index readback/reuse and five local
vector self-queries were verified separately. No semantic retrieval benchmark is claimed.

Frozen-binding adaptation, 2026-11-15: 319 tests passed, including all 153 shared wire
payload cases, 22 simulated exchanges, actual health authentication/correlation cases,
strict JSON admission, independent retrieval provenance and a cold key/corpus/index-free
mock check. The real loopback HTTP smoke also passed. An offline RAG wheel was rebuilt
and checked for the shared-package dependency and absence of stale contract copies.
No provider call or index rebuild was made for this adaptation.
