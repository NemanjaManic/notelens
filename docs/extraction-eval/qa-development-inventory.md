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

## Joint A/D reference decisions

Nemanja confirmed the nine development ratings and four source-reference
decisions on 2026-11-22. The [development QA manifest](../../eval/references/qa/d007-a008-development-qa-manifest-v1.json)
applies the cause-only alternate for A-QA-02 and the exact A-QA-09 topic 4452
slice `[0,105)`. The review establishes source support for these development
references. It does not establish clinical validation.

The input has 75 QA rows. `D-DOC/limited-04/absent` has the same document digest,
normalized question and outcome as `D-DOC/negation-01/absent`. The latter is the
retained development reserve. The former is recorded as an excluded duplicate.
The proposed 54 selected candidates and 20 reserves account for all 74 unique
rows. All of these source families stay in development.

The A/D split proposal has 54 development cases and 26 unseen final cases. The
final proposal is eight document-only, eight literature-only, eight mixed and
two out-of-scope cases. At least nine cases in the supported routes should
require multiple sources and at least three should have insufficient evidence.
B's agreement and the final source and review evidence remain pending before
freeze.

Nemanja confirmed the v2 handoff ZIP, the duplicate exclusion and the nine
joint references on 2026-11-22. D independently checked both identical ZIP
copies at SHA-256 `c05f7a2001f94fd7f1df0c2ac63f3ccab63cd5ed46f480da20d686e8041c6b7c`.
All ten file checksums passed. D reproduced 75 raw rows, 74 unique candidates,
54 proposed selections, and 20 reserves. The nine ratings and part states
match A's source review. D matched 12 original and 15 current reference
entries to the pinned passages, including A-QA-09 topic 4452 at `[0,105)`.
The eight targeted QA tests passed.

## B's coverage check and final source separation

Goran checked the [26 proposed final slots](../../eval/reports/development/d007-final-author-review-plan-v2.json)
and confirmed the coverage counts. His availability for 13 author assignments
and 13 independent reviews is pending. Sara accepted her assignments and the
custodian role. She supplied the restricted Drive link and confirmed that she
owns the folder and Goran is its named editor. During authoring and review,
these are the two accounts with access. The split still awaits explicit
approval. B's key-free app-routing check can proceed with development or
synthetic inputs.

D rebuilt the development source inventory from its pinned inputs. The 54
proposed selections and 20 reserves account for all 74 unique candidates and
include all nine reviewed cases. The excluded duplicate belongs to an exposed
development family. Including accepted reference alternatives and additional
context, the development inventory contains 14 connected source groups, 23
distinct canonical document digests, and 12 distinct literature passage IDs
across 12 topics.

Before authoring, Sara and Goran should list each slot's intended sources in
the restricted folder and compare them with the pinned [development exclusions](../../eval/reports/development/d007-development-source-exclusions-v1.json).
Sara confirmed the handoff package checksums and verified that all 26 blank
intake slots match the v2 staffing plan. On 2026-11-22 Goran confirmed the 54
development / 26 unseen-final split and v2 coverage plan, accepted his 13 author
and 13 independent-review assignments, and confirmed Sara as custodian. Sara and
Goran will complete the source list in Sara's restricted folder and check every
slot for source-group overlap before drafting. Sara will send the list version,
SHA-256, checked-slot count, and overlap dispositions. The current intake still
has zero checked source slots. Nemanja's pinned-passage handoff to the authors
remains outstanding.
The [source guidance](d007-final-source-intake.md) and [blank intake template](../../eval/reports/development/d007-final-source-intake-template-v1.json)
pin the exact v2 staffing plan and the existing MedlinePlus passage snapshot.
Sara requested the pinned `passages.jsonl` from Nemanja for the literature
slots. D reverified the A-supplied ZIP's two members and confirmed that the
JSONL and its checksum match the passage manifest and index pin. The artifact
contains 617 passages across 401 topics. Its delivery to Sara and Goran awaits
A's private handoff.
Check document families and canonical digests, and literature origins,
passages and corpus topics. The custodian can share the source-list version,
digest, number of checked slots and overlap disposition with D. The planned
source list is pending. Recheck the completed inventory before freezing,
including any source substitutions, and record the result and manifest
versions. A/D evaluation access follows configuration and manifest freeze.

## A-008 pinned RAG handoff

Nemanja selected `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4` for the key-free
A-008 app rehearsal. D retrieved the exact GitHub archive and installed the
locked indexing dependencies in an isolated Python 3.13.7 environment. From
the repository root, A's commands are:

```powershell
uv sync --locked --directory services/rag --python 3.13 --extra indexing
uv run --locked --offline --directory services/rag --python 3.13 --extra indexing python -B ../../docs/rag/evaluation/serve_indexed_demo.py
```

The launcher defaults to `127.0.0.1:8001`. Set `NOTELENS_DEMO_RAG_PORT=8001`
in the web process and match the service tokens if configured. Append
`--check` for the standalone TCP smoke. D's indexed check stopped before
HTTP startup because Windows Application Control blocked Python's `_sqlite3`
extension during Chroma initialization. The 26 targeted failure, runtime and
non-indexed HTTP tests passed on repeat after an initial readiness timeout.

B reported that the key-free app-routing check passed on `d2f85fb`: the partial
literature answer retained its citation and disclosed the missing start date.
Both mixed runs preserved supported document claims and citation links, with
separate notices for insufficient literature evidence and service unavailability.
Record this as B's owner report. The shared benchmark manifest and configuration
freeze remain open, so A-008 is not closed.

## Frozen development handoff for A-008

On 2026-11-22 D froze the 54-case development selection in
[`d007-a008-development-qa-manifest-v2`](../../eval/references/qa/d007-a008-development-qa-manifest-v2.json).
Its SHA-256 is
`04d14df1a578e4dde2ebd17ef48fae3872e2924b8a0c9b211720bbf0f1aad1ee`.
This supersedes v1 for development measurement and preserves its nine joint
A/D reference decisions, alternatives and A-QA-09 topic 4452 slice `[0,105)`.
The selection contains 27 document-only, nine literature-only and 18 mixed
cases. All 20 reserves and the excluded duplicate remain development-only.

D rebuilt the 74-candidate inventory from the pinned sources and verified the
54 selected IDs, all source pins, 12 original citation slices and 15 current
reference entries including alternatives and context. The nine literature
references have joint A/D technical confirmation. Document and mixed references
retain their synthetic-fixture provenance. This freeze adds no human quality
ratings or provider-generated outputs.

The private handoff `D007-A008-development-freeze-v3.zip` contains the frozen
manifest, its pinned inputs and checksum list. Send it through the approved
one-to-one private chat. No unseen final cases are included. Preserve the v1
manifest and previous packages as historical artifacts.

Nemanja's latest A-008 update identifies three remaining gates: this frozen
development handoff, development measurement against it, and Goran's published,
reviewed web-admission fix commit. The handoff is now prepared locally and still
needs delivery. Development measurement and the admission-fix commit remain
outstanding. A-011 retains the separate final RAG freeze and measurement.
The final QA source checks, final manifest and system configuration are not
frozen by this development handoff. A/D final access remains restricted.
