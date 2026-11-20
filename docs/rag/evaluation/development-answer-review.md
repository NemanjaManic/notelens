# Literature answer review packet

Owner: Nemanja (A). Prepared: 2026-11-18. Status: ready for independent review.

The [review packet](development-answer-review.json) gives D one actual public
completion and five local fixtures. Each case records the question, answer text,
evidence state and exact source coordinates for each claim. Source bodies stay in
the prepared local corpus. A-QA-01 includes the recorded live prompt and response
versions. The [actual run record](answer-trial-results.json) has its usage and
provenance. The packet leaves reviewer judgments open.

| Case | Origin | Reviewer focus |
| --- | --- | --- |
| A-QA-01 | Actual public GPT-6 Luna completion | Both blood-pressure definitions and their exact citations. |
| A-QA-02 | Authored partial fixture | The cause is supported and the contagiousness gap stays explicit. |
| A-QA-03 | Local abstention fixture | The requested Serbia incidence statistic has no cited evidence in the reviewed search. |
| A-QA-07 | Authored two-topic fixture | Match each claim about a nerve to its own source. |
| A-QA-08 | Authored two-topic fixture | Match the definition of adhesions and the separate obstruction-cause claim. |
| A-QA-09 | Authored two-topic fixture | Match bile storage and jaundice color to distinct references. Consider equivalent alternate sources. |

The fixture cases reuse the saved vector passage order and canonical spans from
[A's development proposals](../qa-proposals.json). Fixture scores encode order.
The fixture wording was supplied by the proposal author. These cases can check
rendering, evidence linkage and review procedure. Only A-QA-01 measures actual
model wording. The full packet stays in development and cannot enter the final
holdout. Live partial behavior remains subject to A/B agreement.

## Inspect the exact evidence

From the repository root with the RAG Python environment and the prepared corpus:

```powershell
& services/rag/.venv/Scripts/python.exe docs/rag/evaluation/prepare_answer_review.py --evidence-case A-QA-01
```

Choose a packet case ID. For a partial or missing outcome, the command also shows
the reviewed candidate passages. It prints the canonical slices from the pinned
snapshot and verifies their hashes. Without those local corpus artifacts, use the
attributed source URLs to orient the review and mark exact-slice checks unable to
verify. The command runs offline with no API calls.

## Independent review record

The fields follow the draft D rubric at `docs/extraction-eval/answer-review-rubric.md`
on D's branch (reviewed commit `36ea2a1`). A reviewer records a separate response
before looking at the proposal's author judgments. Use `2` for meets, `1` for a
minor issue, `0` for a major issue, or `U` if evidence is unavailable. Add the claim
or source ID and a reason for each score below `2` or `U`. D can resolve candidate
alternate sources and retain both independent records.

```text
Packet revision:
Case ID:
Reviewer:
Date:
Origin and mode:
Preferred verdict on evidence coverage (full / partial / none / unable to judge):
Source support (2 / 1 / 0 / U):
Required facts (2 / 1 / 0 / U):
Extra facts (2 / 1 / 0 / U):
Uncertainty and context (2 / 1 / 0 / U):
Evidence gaps (2 / 1 / 0 / U):
Scope and safety (2 / 1 / 0 / U):
Clarity and English (2 / 1 / 0 / U):
Notes and smallest needed correction:
Alternative sources, if any:
```

The local run verified all 12 claim-to-passage references. Each two-topic
fixture kept two claims and evidence from two distinct topics. The absent case
kept zero claims and sources. There are no new model results or independent
scores, and neither the QA labels nor an acceptance threshold are frozen here.

## Updated packet with the actual partial answer

The separate [v2 packet](development-answer-review-v2.json), prepared on 2026-11-19,
uses the completed CQ-02 response for A-QA-02. It gives the reviewer two actual
public completions and four fixtures. The A-QA-02 claim and the missing-duration
warning are from the [retained result](partial-answer-trial-results.json).
The other five cases reproduce their original content. All twelve canonical
evidence references were checked. Independent scores remain pending.

To reproduce v2 or inspect its exact partial-answer evidence, run from the root
with the prepared corpus and RAG environment available.

```powershell
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/prepare_answer_review.py --include-actual-partial
uv run --locked --offline --directory services/rag python -B ../../docs/rag/evaluation/prepare_answer_review.py --include-actual-partial --evidence-case A-QA-02
```

The evidence command includes all five retained candidates for this partial case.
A portable Markdown copy under A's ignored review folder contains the actual
answer, these five public passages, source attribution and hashes, blank D rubric
fields, and a blank B decision on partial-wire behavior. Preparing the packet
made zero provider calls. The review covers this known development question.
