# C-002 and C-010 coordination for D

**From:** Sara / C

**Date:** 2026-11-19

Hi D,

C's draft has 860 training, 185 validation and 183 draft test documents,
plus 101 unassigned documents. Three potential duplicate pairs remain
quarantined. The local ledger tracks all 1,045 groups already used for
development. The split and canonical text mapping still need review
before they can serve as assignment inputs.

Could you confirm the information D needs from the reviewed C-002 handoff?
I expect the minimum to be the split and preparation versions, a stable
dataset document ID and duplicate group ID, the split designation, the
exact prepared-text digest, and a reference to the authorized local
document. Please flag any missing field or access constraint.

For D-003, please allocate both my primary annotation assignments and
my independent review assignments from development groups only. Keep
the two sets of records separate. Please also confirm how you want
substantive review exposure recorded and how changes to a duplicate
component should be communicated before assignments are finalized.

I will record pair review exposure before opening text, preserve the
entire exposed duplicate component in development and flag any conflict
with the proposed test partition. I will provide the reviewed metadata
through the agreed access path once C-002 is ready. Until then the
draft counts are for planning, and C-010 assignments remain pending.

Thanks,

Sara / C

## D's confirmation, 2026-11-19

D confirmed the requested handoff fields and the additions below.
Assignment selection can start once the manifest and access are
confirmed.

| Item | Agreed requirement |
| --- | --- |
| Candidate record | Dataset document ID, duplicate group ID, split, specialty label, annotation permission, canonical preparation version, prepared-text SHA-256 and authorized local reference. |
| Manifest | Frozen manifest version and checksum, with the applicable access, retention and redistribution limits. |
| Submission identity | Follow the [identity convention confirmed on 2026-11-20](#assignment-identifiers-and-access-2026-11-20). |
| C's assignments | Primary and independent review assignments use approved development groups only. The two sets stay separate and C reviews work C did not annotate. |
| Exposure | Reserve access before opening text. Record the reviewer, actual access time, document and group IDs, split version and scope of review. Keep every exposed duplicate component in development and flag proposed test overlap. |
| Group changes | Before assignments are frozen, send D the old and new group IDs, affected documents and splits, and the reason for any merge or split. |

The [local review workflow](splits.md#prepare-review-records-after-access-is-approved)
now records reservations and actual access separately. Its preview
reports old and proposed new group IDs for confirmed merges. If a
regrouping splits a component, include its old-to-new membership
mapping in the same review before D freezes assignments.

The approved access path and retention and redistribution conditions
are still open. B confirmed the
`nfc-lf-v1` preparation rules. The dataset preparation entry point,
authorized local copy, named reviewers and restricted mapping
location are still pending. The frozen manifest and D-003 assignments
remain pending. [B's confirmation](c002-handoff-to-b.md#bs-confirmation-2026-11-19)

## D-002 intake request, 2026-11-19

D requested the reviewed, frozen C-002 manifest and confirmation of the
authorized route for canonical document access before starting D-002
selection. Include the manifest version and checksum and the agreed
candidate fields. Each eligible record needs explicit annotation
permission. Flag quarantined groups and access restrictions for D's
selection. Deliver the reviewed records through the agreed restricted
location once B and D confirm access and the mapping.

GitHub confirmed the D reconciliation branch
`member-d/reconcile-main-2026-11-19` at
`90fc3e26a2f851bc5c8eb61843434cfb50bca318`. This is a D code contribution
available for B's coordinated verification. The current published
`main` at `1ac8bfe` still records F-014 as pending. C-002 review, freeze
and D-002 data intake remain pending.

## Assignment identifiers and access, 2026-11-20

D confirmed that the stable `doc_id` is the C-002 dataset document
ID. A primary submission and its independent review share that
`doc_id`, the D-issued `assignment_id` and the canonical text SHA-256.
Each submission has its own unique `submission_id`. D issues
assignment IDs when assignments are frozen. Mapping to B's runtime
document IDs can be handled separately.

D needs the complete evaluation mapping for selection and adjudication.
Annotators and reviewers receive their assigned rows only. C's primary
and independent review access is limited to approved development groups.
Once C-002 is frozen and the restricted location and access are
confirmed, place the versioned manifest and checksum there and
provide D the access-controlled link. Keep local identifiers and
review artifacts outside Git and chat.

## Published selector and evaluator update, 2026-11-20

The published D reconciliation branch advanced to `97bf35a`. Its
history contains the evaluator update `76290e1` for D-010 and the
development-only independent review reservation at `97bf35a` for D-002.
D reports 65 evaluator tests, all five mock HTTP routes and three
Promptfoo scenarios passing. The selector reports insufficient
development capacity before assignment freeze.

At this D commit the candidate fields are `doc_id`, `group_id`,
`specialty`, `split`, `text_sha256` and an explicit boolean
`permitted_for_annotation`. Eligible split values in the selector
are `validation` and `test`. For C's development-only work the selector
must reserve from approved development groups. The tool also rejects
an exact canonical digest that appears under different group IDs.
These checks guide the reviewed handoff. The actual D-002 and D-003
task items remain open until the approved C-002 manifest and access
are available. F-014 remains open at verified `main` `1ac8bfe`.

## C-002 preparation and review scope, 2026-11-20

B approved Sara as the sole reviewer of the three quarantined pairs.
The reports and source-row mapping stay in Sara's local checkout.
D can receive only permitted handoff metadata through the agreed
access path. Where D already has authorized access to benchmark text,
verify its SHA-256 against the handoff and use that exact canonical
text with the frozen code-point offset convention.

The C-owned entry point is
`data/mtsamples/prepare_transcription.py::prepare_transcription`
and implements `nfc-lf-v1`. The [B review record](c002-handoff-to-b.md#review-authorization-and-preparation-entry-point-2026-11-20)
describes the scope and the pinned F-012 checks. The three pair
decisions, reviewed frozen manifest and final access handoff remain
pending. Final-test access remains restricted.

## Published foundation baseline, 2026-11-20

F-014 is complete at tag `f-014-foundation`
(`7eb12e56f33240a428f916ba583b9e00077712df`).

## Local split freeze, 2026-11-20

Sara signed off on the assisted review. One pair remains quarantined,
and two merged components are in training. Local split version
`c002-split-v1` contains 864 training, 185 validation and 183 test
documents. The original test membership is preserved.

The local manifests record group and split membership.

## Development metadata package, 2026-11-20

Sara confirmed development annotation permission. The locally prepared
`c002-d002-development-v1` package contains 185 frozen validation
candidates, their canonical SHA-256 digests, annotation permission,
two development group changes and the quarantine flag. The checksum
sidecar covers the exact manifest bytes. The package contains only
permitted metadata. D verifies canonical digests against the benchmark
copy D is authorized to access.

A local trial with D's selector at `97bf35a` produced a 40-document
development-only proposal and reserved an independent review for C.
The trial saved no assignments.

On 2026-11-20 Sara reported that Milica received the validation manifest
and checksum through the restricted handoff folder. Final-test access
remains restricted. D manages the actual assignment selection.
