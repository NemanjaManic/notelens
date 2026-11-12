# Classification experiment plan

**Owner:** C

**Date:** 2026-11-11

**Status:** Proposed development protocol; no training, model selection or numeric confidence thresholds executed.

**Data prerequisite:** [Cleaning and duplicate-grouping proposal](cleaning-and-duplicate-grouping-proposal.md)

## 1. Objective and gates

Compare a majority baseline, TF-IDF plus Logistic Regression, and TF-IDF plus XGBoost
on the same reproducible five-specialty benchmark. Choose a deployable model from
validation evidence, preserve the simpler model when warranted, and reserve final-test
measurement for a frozen selection. Classification labels are not diagnoses.

C-003 starts only after C-002's frozen grouped splits. C-002 requires C-001, C-009 and
F-014; C-009 requires F-003/F-004. C-004 compares XGBoost after C-003; C-005 reports the
uncertainty policy and limitations. Packaging/integration are C-006/C-007. C-008 requires
C-007 and C-010 plus the final selection freeze. D's assignments are required for C-010,
not for initial training. See [tasks](../../specs/003-classification/tasks.md).

This is ordinary C-owned proposal documentation, not a rerun of the Spec Kit planning
workflow or evidence that any implementation task has passed. The deadline remains
2026-11-24. No available hours, compute allowance or experiment capacity is assumed.

## 2. Input contract for every experiment

Before training, record and verify:

- Source checksum, cleaning/grouping version and frozen train/validation/test manifest hashes.
- All five categories in a fixed order: Cardiovascular / Pulmonary, Orthopedic,
  Gastroenterology, Neurology and Urology; never let observed output order silently remap scores.
- Counts of documents and unique groups per class and split, conflicts/exclusions and
  development-only review exposure. The current 1,329 nonempty rows are not final support.
- A single text preparation version aligned with B's frozen canonical document rules.
  Internal feature extraction may transform a derived representation, not the canonical text.
- Only transcription-derived features. Do not use descriptions, titles, keywords,
  specialty metadata, document/source IDs, split IDs or annotation answers as predictors.
- Final-test bodies, predictions and metrics unavailable to ordinary training/selection
  commands. Structural metadata may be checked without tuning against final examples.

Keep all duplicate-group members in one split. The main benchmark retains eligible
same-label copies, so report both row-level and group-adjusted metrics. No candidate may
remove hard cases, alter exclusions or replace the split for a favorable comparison.

## 3. Required comparisons

The following experiment IDs are proposed ledger names, not existing runs:

| ID | Candidate | Purpose and controlled inputs |
| --- | --- | --- |
| E0 | Majority-class baseline | Select the majority using training labels only, then predict that category for every validation document. Resolve a count tie by the fixed category order. |
| E1 | Word TF-IDF + Logistic Regression | Required simple text baseline. Learn vocabulary/IDF and estimator from training documents only. |
| E2 | The same frozen TF-IDF features + XGBoost | Required controlled estimator comparison. Reuse E1's training-fitted feature artifact and identical rows; change the estimator, not the benchmark. |
| E3, if justified | Declared feature or weighting ablations | For example, unigrams versus unigrams+bigrams, or training-derived class weighting. Change one named factor and compare on the same validation set. Report separately from the matched E1/E2 comparison. |

Start with local CPU execution and no external inference APIs. Embeddings are optional
future work requiring scope/time/cost review, not part of the required comparison. No
model training, provider activation or package installation happens in this document.

Use a multiclass probability-producing configuration for XGBoost if its output is to be
reported as `probability`; its documented `multi:softprob` objective provides class
probability outputs. This does not establish calibration or clinical confidence.
[XGBoost learning-task parameters](https://xgboost.readthedocs.io/en/stable/parameter.html#learning-task-parameters)

## 4. Pre-register configurations before execution

Create an explicit experiment configuration in C's service paths when execution becomes
eligible. Record every relevant value, including library defaults actually used. The
future service lockfile, not a moving documentation website, determines installed versions.

| Component | Values to record before the run |
| --- | --- |
| Text features | Tokenization, case handling, n-gram range, stop-word policy, vocabulary limits, min/max document frequency, TF scaling and normalization. |
| Logistic Regression | Regularization, solver, class weighting, convergence tolerance and iteration limit. Record convergence warnings instead of hiding them. |
| XGBoost | Booster, objective, tree method, depth/leaf controls, learning rate, boosting rounds, sampling, regularization, class/sample weighting and thread count. |
| Shared controls | Seed list, feature artifact hash, label order, row weighting, validation metric definitions and tie policy. |
| Resource accounting | Machine/runtime description and measured elapsed time, memory observations and artifact size; no invented resource guarantees. |

Propose retaining negation and numbers in the first text baseline, without generic stop-word
removal, stemming, metadata concatenation or oversampling. Record tokenization limitations
in error analysis. Any later preprocessing change is a named development experiment,
not an untracked cleanup of validation/test documents.

Numeric hyperparameter values, search ranges, trial count and resource allowance are not
selected here. C must register a bounded comparison plan before training, based on the
available environment, and record any later amendment and reason. Do not call an unbounded
search a controlled comparison or imply equal tuning effort when it was unequal.

## 5. Training, tuning and leakage prevention

1. Verify frozen split invariants and open only the training and validation inputs.
2. Fit E0 on training labels. Fit E1's vectorizer and estimator on training text/labels.
3. Apply the fitted vectorizer to validation without updating vocabulary, IDF or feature
   selection. Reuse the same fitted features for the controlled E2 comparison.
4. Record all attempted configurations and validation outputs, including failed or worse runs.
5. If tuning is needed, propose group-aware folds inside training when group support permits.
   Refit the entire preprocessing pipeline on each fold's training portion. Freeze fold
   assignments for comparisons. If support is inadequate, report the limitation and use a
   predeclared small validation comparison, not an improvised row-wise cross-validation.
6. Prefer fixed predeclared boosting rounds for the first XGBoost comparison. If early
   stopping is introduced, use a documented group-separated training-internal holdout and
   record the selected iteration. Never use the final test as an evaluation/stopping set.
7. Any class weighting or resampling is derived from the current training portion only.
   Validation/test class proportions and examples remain untouched.

Learned preprocessing must not be fitted on validation or test data. Pipelines help keep
fit/transform boundaries consistent, including during tuning.
[scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)

Training-internal folds must keep duplicate groups intact; class balance is secondary to
that separation. Group-aware stratification is a candidate only after feasibility checks.
[Grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#stratifiedgroupkfold)

Repeated validation use creates selection optimism. Disclose the number of trials and
changes prompted by error inspection; validation performance is not a final unbiased estimate.

## 6. Metrics and report format

First report forced-choice classification for all eligible in-scope validation documents,
before adding an abstention policy. This prevents a model from appearing better merely
because difficult examples were removed from the denominator.

| Metric / evidence | Required reporting rule |
| --- | --- |
| **Macro-F1, primary selection metric** | Arithmetic mean of the five per-class F1 values, not the F1 of averaged precision/recall. Fix the full label set for every candidate. |
| Per-class precision, recall and F1 | Show all five classes, row support, unique-group support and zero-prediction cases. |
| Confusion matrix | Rows = true class, columns = predicted class, fixed category order. Show counts and row-normalized proportions. |
| Accuracy and weighted-F1 | Secondary context; neither replaces macro-F1 or minority-class inspection. |
| Group-adjusted metrics | Recompute using per-row weight `1 / group_size_in_evaluation_split`, so each group contributes total weight one. Clearly distinguish these from ordinary row metrics. |
| Baseline comparison | Same split and metric definitions for E0/E1/E2; report deltas without calling them significant by default. |
| Practical behavior | Measured fit/inference time with measurement method, model size, deterministic repeat checks and failures. No latency target is assumed. |

The metric implementation should follow documented multiclass averaging conventions.
For a zero denominator, use a declared zero-division convention of zero and flag the
affected class; do not silently omit it from macro-F1. Missing class support in a required
split is a feasibility problem to disclose, not an excuse to change the label set.
[scikit-learn classification metrics](https://scikit-learn.org/stable/modules/model_evaluation.html#classification-metrics)

If uncertainty intervals are calculated, resample whole groups rather than individual
duplicate rows, and record the method/seed/replicate count before interpreting results.
Intervals are optional analysis, not an invented statistical-significance guarantee.

## 7. Validation error analysis

Review validation examples only, identifying them by ID in shareable reports. Include
errors from each supported class and some correct cases. Record the sampling method
instead of selecting only favorable examples. Examine:

- Specialty overlap or source-label ambiguity, especially shared procedures/templates.
- Short/fragmentary documents, vocabulary coverage and feature-tokenization failures.
- Whether one large same-label duplicate group dominates a result.
- High-confidence mistakes and which categories are repeatedly confused.
- Metadata leakage, residual duplicate relationships and distribution differences.

Do not relabel or remove validation errors merely because a model gets them wrong. If a
real data defect requires correction, record it, create a new benchmark version and rerun
all comparison candidates. A final-test defect found later requires separate disclosure
and a documented new evaluation version; do not tune on the exposed final results.

Public/synthetic review material is distinct from user submissions. Do not copy document
bodies into logs or versioned experiment tables; use IDs and aggregate findings, with
permitted local access for inspection. No clinical validation is claimed.

## 8. Model selection rule

1. Exclude technically invalid candidates: leakage, corrupted artifacts, wrong labels,
   unresolved fitting failures, incompatible outputs or nonreproducible configuration.
2. Compare the remaining candidates on validation macro-F1 and inspect per-class,
   group-adjusted and practical results. Keep every comparison visible.
3. If Logistic Regression matches or exceeds XGBoost's macro-F1, prefer Logistic Regression
   unless a documented review identifies a concrete justified tradeoff. Do not make XGBoost
   win by changing splits, features or reporting denominators.
4. If XGBoost scores higher, record the gain, per-class regressions and added complexity.
   Propose it for selection only when the measured tradeoff warrants it. A numerically
   small gain is not automatically meaningful; no minimum improvement is invented here.
5. If the majority baseline is competitive or best, report that honestly and investigate
   on development data. Do not present an unhelpful classifier as accepted merely to ship.
6. Record the selected configuration, alternatives, rationale and actual review decision.
   Team acceptance of a regression or a changed demo expectation must remain explicit.

This is a selection protocol, not a preselected winner. Substantive quality targets remain
unset pending measured development review; the target review date remains 2026-11-14,
not a claim that the team has already accepted thresholds or can meet that date.

## 9. Uncertainty and unsupported-input evaluation

After the model comparison, evaluate a proposed uncertainty policy on development data.
Candidate signals include the largest class score and the margin between the top two
scores. Do not pick numeric cutoffs now or tune them on the final test.

Report coverage (accepted in-scope documents / all in-scope documents), error rate among
accepted predictions, per-class rejection rates and forced-choice metrics alongside any
selective metrics. If nothing is accepted, selective error is undefined, not zero. An
always-rejecting policy does not pass simply because it avoids incorrect accepted answers.

For unsupported behavior, use a separately documented development suite with permitted
synthetic inputs and, only after cross-population duplicate checks, any approved other-label
examples. Report false acceptance and rejection separately from five-class macro-F1.
Out-of-scope source labels are not automatically clean negatives; categories may overlap.

Non-English handling needs the agreed B/C/D boundary and an evaluated method. A language
declaration or low class score does not establish language/scope. Probability outputs need
calibration assessment before a calibration claim; any optional fitted calibrator uses only
an appropriate development/training partition and has its own version. No paid LLM judge,
new detector or optional embedding model is assumed.

Align returned `supported`/`uncertain`/`unsupported` semantics with the frozen shared
contract, not just [C's current proposal](member-c-response-to-b.md).

## 10. Experiment ledger and freeze record

Proposed artifacts stay under C-owned `docs/ml/experiments/**` and
`services/classifier/artifacts/manifests/**`; model binaries remain ignored. Record:

- Experiment ID, date, code commit plus dirty-state/patch fingerprint if applicable.
- Python/package versions, dependency-lock hash, platform and relevant execution settings.
- Source, grouping, split, canonicalization, feature and model hashes/versions.
- Explicit hyperparameters, seed/fold assignments, weighting and stopping policy.
- Training/validation row and group counts, fixed label order and metric conventions.
- Actual results, confusion matrices, row/group metrics, warnings, failures and timing method.
- Validation prediction IDs/scores as permitted local outputs, review exposure and selection rationale.
- Status of team review, remaining objections and no fabricated acceptance.

Before C-008, freeze the selected fitted pipeline, label mapping, uncertainty policy,
code/configuration versions and evaluation procedure. Proposed first-release policy:
evaluate the same training-fitted artifact selected on validation; do not silently refit
on train+validation and call it the same model. Any refit needs a declared new artifact and
a development-only plan for its uncertainty/calibration policy before final access.

Final evaluation then runs on the locked test under its actual task/approval gates, with
predeclared baseline comparisons, counts and limitations in the model card. Do not select
the winner from final scores. Repeating a final measurement requires a new version and
documented reason; disclose prior exposure.

## 11. Planned verification and current status

When implementation files and prerequisites exist, the backlog calls for tests such as
`test_training_leakage.py`, `test_comparison.py`, `test_uncertainty.py` and
`test_final_freeze.py` within `services/classifier/tests/`. They should establish training-only
fit boundaries, group separation, common comparison inputs, honest abstention denominators
and final-test gating. These are future checks, not commands executed in this package.

Only documentation has been produced here. No experiment configuration has been executed,
no model fitted, no numeric score threshold selected, no split changed and no final-test
measurement performed. Official documentation was consulted for conceptual behavior;
version-specific APIs and compatibility must be verified against the later service lockfile.
