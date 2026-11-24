# Local classifier model test, 2026-11-19

**Owner:** C. **Model:** the fitted TF-IDF and Logistic Regression
development candidate, with its existing 0.30 threshold.

The [original test suite](../../services/classifier/tests/fixtures/model-check-short-v1.json)
contains 39 hand-written English cases. The cases cover 25 short specialty
passages with labels fixed before inference, 10 unrelated passages and four
ambiguous passages. Every case went through the authenticated classifier
route using the existing model artifact. Each case was sent twice. All 39
outputs validated against the frozen contract and matched on repetition.

## Specialty results

| Expected specialty | Correct | Wrong | Uncertain |
| --- | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 5 | 0 | 0 |
| Orthopedic | 4 | 1 | 0 |
| Gastroenterology | 2 | 3 | 0 |
| Neurology | 1 | 4 | 0 |
| Urology | 1 | 4 | 0 |
| Total | 13 | 12 | 0 |

Accuracy was **52%** and macro-F1 was **0.5163**. The threshold accepted
all 25 specialty examples. All 12 errors were assignments to Cardiovascular
/ Pulmonary. The model also returned that specialty on 6/10 unrelated and
3/4 ambiguous examples. It returned `uncertain` on the remaining four
unrelated and one ambiguous examples.

This small test probes behavior on short inputs. The stronger provisional
validation score, 0.9203 macro-F1, was measured on a separate MTSamples
validation partition. The short-text results identify a pronounced bias
toward the majority class and poor rejection of unrelated text. The cases
do not estimate population-level performance or support a clinical use
claim. The test left the threshold and model artifact as fitted. Final
measurement on the locked set remains pending.

This suite subsequently served as development evidence. The
[improvement report](experiments/short-text-improvement-v1.md) compares
the new candidate and the original on a separate 40-case suite.

## Reproduce the model test

Use the Windows environment and trusted artifact recorded in the
[integration handoff](integration.md). From the repository root:

```powershell
$classifierPython = Join-Path $env:TEMP 'notelens-c-comparison-py313/Scripts/python.exe'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
& $classifierPython -B services/classifier/tests/run_model_check.py `
  --development-model .cache/c-development-comparison-v1-verified `
  --model-manifest-sha256 b2d5b13573c69f9160f87d8fd360f76086875a811a94361ea99013caa193b015
```

The runner emits metrics and synthetic case IDs with predicted labels.
The recorded result is in ignored `.cache/c-development-model-check-2026-11-19.json`.
