# D-008 review preparation

Updated 2026-11-13. Agent implementation evidence only. Rubric remains an
uncalibrated draft; no human reviews, clinical validation or owner approval are claimed.

Use `eval/fixtures/answer-review-template-v1.json` for each separate review.
Keep `human_reviewed=false` and null ratings until a person actually reviews the
canonical document and exact response. Record the document digest and the SHA-256
of the exact UTF-8 response artifact in `response_sha256`, plus response, prompt,
model/mock and rubric versions. Preserve those artifacts through approved access;
never copy real submitted document bodies into the repository. The checker checks
digest syntax, not artifact availability or the truth of a human declaration.

`answerable_from_document` is yes/partly/no/unclear. `response_action` is
answer/partial_answer/abstain/unclear. `critical_error` and `needs_adjudication`
are booleans. Dimension ratings are integers 0/1/2 or U. U is not zero and is
excluded from the numeric denominator. An unresolved review is not silently
converted to a completed review. Supply a timezone-aware completion timestamp
and rationale only after completion.

For a timeout or service failure, use `response_action=operational_error`, leave
dimension ratings null and `human_reviewed=false`. Record a safe error code/run ID
in issue codes/response ID; never count it as abstention or answer quality.

Run from the repository root:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.answer_review eval/fixtures/answer-review-template-v1.json
./eval/.venv/Scripts/python.exe -m pytest eval/tests/test_review_integrity.py -q
```

The read-only CLI accepts separate JSON files or arrays and writes the aggregate
to stdout. It never edits input files. Invalid records and duplicate review IDs
produce a nonzero exit. Reports separate blank, incomplete, operational-error,
invalid and completed declared-human records. They include per-score counts,
U counts, rated denominators, outcome counts and adjudication flags. No report
authenticates human authorship or resolves disagreements automatically.

Before project use, reviewers independently score development examples, retain
the initial records, discuss disagreements and version any rubric revisions.
Preserve a new record/ID for each revised assessment. D may practice on public
synthetic examples independently, but team adoption and calibration require
actual reviewers. Keep final examples for final reporting, never prompt tuning.
The approximate 40-answer and 20-entity/evidence targets remain planned, not done.

## Comparing independent review submissions

Run the review checker on both submissions using
`python -m notelens_eval.answer_review REVIEW_A.json REVIEW_B.json`.
It pairs distinct reviewer aliases only when case, document, response hashes,
mode and versions match. The report includes exact agreement, two-point
disagreement and unable-to-judge counts by dimension. Its adjudication list
identifies score differences, outcome or critical-error disagreements and
pairs explicitly flagged for adjudication.

The checker preserves the original submissions. Pair counts can include
multiple pairs per output when three or more reviewers score it. Synthetic
tests exercise the report format. Actual rubric calibration requires
independent completed reviews and recorded adjudication decisions.

For retained response files, add `--response-artifacts DIRECTORY`. Each completed
review must identify a UTF-8 JSON file named `RESPONSE_ID.json` in that directory.
The checker compares SHA-256 against the exact file bytes, including whitespace.
The report records the number of checked artifacts. Keep restricted outputs in
their approved restricted location. Artifact matching establishes output identity;
human authorship and semantic review still require reviewer confirmation.

## Synthetic rubric practice (2026-11-21)

One agent applied `d-answer-review-rubric-v1` to seven retained mock HTTP answers
and one injected operational failure. The [practice records](../../eval/reviews/d008-synthetic-practice-v1.json)
include each document digest, response digest, scores and a reason for every
dimension rated below 2 or marked `U`. All practice records declare
`human_reviewed=false` and `independent_review=false`. This exercise used zero
provider calls and provides no inter-reviewer agreement measurement.

| Practice case | Outcome | Scoring finding |
| --- | --- | --- |
| Complete answer | Answer | All seven dimensions meet. |
| Correct partial answer | Partial answer | All seven dimensions meet. The question's missing age is named and the available finding is cited. |
| Correct abstention | Abstain | Evidence gaps score 2. Source support, required facts and context are `U` because there is no applicable fact to score. |
| Generic refusal on an unanswerable question | Abstain | Evidence gaps score 1 because the reply leaves the requested diagnosis gap unnamed. |
| False refusal on an answerable question | Abstain | Required facts and evidence gaps score 0. The response action still records what happened. |
| Incomplete answer marked sufficient | Answer | Source support scores 2 for the emitted claim. Required facts and evidence gaps score 0 because a relevant fact was omitted. |
| One side of a contradiction marked sufficient | Answer | Source support scores 2 for the retained quote. Required facts, context and evidence gaps score 0. Severity is flagged for adjudication. |
| Injected HTTP 503 on an unanswerable question | Operational error | The correlated `provider_unavailable` envelope carries no quality scores and earns no rejection credit. |

### Proposed scoring clarifications

- Score required facts against the in-scope evidence available to answer the
  question. A correct partial answer can earn full marks if it covers all
  available required facts and names the unavailable part.
- Use `U` for claim support and factual context when an abstention emits no
  factual claim. Use `U` for required facts when no requested fact is available.
  Use 0 for required facts when an abstention omits available evidence. Score
  the explanation of the abstention under evidence gaps.
- Treat a generic refusal with no unsupported claim as an abstention. Use
  evidence-gaps score 1 when the source lacks the requested fact and the reply
  gives a vague limitation. Use 0 when the refusal hides available evidence or
  a sufficient answer conceals a material omission. The literal gap-phrase
  check remains a separate diagnostic.
- Assess the support for each emitted claim on its own citation. Assess material
  omissions and unresolved contradictions under required facts and context. The
  severity boundary for a one-sided sufficient response remains for adjudication.
- Keep operational failures in their own outcome. Leave all dimensions null
  and retain the correlated error code and run ID.

### Verification

The seven successful responses come from the [21 November HTTP rerun](synthetic-failure-review-v2.md).
The response hashes use the parsed `AnswerResult` in UTF-8 JSON with sorted keys,
compact separators, Unicode preserved and one terminal LF. The injected fault
uses SHA-256 of the exact HTTP error body. The single fixed request ID is
recorded in its practice row.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.answer_review `
  eval/reviews/d008-synthetic-practice-v1.json
```

The checker reports seven `incomplete` agent practice records, one operational
failure, zero invalid records and zero completed human reviews. The agent scores
are excluded from the human-review denominator. The proposed scoring guidance
awaits independent review before any rubric version or acceptance decision changes.
