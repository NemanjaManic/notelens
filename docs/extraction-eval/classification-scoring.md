# C-003 validation replay

On 2026-11-20, D replayed C's saved `c003-d006-validation-v1` export for
`c003-tfidf-logistic-5a25811a79123350` against the restricted C-002 validation
manifest. The [aggregate report](../../eval/reports/development/classification-results.json)
records the export, handoff and split checksums and the full confusion matrix.
Matrix rows are the C-002 reference labels. Columns are the predicted labels.

| Specialty | Support | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 55 | 0.9483 | 1.0000 | 0.9735 |
| Orthopedic | 47 | 0.9216 | 1.0000 | 0.9592 |
| Gastroenterology | 32 | 0.9355 | 0.9063 | 0.9206 |
| Neurology | 28 | 0.9600 | 0.8571 | 0.9057 |
| Urology | 23 | 0.9500 | 0.8261 | 0.8837 |

The classifier correctly labeled 174 of 185 documents (94.05% accuracy, macro-F1
0.9285). Urology had the lowest recall (19 of 23). The forced-choice policy emitted
a label for every document. A descriptive constant-majority comparator, selected
using validation support, scored 55 of 185 (29.73% accuracy, macro-F1 0.0917).
A training-fitted baseline requires training label counts or its saved predictions.

The join matched all 185 IDs and all exported true labels. The restricted manifest
contained 185 distinct duplicate-group IDs and 185 unique canonical digests. The
full training and test split memberships were unavailable for a cross-split
leakage audit. The run used zero provider calls and wrote aggregate metrics and
provenance only. The restricted input files stay in the approved team handoff.
These development measurements carry no team quality threshold decision.

From the repository root, set the three path variables to the supplied files and run:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile classification `
  --references $classificationManifest --predictions $classificationPredictions `
  --predictions-sha256 $classificationChecksum --output eval/reports/development
```
