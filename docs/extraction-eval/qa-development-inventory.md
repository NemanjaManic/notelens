# D-007 public development QA inventory

The inventory checks A's nine public development candidates against the
committed corpus manifest. The proposal labels are seven fully supported,
one partially supported and one unsupported in A's reviewed scope. The
candidates cite twelve passage slices. A-QA-05 and A-QA-07 share a passage
and must remain together if the candidates are partitioned further.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.qa_inventory
```

To verify the twelve exact slices, supply A's pinned JSONL artifact with
`--passages PATH`. The tool checks the artifact SHA-256 before verifying
passage identity, code-point offsets and quote hashes. The artifact was
absent in D's working copies, so the local inventory verified proposal
structure and corpus metadata for the complete proposal.

## Development manifest and available excerpts

The [development candidate manifest](../../eval/datasets/qa/development-candidates-v1.json)
pins the original proposal, corpus manifest and three review packets. It joins
A's proposed labels to D's review by case and part without copying public source
text or changing the original references. A-QA-05 and A-QA-07 share a split group.

On 2026-11-21, D located and independently hashed 9 of the 12 exact proposed
citations in available excerpts. The repeated A-QA-05/A-QA-07 citation counts
once per proposed reference. Eight requested parts had supporting excerpts, two
were missing in their supplied five-passage rankings, and three lacked the exact
excerpt. The scoped gaps concern A-QA-02's duration and A-QA-03's requested rate.
Pending excerpts concern A-QA-06, A-QA-08 part 1 and A-QA-09 part 1. The review
was an agent pass over available snapshots. Corpus-wide support and the final
benchmark remain open.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.qa_inventory `
  --development-manifest eval/datasets/qa/development-candidates-v1.json
```

These public proposals stay in development. Keep the questions and evidence
labels outside the retrieval index. The final partition and the remaining
benchmark cases require separate selection and review.
