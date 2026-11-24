# Offline answer risk and coverage

Run the D-006 profile with independent answerability and answer correctness
judgments for a fixed set of observed outputs.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile answer-risk --references review.json --predictions outcomes.json
```

Both JSON files declare a `version` and contain a `cases` array with matching
unique IDs. Each reference declares Boolean `answerable` and, for every emitted
answer, Boolean `answer_correct` for that exact output. The review rubric can credit a
correct partial answer even when the full question is unanswerable. Predictions declare
`outcome` as `answered`, `abstained`, or `technical_error`. Only emitted answers
can carry an optional numeric `confidence` between zero and one.

Coverage divides emitted answers by all cases. Risk divides incorrect emitted
answers by all emitted answers and is undefined at zero coverage. Answer rate
and correct rejection rate use the answerable and unanswerable denominators,
respectively. Technical errors remain in the denominators and earn no rejection
credit. The optional threshold curve uses all cases as its coverage denominator
and keeps equal confidence scores together. It is emitted only when every
answer has a confidence score. These metrics do not set acceptance thresholds.

## Saved A development pilot (2026-11-20)

The pilot includes both actual completions in [A's v2 packet](../rag/evaluation/development-answer-review-v2.json).
For A-QA-01, the three distinct supplied excerpts match their recorded SHA-256
digests and span lengths across four citations. They support both claims. The
partial A-QA-02 answer correctly states the supported cause and identifies the
missing duration. Its citation slice was checked in the [evidence review](a-qa-02-03-evidence-review.md).
The full passage JSONL is still required for corpus-wide citation verification.

The pilot counts a case as answerable when the supplied passages support at least
one requested fact. A correct partial answer must identify the gap. Both cases
were answered and met this rule in the non-blinded agent review. The measured
coverage was 2/2 and the observed incorrect-answer count was 0/2. The packet has
zero actual unanswerable outcomes and supplies no confidence scores, leaving the
rejection rate and confidence curve unavailable. The four authored fixtures were
excluded. The two-case result has no calibrated human rating or acceptance threshold.

Run from the repository root using the [agent reference labels](../../eval/references/qa/a-answer-risk-pilot-v1.json)
and the [saved output projection](../../eval/reports/development/a-answer-risk-predictions-v1.json).
Both pin the SHA-256 of A's v2 packet. The [aggregate report](../../eval/reports/development/answer-risk-results.json)
records the observed results.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile answer-risk `
  --references eval/references/qa/a-answer-risk-pilot-v1.json `
  --predictions eval/reports/development/a-answer-risk-predictions-v1.json `
  --output eval/reports/development
```
