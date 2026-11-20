# Local lexical measurement on the QA proposals

Owner: Nemanja (A). Run date: 2026-11-18.

BM25 retrieved all proposed topics and all cited passage references among the
first five results on the three two-topic questions. This gives us a local
comparison point for the future vector and hybrid runs. The nine exact English
questions came from [A's development proposals](../qa-proposals.json) and ran
against the 617 unchanged MedlinePlus passages. The run used no query embeddings
or language model requests. The [rank record](lexical-proposal-evaluation.json)
stores the proposal digest, corpus and retriever versions, passage IDs and ranks.

| Proposed references | Questions | Topic Recall@5 | Topic MRR@5 | All proposed topics at 5 | Parts with all cited passages at 5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| One topic | 5 | 1.000 | 0.867 | 5/5 | 5/5 |
| Two topics | 3 | 1.000 | 0.778 | 3/3 | 6/6 |
| No supported topic | 1 | N/A | N/A | N/A | N/A |

Metrics collapse repeated topics in the first five passages. MRR is the inverse
rank of the first matching topic in that deduplicated list, averaged by group.
Passage coverage checks whether every cited passage for a requested fact is present.
A rank hit alone does not establish semantic support. No proposal required more
than five topics. The displayed topic sets and citation spans are A's proposals
and are pending independent adjudication.

| Two-topic case | Positions of original cited passages | Development observation |
| --- | --- | --- |
| A-QA-07 | 1 and 4 | Three passages from the carpal tunnel topic precede the acoustic neuroma source. |
| A-QA-08 | 1 and 2 | Both the alternative obstruction cause and the adhesion definition are near the top. |
| A-QA-09 | 3 and 5 | The original bile-storage citation is fifth. Topics 4645, 5905 and 259 also contain the storage fact in the returned passages and are candidates for alternative credit. |

In the partial COVID-19 case, the top passage supports the cause and the
candidate text does not establish the requested contagiousness period. In the
Serbia incidence case, the first result is the right condition and the five
candidates do not show the requested place, year and numerical rate. These are
observations on the returned passages. The run did not assess the whole corpus
for answerability, calibrate an abstention threshold, or generate final answers.

From the repository root with the prepared local corpus:

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/measure_lexical.py
```

The script uses the existing BM25 implementation and topic metrics. It ranks the
original strings and checks the proposal corpus version. The output omits source
bodies, expected prose answers and caches. The main vector reference is still
the one recorded in the [development handoff](../development-handoff.md). A
fair comparison on the new questions requires vector and hybrid rankings for
their exact wording and reviewed alternatives from D. The integration gate is
unchanged.
