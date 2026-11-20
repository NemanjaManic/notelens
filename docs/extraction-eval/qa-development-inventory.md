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
structure and corpus metadata. Source support and the two gap labels
still need independent review against the corpus.

These public proposals stay in development. Keep the questions and evidence
labels outside the retrieval index. The final partition and the remaining
benchmark cases require separate selection and review.
