# Local partial-evidence HTTP check

Owner: Nemanja (A). Run date: 2026-11-19.

The [runner](run_partial_evidence_flow.py) re-ranks the three acute bronchitis [development proposals](evidence-gap-proposals.json) with local BM25. It sends them through the actual `/v1/retrieve` and `/v1/literature-answer` Python handlers using in-process HTTP. The author-reviewed support labels and the simulated SDK responses are fixtures. The frozen contracts, support checks, answer adapter, and HTTP response handling run as usual.

| Case | Result | Composer requests |
| --- | --- | ---: |
| EG-03, cause only | `200`, `evidence_state=sufficient`, one supported claim and citation | 1 simulated |
| EG-04, comparison only | `200`, `evidence_state=insufficient`, no claims or sources | 0 |
| EG-07, cause and comparison | `200`, `evidence_state=partial`, one supported claim and citation, one explicit gap | 1 simulated |
| EG-07, partial policy absent | Both routes return `503 configuration_required` | 0 |
| EG-07, simulated claim for the unsupported part | The answer route returns a safe `500 internal_error` | 1 simulated |

For EG-07, the response text says that viruses that cause colds and flu often cause acute bronchitis. The sole citation links to the canonical MedlinePlus passage and matches Unicode offsets `[420, 495)` and the proposal's quote digest. The `warnings` field identifies the missing comparison of cough duration by tobacco-smoke exposure. The SDK request includes only the supported part and its evidence. The rejection check attempts to attach that same citation to the unsupported part and confirms the claim stays out of the HTTP response.

The run verified nine HTTP responses, nine BM25 rankings, three simulated generation requests, and zero provider calls. Under the explicitly enabled test policy, `retrieval_provenance.state=sufficient` permits a supported subset and `evidence_state=partial` signals incomplete coverage. B's eventual client must display the gap from `warnings` alongside the answer. B's agreement on that mapping and an independent semantic review with actual model output remain open. The check demonstrates structural handling of a known evidence gap.

Run from the repository root with the prepared public corpus and locked RAG environment available.

```powershell
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/run_partial_evidence_flow.py
```
