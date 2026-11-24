# C-003 validation predictions for D-006

**From** Sara / C

**Date** 2026-11-20

The local C-003 run trained a majority baseline and a TF-IDF + Logistic
Regression baseline on 864 training documents from 862 groups. It
evaluated 185 documents from 185 validation groups. The export matches
the 185 approved records in `c002-d002-development-v1` by `doc_id`, and
every validation transcription matched the canonical SHA-256 in that
manifest. The final-test manifest was outside the run and no test
predictions were produced.

## Validation results

| Baseline | Correct | Accuracy | Macro-F1 |
| --- | ---: | ---: | ---: |
| Majority (Cardiovascular / Pulmonary) | 55 / 185 | 29.73% | 0.0917 |
| TF-IDF + Logistic Regression | 174 / 185 | 94.05% | 0.9285 |

| Specialty | Validation support | Logistic Regression recall |
| --- | ---: | ---: |
| Cardiovascular / Pulmonary | 55 | 100.00% |
| Orthopedic | 47 | 100.00% |
| Gastroenterology | 32 | 90.63% |
| Neurology | 28 | 85.71% |
| Urology | 23 | 82.61% |

TF-IDF and Logistic Regression were fitted only on canonical training
transcriptions. Specialty labels were used as training targets. IDs,
group membership and metadata were used for eligibility, verification
and joining. The run used Python 3.13.7 and scikit-learn 1.7.2 from the
locked classifier environment.

## Export for D

| Item | Value |
| --- | --- |
| Export version | `c003-d006-validation-v1` |
| Model version | `c003-tfidf-logistic-5a25811a79123350` |
| Preparation version | `nfc-lf-v1` |
| Split version | `c002-split-v1` |
| Join keys | C-002 `doc_id` and the matching C-002 handoff version/checksum |
| Delivery files | `predictions.json` and `predictions.sha256` |

Each prediction includes the stable `doc_id`, true specialty, predicted
specialty, status, five probability scores and all three versions. The
status `forced_choice` means every record receives the highest-scoring
label. The scores are native Logistic Regression probabilities. This
run applies no abstention or score-calibration policy, and its measured
coverage is 185/185.

The local check recomputed accuracy and macro-F1 from the JSON,
validated all probability vectors and confirmed both the prediction and
model checksums. The focused suites passed 16 tests and 11 subtests.
To reproduce the run, invoke
`python -B -m notelens_classifier.training.frozen_baseline` from the
repository root with the frozen split directory and its SHA-256, the
C-002 handoff directory and a new output directory under the ignored
local MTSamples directory.

Sara reported that D received the restricted C-002 metadata package.
The C-003 prediction files are staged locally pending a confirmed
delivery location for the prediction export. Report text and trained
model files stay local. D can use this export for development evaluation
once delivered.
