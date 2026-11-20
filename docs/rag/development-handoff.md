# RAG development handoff for B and D

Owner: Nemanja (A). Prepared: 2026-11-18. Branch: `rag`.

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
uv run --locked --offline --directory services/rag python -B -m pytest -o addopts= -q tests/test_indexed_startup.py
```

The check uses a synthetic corpus, a local Chroma index and in-memory SDK
responses. The existing 617-passage development index was separately verified
against the recorded corpus and index versions without provider access. A live
entry point still needs approved provider controls. Application integration
depends on F-014 and B's partial-response agreement.

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
