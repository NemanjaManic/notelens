# NoteLens classifier model card draft

**Owner:** C. **Status:** provisional local candidate, 2026-11-19.

The current candidate uses word and character TF-IDF, balanced Logistic
Regression, short training-only windows and an ambiguity policy to label permitted
English documents across the five agreed specialties. The output is a soft
retrieval signal for an educational demo. Use only authorized public or
synthetic text. The label is a document specialty, not a diagnosis.

The fitted estimator reached 0.9789 forced-choice macro-F1 on 185 provisional validation
documents. On 25 new hand-written specialty examples it returned 25
correct labels, compared with 15 for the original. It assigned a
specialty to one of ten unrelated passages and three of five ambiguous
passages before adding the ambiguity policy. The probabilities are uncalibrated.
The base rule requires a top score of at least 0.35 and a margin of at least 0.05. See the
[improvement report](experiments/short-text-improvement-v1.md) and
[original validation results](validation-report.md).

The [ambiguity policy](experiments/ambiguity-policy-v1.md) checks distinctive
word evidence and support across separate sections. On 49 new examples
it reduced mixed-specialty acceptance from 9/9 to 3/9. Correct returns on
clear examples went from 21/25 to 20/25. Acceptance of low-information
examples remained 2/5.

A [lexical evidence comparison](experiments/lexical-evidence-v1.md)
tested combinations of words and phrases. The alternatives did not reduce
low-information acceptance on a new 50-case suite and each lost one
correct clear result. The current ambiguity policy stays selected locally.

## Release and final evidence

| Evidence | Status |
| --- | --- |
| Approved source, duplicate adjudication and split | Pending C-002 and F-014. |
| Model, score policy and actual integration | Pending measured selection on the reviewed split and C-007. |
| C's development annotations and independent reviews | Pending D-003 and C-010. |
| Final dataset, support, metrics and acceptance | Pending the approved freeze and locked final measurement. |

The [local inference handoff](integration.md) records a checksum-pinned
development model. Retain those exploratory results separately. The final
model must be fitted from the approved training partition, with the
selection and uncertainty policy recorded before held-out access.

## Prepared final measurement

The C-owned runner has been exercised with synthetic packages only. For the
actual run, record the source, grouping and split versions, approved
canonicalization, fit/config/lock hashes, model artifact, fixed score policy,
review reference and reason. The trusted final model manifest has stage
`frozen`. Preserve the trained preprocessing and estimator together.

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
