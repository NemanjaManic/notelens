# Short-text classifier improvement, 2026-11-19

**Owner:** C. **Status:** local development candidate.

The earlier model often assigned short or unrelated passages to the
majority specialty. This experiment fitted three balanced Logistic
Regression candidates on the same 860 provisional training documents.
It compared word TF-IDF, word TF-IDF with short training windows, and
word plus character TF-IDF with the same windows. The window recipes
added 3,392 training-only passages of 24 words. Class weights came from
training document counts. Windows inherit the document label, which can
introduce weak labels when an excerpt has little specialty information.
[Predeclared configuration](../../../services/classifier/config/short-text-improvement-v1.json)

Selection used the 185 complete provisional validation documents and
the 39 previously examined short examples. The score was the mean of
the two cohort utilities. Within each cohort a correct accepted
specialty gained one point, a wrong accepted specialty lost one point,
and an accepted unrelated or ambiguous example lost one point. Each
utility was divided by its cohort size. The original model used its
existing 0.30 cutoff. The selected word and character candidate used a
0.35 cutoff and a minimum 0.05 gap between its two highest scores.
Neither the 40 new examples nor the reserved MTSamples test partition
was used for fitting or selection.

## Development comparison

| Model | Full-document forced macro-F1 | Correct / wrong / uncertain on 185 full documents | Correct / wrong / uncertain on 25 short examples | Unrelated accepted | Ambiguous accepted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original word model | 0.9203 | 169 / 6 / 10 | 13 / 12 / 0 | 6/10 | 3/4 |
| Balanced word | 0.9767 | 171 / 3 / 11 | 14 / 0 / 11 | 1/10 | 0/4 |
| Balanced word and windows | 0.9789 | 173 / 3 / 9 | 21 / 0 / 4 | 1/10 | 1/4 |
| Selected word, character and windows | 0.9789 | 179 / 3 / 3 | 21 / 0 / 4 | 1/10 | 1/4 |

## Results on 40 new synthetic examples

The [suite](../../../services/classifier/tests/fixtures/model-check-short-v2.json)
was recorded before fitting. Both checksum-pinned artifacts processed
the same cases through the authenticated classifier route after the
candidate was selected.

| Outcome | Original | Selected candidate |
| --- | ---: | ---: |
| Correct specialty returned | 15/25 | 25/25 |
| Wrong specialty returned | 6/25 | 0/25 |
| Uncertain specialty response | 4/25 | 0/25 |
| Forced-choice macro-F1 on the 25 specialty cases | 0.6778 | 1.0000 |
| Unrelated passages assigned a specialty | 7/10 | 1/10 |
| Ambiguous passages assigned a specialty | 2/5 | 3/5 |
| Responses matching the API contract and repeated prediction | 40/40 | 40/40 |

The candidate gave all five labels correctly on their five short
examples. It accepted one unrelated passage and more ambiguous passages
than the original on this small suite. The threshold and margin do not
establish scope. These hand-written examples probe selected failure
patterns. The provisional validation and synthetic results do not
establish final performance or team acceptance. Both model files are
local and ignored. The candidate artifact is about 9.20 MB, versus
0.88 MB for the original.

## Reproduction and receipts

Use the [classifier environment](../integration.md) and the existing
checksum-pinned reference bundle. From the repository root:

```powershell
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $classifierPython -B -m notelens_classifier.training.improve_short_text `
  --reference-model .cache/c-development-comparison-v1-verified `
  --output .cache/c-short-text-improvement-new-run
```

The executed run used `.cache/c-short-text-improvement-v1` and
produced manifest SHA-256
`fa5dcd941449dac01314596225577d8e2878e0c4dca645f7d82cdf162e873df8`.
Its `metrics.json` records data, lock, configuration and code hashes.
The two ignored comparison receipts are
`.cache/c-short-text-check-v2-reference.json` and
`.cache/c-short-text-check-v2-candidate.json`. To repeat either check,
use the [model test runner](../../../services/classifier/tests/run_model_check.py)
with `--suite-file services/classifier/tests/fixtures/model-check-short-v2.json`
and the matching bundle directory and manifest checksum.

Python 3.13.7 and scikit-learn 1.7.2 were used. The classifier test suite
passed 118 tests. The installed Python contract checks passed. The new
bundle also passed a real Uvicorn loopback smoke check for readiness,
supported and uncertain results, request correlation and process cleanup.
