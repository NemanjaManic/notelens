# Annotation Assignment and Independent Review Workflow

**Owner:** D. **Status:** The user accepted the D-003 assignment and workflow proposal on 2026-11-20. The assignment manifest is frozen. Packet access is confirmed per member.

## Current D-003 proposal

The accepted assignment manifest uses C's source version `c002-d002-development-v1` and SHA-256 `e8596143168c2631eebb60ba080f996d0f9a13efa6d236ceae1de35eaa2769c6`. It contains 40 unique validation groups from the development portion, balanced at eight documents per specialty. A, B, C and D each have ten primary assignments. Ten additional assignments have a distinct secondary reviewer. Assignment IDs and workflow paths are frozen; every annotation/review template remains pending and none is a completed annotation.

See [the assignment manifest](../../eval/datasets/annotation-assignments.json), [pending coordinator templates](../../eval/datasets/annotation-submission-templates.pending.json), and [selection preflight](selection.md). The manifest has no canonical text, and all assignments say `access_state: pending_source_access`. Distribute assigned rows only after C and B/D provide the approved text-access path.

### Nemanja's development packet

D checked the frozen manifest for Nemanja and found ten primary assignments
and three independent reviews, all in development. Goran reported that Sara
verified all 13 canonical UTF-8 digests and that the packet's `assignments.json`
maps each file to its assignment ID, document ID and SHA-256. On 2026-11-21,
Nemanja confirmed that he could open the private packet, that all 13 canonical
UTF-8 text digests matched the frozen allocation, and that the assignment IDs,
document IDs and roles matched his reviewed submission. He also confirmed that
the packet contained zero primary label records for his three independent reviews.

On 2026-11-21, D received Nemanja's completed A-007 submission packet through
the user and verified all six listed file digests. The ten primary submissions
and three secondary reviews match the frozen allocation. All 13 carry an A
review attestation and `needs_clarification`, with 27 open questions. D checked
the internal span lengths and mention/evidence alignment for 271 mentions and
393 evidence spans. Nemanja's validation receipt records zero structural errors.
D received the complete private source packet and verified all 13 text hashes
against the frozen allocation. D checked all 271 mention spans and 393 evidence
spans against the canonical texts. All 27 open questions have source-grounded
proposals ready for human adjudication.

On 2026-11-22, Sara confirmed Milica's access to Nemanja's 13 canonical texts.
D reopened the local private packet and matched all 13 UTF-8 texts, document
IDs and SHA-256 digests to the frozen allocation. A fresh check of Nemanja's
already-received reviewed ZIP matched its archive digest and six listed file
digests. All 271 mention spans and 393 evidence spans matched the canonical
texts. Sara approved Nemanja's existing direct private chat with Milica for
any revised D-013 packet, with an updated submission manifest and SHA-256
checksums. Sara approved extending the one-to-one private chat route to the
whole team, and Milica relayed the team's confirmation. Each member sends
their reviewed package directly to Milica in a one-to-one private chat with
the submission manifest and SHA-256 checksums. Nemanja still needs to confirm
the approved retrieval location for the pinned passages packet.

The [D-013 intake receipt](../../eval/reports/development/d013-member-a-intake-v1.json)
identifies the four counterparts from C. D verified the updated drafts for 000,
003, 006 and 010 against the supplied canonical texts and compared them with A's
reviewed records. D also checked three C/D pairs for 002, 005 and 008. The C
handoff contains 11 drafts, 278 mentions, 307 evidence spans and 14 open questions.
D prepared feedback for C. Sara confirmed that she reviewed the full canonical
document for all 11 assignments and reported sharing her finalized C-010
package privately. She confirmed that the final manifest covers ten primary
annotations and one independent review and that all eleven record hashes
matched. Her final manifest SHA-256 is
`9d7e71d05cee8339d29b104be8117fc19ecc8ccb1417b9f62fad35ae113a6e48`.
D received the final ZIP through Milica, matched the manifest and all eleven
record hashes, and checked its assignment identities against the frozen D-003
allocation. All 305 mention spans and 335 evidence spans match the hashed
canonical texts. Structural validation found zero errors. The eleven records
include ten primary annotations and the secondary review for 010. Sara's
final records retain zero open questions. D prepared seven comparisons using
the final C records and the received A and D counterparts. The comparisons
remain pending human adjudication.

### Milica's development packet

On 2026-11-21, Sara supplied Milica's private development packet. D verified
the ten primary and three independent review assignments against the frozen
D-003 allocation and the pinned C-002 manifest. All 13 UTF-8 files matched
their canonical SHA-256 values and `nfc-lf-v1`. The packet contained the
assigned texts and metadata. Independent review label files were absent.
Separate local draft forms are ready for Milica's review and submission.
The [verification receipt](../../eval/reports/development/d012-member-d-packet-verification-v1.json)
records the checks and counts. The frozen assignment manifest preserves the
original allocation checkpoint.

### Goran's development packet

D verified Goran's ten frozen primary assignments, 020 through 029, and three
independent reviews, 001, 004 and 007. Goran's allocation CSV contains the role,
assignment ID, document ID and canonical SHA-256 for each of these 13 rows.
Goran reported that all 13 canonical hashes in his ZIP matched the frozen
allocation. Sara confirmed that the ZIP is Goran's authorized frozen D-003
packet and that she sent the access instructions directly to him. She will
hold the primary labels for 001, 004 and 007 until Goran submits those
independent reviews. The B-011 access handoff is confirmed and annotation
submissions remain pending.

## Per-assignment procedure

1. Give an annotator access only to their assigned canonical row through the approved source route. Verify the stable C `doc_id`, `group_id`, `nfc-lf-v1` canonicalization and exact UTF-8 text SHA-256 before annotation. Never put the canonical text in the shared repository or assignment manifest.
2. The primary annotator records every in-scope diagnosis, symptom and procedure using D's current guide, exact code-point spans and evidence. Preserve unresolved questions instead of guessing.
3. Store the primary submission only in that annotator's owned directory. Use an immutable unique `submission_id`; do not overwrite or edit another member's file.
4. The assigned secondary reviewer receives the same canonical row and assignment identity, but not the primary labels until their independent record is complete. Save the secondary review separately in the reviewer's owned directory.
5. D runs structural lint and comparison after both submissions are preserved. A lint pass checks structure and workflow only; it does not certify completeness or correctness.
6. Preserve disagreements. D-013 records a separate human adjudication decision with source-record hashes, named adjudicator and rationale. The merge tool never chooses a winner automatically.

## File ownership and proposed paths

Each member owns their own annotation directory. The proposed files are:

| Member | Assignment path | Primary submissions | Independent reviews |
| --- | --- | --- | --- |
| A | `eval/annotations/member-a/submission-manifest.json` | `eval/annotations/member-a/primary.jsonl` | `eval/annotations/member-a/secondary.jsonl` |
| B | `eval/annotations/member-b/submission-manifest.json` | `eval/annotations/member-b/primary.jsonl` | `eval/annotations/member-b/secondary.jsonl` |
| C | `eval/annotations/member-c/submission-manifest.json` | `eval/annotations/member-c/primary.jsonl` | `eval/annotations/member-c/secondary.jsonl` |
| D | `eval/annotations/member-d/submission-manifest.json` | `eval/annotations/member-d/primary.jsonl` | `eval/annotations/member-d/secondary.jsonl` |

The user accepted these path conventions. D changes only D's member directory and the shared D-owned assignment manifest. Each member creates or approves files in their own path. Do not copy all pending templates to every member directory.

## Split, reviewer and access rules

- All 40 selected rows are from C's validation split, treated as development. No final/test rows were present or selected.
- C's primary and secondary assignments must remain development-only. The current proposal satisfies this condition.
- Primary and secondary roles are distinct. A member never reviews their own primary record.
- Annotators and reviewers receive assigned rows only, through the access method C approves. The supplied manifest contains hashes and metadata but does not itself provide canonical text access.
- If C reports an exposed duplicate component or changed split after selection, pause affected assignments, keep the full duplicate component in development, and record the changed source version before continuing.
- Assignment IDs, reviewer allocation and path conventions are frozen by the user's acceptance. Actual row delivery still requires the source-access route. The assignment manifest does not record that A, B or C have received or accepted their rows.

## D-012 boundary

D-012 is complete when Milica's ten primary annotations and three assigned
independent reviews are delivered through the approved private route. The
submission folder has separate `primary` and `reviews` subfolders and a root
`submission-manifest.json`. Nemanja confirmed receipt and verification on
2026-11-22. Goran confirmed readability and the listed hashes. Sara also
confirmed receipt, readability and verified checksums. D recorded
[completion](../../eval/reports/development/d012-private-submission-receipt-v1.json).
The source-gap question on 005 remains under D-013.

Independent reviews by other members of selected D primary annotations contribute
to D-013's team-wide minimum of ten independent reviews. Milica reported that the
team confirmed Goran for 034, Sara for 036 and Nemanja for 038. The individual
private handoffs contain each assigned canonical text and its metadata. Hold the
primary labels until each reviewer returns their independent record.

On 2026-11-22, Sara returned her reviewed 036 submission v2. D verified its
canonical spans and its link to the superseded v1 record. The v2 clarification
retains separate planned counseling and consult mentions and a hypothetical
primary-care referral. The paired comparison is ready for D-013 adjudication.

Nemanja returned his reviewed 038 submission v2 and confirmed prior exposure
to the primary labels. D verified all ten package checksums, the frozen
assignment and canonical text, and the exact spans of all 24 secondary mentions
and 24 evidence citations. D paired it with Milica's submitted primary record
and queued its four open questions for human adjudication. It is a non-blinded
secondary review with zero credit toward the ten-review independent minimum.
Nemanja reconfirmed that v2 was submitted. Assignment 038 has no outstanding
submission request for him. D prepared proposed decisions for all four
questions in the private adjudication workspace with exact source anchors.
If the team needs a replacement to reach that minimum, arrange a reviewer
without prior label exposure for 038 or another eligible assignment through
the approved private workflow.
