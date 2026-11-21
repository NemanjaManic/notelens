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
passage identity, code-point offsets and quote hashes. The full pinned artifact
was verified after A's 2026-11-21 handoff.

## Development manifest and available excerpts

The [development candidate manifest](../../eval/datasets/qa/development-candidates-v1.json)
pins the original proposal, corpus manifest and three review packets. It joins
A's proposed labels to D's review by case and part without copying public source
text or changing the original references. A-QA-05 and A-QA-07 share a split group.

Before the full artifact handoff on 2026-11-21, D located and independently hashed 9 of the 12 exact proposed
citations in available excerpts. The repeated A-QA-05/A-QA-07 citation counts
once per proposed reference. Eight requested parts had supporting excerpts, two
were missing in their supplied five-passage rankings, and three lacked the exact
excerpt. The scoped gaps concern A-QA-02's duration and A-QA-03's requested rate.
Missing excerpts at that checkpoint concerned A-QA-06, A-QA-08 part 1 and
A-QA-09 part 1. The pinned review below supersedes those pending excerpt states.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.qa_inventory `
  --development-manifest eval/datasets/qa/development-candidates-v1.json
```

## Pinned source review after A's handoff

The supplied MedlinePlus JSONL contains 617 unique passages across 401 topics.
Its SHA-256 matches both the supplied sidecar and A's committed corpus manifest.
D reran the inventory and independently verified all **12/12** proposal
citations, including the three excerpts missing earlier. Passage IDs, topic and
passage code-point offsets, and exact quote SHA-256 values matched. The
[pinned source review](../../eval/references/qa/a-public-qa-pinned-source-review-v1.json)
records the artifact identity, each part judgment and the gap searches.

The source review supports 11 requested parts. A-QA-02 remains partial: the
pinned snapshot states the cause and a transmission mechanism, and the reviewed
COVID-related passages supply no contagious period. A-QA-03 remains without the
required evidence: the disease passages give no 2025 incidence rate for Serbia,
and the search found no Serbia mention. These findings cover the pinned
snapshot. The resulting case counts are seven full, one partial and one without
the requested evidence.

D also found alternate supporting passages for A-QA-01 and the supported part
of A-QA-02, and recorded context for A-QA-07 and a narrower citation for A-QA-09.
The original proposal labels remain the inputs to the published retrieval
replay. Alternate passages are available for relevance review before the
benchmark freeze.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.qa_inventory `
  --passages $d007PassageArtifact `
  --development-manifest eval/datasets/qa/development-candidates-v1.json
```

The command validates source slices. The semantic findings above come from the
recorded agent review. The earlier development manifest preserves the excerpt-only
checkpoint and its results alongside the pinned source review.

These public proposals stay in development. Keep the questions and evidence
labels outside the retrieval index. The final partition and the remaining
benchmark cases require separate selection and review.

## Cross-module development candidates

The [versioned cross-module manifest](../../eval/datasets/qa/cross-module-development-v1.json)
joins the public literature proposals and pinned source review to the existing
synthetic document QA fixture. It adds ten authored mixed requests with separate
document and literature expectations. Each mixed case names a document exercise
and the exact literature question parts it requires. The checker derives answerability
from those references and checks it against the declared case expectation.

| Requested sources | Sufficient | Partial | Insufficient | Total |
| --- | ---: | ---: | ---: | ---: |
| Document only | 22 | 1 | 24 | 47 |
| Literature only | 7 | 1 | 1 | 9 |
| Document and literature | 6 | 3 | 1 | 10 |
| Total | 35 | 5 | 26 | 66 |

The inventory counts one identical question on identical canonical text once.
Both original synthetic fixtures remain available for regression testing. There
are 13 requests for more than one source, including the three multi-topic
literature questions and ten mixed questions. None requires more than five
literature topics. Of the 31 requests with an expected gap, 23 ask only for the
patient's age. This distribution should inform benchmark selection.

The mixed cases cover a complete response, a literature gap, a missing document
fact, a literature-only supported subset and insufficient evidence on both sides.
One case requires two distinct literature topics as well as the document. The
inventory records 22 source groups, including 21 with shared inputs. Requests sharing a canonical text,
a literature origin or a passage stay together, even when the overlap is transitive.
This keeps A-QA-05, A-QA-07 and D-MIX-07 together with the related synthetic
document questions.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.qa_development `
  --passages $d007PassageArtifact
```

The command checks the four source-file SHA-256 pins, the synthetic references,
literature mappings, expected states and shared groups. With the pinned JSONL it
reverifies the 12 original citation slices. The inventory runs locally with no
service or provider calls. These cases and expectations are development candidates
with authored labels. Benchmark selection, independent review and the held-out
partition remain separate acceptance steps.

## Expanded development candidates

The [v2 manifest](../../eval/datasets/qa/cross-module-development-v2.json)
adds eight mixed requests that exercise assertion, subject, procedure status,
missing document facts and unavailable literature evidence. Four new cases have
sufficient evidence, three have partial evidence and one has insufficient
evidence. The inventory now has 74 development candidates and 21 multi-source
requests. None of the eight new prompts asks for age.

The [coverage comparison](../../eval/reports/development/d007-development-coverage-v2.json)
records the new cases, source groups and proposed reference decisions for joint
A/D review. The run checked all 12 original citation slices and four additional
slices against the pinned MedlinePlus snapshot. Reused document and literature
sources connect the 74 candidates into 14 groups, the largest with 23 cases.
Keep these exposed groups in development. The held-out inventory still needs
unexposed inputs and an agreed split.
