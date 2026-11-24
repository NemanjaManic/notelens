# D-to-C Handoff: Annotation and Evaluation Dependencies

- **Prepared:** 2026-11-11
- **Author:** Coding agent assisting D / Milica; human and team review pending
- **Basis:** C's supplied status report dated 2026-11-11, initial documentation
  commit `e7bc839c0632`, and D's [draft annotation guide](annotation-guide.md).

## Immediate conclusion

C's initial model training does not depend on D completing document annotations.
C reports C-001 completed locally, but says C-009 requires F-003/F-004 and C-002 also
requires the reviewed F-014 base. These are the current documented dependencies, not
proof of the state of unpublished work in B's or C's working copies. D cannot complete
C's foundation or contract-freeze tasks on B's behalf.

C-003 initial baseline training follows C-002; it does not depend on C-010 annotation.
C-010 follows D-003 assignments, and C-008's final-task gate includes C-010. C's own
task backlog remains the source for the full dependency and acceptance details.

D has prepared an annotation guide for review. The guide contains draft entity,
context, evidence, independent review, adjudication and matching instructions. Its
[practice examples](annotation-training-examples.json) contain 16 synthetic documents
and proposed labels for training and discussion. These are not real annotations or a
final benchmark. D's interface proposals for B are in [D's response](member-d-response-to-b.md).
The interface review was published on D's branch in commit `c496595`; the guide and
practice examples followed in `e468d2f`. Neither commit means the documents are in
`main`, approved by the team or a completed D-001 handoff.

## What C can review now

1. Read the entity and evidence rules in the guide, including how to distinguish a
   diagnosis, a symptom and a procedure and how negation, time and subject are handled.
2. Practice with the synthetic examples. First record an independent answer, then
   compare with the proposed labels and flag ambiguity to D. In particular, check
   family history, repeated mentions and the scope of negation. The examples contain
   the answer key and are not independent test or final-evaluation material.
3. Give D feedback on the proposed annotation format, primary/secondary review
   procedure and development-only allocation before actual assignments are frozen.
   Planned/cancelled procedure representation and unknown assertion remain open for
   D/B review; no contributor should force them into an unagreed API value.
4. Continue C's own permitted foundation review and data-split design while shared
   dependencies are pending. Actual C-009/C-002 work follows its recorded task gates;
   D's annotation guide does not claim to remove those gates.

## What C can expect from D

| When | D deliverable | Actual status / condition |
| --- | --- | --- |
| Now | D-001 draft annotation guide, synthetic practice examples and evidence/matching proposals. | Available on D's branch for human review; not team-approved, and no real reference annotations exist. |
| After C-002 and D-001 | D-002 selection from C's published manifests. | Pending actual stable group-disjoint manifests, source access and feasibility review. |
| After D-002 | D-003 frozen primary/reviewer assignment manifest. | Pending; target ten primary documents per member and at least ten independent second reviews across the team. |
| After D-003 | Clarification and separate adjudication of preserved submissions. | Pending actual assignments and submissions; D does not edit C's files. |
| After agreed interfaces and outputs exist | Shared classification evaluation/report integration. | A document-only synthetic runner is now implemented locally; C's classification adapter, real scores and agreed format remain pending. |

Before C selects a model, **both** C's primary and review assignments must use the
approved development portion. C must not receive final-reference content, decisions
or performance feedback for model selection. D and the team still need to decide a
practical final-set access procedure, especially because D develops the extractor.

## What D needs from C after C-002

Provide a reviewable handoff with:

1. Version/checksum and location of the source and frozen split manifests, actual
   duplicate grouping method, split seed and exact document ID/group ID/split mapping.
2. Target specialty labels, measured class/split counts and documented excluded
   conflicting-label groups. Report any split/class feasibility limits; do not copy
   preliminary C-001 counts as final split counts.
3. A way for authorized annotators to access each permitted canonical document and
   verify the canonicalization version and exact text SHA-256 without committing raw
   source content before provenance/redistribution review. Agree how C's dataset IDs
   map to per-submission API document IDs; do not assume they are interchangeable.
4. Clear development/final separation by document and duplicate group. D needs a
   feasible development allocation for C's primary **and review** work. If ten
   development documents cannot be assigned to C, report it before freezing.
5. Any source/license or access limitations affecting text, excerpts, IDs, annotation
   artifacts or redistribution. Do not send credentials or document bodies in chat.

D will then select a feasible approximately specialty-balanced set, freeze versions
and produce separate primary/reviewer allocations and exact paths. No IDs, counts,
reviewers or split proportions are invented in this handoff.

## Proposed classification evaluation exchange

The local D continuation implements a mock document-service/evaluation slice and
synthetic selection/template/adjudication tooling. See [integration](integration.md)
and [annotation tooling](annotation-tooling.md). This is not evidence that C's model,
real split manifests or shared classification benchmark exist; the proposal below
still needs C/B review.

This is an owned evaluation proposal for C/B review, not a new canonical API or an
implemented runner. It preserves C's control of classifier training and B's control
of `contracts/v1`.

- C supplies a versioned prediction artifact or adapter output for permitted
  development examples, with stable evaluation document IDs, manifest/split version,
  true-label reference version where permitted, predicted state/category, per-category
  scores and score kind, model/preprocessing/label-map versions, run configuration,
  and a clear mock versus actual-model label. Never include submitted user documents.
- D and C agree the join between the evaluation IDs and source/group manifests, and
  ensure exactly one intended record per evaluated example. Record missing/duplicate
  predictions, invalid labels, excluded groups and per-class support explicitly.
- Report majority and model baseline comparison, macro-F1, per-class precision,
  recall and F1, class support, confusion matrix and duplicate-group leakage evidence.
  Define how uncertain/unsupported outcomes enter denominators and the confusion
  matrix; report coverage and exclusions instead of silently dropping those outcomes.
- Fit all learned transformations on training data only. Use development data for
  model/threshold decisions. Do not disclose final-test results for tuning; freeze
  configuration and references before the documented final measurement.
- No numeric substantive threshold, probability-sum tolerance, classifier quality,
  endpoint readiness or team acceptance is claimed. The evaluation artifact format,
  treatment of missing predictions and state-specific scoring need C/D agreement.

## B-owned prerequisites C identified

F-008 prepares positive/negative contract fixtures and validators; F-003 records real
owner review and freezes the contract; F-009 generates reproducible bindings; F-004
creates the coordinated scaffold and F-011 health/readiness; the remaining foundation
chain leads to reviewed F-014 publication. C then performs its own C-009 and C-002 in
the documented order. Actual artifacts, checks and a shared foundation commit must be
reported by B; a draft guide or local illustration does not satisfy these gates.

C, A and D propose owner-created service scaffolds coordinated by B. This remains a
proposal until B and affected owners agree and record task responsibilities. No direct
edit of B's shared files, other owners' service files, commit, push or message is made
by this handoff. The final delivery date remains 2026-11-24.
