# Classifier interface proposal for B

**Owner**: C. **Date**: 2026-11-11. **Status**: assistant inspection/proposal only.
This is not affected-owner acceptance, contract freeze or completion of C-009.
Canonical definitions remain in [contracts/v1](../../contracts/v1/README.md).

The measured five source labels map exactly to the five proposed classification display
labels after removing source-label surrounding whitespace. No enum change is needed for
this local release. C will consume B's prepared text without altering it and return the
same `doc_id` and `text_sha256` through `POST /v1/classify`.

Before C-009 can implement consumer checks, B's F-003/F-004 work needs to provide frozen
schemas, generated Python bindings and representative fixtures. Suggested acceptance
cases for B's review:

- Supported: exactly one score for each of the five categories, no duplicate category,
  selected category present, model version and honest confidence note.
- Uncertain/unsupported: null category; define whether available scores may still be
  returned. Do not imply that low confidence detects every unfamiliar language or domain.
- Probability scores: finite values in [0,1]; confirm the probability-vector sum tolerance
  if normalization is to be checked. Decision scores can be signed and are not probabilities.
- Identity: unchanged canonical text and matching document digest, including non-BMP text.
- Missing/incompatible model: safe shared configuration/unavailable error, not a fabricated
  successful prediction. Mock output must remain distinguishable from real-model output.
- Invalid/empty/oversized input: shared English validation behavior and unchanged approved
  100,000-code-point limit; no submitted-text logging or persistence.

The schema's category-count constraint alone cannot enforce unique coverage of all five
categories. The shared README already requires uniqueness; the eventual tests should check
it explicitly. Semantic language and digest checks also require runtime verification.
No schema changes or competing hand-maintained models have been introduced.

After B publishes F-014, C can complete C-002 and give D source-checksum-bound group/split
IDs. D should use those frozen manifests for assignments, not the current nonempty
inspection subset, which still contains known conflicting duplicate groups. Before model
selection, C must receive only development annotation assignments. Team/human review and
substantive quality thresholds remain pending.


## Shared candidate review update (2026-11-15)

The [F-004 review report](member-c-f004-review.md) records checks against shared
commit `8282a739727f3c696be8b63d5c1c13ea13ae81fc`. Python 3.13.7 is now installed;
after earlier timeouts, the complete coordinated runner and its checker passed.
C-009 remains open. The proposal above is retained as historical context; frozen
v1.0.0 contracts govern current behavior.

## C-009 consumer review (2026-11-16)

**Owner:** C / Sara. **Review:** coding agent assisting C; human/team acceptance is
not implied. B recorded F-004 technical completion in commit `f4173b8` on
`member-b/task-f-004-web-workspace`, for the checked package `8282a739727f3c696be8b63d5c1c13ea13ae81fc`.
The latest fetched branch tip was `60b2b27986649e230f90723693c4e05b88e8891a`.
F-003 and generated v1.0.0 bindings were published in `aabbfc7844a8092194b4ab1cae561563e83ae13d`.
F-014 remains a separate prerequisite for C-002.

The service consumes `ClassificationRequest` and returns `ClassificationResult`
through the installed `notelens_contracts.v1` validators. `PreparedDocument` is
validated without changing its canonical text; results bind the incoming `doc_id`
and `text_sha256`. Error responses use `ErrorEnvelope` and request-ID correlation.
These are frozen contract boundaries; C has not changed the shared schema.

| State | Category | Scores and version in the synthetic mock |
| --- | --- | --- |
| Supported | One of the five categories | Five ordered finite decision scores; fixture model version. |
| Uncertain | Null | Five ordered finite decision scores; fixture model version. |
| Unsupported, skipped | Null | Empty scores and null score kind/model version; fixture scope policy. |
| Unsupported, performed | Null | Five ordered finite decision scores and fixture model version; fixture scope policy. |

The canonical categories are Cardiovascular / Pulmonary, Orthopedic,
Gastroenterology, Neurology and Urology, in that order. Probability scores are
bounded individually to [0,1]; signed decision scores have no probability meaning.
No probability-sum tolerance or clinical calibration is asserted. A confidence
note communicates limitations. Unsupported live scope detection remains unapproved;
fixture scope and model versions do not imply a real model or detector.

`services/classifier/tests/test_contract.py` verifies all four mock responses
against frozen fixtures and actual input identity, native non-finite rejection,
category ordering/uniqueness, invalid state-dependent category/model/score-kind
combinations, and probability endpoints/out-of-range values. The separate HTTP and
transport tests cover malformed input, safe errors, correlation and a real loopback
mock request. Python 3.13.7, uv 0.13.7, locked offline dependencies: **24 contract
tests passed**, **61 full classifier tests passed**, and installed bindings passed
**153/153 payload outcomes and 22/22 simulated exchanges**. Starlette deprecation
warnings were treated as errors. Full-suite coverage includes the transport smoke.

These are deterministic synthetic/mock checks, not a trained classifier, measured
accuracy, live language validation, OOD performance or clinical validation. No live
provider is required for C-009. No new shared contract change is requested from B.
The F-004 shared candidate receipt predates C's independently published test-client
dependency update and this C-009 work; it is not presented as a run of this working tree.

## Archived contract review evidence

- [Initial C response](../../docs/team/contract-reviews/p1/member-c-response-to-b.md)
- [C clarification response](../../contracts/candidates/p2-rc1/reviews/member-c-response-to-b-p2-clarifications.md)
- [C review and dependencies](../../contracts/candidates/p2-rc1/reviews/member-c-p2-review-and-next-dependencies.md)
- [C artifact review](../../contracts/candidates/p2-rc1/reviews/member-c-p2-rc1-artifact-review.md)
- [C revision 2 approval](../../contracts/candidates/p2-rc1/reviews/member-c-p2-rc1-revision-2-approval.md)
- [C revision 3 approval](../../docs/team/contract-reviews/p2-revision-3/member-c-approval.md)
