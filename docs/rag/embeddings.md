# OpenAI Embedding Preparation

Owner: Nemanja (A). Updated: 2026-11-14.

The user selected OpenAI as the provider and explicitly approved
`text-embedding-3-small` with 1,536 dimensions on 2026-11-14. This is an initial
embedding-only baseline candidate, not a measured retrieval-quality result.
The generative model is a separate choice; no LLM generation is introduced here.

## Scope and activation

The owner-local A-003 preparation increment adds offline planning, a narrow OpenAI
SDK adapter, isolated fake-transport checks and explicit local `.env` loading.
It does not promote shared contracts, complete A-010/A-003, create a shared foundation
checkpoint, expose live HTTP business routes or authorize deployment.
The existing service remains pinned to its provisional revision-2 contract snapshot.

The user requested small local commits. Pushes remain separately authorized.
The user separately approved the initial public-corpus embedding run plus one small
probe, capped at USD 0.10 for that step, batches of at most 32 inputs, a 30-second
timeout and zero automatic retries. Local Chroma is approved without a cloud account.
These approvals do not cover generation, deployment or unrelated API usage. Merely
finding an API key never enables execution. Routine tests use a fixture key and local
transport. At the adapter/preflight checkpoint no paid request has been executed.

## Local secrets

Use `services/rag/.env`; the repository's existing `.env` ignore rule covers this path.
`services/rag/.env.example` is the versioned template with an empty key. Preserve an
existing `.env`; never copy its content into documentation, logs, Git or chat.
Process environment values take precedence over this file. Variable interpolation
is disabled, so key characters are not expanded. The configuration representation
and public summaries omit the key value. This is application configuration, not a
claim of machine-wide secret protection or a complete security audit.

```dotenv
OPENAI_API_KEY=
NOTELENS_RAG_EMBEDDING_MODEL=text-embedding-3-small
NOTELENS_RAG_EMBEDDING_DIMENSIONS=1536
NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=false
```

Both a caller's explicit activation and a positive finite per-run budget are needed
by the paid adapter. The mock HTTP service does not import or activate it at startup.
The fixed API origin is `https://api.openai.com/v1`; environment base-URL overrides
cannot redirect this adapter's requests.

## Exact inputs and versions

Embed the unchanged canonical passage text only. Do not flatten newlines, prepend
titles, translate or re-clean it. Count literal special-token strings as ordinary
text. The tokenizer is `cl100k_base`, with a SHA-256-verified public vocabulary.
Normal planning requires that vocabulary in the local cache and fails without it;
there is no implicit vocabulary download during offline checks.

The embedding-space identity includes provider, model, dimensions and the input
policy `unchanged-canonical-passage-text-v1`. The plan identity additionally binds
the corpus version and passage-manifest/artifact digests. These identities are
preparation records, not a built index or retriever version. Changing the embedding
space requires new vectors and a new index.

The API's documented limits are 8,192 tokens per input, 2,048 inputs per request and
300,000 tokens in total per request. They are provider limits, not approved product
question-size limits. Runtime batching/timeout/rate policies remain explicit run
configuration and later service activation decisions.

## Offline planning on Windows

From the repository root, install the updated service lockfile using the service
README. Prepare the public tokenizer once; this downloads vocabulary, not an LLM,
and sends no corpus text or API key:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.embeddings --prepare-tokenizer
```

If Python cannot download using the machine's trust configuration, download the
official vocabulary using PowerShell's system trust and verify its digest:

```powershell
$tokenizerUri = 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken'
$tokenizerCache = Join-Path (Get-Location).Path 'services/rag/.cache/tiktoken'
New-Item -ItemType Directory -Force -Path $tokenizerCache | Out-Null
$sha1 = [Security.Cryptography.SHA1]::Create()
$cacheName = ([BitConverter]::ToString($sha1.ComputeHash([Text.Encoding]::UTF8.GetBytes($tokenizerUri)))).Replace('-', '').ToLowerInvariant()
$tokenizerFile = Join-Path $tokenizerCache $cacheName
Invoke-WebRequest -UseBasicParsing -Uri $tokenizerUri -OutFile $tokenizerFile -TimeoutSec 30
if ((Get-FileHash -LiteralPath $tokenizerFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7') { throw 'Tokenizer checksum mismatch.' }
```

Then run the entirely offline plan:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.embeddings
uv run --locked --offline --directory services/rag python -m pytest tests/test_embeddings.py
```

The CLI only emits versions, counts, pricing assumptions and key presence. It has
no paid execution option and never writes vectors or source text. Its explicit
`--prepare-tokenizer` option is the only vocabulary-download path.

## Measured preflight, 2026-11-14

Executed on Python 3.13.5 using tiktoken 0.14.0 and the verified prepared corpus:

| Item | Measured value |
| --- | --- |
| Topics / passages | 401 / 617 |
| Total input tokens | 207,790 |
| Largest passage | 621 tokens |
| Referenced standard input price | USD 0.02 per million tokens |
| Corpus-only estimated input charge | USD 0.0041558 |
| Paid provider calls during planning | 0 |

The estimate is calculated from local token counts and the documented price checked
on 2026-11-14. It excludes later questions, generation, taxes and unrelated account
usage. It is not a provider invoice or an approved account-wide spending cap.
Actual account access, usage and billing have not been tested at this checkpoint.

The paid adapter reserves counted tokens before sending a request, keeps a failed or
uncertain request's reservation and disables SDK retries. It checks raw JSON before
SDK model coercion, rejecting booleans/non-finite numbers, wrong model/dimensions,
zero vectors, duplicate/missing response indices and inconsistent token usage.
It restores vector order by the returned index and emits fixed English errors.
Its budget is per adapter/run; it cannot cap other processes or dashboard usage.

## Sources

The subsequent initial paid attempt was rejected for provider authentication or
permissions before any corpus batch; see [the exact index/run evidence](indexing.md).
The key was confirmed as tutor-supplied. An official OpenAI read-only model-list
request succeeded but did not list the selected embedding model. The tutor/project
owner must confirm embedding permissions before another paid attempt. The price
above is a reference estimate, not measured billing. The adapter/preflight checkpoint's
zero-call evidence above remains historical and does not hide the later failed attempt.

- [OpenAI developer quickstart](https://developers.openai.com/api/docs/quickstart).
- [Embedding guide and dimensions](https://developers.openai.com/api/docs/guides/embeddings).
- [Model and current pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small).
- [Embedding API limits](https://developers.openai.com/api/reference/resources/embeddings/methods/create).
- [Official Python SDK](https://github.com/openai/openai-python).
- [Official tokenizer vocabulary definition](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py).
