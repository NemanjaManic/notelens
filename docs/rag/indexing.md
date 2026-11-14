# Local Public-Corpus Chroma Index

Owner: Nemanja (A). Updated: 2026-11-14.

The user approved local Chroma without a cloud account/subscription and an initial
OpenAI embedding step capped at USD 0.10, including one small probe and the 617
prepared public passages. The model is text-embedding-3-small, 1,536 dimensions;
batches contain at most 32 inputs, requests time out after 30 seconds, and SDK
retries are disabled. This approval excludes generation, deployment and push.

## Boundary and storage

The owner-local A-003 CLI/library does not change shared contracts, bindings, root
configuration or HTTP mocks. A-010/F-014 and formal integration gates remain open.
Chroma 1.5.9 is pinned in the service lockfile. PersistentClient uses explicit vectors,
embedding_function=None and anonymized_telemetry=False. No default embedding model,
CloudClient, account or subscription is used. The OpenAI adapter verifies TLS with
system trust and keeps the key in ignored services/rag/.env.

Only public literature, its vectors and index metadata persist. No submitted
document or evaluation QA enters this index. The owned Git-ignored layout is:

```text
data/knowledge/indexes/<index-version>/
  manifest.json
  usage.json
  chroma/
```

The index identity binds the embedding plan/space, corpus/manifests, model/dimensions,
mock/live origin, Chroma version, cosine configuration and float32 storage format.
Mock and live indexes have different identities. Every stored passage retains its
exact canonical text/ID, source URL/title, topic, offsets, snapshot and digests.
Specialty metadata never becomes a hard retrieval filter.

New vectors are compared numerically against provider values to accommodate float32
roundtrip rounding (relative tolerance 1e-5, absolute 1e-7). Their actual stored float32
representation is then SHA-256 fingerprinted. Later verification requires exact
stored hashes, unchanged corpus text/metadata, all expected IDs, correct collection
identity and cosine configuration. These are storage checks, not retrieval-quality
or medical-support thresholds. An incomplete or changed index cannot be ready.

## Execution and recovery

Normal CLI execution only verifies a complete index and makes zero API calls.
Building requires --execute, an explicit budget and paid execution enabled in that
process. The key is read from the local .env, never from a command-line argument.

An exclusive lock prevents concurrent builds of this index. Each request reserves
its counted possible charge atomically in usage.json before transmission; failed
or uncertain reservations remain. This is a local run/index ceiling, not a cap on
unrelated account usage. Only one small probe is attempted. A completed unchanged
index is verified and reused without more embeddings.

Processing stops on authentication errors, 429, timeout or other failure. There
is no automatic retry or resume. An explicit --resume preserves the original budget,
skips verified saved batches and never repeats an attempted probe. Unverified partial
writes or stale locks require inspection. Do not silently increase the budget.

From the repository root, after the explicit run approval and local key setup:

```powershell
$env:NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS = 'true'
try {
    uv run --locked --offline --directory services/rag python -m notelens_rag.indexing --execute --budget-usd 0.10
    if ($LASTEXITCODE -ne 0) { throw 'Index build stopped; inspect before an explicit resume.' }
} finally {
    Remove-Item Env:NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS
}
```

Read-only verification and deterministic local tests:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.indexing
uv run --locked --offline --directory services/rag python -m pytest tests/test_index_version.py
```

Before the initial paid attempt, all 126 service tests passed on Python 3.13.5,
including 12 real-local-Chroma checks with synthetic vectors and denied network.
Actual offline preflight counted 207,790 tokens; no provider call was needed for it.
The CLI emits only counts, versions, safe statuses and usage amounts. Index completion
does not implement a live retrieval HTTP route, a sufficiency threshold, generation,
medical validation or deployment.

## Initial live attempt, 2026-11-14

After the complete 126-test suite passed, the approved initial run loaded the key
from the local .env and attempted one 7-token public-text probe. The official OpenAI
endpoint rejected authentication or permissions (`provider_authentication`). No
retry was made, no corpus batch was sent and zero passage vectors were stored.

The attempted index identity is
`209656e7be0e9db1885407de4fef824b5e0209c78a7d2fdc71e418c7a3d4a146`.
Its local status is interrupted, probe status attempted, reserved tokens 7 and
confirmed successful tokens 0. The retained reference-price reservation is USD
0.00000014; this is conservative bookkeeping, not an actual invoice or confirmed
charge. No ready index, live retrieval quality or generation result is claimed.

The user confirmed that the key came from a tutor and has no additional endpoint
instructions. Local checks confirmed correct .env loading, no process override
and no whitespace, without printing any secret value. A subsequent read-only
model-list request to the official OpenAI API succeeded, but the returned IDs did
not include text-embedding-3-small. This establishes model-list access, not access
to embeddings, and suggests a model/project permission limitation. The exact
embedding permission still requires confirmation from the key/project owner.

No second embedding probe or generation request was made. Ask the tutor to enable
or confirm text-embedding-3-small and the embeddings endpoint for this key/project,
or supply the intended supported embedding model/configuration. Do not infer that
LLM access grants embeddings, change the selected model without agreement, redirect
the key to another host or repeat paid execution without resolving access. The API
origin remains fixed to official OpenAI in the current adapter. Provider billing
and successful embedding usage have not been independently confirmed.

## Sources

- [Chroma Python clients](https://docs.trychroma.com/reference/python/client).
- [Collection operations](https://docs.trychroma.com/reference/python/collection).
- [Cosine/index configuration](https://docs.trychroma.com/docs/collections/configure).
- [Chroma Apache-2.0 license](https://github.com/chroma-core/chroma/blob/main/LICENSE).
- [OpenAI embedding approvals, pricing and preflight](embeddings.md).
