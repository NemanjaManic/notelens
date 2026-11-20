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
