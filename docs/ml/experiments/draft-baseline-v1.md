# Exploratory classifier baseline on a provisional split

**Date:** 2026-11-16. **Owner:** C / Sara. **Executed by:** coding agent.
**Status:** preliminary development run; no model selection or final measurement.

Sara requested a review and initial training before the draft C-002 split is frozen.
The [split report](../splits.md) documents the unreviewed duplicate candidates,
provisional grouping thresholds and unresolved source/language/canonicalization
issues. This run is explicitly exploratory: neither C-002 nor the final C-003
deliverable is complete. F-014 and the team-reviewed final-set procedure remain open.

## Data and safeguards

The source is the locally supplied MTSamples CSV, SHA-256
`a92cb78569f460606661ee7da50c92305b60d0fac2be4b06c8d2de0f234612d4`.
The provisional manifest SHA-256 was
`301176ae47ff28e2487fbfd373f007ce84a546b0263f98f951481f97e0e26d95`.
Flagged conflicts and unresolved near-candidate groups were excluded from all draft
partitions. There were **860 training rows / 860 groups** and **185 validation rows /
185 groups**. Text and labels were verified against the manifest for development
rows; group IDs and memberships were checked for uniqueness and disjointness.

Only transcription text was used as a feature. The majority label was chosen from
training labels. The TF-IDF vocabulary and IDF and the classifier were fitted on
training text only; validation was transformed and predicted afterward. The source
CSV is checksummed and streamed as a whole; non-training/non-validation rows are
parsed transiently and discarded, not retained for fitting, prediction or metrics.
The 183 draft test rows were not scored. There is no frozen final test yet, so no
claim is made that a final evaluation set has been established or kept untouched.

## Configuration and execution

One configuration was registered before this run in
`services/classifier/config/draft-baseline-v1.json`: word unigrams, lowercase,
no stop-word removal, scikit-learn's specified two-or-more-word-character token
pattern, TF-IDF L2 normalization and a Logistic Regression estimator with
`C=1.0`, `lbfgs`, `max_iter=1000`, `tol=0.0001`, no class weights and random state
42. Other estimator settings are scikit-learn 1.7.2 defaults. The tokenizer excludes
single-character tokens; this may lose medically relevant information. There was
one run and no hyperparameter search or XGBoost comparison.

Python **3.13.7**, scikit-learn **1.7.2**, NumPy **2.5.5**, SciPy **1.18.1**;
the classifier training dependency group is pinned in `uv.lock`. The configuration
SHA-256 was `71f04a5d6b6edd9ef326674b0a71ea6fd46e6d7977e2345cbeb897d0d76b0e46`,
lock SHA-256 `fd0df43c0963ceee8dce60b96f8125201887176b0f1222ec5f1f0a3100edbed6`,
and executed script SHA-256
`8021e8ef8e28db5995149d3def34d313b41cb4514d9ab15cbf6c9d14a302aa1d`.
The source tree was dirty with the uncommitted C-002 and experiment work. No live
provider, GPU service or paid API was used.

## Validation results

These results apply only to the provisional validation portion and must not be
presented as final performance, clinical confidence or production readiness.
Zero-division values are reported as zero; all five labels are included in macro-F1.

| Model | Accuracy | Macro-F1 | Weighted F1 | Group-adjusted macro-F1 |
| --- | ---: | ---: | ---: | ---: |
| Majority: Cardiovascular / Pulmonary | 0.2973 | 0.0917 | 0.1363 | 0.0917 |
| Word TF-IDF + Logistic Regression | 0.9351 | 0.9203 | 0.9335 | 0.9203 |

Every validation group contains one row, so the **group-adjusted macro-F1 equals
the row-level macro-F1** in this run.

| Specialty | Precision | Recall | F1 | Validation rows / groups |
| --- | ---: | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 0.9483 | 1.0000 | 0.9735 | 55 / 55 |
| Orthopedic | 0.9216 | 1.0000 | 0.9592 | 47 / 47 |
| Gastroenterology | 0.9063 | 0.9063 | 0.9063 | 32 / 32 |
| Neurology | 0.9600 | 0.8571 | 0.9057 | 28 / 28 |
| Urology | 0.9474 | 0.7826 | 0.8571 | 23 / 23 |

Logistic confusion matrix, rows true and columns predicted in the table's order:

```text
55  0  0  0  0
 0 47  0  0  0
 1  1 29  0  1
 1  3  0 24  0
 1  0  3  1 18
```

The majority baseline predicts Cardiovascular / Pulmonary for all 185 examples;
its recall is 1.0 for that class and 0.0 for each other class. Fit time was
1.545 seconds and validation prediction time 0.226 seconds in this local run;
these are observations, not performance guarantees. No convergence warnings
were reported.

## Review and next steps

The high validation result needs careful investigation: the split and near-duplicate
cutoffs are provisional, candidate pairs have not been adjudicated, label-revealing
text and residual shared templates have not been ruled out, and source-language and
patient-level separation are unverified. Do not tune duplicate rules to improve this
score or report it as an independent final benchmark. Any substantive development
example review must be recorded in an exposure ledger and kept out of the future
final set. A reviewed, frozen split and consistent canonicalization are required
before the formal baseline, model comparison and eventual final measurement.

The local model and full metrics are in ignored `.cache/c002-draft-baseline-v1/`.
The model contains information learned from source text and is not approved for
redistribution or deployment; load serialized models only from trusted local sources.
The run refuses to overwrite that directory. No document bodies or individual
predictions were committed or logged.

The executed entry point from the repository root was:

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$trainingPython = Join-Path $env:TEMP 'notelens-c-training-py313/Scripts/python.exe'
& $trainingPython -B -m notelens_classifier.training.draft_baseline
```

The installed environment used `uv sync --locked --group training` against the
classifier project. Repeating an experiment requires a separately versioned output;
the entry point intentionally rejects an existing output directory.

The synthetic isolation tests and draft-split tests passed **8/8**; the full
classifier suite passed **69/69** with Starlette deprecation warnings treated as
errors. The Spec Kit resolver selected the C feature and its requirements checklist
had 16/16 checked. No extension hooks were registered. Initial installation into
the OneDrive-based environment failed with Windows access-denied errors; the locked
training dependencies were installed into a separate temporary environment instead.
