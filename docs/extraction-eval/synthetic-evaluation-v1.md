# Member D: expanded synthetic extraction and QA evaluation

Date: 2026-11-12. Author/reviewer: Codex agent working for Member D (Milica).
Status: implemented and checked locally; human/team review pending.

## Purpose and scope

Exercise the existing extraction and document-answer service over 24 agent-authored
synthetic documents, with two questions per document and four documents in each of
six groups. This extends the earlier one-document smoke. It is inspectable development
and regression material, not a held-out benchmark, actual patient data, or a replacement
for the planned C-manifest-based independent human annotation exercise.

The fixture is separate from the 16 annotation-training examples. Some simple phrases
overlap with the existing fake catalog and examples; no independence or generalization
claim is made. One canonical text is intentionally reused with a different question.
No third-party text, credentials or real personal data were added.

## Files and execution

- [Reference fixture](../../eval/fixtures/extraction-qa-synthetic-v1.json): canonical
  documents, hashes, 29 occurrence-level entity mentions, 48 questions, exact expected
  support quotes and per-case rationales. All labels are authored proposals, not human gold.
- [Suite evaluator](../../eval/src/notelens_eval/suite.py): reference validation,
  grouped metrics, per-case outcomes, required-support checks and failure analysis.
- [Runner](../../eval/src/notelens_eval/run.py): new `synthetic-suite` profile; original
  `smoke` profile remains available. Optional prediction-file rescoring still works.
- [Regression tests](../../eval/tests/test_synthetic_suite.py): malformed references,
  isolation of labels from generation, technical errors, wrong-topic answers and CLI reproducibility.

From the repository root in PowerShell, using the existing evaluation environment:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile synthetic-suite --output eval/reports/local/synthetic-v1
```

This generates `predictions.json`, `results.json` and `report.md` in the ignored output
directory. Only explicitly synthetic inputs are accepted. The runner calls the real
local service function with its unchanged fake provider; this 72-operation suite does
not run over HTTP. Existing HTTP transport tests are separate.

Rescore saved predictions without generation:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile synthetic-suite --predictions eval/reports/local/synthetic-v1/predictions.json --output eval/reports/local/synthetic-v1-rescored
```

Verification commands actually run:

```powershell
./eval/.venv/Scripts/python.exe -m pytest eval/tests -q
./services/extraction/.venv/Scripts/python.exe -m pytest services/extraction/tests -q
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile smoke --output eval/reports/local/smoke-regression
git diff --check
```

Results: 19 evaluation tests and 40 service tests passed. The service suite includes
CLI and HTTP checks. One existing Starlette/httpx deprecation warning remains.
The original smoke retains TP=4, FP=0, FN=1 and three correct QA states.
Promptfoo was not rerun for this extension; its configuration/provider were unchanged.
The Spec Kit prerequisite resolver selected `specs/004-extraction-evaluation` explicitly;
the built-in checklist had 16 checked items and no unchecked items. No extension hook
file was present before or after implementation. The D-006 local subtask was updated;
the parent task and shared gates remain open.

## Findings and interpretation

All 72 returned records pass schema and evidence/relationship validation. Extraction
finds 14 of 29 reference mentions: TP=14, FP=0, FN=15, recall=0.4828 and F1=0.6512.
Zero false positives on this small mock suite does not demonstrate general precision.
Context attributes are correct on the 14 matched mentions; missing mentions are still
false negatives and do not enter matched-attribute accuracy.

QA expected states match on 37/48 questions. Requiring both the expected state and all
authored source quotes reduces that to 35/48. All 25 unanswerable questions receive
valid abstentions; only 12/23 answerable questions receive claims. These numbers
describe the literal mock catalog, not a language model's medical understanding.

The main limitation is deliberate catalog coverage: cough, hypertension, several
family/history variants and procedure wording are not recognized. Arbitrary question
wording is also outside the fake question catalog. Keep these failures visible rather
than adding fixture-specific answers to the provider.

Two particularly useful cases pass the state check but fail required support:

- `complex-03`: the generic symptom answer includes chest-pain negation but omits cough.
- `limited-02`: the answer includes the denial but omits the contradictory positive
  chest-pain statement. Valid evidence for one sentence does not establish completeness.

The injection example preserves its supported chest-pain answer and does not follow
the embedded instruction. This is one targeted regression, not a general security result.
The repeated-mention and non-BMP examples pass the exact occurrence/offset checks.

## Open questions and dependencies

1. Member B: planned and cancelled procedures cannot be faithfully represented by the
   current assertion/temporality enums alone. Their reference attributes are `null`
   in this private evaluator format, not new shared API values. Four attribute values
   remain unresolved across two mentions. Entity presence is still scored; unresolved
   attributes are excluded only if those mentions are matched. No schema was changed.
2. Team: review whether `sufficient` is the right state when answering a question by
   explicitly describing conflicting source statements (`limited-02`). This fixture
   proposes that policy; it is not agreement by B or a clinical resolution of the conflict.
3. Member C: actual permitted canonical documents, group/split manifests and independent
   annotations are still needed for real-data evaluation. This suite does not assign
   annotation work or complete C's dependencies.
4. Live-provider work still needs an approved provider/model, spending and retention
   configuration. No live calls or model/prompt tuning occurred.
5. Human review is needed for semantic completeness, summary quality, extra irrelevant
   claims, English quality and clinical interpretation. Exact support-quote coverage
   cannot replace those judgments. Summary structure/evidence is validated as part of
   extraction, but summary completeness has no independent reference score here.

The next implementation step after these dependencies are resolved is to run the same
cases against an approved real provider and compare failure categories. Do not treat
these visible fixtures as a frozen final test set or choose production thresholds from
their mock scores.

## Local change package

Changes are limited to D-owned evaluation, documentation and task tracking. They are
not committed or pushed by this task. Suggested later commit boundaries:

1. `test: add synthetic extraction and QA evaluation cases`
2. `feat: evaluate extraction and QA across multiple documents`
3. `docs: report synthetic evaluation results and limitations`

## Recorded detailed run

The following section is rendered from the locally generated results. Generated raw
predictions and JSON results remain ignored under `eval/reports/local/`.

# Detailed synthetic extraction and QA evaluation

Agent-authored development fixtures; no human, clinical or live-model validation.

Documents: 24; questions: 48.

Reference version: `d-extraction-qa-synthetic-v1`.
Reference normalized JSON SHA-256: `517b78e8a842e1adc0cf55432801cc17dbffa0999e1b71203d6b1eeceb217785`.

| Group | Documents | Exact TP | FP | FN | QA states correct |
| --- | ---: | ---: | ---: | ---: | ---: |
| complex | 4 | 6 | 0 | 1 | 8/8 |
| confirmed | 4 | 1 | 0 | 4 | 5/8 |
| history | 4 | 1 | 0 | 3 | 5/8 |
| limited | 4 | 3 | 0 | 1 | 8/8 |
| negation | 4 | 2 | 0 | 3 | 6/8 |
| procedures | 4 | 1 | 0 | 3 | 5/8 |

Exact entity scores: `{"assertion": {"accuracy": 1.0, "correct": 14, "excluded_unresolved": 0, "matched_evaluated": 14}, "f1": 0.6511627906976745, "fn": 15, "fp": 0, "precision": 1.0, "recall": 0.4827586206896552, "subject": {"accuracy": 1.0, "correct": 14, "excluded_unresolved": 0, "matched_evaluated": 14}, "temporality": {"accuracy": 1.0, "correct": 14, "excluded_unresolved": 0, "matched_evaluated": 14}, "tp": 14}`.

Record validation: `{"evidence_or_relationship_invalid": 0, "schema_invalid": 0, "schema_valid": 72, "technical_errors": 0}`.

Required literal support and expected state: 35/48.

State matching and exact quote coverage do not establish semantic completeness or clinical accuracy.

## Case outcomes

| Case | Group | Failure records | Unresolved reference attributes |
| --- | --- | ---: | ---: |
| confirmed-01 | confirmed | 0 | 0 |
| confirmed-02 | confirmed | 3 | 0 |
| confirmed-03 | confirmed | 3 | 0 |
| confirmed-04 | confirmed | 4 | 0 |
| negation-01 | negation | 0 | 0 |
| negation-02 | negation | 0 | 0 |
| negation-03 | negation | 4 | 0 |
| negation-04 | negation | 3 | 0 |
| history-01 | history | 0 | 0 |
| history-02 | history | 3 | 0 |
| history-03 | history | 3 | 0 |
| history-04 | history | 3 | 0 |
| procedure-01 | procedures | 0 | 0 |
| procedure-02 | procedures | 3 | 2 |
| procedure-03 | procedures | 3 | 2 |
| procedure-04 | procedures | 3 | 0 |
| complex-01 | complex | 0 | 0 |
| complex-02 | complex | 0 | 0 |
| complex-03 | complex | 2 | 0 |
| complex-04 | complex | 0 | 0 |
| limited-01 | limited | 0 | 0 |
| limited-02 | limited | 2 | 0 |
| limited-03 | limited | 0 | 0 |
| limited-04 | limited | 0 | 0 |

## Failure analysis

Failure records can overlap: one answer may fail both state and required-support checks.

### confirmed-02 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 20, "end": 25, "quote": "cough"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-confirmed-02"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-02 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-02 / supported / qa_support

Expected: `["The patient reports cough."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-03 / extraction / missing_entity

Expected: `{"type": "diagnosis", "mention": {"start": 16, "end": 28, "quote": "hypertension"}, "assertion": "confirmed", "temporality": "current", "subject": "patient", "doc_id": "d-suite-confirmed-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-03 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-03 / supported / qa_support

Expected: `["The patient has hypertension."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-04 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 20, "end": 26, "quote": "nausea"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-confirmed-04"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-04 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 31, "end": 40, "quote": "dizziness"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-confirmed-04"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-04 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### confirmed-04 / supported / qa_support

Expected: `["The patient reports nausea and dizziness."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-03 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 19, "end": 24, "quote": "fever"}, "assertion": "negated", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-negation-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-03 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 37, "end": 42, "quote": "cough"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-negation-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-03 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-03 / supported / qa_support

Expected: `["The patient denies fever but reports cough."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-04 / extraction / missing_entity

Expected: `{"type": "diagnosis", "mention": {"start": 21, "end": 29, "quote": "migraine"}, "assertion": "suspected", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-negation-04"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-04 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### negation-04 / supported / qa_support

Expected: `["The patient may have migraine."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-02 / extraction / missing_entity

Expected: `{"type": "diagnosis", "mention": {"start": 16, "end": 25, "quote": "pneumonia"}, "assertion": "confirmed", "temporality": "historical", "subject": "patient", "doc_id": "d-suite-history-02"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-02 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-02 / supported / qa_support

Expected: `["The patient had pneumonia in 2019."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-03 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 28, "end": 38, "quote": "chest pain"}, "assertion": "negated", "temporality": "unknown", "subject": "family", "doc_id": "d-suite-history-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-03 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-03 / supported / qa_support

Expected: `["The patient's father denies chest pain."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-04 / extraction / missing_entity

Expected: `{"type": "diagnosis", "mention": {"start": 25, "end": 31, "quote": "asthma"}, "assertion": "confirmed", "temporality": "historical", "subject": "family", "doc_id": "d-suite-history-04"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-04 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### history-04 / supported / qa_support

Expected: `["The patient's sister had asthma in childhood."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-02 / extraction / missing_entity

Expected: `{"type": "procedure", "mention": {"start": 29, "end": 40, "quote": "colonoscopy"}, "assertion": null, "temporality": null, "subject": "patient", "doc_id": "d-suite-procedure-02"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-02 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-02 / supported / qa_support

Expected: `["The patient is scheduled for colonoscopy next week."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-03 / extraction / missing_entity

Expected: `{"type": "procedure", "mention": {"start": 14, "end": 20, "quote": "biopsy"}, "assertion": null, "temporality": null, "subject": "patient", "doc_id": "d-suite-procedure-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-03 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-03 / supported / qa_support

Expected: `["The patient's biopsy was cancelled before it occurred."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-04 / extraction / missing_entity

Expected: `{"type": "procedure", "mention": {"start": 25, "end": 35, "quote": "ultrasound"}, "assertion": "confirmed", "temporality": "historical", "subject": "patient", "doc_id": "d-suite-procedure-04"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-04 / supported / qa_state

Expected: `"sufficient"`.

Actual: `"insufficient"`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### procedure-04 / supported / qa_support

Expected: `["The patient underwent an ultrasound yesterday."]`.

Actual: `[]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### complex-03 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 35, "end": 40, "quote": "cough"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-complex-03"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### complex-03 / supported / qa_support

Expected: `["No chest pain.", "The patient reports cough."]`.

Actual: `["No chest pain."]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### limited-02 / extraction / missing_entity

Expected: `{"type": "symptom", "mention": {"start": 51, "end": 61, "quote": "chest pain"}, "assertion": "confirmed", "temporality": "unknown", "subject": "patient", "doc_id": "d-suite-limited-02"}`.

Actual: `null`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

### limited-02 / supported / qa_support

Expected: `["The patient denies chest pain.", "The patient reports chest pain."]`.

Actual: `["The patient denies chest pain."]`.

Likely cause: Limited literal mock catalog or a candidate behavior mismatch; inspect this case.

Proposed next action: Retain the regression case for the approved real provider; review reference semantics with the team.

## Limitations

- semantic_support: Requires independent human review or an approved calibrated judge.
- english_output_quality: The en declaration and English catalog do not prove language compliance.
- unsupported_item_rate: No independent support judgments are present.
- risk_vs_coverage: Needs independent correctness labels, not quote existence alone.
- classification_and_retrieval: Requires C outputs and A corpus/relevance handoffs.
- real_model_performance: No approved live provider/model or real reference set is available.
