# A-011 selected RAG configuration freeze and handoff

Frozen: 2026-11-23. Owner: Nemanja (A). Status: **A-owned configuration and handoff complete**.

After the [accepted A-008 closure](a008-closure.md), Nemanja requested completion of
A-011. The [freeze manifest](../../services/rag/config/frozen-rag-v1.json) pins the
selected RAG configuration and 56 source/evidence files by SHA-256. It records
the actual final-run status as **not run**, with the reason and remaining gates.
This completes A-011's configuration/inventory/handoff deliverable. The shared
system final freeze, final measurement and provider-backed application acceptance
remain separate; neither B nor D has accepted those through the A-008 messages.

## Frozen selection

| Component | Selected version |
| --- | --- |
| Implementation | `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4` |
| Corpus | MedlinePlus 2026-11-10; 401 topics, 617 immutable passages |
| Corpus version | `2922f29e08b74bf668272c33a7f3f0599d8d16fc90d2242976e3d4476010579b` |
| Passage artifact SHA-256 | `4915adc09d6719f84e3315f8a0ea0ac37bc363d8b1a178c6d14f449aac85c938` |
| Embedding | `text-embedding-3-small`, 1,536 dimensions |
| Index | Chroma 1.5.9, cosine; `209656e7be0e9db1885407de4fef824b5e0209c78a7d2fdc71e418c7a3d4a146` |
| Retrieval | Question-only vector, top five passages; `65c6c61888e64d658e18f741ccb037f76264306583bf2cc275cfad7ee5d3bc47` |
| Generation model | `gpt-6-luna` |
| Prompts | `literature-question-parts-v1`, `literature-support-selection-v2`, `literature-answer-v1` |
| Composition / contract | `rag-cited-claims-v1` / shared v1.0.0 |
| Development questions | Frozen D manifest v2 and configuration hash recorded in the freeze manifest |

Vector retains all 22 topic-referenced cases and 27 supported requested parts in
the accepted development set. BM25 has lower first-topic MRR; hybrid misses one
topic case and one supported part. Retain the existing vector choice without
changing the corpus, prompts, query wording or thresholds. Similarity scores are
not confidence. No calibrated numeric rejection threshold has been accepted;
support is assessed for each requested part, with explicit gaps and separate
document provenance.

The pinned model parameters are the historically executed five-public-case HTTP
profile: reasoning `none`, 512 maximum output tokens per completion, input ceilings
4,096/20,000/4,096 for question parts/support/answer, 30-second timeout and zero
automatic retries. That scope is closed. Earlier USD 0.10 corpus, USD 0.01 query,
USD 0.02 support, USD 0.025 HTTP smoke and USD 0.001 mixed-embedding allowances
are historical scopes, not a standing service budget. All are recorded with their
limits; no new provider request or paid CI is enabled by this freeze.

## Actual outputs for B and D

These existing artifacts are pinned by the manifest; do not relabel fixtures as
model outputs:

- [CQ-01 actual completion](evaluation/answer-trial-results.json) and
  [CQ-02 actual partial completion](evaluation/partial-answer-trial-results.json).
- [v2 answer-review packet](evaluation/development-answer-review-v2.json): two
  actual completions and four explicitly identified fixtures.
- [Partial evidence HTTP results](evaluation/partial-evidence-flow.json) and
  [local HTTP flow](evaluation/local-http-flow.json): mock-mode composition using
  cached public evidence.
- [Accepted development retrieval aggregates](evaluation/frozen-development-summary.json).
  B and D already confirmed receipt and acceptance of the private full v2 package.

The five-case historical [live HTTP record](evaluation/live-http-smoke.md) and
[D feedback/revisions](evaluation/live-http-smoke-review.md) remain development
evidence. CQ-05 adjudication and wider answer-quality acceptance are not silently
resolved by configuration freeze. No private document fixtures, question bodies,
vectors or credentials are added to this handoff.

## Startup and independent shutdown

From the repository root on Windows, install the locked optional indexing extra.
The first installation needs registry access when packages are absent locally.
The commands below perform key-free checks:

```powershell
uv --system-certs sync --locked --directory services/rag --python 3.13 --extra indexing --dev
if ($LASTEXITCODE -ne 0) { throw 'Locked RAG setup failed.' }
uv run --locked --offline --directory services/rag --extra indexing python -B ../../docs/rag/evaluation/serve_indexed_demo.py --check
if ($LASTEXITCODE -ne 0) { throw 'Indexed RAG smoke failed.' }
uv run --locked --offline --directory services/rag --extra indexing python -B -m pytest tests/test_contract.py tests/test_index_version.py
if ($LASTEXITCODE -ne 0) { throw 'RAG freeze checks failed.' }
```

Without `--check`, the indexed script serves on `127.0.0.1:8001`; Ctrl+C stops its
owned listener. `--port` selects another loopback port. This profile uses two
synthetic passages, fixture adapters and `mode=mock`; it is not the 617-passage
provider-backed service. The default `notelens_rag.main:app` also remains mock.
See the [development startup guide](development-handoff.md) for token/readiness
configuration and the injected `create_app(settings, indexed_backend=backend)` API.
The freeze manifest is an audit artifact, not an automatically loaded runtime setting.

Goran's exact launcher snapshot `14e4b9dfdfdd5832cae7f03d12e92cc5f9a00593` passed
the [A-owned review](evaluation/launcher-review-14e4b9df.json). Its default stack
still uses mocks. Indexed RAG is an explicit `start_stack(indexed_rag_job=...)`
option with separate process ownership. The app check stopped only RAG, verified
the RAG port was closed while web/extraction remained up, checked the fallback,
then verified closure of all four listeners. The fitted classifier is independently
opted in; its actual fitted-model acceptance remains C/B work.

## Final measurement and remaining live limits

No unseen final measurement was run. A has no approved unseen-final manifest,
final execution scope or operational provider budget in this checkout. Keep the
final set locked until D supplies the frozen reference and the team confirms the
scope, operator and budget. Record a separate versioned execution receipt; do not
reuse the development measurement as final evidence or tune prompts on final cases.
There has been no repeat final run.

D-004's existing receipt must be preserved. D-005's completed mock HTTP check
does not establish a configured live provider. The relayed requirement for at most
two approved synthetic calls, zero retries and a cumulative USD 0.10 cap remains
D's separate gate; operator setup, approved-model access and remaining budget still
need confirmation before dependent execution. No D-owned service or receipt was
changed. B-005/B-009 and the shared release freeze remain with their owners.

The 128 focused RAG tests, 81-result offline replay, 617-passage index readback,
production app build and requested loopback checks passed. No provider call,
final-test access, publication or deployment occurred during this package. The
[workflow record](a008-closure.md#workflow) applies to both tasks. The older
`development-handoff.json` and dated checkpoints remain unchanged historical records.
