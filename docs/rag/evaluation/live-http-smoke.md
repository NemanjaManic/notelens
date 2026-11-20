# Five public RAG HTTP smoke cases

On 2026-11-19, Nemanja approved one complete local request per specialty with
a combined USD 0.025 ceiling, a 30-second provider timeout and zero retries.
The [runner](run_live_http_smoke.py) used the explicit authenticated indexed
backend through the in-process HTTP client. Each request performed fresh
question decomposition, embedding, Chroma ranking, evidence selection and
answer generation. It used the pinned 617-passage MedlinePlus development index
and sent public questions and supporting literature to the provider.

| Case | Specialty | HTTP and evidence | Claims | Exact citations | Standard-price reference USD |
| --- | --- | --- | ---: | ---: | ---: |
| CQ-01 | Cardiovascular / Pulmonary | 200, sufficient | 1 | 3 | 0.00137968 |
| CQ-03 | Orthopedic | 200, sufficient | 2 | 2 | 0.00127986 |
| CQ-05 | Gastroenterology | 200, sufficient | 2 | 2 | 0.00159816 |
| CQ-07 | Neurology | 200, sufficient | 2 | 5 | 0.00110368 |
| CQ-09 | Urology | 200, sufficient | 1 | 7 | 0.00092410 |
| **Total** | | **5/5** | **8** | **19** | **0.00628548** |

Readiness and all five responses passed. The coding agent rechecked all 19
citation slices and claim-to-passage links against the canonical corpus. CQ-03's
selected excerpt names the median nerve and shows its path through the tunnel.
The surrounding text in the same returned passage explains compression. A more
direct excerpt for that claim would make review easier. The [D feedback
record](live-http-smoke-review.md) documents the supplied draft ratings and
the authored corrections. These are public development cases. Application
routing and the locked final evaluation remain pending.

Usage was 64 embedding input tokens, 52,882 Responses input tokens and 1,992
Responses output tokens across 5 embeddings and 15 completions. Each completion
had a free input-token count. The USD 0.0236200800 reservation includes the
published cache-write rate and regional allowance. The table uses confirmed
token counts at Standard reference prices. The actual invoice is unverified.
[GPT-6 Luna rates](https://developers.openai.com/api/docs/models/gpt-6-luna),
[embedding rates](https://developers.openai.com/api/docs/models/text-embedding-3-small),
[token-count pricing](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens).

The one-time scope is closed. The local receipt is
`services/rag/.cache/live-http-smoke-2026-11-19/run.json`, SHA-256
`9c5a16ef6020ba4963ae4f3be20aab2ac85a8a65d6a3a7da35de6ec536d7509a`.
Run the key-free scope inspection from the RAG checkout to see the exact case
IDs, models, prompt identities and limits.

```powershell
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/run_live_http_smoke.py
```
