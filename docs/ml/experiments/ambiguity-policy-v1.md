# Classifier ambiguity policy, 2026-11-19

**Owner:** C. **Status:** local development candidate.

The policy is applied after the existing top-score and margin check. It
uses the fitted Logistic Regression coefficients for individual words to
check that at least one matched word favors the chosen specialty. It also
scores sections and some coordinated clauses separately. A conflict
requires two different specialties to have both independent support and
a meaningful share of the document. The competing specialty must also
have support in the document-level scores. Leading explicit negations,
such as “No history of ...”, are excluded from section voting by a
limited text rule. These are uncertainty heuristics.

The selected policy uses a minimum word coefficient gap of 0.20, section
score of 0.38, section margin of 0.05, competing document score ratio of
0.35, and minimum share of 10% of document words for each voting specialty.
The classifier returns its existing `uncertain` status with an English
explanation for weak word evidence or conflicting sections. The fitted
model and document scores are the same as the
[short-text candidate](short-text-improvement-v1.md).

## Development selection

Selection used 185 provisional validation documents and the 79 previously
seen synthetic examples in the first two check suites. The initial rules
without a minimum share for each specialty reduced the combined
development utility. The selected version adds that share and compares
competing document-level scores to limit rejection from incidental mentions.
Utility is the mean of correct specialty acceptance minus incorrect and
inappropriate acceptance, normalized within the two cohorts.

| Outcome | Existing policy | Ambiguity policy |
| --- | ---: | ---: |
| Full validation correct / wrong / uncertain | 179 / 3 / 3 | 176 / 2 / 7 |
| Seen short specialty correct / wrong / uncertain | 46 / 0 / 4 | 46 / 0 / 4 |
| Seen mixed or low-information cases assigned a specialty | 4/9 | 1/9 |
| Seen unrelated cases assigned a specialty | 2/20 | 2/20 |
| Combined normalized utility | 0.7288 | 0.7424 |

## Comparison on 49 new synthetic cases

The [third suite](../../../services/classifier/tests/fixtures/model-check-ambiguity-v3.json)
was fixed before policy selection. Both candidates processed the same
49 examples. The 14 ambiguity examples comprise nine mixed-specialty
passages followed by five low-information passages.

| Outcome | Existing policy | Ambiguity policy |
| --- | ---: | ---: |
| Correct specialty returned on clear cases | 21/25 | 20/25 |
| Wrong specialty returned on clear cases | 0/25 | 0/25 |
| Uncertain response on clear cases | 4/25 | 5/25 |
| Mixed-specialty cases assigned a specialty | 9/9 | 3/9 |
| Low-information cases assigned a specialty | 2/5 | 2/5 |
| Unrelated cases assigned a specialty | 1/10 | 1/10 |
| Responses matching the API contract and repeated result | 49/49 | 49/49 |

Section disagreement accounted for all six newly uncertain mixed cases.
The word-evidence rule also withheld a correct Neurology label for a
clear electromyography example. It did not improve the five
low-information results in this suite. Treat both the coverage cost
and residual acceptance as open review findings. The reserved MTSamples
test partition remains locked for the final measurement.

## Reproduction and evidence

Use the [local classifier environment](../integration.md).

```powershell
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $classifierPython -B -m notelens_classifier.training.select_ambiguity_policy `
  --reference-model .cache/c-short-text-improvement-v1 `
  --output .cache/c-ambiguity-policy-new-run
```

The executed output is `.cache/c-ambiguity-policy-v1-selected` with
manifest SHA-256 `e0674f10f2adb1c81ffdac1d157d10947662d0fff913fd37352d973fdf7c61a2`.
The ignored receipts are `.cache/c-ambiguity-check-v3-reference.json`
and `.cache/c-ambiguity-check-v3-candidate.json`. Reuse the
[model check runner](../../../services/classifier/tests/run_model_check.py)
with `--suite-file services/classifier/tests/fixtures/model-check-ambiguity-v3.json`.

All 121 classifier tests and the installed binding checks passed.
The candidate also passed an authenticated Uvicorn loopback smoke run
covering readiness, a supported response, both abstention explanations,
the API contract and process cleanup.
