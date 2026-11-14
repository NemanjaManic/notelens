# Contract Freeze: NoteLens v1.0.0

**Recorded:** 2026-11-13. **Coordinator:** B.
**Accepted proposal:** p2-rc1 revision 3, wire version 1.0.0, commit
`92626f5d037425f74eb65cadf1294a4d8bbfac35`, manifest SHA256
`1848e81898c5a98235b49c2e0ad854a777ff3e6afe7bf9517e29c5de8b1ac8bc`.

## Approved bytes and promotion

The user explicitly confirmed human approval by Nemanja (A), Sara (C) and Milica (D)
after providing the completed D review. [Recorded confirmation](../team/contract-reviews/p2-revision-3/user-owner-confirmation.md)
distinguishes human consent from agent checks. The canonical schema/API are promoted
to contracts/v1. Promotion changes only the schema identifier/title/comment and API
title/description to canonical labels; all approved definitions, operations, response
shapes and fixture payloads are preserved. The initial unfrozen P1 proposal is retained
under contracts/history/p1. The exact reviewed candidate stays under contracts/candidates
and at its immutable Git commit. Historical candidate-building commands must be run in
that pinned checkout; they are not the canonical regeneration workflow after promotion.

contracts/v1/freeze.json binds the canonical schema, API and complete fixture bundle to
the dated A/B/C/D decisions below. Changes to shapes/behavior require a new proposal,
affected-owner agreement, generation and compatibility checks; generated outputs are
never a second handwritten schema. This record does not claim semantic medical validity.

## Member A

**Decision:** approved. **Owner:** Nemanja. **Date:** 2026-11-13.
The user explicitly reports Nemanja's human approval of the exact proposal above.
A's preceding agent review found no remaining blocker: completed retrieval provenance
is independent of generation; insufficient retrieval and partial document answers retain
truthful versions/modes; clarification/failures fabricate no search history; generation
requires sufficient retrieval with matching versions. Provider/model/budget/operational
and live language/ambiguity choices remain activation gates.

## Member B

**Decision:** approved. **Owner:** B, the coordinating user. **Date:** 2026-11-13.
The user's approved contract-resolution and freeze/binding plan, followed by the explicit
all-owner confirmation, authorizes this canonical promotion. B retains shared schema,
frontend/integration, generated bindings and root/startup ownership. The approved wire
version and all data fields stay as reviewed; mechanical canonical labels are documented.

## Member C

**Decision:** approved. **Owner:** Sara. **Date:** 2026-11-13.
C's [human approval file](../team/contract-reviews/p2-revision-3/member-c-approval.md)
accepts the exact revision-3 commit/hash for its interfaces and shared behavior; the user
also explicitly confirms Sara's approval. Classification/scope/score metadata, finite
numbers, language boundary, request IDs, health authentication and C's scaffold ownership
remain as accepted. Its reported comparison checks are not a new B-side test run.

## Member D

**Decision:** approved. **Owner:** Milica. **Date:** 2026-11-13.
The user explicitly reports Milica's human approval. The completed D agent review
reported all 41 files verified and no blocking change in extraction, summaries, document
answers, evidence or mixed provenance. D accepts the fixture-only development boundary,
with real input-language evaluation before B-001 and real ambiguity handling before B-003.
The agent's separate lack of authority to approve does not override the supplied later
human confirmation; neither is treated as independent clinical validation.

## Remaining activation and implementation gates

No detector, substantive metric threshold, provider/model, spending cap, timeout/retry/
history/rate setting, paid call, deployment or automatic history expansion is selected.
F-009 must prove reproducible generation and Python/TypeScript fixture compatibility.
F-004 service contributions remain owner-built. F-014 still needs the runnable checked
mock foundation, acceptance/handoffs and separate publication authorization. This contract
freeze is not the runtime-foundation checkpoint or a service migration.
