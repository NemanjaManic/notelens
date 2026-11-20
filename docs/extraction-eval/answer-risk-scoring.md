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
