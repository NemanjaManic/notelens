# A-005 public development retrieval comparison

Owner: Nemanja (A). Run date: 2026-11-18.

Keep the question-only vector retriever as the development reference for now.
The hybrid run ties it on context-topic ranking and on the number of questions
with usable evidence. The hybrid adds a second index and search, and the observed
changes do not yet justify adopting it. This choice is provisional pending the
versioned single-source and multi-source QA cases coordinated by D.

Both runs used the exact questions from the [public development registry](../retrieval-smoke-questions.json),
the same 617 passages and the same validated cached query vectors. The original
vector ranking matched all ten recorded top-five passage sequences. The hybrid
ranks the canonical passage words using BM25 and fuses up to 20 Chroma neighbors
with up to 20 lexical candidates using reciprocal rank fusion. It returns five
passages with ties resolved by passage ID. Inputs contain the question only,
which isolates the lexical change from the optional A-006 signals. Tokenization
uses Unicode NFKC and case folding. The starting parameters were BM25 `k1=1.2`,
`b=0.75` and RRF `k=60`. [Lucene BM25 reference](https://lucene.apache.org/core/10_2_2/core/org/apache/lucene/search/similarities/BM25Similarity.html),
[RRF paper](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf).

| Development observation | Vector | Hybrid |
| --- | ---: | ---: |
| Questions with all registered context topics in the first five passages | 10/10 | 10/10 |
| Mean context-topic Recall@5 | 1.00 | 1.00 |
| Context-topic MRR@5 | 0.95 | 0.95 |
| Questions with a fully supporting passage | 8/10 | 8/10 |
| Questions with at least a partially supporting passage | 9/10 | 9/10 |
| Additional paid calls / cost | 0 / USD 0.00 | 0 / USD 0.00 |

Topic metrics collapse repetitions within the first five passages. The mean
reciprocal rank uses the first reference match within that distinct-topic list.
The registry names one context topic for each question, including the question
with a missing statistic. Context topics are development references. Finding one
does not establish evidence. There are zero multi-topic cases and no topic set
with more than five references in this registry. Split metrics over reviewed
multi-source references and the locked final benchmark remain open.

## New passage review

The [ranking record](hybrid-comparison.json) reports matches with the prior agent
review and flags 14 question/passage pairs that were new to the hybrid top five.
The table records this run's additional agent judgments over those exact passages.
One gave full support, four gave partial support and nine did not support the
requested information. All questions with added support already had full evidence
in the baseline. No new passage filled the missing part of CQ-02 or the requested
statistic in CQ-08. The judgments are from the coding agent without independent
review. Passage ID is available at the corresponding hybrid rank in the JSON.

| Question | Hybrid rank | New source | Support | Reason |
| --- | ---: | --- | --- | --- |
| CQ-01 | 5 | Pulmonary Hypertension | None | Explains pressure in pulmonary vessels without defining systolic and diastolic pressure. |
| CQ-02 | 4 | Polio and Post-Polio Syndrome | None | Discusses a different virus and its transmission window. |
| CQ-02 | 5 | Hepatitis | None | Discusses hepatitis causes, transmission and symptom onset. |
| CQ-03 | 5 | Wrist Injuries and Disorders | Partial | Describes nerve compression in the wrist without naming the nerve. |
| CQ-04 | 3 | Joint Disorders | Partial | Explains chronic strain without defining sprain. |
| CQ-04 | 5 | Wrist Injuries and Disorders | Full | Distinguishes ligament injury from muscle or tendon injury in the same sentence. |
| CQ-05 | 5 | Liver Diseases | Partial | Describes jaundice as yellowing of skin and eyes without attributing the color to bilirubin. |
| CQ-06 | 5 | Small Intestine Disorders | None | Lists obstruction without giving its causes or symptoms. |
| CQ-07 | 2 | Neuroblastoma | None | Covers a different tumor. |
| CQ-07 | 4 | Pain | None | Discusses pain in general without describing acoustic neuroma. |
| CQ-08 | 3 | Shingles | None | Discusses postherpetic neuralgia and gives no Serbia 2025 trigeminal neuralgia statistic. |
| CQ-09 | 3 | Urinary Incontinence | Partial | Identifies UTI as a possible cause of bedwetting in adults. |
| CQ-09 | 4 | Enlarged Prostate (BPH) | None | Describes BPH symptoms and lists UTI as a complication without linking the listed symptoms to UTI. |
| CQ-10 | 5 | Prostate Diseases | None | Lists PSA and biopsy among tests without stating what an elevated PSA alone establishes. |

## Reproduce and verify

Run from the repository root with the prepared corpus, matching local index, and
intact cached vectors from the prior public development run.

```powershell
& services/rag/.venv/Scripts/python.exe -m notelens_rag.hybrid_smoke
& services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

The command writes the rank comparison to standard output without passage bodies.
It verifies the registry and baseline version, refuses changed baseline ranks,
and reuses cached vectors through a provider-forbidden session. All 20 ranking
replays hit the cache. The vector files and usage ledger remained byte-identical.
The full 741-test suite passed, including six new hybrid and measurement tests.
The local Spec Kit resolver selected `specs/001-rag` with 16 of 16 requirements
checklist items checked and no extension hooks.
