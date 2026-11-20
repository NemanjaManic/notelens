# RAG development answer review for B and D

Prepared by A on 2026-11-19 from `rag` at `24f7721` and its local development
drafts. This handoff accompanies the interim mock checkpoint `7aa6c321`.

## D's evidence review

Start with the two actual public development completions in the
[review packet](development-answer-review-v2.json). The four remaining cases
are fixtures for checking abstention, evidence links and multi-topic coverage.
All six cases belong to development.

| Packet case | Record | Review |
| --- | --- | --- |
| A-QA-01 (CQ-01) | [Full answer](answer-trial-results.json) | Check both blood pressure definitions and the four citations. |
| A-QA-02 (CQ-02) | [Partial answer](partial-answer-trial-results.json) | Check the one supported cause claim and its citation, and whether the warning clearly identifies the missing infectiousness duration. |

The packet records 12 exact citation spans. Each has a passage ID, source URL,
Unicode code-point offsets and a SHA-256 digest. Exact text verification uses
A's prepared corpus. Contact A for the pinned source slices if the corpus is
unavailable. A live source page can help assess meaning, while only the pinned
snapshot can verify exact offsets and digests. Some hashed inputs in the packet
come from the owner checkout, including its local CQ-02 trial draft. The two
result records and their hashes are included here.

Record the reviewer, date, case ID, evidence coverage verdict, source support,
correctness, completeness, citation accuracy, clarity and any correction. Flag
any criterion that cannot be judged. Independent ratings are pending.

## B's routing decision

Confirm whether the existing v1.0.0 response can carry a supported literature
subset with `evidence_state=partial`, `retrieval_provenance.state=sufficient`,
claim-linked citations and a gap in `warnings`. The UI needs to show the supported
claim with its citation and display the gap alongside it. In a mixed answer,
preserve separately supported document claims when literature is insufficient
or temporarily unavailable. Record B's decision before the real RAG integration.

The [retained HTTP run](partial-evidence-flow.json) covers nine in-process
responses through the Python routes on A's development checkout. The run used
local BM25, reviewed development labels and simulated generation. It made zero
provider calls.

| Case | HTTP responses | Observed outcome |
| --- | ---: | --- |
| EG-03 | 2 | Sufficient result with one cited claim. |
| EG-04 | 2 | Insufficient result with an explicit gap and zero generation requests. |
| EG-07 | 2 | Partial result with one cited claim and a gap for the unsupported comparison. |
| EG-07, policy unset | 2 | Safe `503 configuration_required` before generation. |
| EG-07, unsupported simulated claim | 1 | Safe `500 internal_error`. |

The replay runner and its RAG implementation dependencies are in the owner
checkout. The interim shared checkpoint can run its own key-free mock suite.
Application routing, independent answer review and the configured real service
remain open.
