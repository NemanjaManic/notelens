# Development check of an embedding-score cutoff

Owner: Nemanja (A). Run date: 2026-11-18.

Keep evidence assessment in the retrieval flow. On these exact nine published
development proposals, a score cutoff alone could not remove the case with
missing evidence while keeping all the known supporting passages. The result
supports continuing to separate ranking from evidence checks. No runtime
cutoff or acceptance rate is selected here.

The [diagnostic](measure_score_gate.py) repeated the vector searches on the
same verified index and cached questions. It evaluated every distinct score
from the top five, plus a cutoff above the highest observed score. For each
cutoff it kept passages whose score met or exceeded it. A question was allowed
if at least one result remained. The [result record](vector-score-gate.json)
reports both question eligibility and whether every original cited passage
for a supported part survived. These are two different outcomes.

| Observed setting | Questions allowed | Allowed without reviewed support | Supported questions rejected | Cited parts retained |
| --- | ---: | ---: | ---: | ---: |
| No cutoff | 9 | 1 | 0 | 11/11 |
| Highest cutoff preserving every originally cited part, 0.485411 | 9 | 1 | 0 | 11/11 |
| Lowest tested cutoff rejecting the missing-evidence question, 0.496443 | 7 | 0 | 1 | 9/11 |

A-QA-03 ranked a related trigeminal neuralgia passage first at 0.492646. Its
reviewed passages lacked the requested Serbia 2025 incidence statistic. The
fully supported A-QA-01 ranked its blood-pressure reference at 0.485411. The
first tested cutoff that excludes A-QA-03 therefore also rejects A-QA-01. It
also removes the initially cited bile-storage passage in A-QA-09. The latter is
a citation-retention result. Previously reviewed alternate sources may still
support that fact. A-QA-02 remains eligible despite only partial evidence.

This development slice has seven full, one partial and one missing-evidence
proposal. It is too small for threshold selection and uses author judgments
relative to reviewed passages. The empty-support case does not claim absence
from the entire corpus. An eligible question would merely reach a later
evidence decision. It does not predict that the model produces a supported
answer. No final questions or new model outputs were used.

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/measure_score_gate.py
```

Run from the existing RAG checkout with its prepared corpus, index and two
public query caches. The nine searches made zero API calls and preserved the
query ledgers and vectors. Run this diagnostic and the local HTTP flow separately
because both use the same protected cache directories. The initial concurrent
HTTP check failed. Running the HTTP check alone reproduced its prior output
byte for byte.
