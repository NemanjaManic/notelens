# C-004 controlled comparison on the frozen C-002 split

**Owner** C

**Date** 2026-11-20

C compared Logistic Regression and CPU XGBoost on `c002-split-v1`.
Both models used the same TF-IDF matrix. The vectorizer was fitted on
864 training documents in 862 groups and transformed the 185 validation
documents in 185 groups. Input used `nfc-lf-v1`. The runner checked
validation text digests against the permitted C-002 handoff. The
Logistic Regression validation metrics reproduced [C-003](../c003-handoff-to-d.md)
exactly. The run evaluated development data only.

The experiment used the existing [TF-IDF and Logistic Regression settings](../../../services/classifier/config/draft-baseline-v1.json)
and [CPU XGBoost settings](../../../services/classifier/config/development-comparison-v1.json)
unchanged. XGBoost used 100 trees, depth 4, learning rate 0.1, one
thread and seed 42. Python was 3.13.7, scikit-learn was 1.7.2 and
xgboost-cpu was 3.1.2.

## Validation results

| Model | Correct | Accuracy | Macro-F1 | Weighted F1 |
| --- | ---: | ---: | ---: | ---: |
| Majority (Cardiovascular / Pulmonary) | 55 / 185 | 29.73% | 0.0917 | 0.1363 |
| TF-IDF + Logistic Regression | 174 / 185 | 94.05% | 0.9285 | 0.9393 |
| TF-IDF + XGBoost | 165 / 185 | 89.19% | 0.8750 | 0.8890 |

Each validation document belongs to a distinct group, so group-adjusted
macro-F1 equals row-level macro-F1 for all three models.

| Specialty | Support | Logistic precision | Logistic recall | Logistic F1 | XGBoost precision | XGBoost recall | XGBoost F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 55 | 0.9483 | 1.0000 | 0.9735 | 0.8462 | 1.0000 | 0.9167 |
| Orthopedic | 47 | 0.9216 | 1.0000 | 0.9592 | 0.9362 | 0.9362 | 0.9362 |
| Gastroenterology | 32 | 0.9355 | 0.9063 | 0.9206 | 0.8438 | 0.8438 | 0.8438 |
| Neurology | 28 | 0.9600 | 0.8571 | 0.9057 | 0.9231 | 0.8571 | 0.8889 |
| Urology | 23 | 0.9500 | 0.8261 | 0.8837 | 1.0000 | 0.6522 | 0.7895 |

Confusion matrices use the table's specialty order for both axes,
with reference labels on rows and predicted labels on columns.
The majority model assigns every row to the first column.

```text
Logistic Regression         XGBoost
55  0  0  0  0             55  0  0  0  0
 0 47  0  0  0              0 44  1  2  0
 1  1 29  0  1              4  1 27  0  0
 1  3  0 24  0              4  0  0 24  0
 1  0  2  1 19              2  2  4  0 15
```

C carries Logistic Regression into C-005. It leads by 0.0535 macro-F1
and 9 correct predictions in this comparison. The existing threshold
sweep at 0.30 accepted 177 of 185 validation cases, including 171 correct
predictions and 6 errors. That point is exploratory input for C-005.
The result applies to the five supported specialties in this validation
set. Final-test performance and out-of-scope behavior remain unmeasured
by this run.

## Reproduce locally

Use the locked classifier environment with the `comparison` group
installed. Run from the repository root with the signed-off split and
approved local handoff package.

```powershell
$reviewDir = 'data/mtsamples/raw/c002-assisted-review/20261120T121852434438Z'
python -B -m notelens_classifier.training.development `
  --split-dir "$reviewDir/c002-split-v1" `
  --split-sha256 21cbaceb2166185613628e347ccac4f3b335cae3bc745d10e77d0854c017185d `
  --handoff-dir "$reviewDir/c002-d002-development-v1" `
  --output '.cache/c004-frozen-comparison-v1'
```

The output directory must be new. The ignored output contains aggregate
`metrics.json`, `model-manifest.json` and `model.joblib`. Verification
matched the model's SHA-256 to its manifest, checked the input pins against
C-003 and compared the complete Logistic Regression metric records.
The classifier and MTSamples suites passed 154 tests and 11 subtests.
A C-003 rerun after sharing the frozen loader reproduced every prediction
and score. Its serialized model SHA-256 differed, which produced a different
model version in the rerun export. D's delivered export has its own
version and checksum.
