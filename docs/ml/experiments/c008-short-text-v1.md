# C-008 short-text development comparison

**Owner** C. **Date** 2026-11-22.

The comparison kept the frozen C-002 development split and the previous
C-005 bundle pinned. One new Logistic Regression pipeline was fitted on
864 training documents in 862 groups and 3,408 training-only windows of
24 words. It reused the earlier balanced word and character recipe with
word unigrams and bigrams, character 3–5-grams and class weighting. The
comparison measures the combined recipe. [Training recipe](../../../services/classifier/config/short-text-improvement-v1.json)

The 185 validation documents and 128 prior synthetic development cases
were used for the existing C-005 policy selection objective. The grid
tested 2,400 policy settings on the single new fitted pipeline. The
separate 50-case follow-up was pinned before fitting and scored after
policy selection. It contained 25 clear cases across the five specialties,
10 mixed-specialty cases, 10 low-information cases and five unrelated cases.
It shared no exact normalized text with earlier synthetic suites. The
locked final test was excluded throughout.

## Results

| Model and policy | Validation correct / wrong / uncertain (185) | Selective macro-F1 | Short clear correct / wrong / uncertain (25) | Mixed assigned a specialty (10) | Low information assigned a specialty (10) | Unrelated assigned a specialty (5) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C-005 reference | 169 / 6 / 10 | 0.9233 | 16 / 1 / 8 | 4 | 0 | 0 |
| New pipeline with the C-005 policy | 176 / 2 / 7 | 0.9662 | 21 / 1 / 3 | 2 | 0 | 0 |
| New pipeline with the development-selected policy | 175 / 2 / 8 | 0.9628 | 21 / 0 / 4 | 2 | 2 | 0 |

With the C-005 policy, validation coverage rose from 94.59% to 96.22%
and errors among accepted documents fell from 3.43% to 1.12%. Forced-choice
macro-F1 rose from 0.9285 to 0.9789. On the new short cases, Neurology
improved from three to four correct labels out of five and Urology
improved from one to three. The one remaining wrong clear-case label was
in Urology. Two mixed cases still received a specialty.

The development-selected policy used a top-score threshold of 0.35, a
minimum margin of 0.05 and a minimum two-word evidence sum of 0.50. It
had a higher prior development utility than the matched policy, 0.6863
versus 0.6773. On the new follow-up it abstained on the wrongly labeled
clear case and accepted two low-information cases. The matched C-005
policy was selected because it improves clear
coverage and mixed-case behavior while preserving abstention on every
low-information and unrelated case in this suite.

## Reproducibility and review

The experiment used the Python 3.13.7 locked environment. All 150 runtime
contract checks passed across the three profiles. The separately packaged
matched-policy candidate reproduced all 50 follow-up outcomes. All nine
existing uncertainty tests passed.

| Private artifact | SHA-256 |
| --- | --- |
| Follow-up suite | `78e8f77aa3737f650683d4bccd6cd929be7ba70bd02d12ebb98c14c07bfc1cf5` |
| Metrics report | `e83b41a8bfbcb673b78fe068fc3c3f87f83b76aa25915583e36e7d27ba7b862d` |
| New fitted model | `5951f751949747cb3c251987b1503ffaf1d79df9933862c7a692f01a5d65622c` |
| Matched-policy candidate manifest | `affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32` |

Local inputs and results are under `.cache/c008-short-text-v1/`. The
matched-policy bundle is in `matched-policy/`. The tuned result and
full aggregate metrics are in `result/`. Sara approved the matched-policy
candidate on 2026-11-22. The exact selection and local loopback verification
are recorded in the [model card](../model-card.md) and
[integration handoff](../integration.md#c-008-selected-bundle-2026-11-22).
