# RAG development integration evidence

Owner: Nemanja (A). Initial checkpoint: 2026-11-18. Latest local evaluation: 2026-11-22. A-008 remains open.

The [received D source record](evaluation/reviewed-development-evaluation.md#received-d-source-record-2026-11-22)
now supplies the exact ratings and additional slices for the nine cases. All
12 original citations and four additions checked against the pinned corpus;
the received decisions match the A evaluator. Its v2 provenance/result records
reproduce the earlier method results with zero provider calls. D's wider
candidate inventory still needs reconciliation and a team-approved split;
receiving this package does not freeze the benchmark or complete B acceptance.

The [D-reviewed development evaluation](evaluation/reviewed-development-evaluation.md)
adds the relayed nine-case D ratings and scoped alternative references to a
reproducible re-score of the existing vector, hybrid and BM25 rankings.
Vector retains all reference topics for eight of eight cases with topic
labels and all 11 supported parts. The no-support case is excluded from
topic-recall denominators, and partial coverage remains explicit. Fourteen
canonical spans and all source input hashes were checked without provider
calls. All 105 targeted metric/contract/answer/failure tests passed. D's
canonical joint record, wider benchmark and B's application routing remain
open; this local report does not freeze the shared evaluation.

The portable [synthetic indexed profile](development-handoff.md#run-the-indexed-demo-without-a-provider)
now supplies a key-free TCP probe for sufficient, partial and insufficient
responses without A's ignored corpus or query caches. It checks both health
routes, six business responses, request correlation, unregistered-question
rejection and configured service-token denial. A fresh source export with A's
local overlay and a new locked environment reproduced the smoke. The targeted
suite including the portable profile and indexed startup passed 116 tests.
This is Python service integration evidence; B's frontend routing and the
shared/final evaluation remain separate gates.

## Actual web client/router probe, 2026-11-22

The [probe runner](evaluation/run_web_rag_probe.py) starts A's synthetic indexed
HTTP profile and invokes B's unchanged TypeScript HTTP client and routing module
through [the Node probe](evaluation/probe_web_routing.mjs). The [result record](evaluation/web-rag-client-probe.json)
contains 12 passing cases and two successful health responses. It binds the
inspected web sources, generated bindings, fixtures and workspace lock by SHA-256;
their bytes were unchanged after execution.

| Cases | Observed result |
| --- | --- |
| Literature full / partial / absent support | `literature/sufficient`, `literature/partial`, `none/insufficient`. |
| Mixed full / partial support | `mixed/sufficient`, `mixed/partial`; both origins retain claim/source/component links. |
| Mixed absent literature support | `document/partial`; document claims remain, and the literature branch retains its accepted insufficient-evidence record. |
| Unregistered question, literature-only / mixed | `none/unsupported`, `document/partial`. |
| Invalid service token, literature-only / mixed | `none/unavailable`, `document/partial`. |
| Stopped RAG service, literature-only / mixed | `none/unavailable`, `document/partial`. |

The healthy phase made ten actual RAG HTTP requests: six `200`, two `422` and
two `401`. After stopping the listener, two connection attempts confirmed the
unavailable outcomes. Each case made one literature attempt, with no retries.
Only question/schema fields went to RAG; document text stayed out of that request.
Partial responses retained the explicit missing start-date warning. Supported
document claim text and source text were preserved in every mixed case.

The document branch uses the frozen synthetic document-answer fixture. No D HTTP
service, browser, web session or submitted-report flow is exercised here. This
is an owner-local check of B's client/router with actual A HTTP, not B's complete
application acceptance or a real-model measurement. There were zero provider calls
and no final-test access. A-008 remains open for the canonical shared benchmark
and B's application review.

Run from a working copy with Node 24 and the locked Node workspace installed:

```powershell
uv run --locked --offline --extra indexing --directory services/rag python -B ../../docs/rag/evaluation/run_web_rag_probe.py
```

Use `--web-root <working-copy-root>` to select another dependency-equipped copy;
its protected source/fixture/lock hashes must match the inspected checkout. The
recorded execution used an isolated export of `986adfb`, Node 24.12.0 and Python
3.13.5. Initial offline npm installation lacked one cached package. The normal
locked install then required Node's `--use-system-ca` option for the local Windows
certificate setup; TLS verification remained enabled. Root configuration and
lockfiles were not changed. Temporary RAG indexes contain only synthetic fixtures.

The default RAG app exposes the frozen mock routes. B can verify the contract
and error handling locally using the [service startup guide](../../services/rag/README.md)
and [failure fixtures](../../services/rag/tests/test_failures.py). The composed
adapter was tested in an injected Python test app, including SDK responses via
in-memory transport. It has no server-configured live backend. Team confirmation
is required before connecting RAG to the application.

| Observed scenario | Route outcome | Meaning for composition |
| --- | --- | --- |
| Completed empty search | `200`, `insufficient` | For `/v1/literature-answer` the service provides retrieval provenance and zero literature claims. Assessment and generation are skipped. |
| Embedding timeout | `504`, `timeout` | Literature search stopped before vector access. |
| Provider rate limit | `429`, `rate_limit` | Provider declined the request. |
| Local embedding allowance exhausted | `429`, `budget_exceeded` | Local reservation rejected the call before contacting the provider. This is the provisional status mapping for the frozen error code. |
| Provider unavailable | `503`, `provider_unavailable` | Literature evidence could not be searched. |
| Invalid index or provider authentication | `503`, `configuration_required` | Check the RAG service configuration. |
| Invalid context with an empty candidate list | `500`, `internal_error` | Context validation failed before a search verdict could be returned. |

All error outcomes use `ErrorEnvelope` and echo the received valid request ID.
They omit claims, retrieval provenance, question text and provider details.
An operational stop carries no literature verdict. In a mixed response B can
preserve independently supported document claims and describe the literature
gap or outage separately. On 2026-11-20, B confirmed the [frozen retrieval semantics](answer-support-policy.md#frozen-interface-interpretation).
For partial coverage, the web app will show cited claims and the unanswered parts
from `warnings`. The shared application check will verify this behavior over B's
routing and rendering.

## Saved development evidence

The [evaluation record](evaluation/saved-development-evaluation.json) uses the
same question ID **and** exact question text before joining a proposal to a saved
ranking. It binds the source files by SHA-256 and records corpus, index, retriever,
and support-assessment versions. Repeated passages from one topic count once.

- Four of the nine proposals had exact matches in the saved development rankings.
  Three have proposed topic references. All three found the required topic at
  rank 1 and all three cited source parts were present among the first five
  passages. The missing-evidence probe contributes no topic-recall denominator.
- The three multi-topic proposals and two additional single-topic proposals had
  no saved query for their exact wording. Their measured ranking metrics remain
  unset. None of the nine proposals currently requires more than five topics.
- The three earlier real support assessments match the local full, partial and
  missing evidence labels. Two of three would permit some grounded output, and
  neither asserted a higher coverage category than the proposal. This is a small
  measurement of support decisions against author judgments. Final answer
  grounding, completeness and clinical accuracy require their own review.

From the repository root:

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/measure_saved.py
& services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

The saved-evidence calculation reads existing records and made zero provider
calls. All 750 service tests passed, including nine new failure/empty-search
checks. D-007's adjudicated QA, actual multi-topic metrics, independent answer
review and B's application routing verification remain required for the final
evaluation. No model, prompt, score threshold or deployment setting was selected
from these results.

The [local lexical follow-up](evaluation/lexical-proposal-evaluation.md) measured
all nine proposals, including the three two-topic cases. Its five-passage window
included both proposed topics and all cited passages in every two-topic case.
The later [nine-question comparison](evaluation/vector-proposal-comparison.md)
adds the complete vector and hybrid rankings. All three two-topic cases retain
their exact proposed evidence in the vector run. D's reference adjudication
and independent answer review remain open.

The [first actual cited answer](evaluation/answer-trial.md#actual-answer-and-review)
used the existing full-support CQ-01 public context. It passed wire validation
and an agent review of both claims against four exact citations. Independent
answer review and measurement on the shared QA set remain open.

The [independent review packet](evaluation/development-answer-review.md) adds
the actual answer and five public fixtures for a separate reviewer. It verifies
exact source slices locally and includes three multi-topic composition checks.

The [local HTTP flow](evaluation/local-http-flow.md) exercises eight fresh Chroma
rankings from cached vectors and routes full, two-topic, partial and missing
outcomes through the frozen Python responses. It provides an additional
pre-integration check with zero API calls.
