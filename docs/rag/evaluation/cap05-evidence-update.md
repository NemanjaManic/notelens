# CAP-05 evidence update and review handoff

Prepared: 2026-11-24. Owner: Nemanja (A).
Status: A-owned evidence proposal for Milica (D) and B; score reassessment pending.

Later on the same date, the user relayed approval of the bounded final scope and
A supplied the [v3 runtime/corpus handoff](../d009-watchdog-reconciliation-v3.md).
Those preparation checks do not add a final measurement to this CAP-05 evidence.
The original development comparison and pending corrected-answer ratings below
remain unchanged.

The supplied preliminary assessment awards CAP-05 9/14 and cites the historical
nine-case development checkpoint. The accepted A-008 v2 record now provides a
wider development comparison. This update proposes replacement evidence wording;
it does not change the shared scorecard or establish a new score.

## Suggested replacement evidence wording

> The accepted frozen development evaluation compares vector, BM25 and hybrid
> retrieval on 27 literature/mixed queries (81 case/method results). Vector
> achieves unique-topic Recall@5 of 1.000, all required topics in 22/22 eligible
> cases, and reviewed evidence for 27/27 supported requested parts. The recorded
> offline replay reproduces all 81 results; the comparison supports retaining
> vector retrieval. Generated-answer corrections still require follow-up review,
> and unseen final system measurement remains unexecuted.

Use the [A-008 closure](../a008-closure.md),
[public aggregate results](frozen-development-summary.json),
[answer-review follow-up](live-http-smoke-review.md) and
[A-011 final-measurement limits](../a011-freeze.md#final-measurement-and-remaining-live-limits)
as the supporting links. Retain 9/14 until the assessor explicitly revises it;
the detailed scoring rubric is unavailable in this checkout.

## Accepted development evidence

The source record is dated 2026-11-23 and records B's and D's acceptance of
A-008 v2. Those received acceptances cover development retrieval and the recorded
application-routing evidence, with final evaluation kept separate. This document
does not record a new reviewer acceptance.

| Method | Unique-topic Recall@5 | Topic MRR@5 | All required topics@5 | Supported parts with evidence@5 |
| --- | ---: | ---: | ---: | ---: |
| Vector | 1.000000 | 0.909091 | 22/22 | 27/27 |
| BM25 | 1.000000 | 0.852273 | 22/22 | 27/27 |
| Hybrid | 0.977273 | 0.931818 | 21/22 | 26/27 |

The frozen development manifest selects 54 cases: 27 document-only reference
controls, nine literature queries and 18 mixed queries. Only the latter 27 are
included in literature retrieval metrics. Five have no supported-topic reference,
so the topic-metric denominator is 22. The 27 supported requested parts are a
different denominator. Document-only reference controls do not measure D-service
quality. Twenty development reserves are excluded.

The five-passage limit is applied before topic deduplication; passage evidence
credit requires the reviewed evidence bundle. Hybrid has higher overall MRR but
misses one required-topic case and one supported part. Vector preserves coverage
and has higher MRR than BM25. This supports the existing frozen vector selection;
it is not evidence of a new model or prompt improvement.

The historical closure records 81/81 offline replay results, 128 focused RAG
tests and readback of 617 index passages. Replay checks saved rankings and metric
arithmetic. That measurement generated no answers. These counts must not be
presented as newly executed checks or as 81 reviewed generated answers.

## Follow-up requested from Milica (D)

Review the authored revisions against the pinned evidence and preserve both the
original and revised ratings using the existing `d-answer-review-rubric-v1`.

| Case | Existing proposed correction | Requested review outcome |
| --- | --- | --- |
| CQ-03 | Add the compression excerpt to the second claim's evidence. | Confirm that the combined citations support the claim and resolve the original support/gap deductions. |
| CQ-05 | Restrict the second claim to bilirubin buildup and yellow color. | Adjudicate the original extra-fact severity and the pinned-source concern; rate the narrower revision separately. |
| CQ-09 | Use the simpler wording already recorded for urine appearance and smell. | Re-rate clarity and English while checking that the claim's meaning and evidence remain supported. |

Record reviewer identity, date, case ID, original/revised artifact identity,
criterion ratings, remaining errors and acceptance or unresolved findings in
D-owned review records. Preserve CQ-01/CQ-07 as unchanged controls. These are
authored development revisions that passed a historical offline validator replay;
they are not fresh provider completions. No new independent ratings or before/after
quality gains are claimed here. A source or runtime change, if proposed after
adjudication, needs a separate versioned change and evaluation decision.

## Remaining final-evaluation gates

| Responsible owner | Required next evidence |
| --- | --- |
| D, with the team | Frozen unseen-final QA/reference manifest, case counts, review assignments and agreed quality criteria. Keep final cases locked until the approved measurement. |
| B and affected module owners | Confirm the integrated system versions and final execution scope, including actual-provider versus fixture coverage. |
| User and designated operator | Explicit approval of any required provider execution and its budget/limits. Historical trial allowances do not authorize new calls. |
| D coordinating evaluation; A contributing RAG results; B recording integration evidence | A separate versioned final report with measured counts, retrieval and answer-quality results, supported/partial/refused coverage, errors and limitations. Preserve receipts and do not tune on final cases. |

The [A-011 record](../a011-freeze.md) explicitly reports final measurement as
not run. Final-set access, provider-backed D integration and system release
acceptance remain separate gates. The small historical support-assessment subset
does not establish semantic quality or rejection performance across all 27 queries.

## Verification scope for this update

This is a documentation update using existing public records. Checks cover the
aggregate JSON counts, denominators and table values, local Markdown link targets,
the A-011 pinned file hashes, and `git diff --check`. They do not rerun retrieval,
private-archive replay, model generation, the 128-test suite or final evaluation.
No provider call, external message, commit, push or deployment is part of this update.
No Spec Kit implementation workflow is claimed for this documentation change.
