# RAG development handoff for B and D

Owner: Nemanja (A). Initial checkpoint: 2026-11-18. Latest owner-local verification: 2026-11-21. Branch: `rag`.

The current portable indexed profile passed 116 targeted tests and an
authenticated TCP smoke in the owner checkout. It also passed from a complete
Git export plus A's local changes, with a new Python 3.13.5 environment installed
offline from the locked package cache and no public corpus, saved queries or
provider credentials. The earlier published reference `94884c9` does not contain
the launcher; use a revision that includes `evaluation/serve_indexed_demo.py`.
This owner-local result prepares B's integration probe and leaves A-008 open
for the shared benchmark and B's application acceptance.

This checkpoint provides a key-free HTTP demo for B and saved development
evidence for D. The [checkpoint manifest](../../services/rag/config/development-handoff.json)
records the exact Git revision, corpus, Chroma index, retriever, question sets,
three prompts, frozen contract and SHA-256 digests. The manifest is an inventory
for review. The service does not read it at startup.

| Part | Development reference |
| --- | --- |
| Corpus | MedlinePlus snapshot, 401 English topics and 617 passages. |
| Search | Local Chroma with `text-embedding-3-small` (1,536 dimensions). Retain the question-only vector retriever provisionally after the ten-question comparison. |
| Support selection | `gpt-6-luna` with `literature-support-selection-v2`. The three saved public probes cover full, partial and absent support. |
| Question parts and final prose | Versioned Python adapters verified with simulated SDK responses. |
| HTTP contract | Frozen v1.0.0. Default mock is available on loopback. A configured live backend is still pending. |

## B: run the local HTTP demo

Use a separate working copy of `rag`. With Python 3.13 and uv installed, run
the following from the repository root in PowerShell. The first installation
requires registry access if the pinned packages are absent from the uv cache.

```powershell
uv --system-certs sync --locked --directory services/rag --python 3.13 --dev
$env:NOTELENS_RAG_MODE = 'mock'
$env:NOTELENS_RAG_MOCK_SCENARIO = 'sufficient'
uv run --locked --offline --directory services/rag uvicorn notelens_rag.main:app --host 127.0.0.1 --port 8001 --no-proxy-headers --no-access-log
```

From another terminal, use `/health/ready` and send a literature answer request:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8001/health/ready'
$ragHeaders = @{ 'X-Request-ID' = [guid]::NewGuid().ToString() }
$ragBody = @{ schema_version = '1.0.0'; question = 'What is the synthetic demo topic?' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8001/v1/literature-answer' -Method Post -Headers $ragHeaders -Body $ragBody -ContentType 'application/json'
```

Expected: readiness reports `status=ok`, `mode=mock`. The answer has
`mode=mock`, `route=literature` and a synthetic cited claim. Stop the owned
process with Ctrl+C. The [routing evidence](integration.md) lists expected
error outcomes and how to preserve separate document evidence. Use the
[service README](../../services/rag/README.md) for other mock scenarios and
service authentication. The mock needs no API key or local index.

### Run the indexed demo without a provider

Install the locked optional `indexing` extra once. From a checkout with the
locked packages available, this command starts RAG on `127.0.0.1:8001`.

```powershell
uv run --locked --offline --directory services/rag --python 3.13 --extra indexing python -B ../../docs/rag/evaluation/serve_indexed_demo.py
```

The launcher builds or verifies a local two-passage synthetic Chroma index in
`services/rag/.cache/indexed-demo`. It uses fixture embeddings, assessments and
answer text. The HTTP app, candidate ranking and citation validation run
through the RAG service. It needs no API key, public corpus, saved embeddings
or tokenizer download. Use `--port` for another loopback port and Ctrl+C to stop.

For a web-side integration probe, point `NOTELENS_DEMO_RAG_PORT` at the
listener. If the client uses `NOTELENS_DEMO_TOKEN`, set the RAG process's
`NOTELENS_RAG_SERVICE_TOKEN` to the same test token. The existing web preset
uses the first question below. The two other questions are available through
the RAG HTTP endpoints for routing checks.

| Question | Literature answer evidence state |
| --- | --- |
| What is the synthetic demo topic? | Sufficient with a cited claim |
| What is the synthetic demo topic, and when did it begin? | Partial with a cited claim and a start-date gap |
| When did the synthetic demo topic begin? | Insufficient with zero claims |

Append `--check` to validate liveness, readiness, both business routes, correlation
IDs and rejection of an unregistered question over TCP. When a service token is
configured, the check also verifies unauthenticated access is denied. It uses a
temporary listener and stops it after all three questions. Partial output uses
the existing partial-evidence policy in this isolated synthetic profile.

Expected: two successful health responses, six successful business responses,
an unregistered-question `422`, and a `401` for unauthenticated readiness when
a token is configured. The unit check independently verifies two compositions
for the three answer questions: the missing-only question skips generation.
The optional-indexing targeted suite passed 116 tests:

```powershell
uv run --locked --offline --directory services/rag --extra indexing python -B -m pytest tests/test_indexed_demo.py tests/test_indexed_startup.py tests/test_reference_metrics.py tests/test_hybrid.py tests/test_failures.py tests/test_answers.py tests/test_contract.py
```

The normal smoke expects `NOTELENS_RAG_MOCK_READY=true` or an unset variable.
To rehearse F-011 with the long-running indexed profile, set it to `false`
before startup: liveness stays `200/alive` and readiness becomes `503/not_ready`.
Restore `true` before the normal smoke. This profile remains loopback-only and
reports `mode=mock`; it does not supply clinical outputs or activate a provider.

In A's working copy, the [loopback replay](evaluation/local-http-flow.md#temporary-uvicorn-server)
also exercises both HTTP routes against the prepared Chroma index and saved public
query vectors. Its temporary server uses mock-mode responses and needs no API key.

### Configured index startup

The explicit Python entry point is `create_app(settings, indexed_backend=backend)`.
Set the corpus manifest and expected corpus version in `Settings`. Supply an
`IndexedBackend` with the expected index version, a mode-matched embedder, an
admission function, question decomposition, support assessment and generation.
The caller owns adapter construction and its resource lifecycle.

Startup verifies the corpus manifest and all stored Chroma passage and vector
hashes before binding the retriever. With an invalid or unavailable index,
liveness remains available and readiness and valid business requests return
`503`. The default Uvicorn entry point still starts the checkpoint mock.

```powershell
uv run --locked --offline --directory services/rag --extra indexing python -B -m pytest -o addopts= -q tests/test_indexed_startup.py
```

The check uses a synthetic corpus, a local Chroma index and in-memory SDK
responses. The existing 617-passage development index was separately verified
against the recorded corpus and index versions without provider access. A live
entry point still needs approved provider controls. Application integration
depends on F-014 and B's partial-response agreement.

The checked-in corpus manifests name the required cleaned and passage artifacts.
For an indexed rehearsal, provide those verified local artifacts and the
matching Chroma directory under `data/knowledge/indexes/<index_version>`.
The startup code reads the pinned versions from the supplied settings and
checks them against the manifest and stored vectors. The indexed profile
requires the locally cached tokenizer vocabulary. See the
[public index run record](indexing.md) for preparation and verification details.

The separate [five-case live smoke](evaluation/live-http-smoke.md) verified
the complete Python HTTP answer path with one public question per specialty and
bounded provider access. That execution scope is closed.

## D: review proposals and reproduce the saved summary

The [nine QA proposals](qa-proposals.md) record exact source references,
including three cases requiring two topics. The [saved evaluation](evaluation/saved-development-evaluation.json)
identifies four proposals with matching prior rankings and three with prior
support decisions. Five new questions, including all multi-topic cases, still
need measured rankings. After installing the RAG environment, run this from
the repository root:

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/measure_saved.py
```

The calculation only needs committed records. Review the proposed required topics
and accepted alternatives before treating them as canonical QA. Keep these public
questions and their overlaps in development and keep final cases separate.

## Verified checkpoint and final gate

An isolated export of complete commit `90546eee1516690201fa6a872a394830dd333157`
installed from the existing uv cache with `uv sync --locked --offline`. It had
no ignored corpus, Chroma index, credentials or previous virtual environment.
The full service suite passed **750 tests**, including the loopback HTTP process
and frozen bindings. The saved evaluation reproduced. A first partial export
omitted the generated contract manifest and failed one check. The complete export
contained the shared binding inputs and passed the full suite. The real index in
A's existing working copy separately passed readback of all 617 entries. No new
model or embedding requests were made.

The USD 0.10 corpus embedding, USD 0.01 public query and USD 0.02 cumulative
support-assessment caps recorded in the manifest belong to the prior public trials.
Live service budgets and deployment configuration remain unset. A-011's final
configuration and locked measurement depend on A-008, D's adjudicated QA,
independent final-answer review and confirmation before application integration.
No final evaluation has run.
