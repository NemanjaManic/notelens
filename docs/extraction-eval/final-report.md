# NoteLens D-009 final measured delivery report

Date: 2026-11-24.

**Delivery status: closed under the previously accepted reduced scope; full
26-case execution acceptance remains unmet.**

The requested tenth attempt was executed once on pinned current main and scored
without selecting a better historical run or combining outputs. It saved 9/26
records: eight completed document cases and one unavailable literature case.
Seventeen cases were not executed. All eight accepted answer branches passed
schema and literal citation checks. Route and evidence-state agreement were each
7/9 saved records. These are structural checks, not semantic accuracy.

See [the complete attempt-10 report](d009-attempt-10-7c1e46b5-ae55-4fa0-acf0-0ca0297b0963.md)
and [aggregate machine-readable results](../../eval/reports/final/d009-attempt-10-summary-v1.json)
for the exact SHA pins, failure, reference binding, accounting and offline checks.

The first nine attempts and the previously accepted reduced-scope decision remain
in [the historical record](../rag/d009-run-attempts-2026-11-24.md). Attempt 9's
22/26 saved records are historical evidence and were not merged into attempt 10.

## Accepted limitations and outstanding quality evidence

- The attempt stopped at F-LIT-01, `answer_service_unavailable`, after successful
  A question-parts and embedding operations. The precise downstream cause was
  not retained; no specific root cause is claimed.
- Final extraction F1 and independent semantic answer risk remain unmeasured.
- Retrieval is a cited-source proxy, not topic Recall@5; interrupted literature
  execution gives zero coverage on the full target denominator for this run.
- D per-call usage is not durably recorded; actual D and historical cumulative
  spend remain unreconciled. The new A/D caps are not cumulative cost clearance.
- The official freeze-based evaluation pipeline was not executed. Mixed answers
  are evaluated per saved branch; no independent semantic assessment is implied.
- Reliability changes followed earlier final-case exposure. This is a repeated
  final-workload evaluation with all attempts disclosed, not an unseen first run.

Raw questions, source documents, gold references, model artifacts, indices,
credentials and original provider/service receipts remain private.
