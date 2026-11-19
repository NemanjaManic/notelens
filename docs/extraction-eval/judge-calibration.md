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
