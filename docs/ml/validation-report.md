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
