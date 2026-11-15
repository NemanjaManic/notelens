# Retrieved Passage Content Review

Owner: Nemanja (A). Reviewer: Codex coding agent for Nemanja (A).
Date: 2026-11-15. Status: agent development review, not human acceptance.

## Scope and method

All fifty passages from the ten completed public development queries were read
against their actual questions. Passage bodies were resolved by the recorded
passage IDs from the verified, unchanged prepared corpus. The review used the
saved [trial results](retrieval-smoke-results.json); no new provider calls,
query embeddings, index rebuilds or LLM answers were needed.

The [structured review](retrieval-content-review.json) records all fifty individual
passage judgments, requested and missing answer parts, expected behavior and
thirteen exact supporting quotes. Each quote has half-open Unicode code-point
offsets in both the canonical topic's cleaned_summary and its retrieved passage.
This is A-owned exploratory work under A-004, separate from D's coordinated
annotations, A-007 acceptance and the frozen final benchmark.

The source report fingerprint and registry/corpus/index/retriever identities are
recorded in that JSON. The reviewed configuration remains text-embedding-3-small,
1,536 dimensions, five passages and the existing cosine ranking policy. The
original trial report and runtime answerability=not_assessed remain unchanged.

## Question-level findings

These labels describe the inspected evidence, not the quality of generated
answers. No answer-generation model was called.

| Question | Requested information | Review of returned evidence | Supporting ranks | Missing part |
| --- | --- | --- | --- | --- |
| CQ-01 | Systolic versus diastolic pressure | Fully supported | 1, 2, 3 | None |
| CQ-02 | COVID-19 cause and duration of infectiousness | Partially supported | 1, for cause only | COVID-19 infectiousness duration |
| CQ-03 | Carpal tunnel syndrome and affected nerve | Fully supported | 1 | None |
| CQ-04 | Sprain versus strain | Fully supported | 1, 2 | None |
| CQ-05 | Jaundice and the substance causing its yellow color | Fully supported | 1 | None |
| CQ-06 | Examples of intestinal obstruction causes and symptoms | Fully supported | 1 | None |
| CQ-07 | Acoustic neuroma and early symptoms | Fully supported | 1 | None |
| CQ-08 | Trigeminal-neuralgia incidence in Serbia during 2025 | Missing in retrieved evidence | None | Requested location/year-specific rate |
| CQ-09 | Possible urinary tract infection symptoms | Fully supported | 1 | None |
| CQ-10 | Whether high PSA alone confirms prostate cancer | Fully supported | 1, 2, 3 | None |

Counts: eight fully supported questions, one partial question and one question
without the requested evidence. Across all fifty passage positions, thirteen
individually cover the whole question, eleven supply only part of it and twenty-six
are related material that does not establish a requested answer part. These are
agent judgments on selected development examples, not an accuracy estimate.

## CQ-01: what the retrieval output means

The first returned passage, High Blood Pressure (topic 34), explicitly defines
systolic pressure during a heartbeat and diastolic pressure between beats.
The second and third returned passages independently contain the same distinction.
The fourth discusses medicines; the fifth discusses risk factors and prevention.
Those last two should not contribute extra claims to this answer merely because
they were retrieved.

The first result's score of 0.4854106903076172 is a ranking value, not a probability
that an answer is correct. The supporting definitions in the passage establish
the agent's evidence judgment; the numeric score alone does not.

## Gaps and misleading alternatives

For CQ-02, the first passage names SARS-CoV-2 and describes transmission, but does
not specify how long an infected person can transmit COVID-19. The fourth passage
does contain infectious-period numbers, but explicitly for RSV. Whooping-cough
timing in the third passage also concerns a different disease. A later answer
must retain the supported cause and explicitly acknowledge the missing COVID-19
duration. It must not borrow a nearby disease's numbers to fill the gap.

For CQ-08, the first result defines trigeminal neuralgia and describes demographic
patterns. None of the five inspected passages supplies new cases per 100,000
people for Serbia in 2025. The expected behavior is an explicit evidence gap for
that statistic. This review does not prove that the statistic is absent from the
entire corpus or from external literature.

The missing-evidence CQ-08 has a top score of 0.49264562129974365, above the fully
supported CQ-01's 0.4854106903076172. The partial CQ-02 has 0.5618729591369629,
above fully supported CQ-09 and CQ-10. A single monotonic top-score cutoff cannot
accept every fully supported case while rejecting these incomplete cases in this
sample. No cutoff is selected or activated by this review.

## Implications for the next increment

The following are proposals for the next approved support-policy package, not
implemented behavior or team-agreed thresholds:

- Evaluate each requested answer part against the actual passage, preserving the
  disease/entity, location, time period, uncertainty and causal relationship.
- Return supported parts with an explicit gap when only part of a question is
  answerable; an unrelated passage must not fill that gap.
- Separate topic relevance, passage support and score-based ranking. CQ-08 finds
  the topic while still lacking the requested evidence.
- Keep CQ-02 and CQ-08 as development regression examples. Expand and independently
  review development cases before selecting a general rejection policy.
- Preserve possible/early symptom wording for CQ-07 and CQ-09, and preserve the
  distinction between screening evidence and diagnosis for CQ-10. Do not turn
  these general literature answers into patient-specific conclusions.
- Measure topic coverage over unique topics in the later evaluation. CQ-03 uses
  three of five positions for one topic; this observation alone does not justify
  changing top-k, introducing deduplication or claiming a recall metric.

Real HTTP retrieval, a general answerability policy, literature generation and
shared integration gates remain open. A-004 is still unchecked.

## Verification and limits

The local evidence check verified the original result and registry fingerprints,
ten matching question identities, all fifty ranked passage identities/metadata,
all thirteen quotes against both passage and canonical topic slices, and the
reported counts. The saved trial results, corpus/index artifacts and public-query
usage ledger were unchanged. No paid calls occurred in this review.

The scoped Spec Kit prerequisite resolver selected specs/001-rag with
SPECIFY_FEATURE_NO_PERSIST=1. The requirements checklist had sixteen checked and
zero unchecked items; no extension hooks were present. This read-only workflow
gate and the review do not close shared dependencies or an implementation task.

No service source or dependency changed, so the prior 358-test suite was not rerun
for this documentation/evidence-only increment. Exact quote validity is a
traceability check, not independent confirmation of the semantic judgments.
The questions were selected earlier by inspecting this corpus and their prior
agent assessments were visible. There is no blinded comparison, independent
human review, clinical validation, held-out measurement or final acceptance here.
