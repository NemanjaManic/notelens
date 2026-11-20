# Document-level lexical evidence comparison, 2026-11-19

**Owner:** C. **Decision:** retain the current ambiguity policy for the local candidate.

The experiment kept the fitted model and section disagreement rules fixed.
It compared the largest coefficient gap for one matched word, the sum of
the two largest distinct word gaps, and the larger of that sum or the
strongest word plus a fitted two-word phrase. These features use learned
coefficient gaps as a heuristic for specialty support. The values are
neither calibrated confidence nor independent evidence.

The reference uses the strongest word with a minimum coefficient gap of
0.20. A cutoff for each alternative was selected using 185 provisional
validation documents and the 128 previously examined synthetic cases.
The new suite was fixed before selection. The [configuration](../../../services/classifier/config/lexical-evidence-v1.json)
records the grid and the development objective.

## Development comparison

| Policy | Cutoff | Full documents correct / wrong / uncertain | Clear synthetic correct / wrong / uncertain | Low-information cases assigned a specialty | Utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current strongest word | 0.20 | 176 / 2 / 7 | 66 / 0 / 9 | 3/11 | 0.6929 |
| Re-tuned strongest word | 0.40 | 176 / 2 / 7 | 63 / 0 / 12 | 0/11 | 0.6929 |
| Two words | 0.50 | 176 / 2 / 7 | 65 / 0 / 10 | 1/11 | 0.6968 |
| Two words or a word and phrase | 0.50 | 176 / 2 / 7 | 65 / 0 / 10 | 1/11 | 0.6968 |

Two words ranked first on development. The phrase variant produced the
same development counts and utility.

## Check on 50 new hand-written examples

The [fixed suite](../../../services/classifier/tests/fixtures/model-check-lexical-v4.json)
contains 25 clear specialty cases, including cases with acronyms and
technical terms, 12 low-information cases, eight unrelated cases and
five mixed-specialty cases.

| Policy | Clear correct / wrong / uncertain | Low-information assigned a specialty | Unrelated assigned a specialty | Mixed assigned a specialty |
| --- | ---: | ---: | ---: | ---: |
| Current strongest word | 24 / 0 / 1 | 2/12 | 0/8 | 1/5 |
| Re-tuned strongest word | 23 / 0 / 2 | 2/12 | 0/8 | 1/5 |
| Two words | 23 / 0 / 2 | 2/12 | 0/8 | 1/5 |
| Two words or a word and phrase | 23 / 0 / 2 | 2/12 | 0/8 | 1/5 |

All three alternatives withheld the same otherwise correct label for the
clear COPD example. The alternatives accepted the same two
low-information cases as the reference. Their development gains did
not transfer to this check, so the current policy remains the local
launcher target. The locked MTSamples test partition was excluded from
fitting and scoring.

All four variants passed the contract and repeatability checks on all 50
responses. All 122 classifier tests passed. The ignored comparison receipts are
`.cache/c-lexical-check-v4-*.json`. The fitted artifact and section policy
were pinned to `.cache/c-ambiguity-policy-v1-selected`. The comparison
variants and development metrics are in `.cache/c-lexical-evidence-v1`.

```powershell
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $classifierPython -B -m notelens_classifier.training.compare_lexical_evidence `
  --reference-model .cache/c-ambiguity-policy-v1-selected `
  --output .cache/c-lexical-evidence-reproduction
```

Use [the check runner](../../../services/classifier/tests/run_model_check.py)
with `--suite-file services/classifier/tests/fixtures/model-check-lexical-v4.json`
and each matching bundle checksum to reproduce the paired results.
