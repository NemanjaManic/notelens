# Synthetic failure review by case

Date: 2026-11-12. Source: local run of `d-extraction-qa-synthetic-v2` using the unchanged deterministic mock catalog.

This is a regression review of authored synthetic cases. It does not describe clinical risk or general model performance. Multiple records can occur for one case when extraction and QA both miss expected behavior. Full expected/actual values are in the ignored local `eval/reports/local/synthetic-v3/report.md`.

Reference cases: 24; questions: 48; unique source mentions: 29; invalid/technical output errors: 0.

| Failure class | Records | Interpretation |
| --- | ---: | --- |
| `expected_gap_not_disclosed` | 25 | The question has an expected information gap that is absent verbatim from answer text and warnings. |
| `missing_entity` | 15 | The fake catalog does not recognize a reference mention. |
| `qa_state` | 11 | Returned evidence state differs from authored expectation. |
| `required_fact_missing` | 13 | One or more required source passages, or all claims for an answerable question, are missing. |

## Completeness checks

- Required facts complete: 35/48.
- Expected gap phrases disclosed: 1/26.
- Questions with all expected gaps disclosed (including questions with no expected gap): 23/48.
- No extra source quotes: 48/48.
- All required facts, gaps and extra-quote checks: 10/48.

Each case below lists observed categories. No failure means only that these narrow literal checks recorded no discrepancy.

| Case | Group | Failure categories | Follow-up |
| --- | --- | --- | --- |
| `confirmed-01` | confirmed | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `confirmed-02` | confirmed | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `confirmed-03` | confirmed | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `confirmed-04` | confirmed | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `negation-01` | negation | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `negation-02` | negation | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `negation-03` | negation | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `negation-04` | negation | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `history-01` | history | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `history-02` | history | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `history-03` | history | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `history-04` | history | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `procedure-01` | procedures | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `procedure-02` | procedures | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `procedure-03` | procedures | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `procedure-04` | procedures | expected_gap_not_disclosed, missing_entity, qa_state, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `complex-01` | complex | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `complex-02` | complex | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `complex-03` | complex | expected_gap_not_disclosed, missing_entity, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `complex-04` | complex | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `limited-01` | limited | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `limited-02` | limited | expected_gap_not_disclosed, missing_entity, required_fact_missing | Retain and inspect with human references and an approved provider. |
| `limited-03` | limited | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |
| `limited-04` | limited | expected_gap_not_disclosed | Retain and inspect with human references and an approved provider. |

## Focused review

- `confirmed-04`, `complex-03`: multi-fact answers miss one required symptom passage.
- `limited-02`: conflicting source statements are not both included.
- All 25 insufficient questions fail the named-gap phrase check; the controlled mock refusal does not identify the missing age/diagnosis explicitly.
- The partial age question includes its gap phrase, but completeness can still fail due to other checks.
- `procedure-02` and `procedure-03` retain unresolved annotation status because the shared draft enums cannot model planned/cancelled states.

## Entity metrics

Exact mentions: TP=14, FP=0, FN=15, recall=0.4828, F1=0.6512.

These are deterministic mock coverage measurements only, not quality targets, a held-out score, a clinical measure, or general language understanding.
