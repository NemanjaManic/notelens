# Synthetic failure review by case

Date: 2026-11-12. Source: local run of `d-extraction-qa-synthetic-v1` using the unchanged deterministic mock catalog.

This is a regression review of authored synthetic cases. It does not describe clinical risk or general model performance. Multiple records can occur for one case when extraction and QA both miss expected behavior. Full expected/actual values and limitation notes are generated in `eval/reports/local/synthetic-v1/report.md` (ignored local output).

Reference cases: 24; questions: 48; unique annotated source mentions: 29; validation or relationship errors: 0; technical generation errors: 0.

| Failure class | Records | Interpretation |
| --- | ---: | --- |
| `missing_entity` | 15 | The small literal fake does not recognize a reference mention. |
| `qa_state` | 11 | The fake returned an evidence state different from the authored expectation. |
| `qa_support` | 13 | The fake omitted a required literal supporting sentence. |

Each case below lists observed evaluator failure categories. A missing category means this run recorded no discrepancy for that check; it does not establish semantic correctness.

| Case | Group | Failure categories | Follow-up |
| --- | --- | --- | --- |
| `confirmed-01` | confirmed | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `confirmed-02` | confirmed | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `confirmed-03` | confirmed | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `confirmed-04` | confirmed | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `negation-01` | negation | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `negation-02` | negation | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `negation-03` | negation | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `negation-04` | negation | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `history-01` | history | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `history-02` | history | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `history-03` | history | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `history-04` | history | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `procedure-01` | procedures | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `procedure-02` | procedures | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `procedure-03` | procedures | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `procedure-04` | procedures | missing_entity, qa_state, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `complex-01` | complex | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `complex-02` | complex | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `complex-03` | complex | missing_entity, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `complex-04` | complex | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `limited-01` | limited | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `limited-02` | limited | missing_entity, qa_support | Retain as a regression; review with an approved provider and human reference review. |
| `limited-03` | limited | None recorded | Keep; mock pass is not a semantic-quality finding. |
| `limited-04` | limited | None recorded | Keep; mock pass is not a semantic-quality finding. |

## Cases for focused review

- `confirmed-04`: mock misses the second symptom in a two-symptom sentence.
- `negation-03`: the fake catalog does not model contrastive negation scope.
- `history-03` and `history-04`: family subject and historical context outside catalog patterns are missed.
- `procedure-02` and `procedure-03`: planned/cancelled status is not represented by the current shared enums; reference attributes remain unresolved.
- `complex-03`: QA state is acceptable but one of two required symptom sentences is omitted.
- `limited-02`: one side of a contradictory source is omitted. The evaluator does not reconcile the conflict.
- `limited-03`: the targeted injected instruction case is retained; a passing instance is not a general prompt-injection guarantee.

## Metrics from this run

- Exact entity: TP=14, FP=0, FN=15, recall=0.4828, F1=0.6512.
- QA expected evidence state: 37/48.
- Required literal support plus state: 35/48.
- Valid extraction and answer records: 24/24 and 48/48.

These are deterministic mock coverage counts on a small author-created suite. They are not quality targets, not a held-out score and not evidence of clinical accuracy.
