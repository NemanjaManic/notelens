# Local RAG HTTP flow with real cached retrieval

Owner: Nemanja (A). Run date: 2026-11-18.

The [flow check](run_local_flow.py) sends four registered public questions
through `/v1/retrieve` and `/v1/literature-answer` using the in-process ASGI
HTTP client. Each request runs a new ranking against the verified local Chroma
index with a hash-checked cached question vector. The previous ranked IDs and
canonical evidence must still match. The whole HTTP response reports mock mode
because the flow replays approved public evidence and uses authored or replayed
answer text. This is an owner-local test of the production-shaped contracts.

| Case | Answer check | Claims | Exact references |
| --- | --- | ---: | ---: |
| A-QA-01 | Sufficient, exact text from the previously validated completion | 2 | 4 |
| A-QA-07 | Sufficient, local fixture preserves both source topics | 2 | 3 |
| A-QA-02 | Partial, local fixture retains the supported fact and explicit gap | 1 | 1 |
| A-QA-03 | Insufficient, local abstention skips answer composition | 0 | 0 |

All eight business responses passed the frozen payload validators and returned
the input request IDs. Readiness reported mock mode and an unregistered question
returned 422 before ranking. The comparison preserved 28 cache and ledger JSON
files byte for byte and left no lock. Key loading and provider creation were
forbidden. The shared review-packet output also reproduced byte for byte.

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/run_local_flow.py
```

Run from the repository root in the working copy that holds the prepared corpus,
local index and existing public query, support and answer caches. Those ignored
inputs are separate from the committed [summary](local-http-flow.json). A fresh
checkout can run the [key-free HTTP demo](../development-handoff.md) without them.

The test exercises Python's HTTP routes in process. It leaves the default app
factory and startup behavior unchanged. The partial wire interpretation is
enabled only in the harness. B's client, shared routing and live activation remain
team integration checks. The result measures evidence transfer and abstention in
the composed flow. Independent semantic evaluation remains open.
