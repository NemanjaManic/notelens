# NoteLens classifier model card

**Owner** C. **Updated** 2026-11-22. **Status** Frozen local measurement complete.

## Frozen classifier

On 2026-11-22 Sara selected the short-text Logistic Regression pipeline
with the existing C-005 uncertainty policy. Its TF-IDF uses word
unigrams and bigrams and character 3–5-grams. The pipeline was fitted on
864 training documents in 862 groups and 3,408 windows drawn from those
training documents. It returns a specialty label or abstains for
permitted English documents. The scores are uncalibrated probabilities
for an educational retrieval signal.
[Development comparison](experiments/c008-short-text-v1.md)

| Setting | Selected value |
| --- | --- |
| Minimum top probability | 0.30 |
| Winner requirement | Unique top score, configured minimum margin 0.00 |
| Document lexical evidence | Sum of up to two distinct word coefficient gaps, at least 0.80 |
| Section minimum word evidence | 0.20 |
| Section score and margin | 0.38 and 0.05 |
| Competing section score ratio and minimum section share | 0.35 and 0.10 |

A single strong word can meet the lexical cutoff. On the frozen 185-document
validation cohort, the selected model produced 176 correct labels, two
incorrect labels and seven abstentions. Coverage was 96.22% and
macro-F1 with abstentions counted as missed labels was 0.9662. The new
follow-up yielded 21 correct and one incorrect label on 25 short clear
cases. Two of ten mixed-specialty cases received a label. All ten
low-information cases and five unrelated cases received `uncertain`.
[Short-text comparison](experiments/c008-short-text-v1.md)

The freeze preserved the model bytes, model version and all policy settings.
The model artifact SHA-256 is
`5951f751949747cb3c251987b1503ffaf1d79df9933862c7a692f01a5d65622c`.
The frozen manifest SHA-256 is
`fd87686bddfe7d3f86103b562161c64c241f6e4759ca69467d1360d35283ac70`.
The local selection record SHA-256 is
`4283b45e04ca44050c80dcebe1da241c5db7799d9a3db0b200549b00eba6800d`.
[Frozen model manifest](../../services/classifier/artifacts/manifests/c008-final-model-v1.json)

## Release and final evidence

| Evidence | Status |
| --- | --- |
| Approved source, duplicate adjudication and split | C-002 frozen as `c002-split-v1`. |
| Model, score policy and actual integration | Short-text selection approved and frozen with the C-005 policy. Local authenticated loopback passed for the selected bundle. B and D coordinated C-007 verification covered the earlier C-005 bundle. |
| C's development annotations and independent reviews | C-010 package received by D on 2026-11-22. |
| Final dataset and measured results | Sara authorized one local run. All 183 reserved test documents were evaluated in run `c008-final-short-text-v1`. |

## Prepared final measurement

The frozen and development manifests produced identical results on all 50
synthetic follow-up cases. The selected development bundle passed authenticated
readiness and both C-007 classification scenarios over local HTTP. All four
synthetic final-run guard tests passed. A separate synthetic input preparation check verified the
locked record format, canonical bytes, checksum handling and group isolation.
The final measurement compared the training-majority baseline,
forced-choice results and selective results on the same reserved documents.
The majority label was Cardiovascular / Pulmonary.

The selection record pins the source, split, canonicalization, dependency
lock, model artifact and policy. The final-run freeze record also binds the
authorized locked test artifact prepared from the audited source and split.

The runner takes an approved freeze record and its independently recorded
SHA-256. Its local format uses stage `approved-final`, `version`,
`review_reference`, `reason`, `majority_label` from training,
`model_manifest_sha256`, `locked_test_sha256`,
`development_document_ids` and `development_group_ids`. The locked test
artifact has stage `locked-test` and `rows`. Each row carries a reviewed
`category`, grouped `group_id` and frozen-contract `document`. Keep
these files in authorized local storage. Record the actual human decision
and obtain its pinned checksum before using the runner. A synthetic
rehearsal supplies only test data.

```powershell
& $classifierPython -B -m notelens_classifier.training.final_measurement `
  --freeze $reviewedFreezePath --freeze-sha256 $approvedFreezeSha256 `
  --model $frozenModelDirectory --locked-test $lockedTestPath
```

The runner checks the freeze and model before accessing test data and
reserves the attempt under `.cache/classifier-final-runs/<version-sha256>`.
It rejects mismatched hashes and development document or group overlap.
It saves aggregate majority, forced-choice and selective metrics. An
interrupted attempt keeps its reservation. Any repeat needs a new approved
version and recorded reason. Keep final results out of model selection.

## Locked final results

The single authorized run on 2026-11-22 evaluated 183 documents in 183
distinct groups from `c002-split-v1`. It used the short-text matched-policy
model, the `nfc-lf-v1` preparation and Python 3.13.7 in the pinned local
environment. The runner recorded the model version and checked the
freeze, locked input and model digests before scoring. The held-out
input and per-document identities stay in private local storage.

| Evaluation | Correct | Accuracy | Macro-F1 | Weighted F1 |
| --- | ---: | ---: | ---: | ---: |
| Training-majority baseline | 55 / 183 | 30.05% | 0.0924 | 0.1389 |
| Classifier forced choice | 176 / 183 | 96.17% | 0.9582 | 0.9616 |

Group-adjusted macro-F1 equals row-level macro-F1 on this cohort because
each group has one document. With the selected uncertainty policy, the
classifier gave 169 correct labels, five wrong labels and nine
`uncertain` responses. Coverage was 174 / 183 (95.08%). Accuracy among
assigned labels was 169 / 174 (97.13%).

| Specialty | Support | Forced precision | Forced recall | Forced F1 | Selective uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 55 | 0.9643 | 0.9818 | 0.9730 | 0 |
| Orthopedic | 47 | 0.9583 | 0.9787 | 0.9684 | 2 |
| Gastroenterology | 32 | 0.9394 | 0.9688 | 0.9538 | 2 |
| Neurology | 27 | 0.9615 | 0.9259 | 0.9434 | 2 |
| Urology | 22 | 1.0000 | 0.9091 | 0.9524 | 3 |

Forced-choice confusion counts use the same specialty order for
reference rows and predicted columns.

```text
54  1  0  0  0
 0 46  0  1  0
 1  0 31  0  0
 1  1  0 25  0
 0  0  2  0 20
```

Urology had the highest abstention rate at 3 / 22. Its two wrong
forced-choice labels went to Gastroenterology. This evaluation measures
specialty labeling on one English benchmark and five specialties. The
probabilities are uncalibrated, and the separate synthetic follow-up
covers selected short and mixed-text limitations. Quality acceptance
remains a team decision. [Synthetic follow-up](experiments/c008-short-text-v1.md)

| Evidence | SHA-256 |
| --- | --- |
| Final run freeze record | `6fd3e5939fdb9289c1d7c6e83a379022ec94e81a07001ada3781b356a7689ab2` |
| Aggregate metrics | `9334ec8d3e89bc773ee501fa59f53a415df680f2a83a5b1000b0968ba4368806` |
