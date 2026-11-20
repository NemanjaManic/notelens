# Provisional classifier validation, 2026-11-19

**Owner:** C. **Data:** 860 training rows and 185 validation rows, with one
row per group in each partition. The grouping and split are provisional.
See [the split report](splits.md) and [experiment configuration](../../services/classifier/config/development-comparison-v1.json).

This report covers the original comparison. The
[short-text improvement](experiments/short-text-improvement-v1.md)
records the current local candidate and its follow-up checks.

Both trained estimators used the same transcription text, fixed label order,
training-fitted TF-IDF vocabulary and IDF, and validation cohort. The training
and validation input preparation used NFC and LF normalization. The majority
label came from the training labels. The XGBoost CPU run used 100 fixed rounds
with no validation-based stopping. XGBoost was installed only in the optional
comparison dependency group. [CPU package](https://pypi.org/project/xgboost-cpu/3.1.2/)

## Forced-choice results

| Candidate | Accuracy | Macro-F1 | Group-adjusted macro-F1 |
| --- | ---: | ---: | ---: |
| Majority, Cardiovascular / Pulmonary | 0.2973 | 0.0917 | 0.0917 |
| TF-IDF + Logistic Regression | 0.9351 | 0.9203 | 0.9203 |
| Same TF-IDF + XGBoost | 0.8865 | 0.8718 | 0.8718 |

Logistic Regression leads by 0.0486 macro-F1 and has higher F1 in all five
classes. It is the local integration candidate. The fit took 0.47 s including
TF-IDF, compared with 33.69 s for the boosted estimator on existing features
in this run. These are local timings for different operations.

| Specialty | Validation support | Logistic P / R / F1 | XGBoost P / R / F1 |
| --- | ---: | --- | --- |
| Cardiovascular / Pulmonary | 55 | .9483 / 1.0000 / .9735 | .8333 / 1.0000 / .9091 |
| Orthopedic | 47 | .9216 / 1.0000 / .9592 | .9348 / .9149 / .9247 |
| Gastroenterology | 32 | .9062 / .9062 / .9062 | .8710 / .8438 / .8571 |
| Neurology | 28 | .9600 / .8571 / .9057 | .9200 / .8214 / .8679 |
| Urology | 23 | .9474 / .7826 / .8571 | .9412 / .6957 / .8000 |

Confusion matrices use true rows and predicted columns in the specialty order
above. The majority baseline puts all rows in the first column.

```text
Logistic Regression             XGBoost
55  0  0  0  0                   55  0  0  0  0
 0 47  0  0  0                    0 43  1  2  1
 1  1 29  0  1                    4  1 27  0  0
 1  3  0 24  0                    5  0  0 23  0
 1  0  3  1 18                    2  2  3  0 16
```

Urology has the lowest forced-choice recall in both trained models. Three
Logistic Regression errors map Urology cases to Gastroenterology. XGBoost
maps five Neurology cases to Cardiovascular / Pulmonary. These are aggregate
error patterns. Document-level causes still require development-only review.

## Provisional uncertainty policy

The predeclared local selection rule maximizes correct accepted minus incorrect
accepted on this validation cohort. Ties favor higher coverage, then the lower
cutoff. The winning top-score cutoff was 0.30. An exact top-score tie or zero
vocabulary matches also produces `uncertain`. Coverage uses all 185 examples
as the denominator. The error rate uses accepted examples only.

| Cutoff | Correct accepted | Incorrect accepted | Uncertain | Coverage | Error among accepted |
| ---: | ---: | ---: | ---: | ---: | ---: |
| .30 | 169 | 6 | 10 | 94.59% | 3.43% |
| .40 | 149 | 2 | 34 | 81.62% | 1.32% |
| .50 | 124 | 1 | 60 | 67.57% | 0.80% |
| .60 | 91 | 0 | 94 | 49.19% | 0.00% |
| .70 | 59 | 0 | 126 | 31.89% | 0.00% |
| .80 | 23 | 0 | 162 | 12.43% | 0.00% |
| .90 | 4 | 0 | 181 | 2.16% | 0.00% |

At 0.30 the model abstained on 6/23 Urology, 2/32 Gastroenterology,
1/28 Neurology, 1/47 Orthopedic and 0/55 Cardiovascular / Pulmonary rows.
The returned values are uncalibrated model probabilities.

Four separate synthetic examples probed behavior outside the dataset. A
novel-token-only example returned `uncertain`. Billing, furniture and software
sentences all returned `supported` with Cardiovascular / Pulmonary. These
three false acceptances are evidence that the threshold alone is unsuitable
for screening unfamiliar input. This small probe gives no population-level
estimate. The development HTTP route has no approved `unsupported` detector.

A subsequent [short-text model test](model-test-report.md) evaluated 39
additional hand-written cases with the same model and threshold. It found
52% specialty accuracy and six false acceptances among ten unrelated cases.

## Reproducibility and limits

- Python 3.13.7, scikit-learn 1.7.2, XGBoost CPU 3.1.2, NumPy 2.5.5,
  SciPy 1.18.1 and joblib 1.6.0. Execution used Windows, CPU and one
  configured XGBoost thread. The second run verified identical complete
  model and threshold metrics after stricter split-identity validation and
  binding the threshold to the model version. The configurations were identical.
- Source SHA-256 `a92cb78569f460606661ee7da50c92305b60d0fac2be4b06c8d2de0f234612d4`.
  Provisional split SHA-256 `301176ae47ff28e2487fbfd373f007ce84a546b0263f98f951481f97e0e26d95`.
  The ignored `metrics.json` records both configuration hashes, the lock
  hash and executed code hashes. See the [integration instructions](integration.md).
- Duplicate candidate review, canonical source access, residual template
  leakage and target-domain evaluation are pending. The 183 draft-test rows
  were excluded from fitting and scoring. The raw source was hashed and
  streamed with only selected training and validation rows retained.
  Final test measurement and team approval remain pending.

## C-005 uncertainty selection on the frozen split, 2026-11-20

C selected a development policy for the C-004 Logistic Regression
artifact on `c002-split-v1`. The experiment kept the fitted model fixed
and used the same 185 validation documents and canonical digests as
C-003 and C-004. It evaluated 1,620 configurations on those documents
and 128 synthetic development cases. The selection objective averaged
the two cohorts' utilities. Correct specialty acceptance contributed
+1, while wrong specialty and inappropriate acceptance contributed
−1. Abstentions stayed in each cohort's denominator.
[Selection configuration](../../services/classifier/config/c005-frozen-uncertainty-v1.json)

The selected policy uses a minimum top score of 0.30, a unique winning
score, and a sum of up to two distinct fitted word coefficient gaps of at
least 0.80. A single strong word can still meet the cutoff. The section
rules abstain when competing specialties have independent support at
section level and sufficient document-level support. The C-004
unigram vectorizer has zero fitted phrase features, so the word-plus-phrase
score collapses to the two-word score for this artifact.

| Policy | Threshold / margin | Validation correct / wrong / uncertain | Validation coverage | Development utility |
| --- | --- | ---: | ---: | ---: |
| C-004 top-score reference | 0.30 / 0.00 | 171 / 6 / 8 | 95.68% | 0.3913 |
| Best score-only rule | 0.35 / 0.05 | 158 / 4 / 23 | 87.57% | 0.4826 |
| Best strongest-word rule, gap 0.80 | 0.30 / 0.00 | 166 / 6 / 13 | 92.97% | 0.5457 |
| Selected two-word rule, gap sum 0.80 | 0.30 / 0.00 | 169 / 6 / 10 | 94.59% | 0.5538 |

Macro-F1 with abstentions counted as missed specialty labels was
0.9319 for the C-004 threshold reference and 0.9233 for the selected
policy. The additional abstentions were two otherwise correct
Neurology predictions, one for limited word evidence and one for section
disagreement. Six wrong labels remained accepted, so the error rate
among accepted validation cases was 3.43% versus 3.39% for the reference.
Each validation document represents a distinct group.

| Specialty | Support | Precision | Recall | F1 | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 55 | 0.9649 | 1.0000 | 0.9821 | 0 |
| Orthopedic | 47 | 0.9388 | 0.9787 | 0.9583 | 1 |
| Gastroenterology | 32 | 0.9655 | 0.8750 | 0.9180 | 2 |
| Neurology | 28 | 1.0000 | 0.7857 | 0.8800 | 3 |
| Urology | 23 | 1.0000 | 0.7826 | 0.8780 | 4 |

The first five columns and the rows use the specialty order above.
The sixth column records `uncertain` results.

```text
55  0  0  0  0  0
 0 46  0  0  0  1
 1  1 28  0  0  2
 1  2  0 22  0  3
 0  0  1  0 18  4
```

### Fixed synthetic follow-up

The [50-case lexical suite](../../services/classifier/tests/fixtures/model-check-lexical-v4.json)
was evaluated after selection and shares no exact text with the 128
development cases. It includes specialty examples with abbreviations
and technical terms.

| Policy | Clear correct / wrong / uncertain (25) | Low information accepted (12) | Unrelated accepted (8) | Mixed accepted (5) |
| --- | ---: | ---: | ---: | ---: |
| C-004 top-score reference | 16 / 7 / 2 | 8 | 7 | 4 |
| Best score-only rule | 12 / 0 / 13 | 3 | 1 | 2 |
| Best strongest-word rule | 14 / 0 / 11 | 0 | 0 | 1 |
| Selected two-word rule | 15 / 0 / 10 | 0 | 0 | 2 |

Compared with the C-004 reference, the selected policy removed all
seven wrong labels in this clear-case suite and withheld one otherwise
correct label. Neurology and Urology each received four uncertain
responses in five clear cases. The previous [provisional candidate](experiments/lexical-evidence-v1.md)
correctly labeled 24 of these 25 examples. It used different fitted
features and training, so the figures characterize two distinct
candidates. The short-text coverage loss and residual mixed-text
acceptance remain review points before promotion.

### Score meaning and reproducibility

The five raw scores are uncalibrated Logistic Regression probabilities.
On frozen validation, mean top score was 58.98% and forced-choice
accuracy was 94.05%. Ten equal-width bins gave descriptive top-label
ECE of 0.3507. The sum-over-classes multiclass Brier score was 0.2679.
These are development diagnostics on a single dataset. The synthetic
counts cover selected failure patterns. They give no distribution-wide
estimate of unfamiliar input. The local policy returns `uncertain` on
weak or conflicting support. A dedicated `unsupported` detector
requires separate scope evidence and evaluation.

From the repository root, use the locked local classifier Python with
the training group installed. The C-004 reference must be the reviewed
local bundle.

```powershell
$reviewDir = 'data/mtsamples/raw/c002-assisted-review/20261120T121852434438Z'
python -B -m notelens_classifier.training.frozen_uncertainty `
  --reference-model .cache/c004-frozen-comparison-v1 `
  --reference-manifest-sha256 7c0f662bec72cf87e11be86179f82354a02babc27f5421daeb11d7a8c8b173b3 `
  --split-dir "$reviewDir/c002-split-v1" `
  --split-sha256 21cbaceb2166185613628e347ccac4f3b335cae3bc745d10e77d0854c017185d `
  --handoff-dir "$reviewDir/c002-d002-development-v1" `
  --output .cache/c005-frozen-uncertainty-recheck
```

The executed bundle is `.cache/c005-frozen-uncertainty-v1` with manifest
SHA-256 `e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f`.
The classifier and MTSamples suites passed 155 tests and 11 subtests.
The authenticated FastAPI test client passed contract and repeatability
checks for all 50 follow-up cases. The final test set stayed locked.
