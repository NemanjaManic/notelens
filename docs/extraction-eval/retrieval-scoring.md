# Offline retrieval scoring

The D-006 retrieval profile scores supplied rankings against separately reviewed
relevance. It does not retrieve documents or call a provider.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.run --profile retrieval --references reference.json --predictions ranking.json
```

Both files contain a `version` string and a `cases` array with matching, unique
`id` values. Each reference case declares `source_scope` (single or multi),
`required_topic_ids`, and `required_passage_groups`. Each passage group lists
alternative reviewed passage IDs for one required piece of evidence. A group
is covered when at least one alternative appears in the first five ranked
passages. Every prediction case supplies `ranked_passages` in rank order, with
`passage_id` and `topic_id` on each passage. An empty ranking represents a
successful retrieval with no results. Technical failures require separate tracking.

Topic recall and reciprocal rank use unique topics in order of first appearance
within the first five passages. A second passage about the same topic contributes
no second hit. Evidence coverage uses reviewed passage IDs independently of topic
hits. The JSON report includes overall and single-/multi-source aggregates and
flags cases with more than five required topics. The committed regression cases
are synthetic. Corpus-measured results require the reviewed D-007 references.

## A public development replay

On 2026-11-20, D prepared and ran a provisional replay of the existing scorer against A's
[public QA proposals](../rag/qa-proposals.json) and
[saved vector top-five rankings](../rag/evaluation/vector-proposal-comparison.json).
The report files joined by case ID and each distinct cited passage served as a
provisional required passage group. The supplied A-QA-02 and A-QA-03 evidence packet
matches the saved vector passage IDs in rank order for both cases. The source passage
JSONL was absent, so canonical quote offsets and SHA-256 values could not be checked.

All eight cases with proposed reference topics retrieved every proposed topic and
cited passage. Topic Recall@5, topic MRR@5 and passage evidence coverage@5 were each
1.0 for the five single-topic cases and the three multi-topic cases.
A-QA-02 contributes the supported cause of COVID-19 and remains partial overall.
A-QA-03 has no supported reference topic and was excluded from the retrieval
denominators. These are exact-match results against A's proposed labels on known
development questions. They do not confirm the correctness or completeness of those
labels, and D-007 review and a shared reference-backed evaluation remain open.

The same D scorer was also run against A's saved hybrid and BM25 rankings. A-QA-03
was excluded because it has no proposed required topics. For passage evidence, each
distinct cited passage ID was treated as one required group. Results are per-case
means; A's proposed labels remain unreviewed.

| Retriever | Cases | Topic Recall@5 | Topic MRR@5 | Cases with all topics at 5 | Passage evidence coverage@5 | Cases with all evidence at 5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Vector | 8 | 1.000 | 1.000 | 8/8 | 1.000 | 8/8 |
| Hybrid | 8 | 0.938 | 1.000 | 7/8 | 0.938 | 7/8 |
| BM25 | 8 | 1.000 | 0.833 | 8/8 | 1.000 | 8/8 |

By source shape, hybrid scored 1.000 topic recall and evidence coverage on the five
single-topic cases. On the three multi-topic cases it scored 0.833 for both measures
and returned all proposed topics in 2/3 cases. BM25's topic MRR was 0.867 for the
single-topic cases and 0.778 for the multi-topic cases. These results reproduce
ranking coverage against A's proposal; they do not judge source entailment or answer
quality.

The [pinned saved development evaluation](../rag/evaluation/saved-development-evaluation.json)
records three topical rankings: A-QA-01, A-QA-02 and A-QA-04. Each has one-case
Recall@5 and MRR of 1.0. It also records a five-passage retrieval for A-QA-03/CQ-08,
which has no expected topic reference and contributes to neither topical metric. The
separate support assessment covers A-QA-01, A-QA-02 and A-QA-03 as one full, one
partial and one no-evidence result. A's assessment says it was not blinded, was not
independently reviewed, and does not claim human gold labels or final-answer evaluation.
The saved corpus and index versions are recorded in that file.

The rerun therefore verifies scorer behavior and reproduces A's proposed-label coverage
where saved ranks exist. D's limited agent review of A-QA-02/A-QA-03 is recorded in the
[evidence review](a-qa-02-03-evidence-review.md); it is non-blinded and does not complete
answer-risk measurement or independently freeze A's reference set. The pinned passage
JSONL, full reference review and C's development predictions remain outstanding inputs.
