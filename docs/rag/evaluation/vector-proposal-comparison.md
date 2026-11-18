# Retrieval comparison on nine public QA proposals

Owner: Nemanja (A). Run date: 2026-11-18.

Retain the vector retriever as the development reference. It returned every
proposed topic and all originally cited passages in the first five results on
this set. BM25 matched that coverage with lower first-topic rank. The hybrid
lost one original passage but found equivalent candidates for the same fact.
This comparison uses A's development references and awaits independent review.

| Group and method | Topic Recall@5 | Topic MRR@5 | All proposed topics at 5 | Parts with original citations at 5 |
| --- | ---: | ---: | ---: | ---: |
| One topic · vector | 1.000 | 1.000 | 5/5 | 5/5 |
| One topic · hybrid | 1.000 | 1.000 | 5/5 | 5/5 |
| One topic · BM25 | 1.000 | 0.867 | 5/5 | 5/5 |
| Two topics · vector | 1.000 | 1.000 | 3/3 | 6/6 |
| Two topics · hybrid | 0.833 | 1.000 | 2/3 | 5/6 |
| Two topics · BM25 | 1.000 | 0.778 | 3/3 | 6/6 |

The ninth case has no proposed supporting topic in its review scope and is
excluded from the topic-metric denominator. The metrics deduplicate topics from
the first five passages. MRR counts the first matching topic, so it can stay high
even when another required topic is missing. No proposal named more than five
topics. The [vector and hybrid rank record](vector-proposal-comparison.json)
preserves the exact ranked IDs. The [BM25 comparison record](lexical-proposal-evaluation.json)
uses the same inputs and references. Retrieval ranks alone do not measure the
quality or safety of a generated answer.

In A-QA-09 the hybrid returned the original Jaundice passage (topic `4452`) but
dropped the original bile-storage passage from Gallstones (topic `4643`). It
returned the exact same alternative passages previously reviewed in the lexical
run for topics `5905`, `4645` and `259`. Each locates bile storage in the
gallbladder. These are candidate substitutes for D to adjudicate. The numeric
table preserves the original labels, so the hybrid's lower original-reference
score does not establish that it lost the underlying evidence.

## Actual query run and replay

Nemanja authorized the exact [five-query scope](vector-proposal-scope.json) with
an upper limit of USD 0.00001. All five embeddings succeeded on their first
attempt, confirming 83 input tokens. At the recorded rate of USD 0.02 per million
input tokens the new reservation and confirmed usage are USD 0.00000166. Earlier
query history stayed intact at 143 tokens. Together the two query runs record 226
tokens and USD 0.00000452 at reference prices. These figures exclude corpus
indexing and support assessment. The actual invoice was not inspected.

The new ledger has five confirmed entries and SHA-256
`d0a0e8a3064bf6f25c45e6f9d28afcb4b17871019ef04de47825b5561908353f`.
The comparison made 18 cached queries across the two methods, with zero provider
calls. It preserved both ledgers and the five new cached vectors byte for byte.
The temporary paid-embedding environment flag was restored and the consumed
execution scope was closed. Attempting execution again was rejected. The closed
scope still reproduced all results from cache.

The measured scope is public development retrieval. D's reference approval,
independent review of final answers and the application integration decision
remain open. No generation or final test run was performed.
