# RAG development integration evidence

Owner: Nemanja (A). Checkpoint: 2026-11-18. A-008 remains open.

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
gap or outage separately. B's actual routing and rendering are outside these
service tests. A partial literature response still needs confirmation of the
[frozen retrieval semantics](answer-support-policy.md#frozen-interface-interpretation-requiring-confirmation).

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
Vector and hybrid rankings for the new questions and D's adjudication remain open.
