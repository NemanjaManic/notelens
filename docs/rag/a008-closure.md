# A-008 closure

Recorded: 2026-11-23. Owner: Nemanja (A). Status: **closed**.

Goran (B) accepted the frozen development retrieval results and application-routing
evidence. Milica (D) accepted the results after verifying both archives and replaying
all 81 recorded case/method results. Nemanja supplied both acceptance messages in
the project conversation. Both reviewers requested **v2** as the closure reference
and explicitly kept A-011 and the final freeze separate.

The closure reference is `Nemanja-A008-frozen-development-results-v2.zip`, SHA-256
`5f96cc4a626a1081d41964097f16948250ba8096f867bc85ffa4d81609d05ff6`.
The original private archive stays in the restricted handoff location; it is not
copied into Git. The [public aggregate record](evaluation/frozen-development-summary.json)
records archive identities, received acceptance, measurement versions and checks.

## Accepted measurement

The frozen development manifest is `d007-a008-development-qa-manifest-v2`, SHA-256
`04d14df1a578e4dde2ebd17ef48fae3872e2924b8a0c9b211720bbf0f1aad1ee`.
Its 54 selected cases include 27 document-only controls, nine literature questions
and 18 mixed questions. Literature retrieval was measured on the latter 27;
document-only reference checks do not constitute a D-service benchmark. Twenty
development reserves were excluded. No unseen final question was accessed.

| Method | Unique-topic Recall@5 | Topic MRR@5 | All required topics | Supported parts with evidence |
| --- | ---: | ---: | ---: | ---: |
| Vector | 1.000000 | 0.909091 | 22/22 | 27/27 |
| BM25 | 1.000000 | 0.852273 | 22/22 | 27/27 |
| Hybrid | 0.977273 | 0.931818 | 21/22 | 26/27 |

Five no-supported-topic cases have no topic-recall denominator. The JSON record
preserves separate literature/mixed and single/multi-topic aggregates. Apply the
five-passage window before deduplicating topics; an exact reviewed evidence bundle
is required for passage credit. No selected case requires more than five topics.

The three historical support assessments allow some evidence in two cases, with
zero observed coverage overstatements among those two. This small author-reviewed
subset is not a semantic rejection or generated-answer benchmark for all 27 questions.
The historical mixed-query embedding run consumed one approved call and 453 input
tokens under USD 0.001; USD 0.00000906 is reference usage, with billing unverified.
There was no answer generation in that measurement. This closure made zero provider calls.

## Verification and app evidence

On 2026-11-23 the agent verified the original v1 archive and all 17 checksum entries,
then v2 and all 19 entries. Measurement JSON, CSV, evaluation configuration, frozen
references, replay report, replay script and executed measurement script are
byte-identical across versions. Version/pin metadata changed to include the web review.
The original archives, receipts and historical `A008_complete=false` fields remain
unchanged; this dated record supersedes those earlier status fields.

The offline replay reproduced **81/81** results from the frozen references and
verified 15 citation-reference entries against the pinned corpus. The focused RAG
suite passed **128 tests**, and the existing index verified all **617 passages**.
The replay checks recorded rankings and arithmetic, rather than making fresh
retrieval or semantic-generation calls.

v2 binds reviewed web commit `4fb192eb157d5e2fb47fc6afdda890af8c229d7e`.
The published review commit `8d4d013c65edae0ce2d98efdbcc651ba27e4b720`
contains the same two file blobs. The RAG, corpus and contract source trees are
unchanged from measured baseline `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4`.
The separate [launcher review](evaluation/launcher-review-14e4b9df.json) verifies
the requested startup and independent shutdown at
`14e4b9dfdfdd5832cae7f03d12e92cc5f9a00593`, using an isolated Windows working copy.
The build, 18 routing tests, 11 classifier transport tests, default mock smoke,
classifier report check and indexed RAG app check passed. Partial literature
kept its citation and start-date gap; insufficient and stopped RAG preserved both
document claims and exact repeated-quote citations, with distinct notices.

B's received application acceptance is separate from these agent-run checks.
The app checks use synthetic indexed RAG and mock extraction; the classifier
report check uses a loopback response double. Browser, fitted-model quality and
provider-backed D behavior were not independently revalidated by this closure.
B-005, B-008, B-009, D-004/D-005 and the shared final freeze retain their own gates.

## Workflow

Used the installed `speckit-implement` agent workflow for A-008/A-011 only.
Explicit context was `SPECIFY_FEATURE_DIRECTORY=specs/001-rag` with
`SPECIFY_FEATURE_NO_PERSIST=1`. The official PowerShell
`check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` selected the existing
feature. The requirements checklist has 16 checked and zero unchecked items.
Ignore rules cover credentials, environments, caches and local corpus/index data.
No `.specify/extensions.yml` exists, so no before/after hooks are registered.
Only A-owned tracked paths changed. No commit, push, external message or deployment
was performed.
