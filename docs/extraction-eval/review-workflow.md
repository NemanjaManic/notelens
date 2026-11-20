# Annotation Assignment and Independent Review Workflow

**Owner:** D. **Status:** The user accepted the D-003 assignment and workflow proposal on 2026-11-20. The assignment manifest is frozen. Row-level distribution awaits the approved canonical-text access route.

## Current D-003 proposal

The accepted assignment manifest uses C's source version `c002-d002-development-v1` and SHA-256 `e8596143168c2631eebb60ba080f996d0f9a13efa6d236ceae1de35eaa2769c6`. It contains 40 unique validation groups from the development portion, balanced at eight documents per specialty. A, B, C and D each have ten primary assignments. Ten additional assignments have a distinct secondary reviewer. Assignment IDs and workflow paths are frozen; every annotation/review template remains pending and none is a completed annotation.

See [the assignment manifest](../../eval/datasets/annotation-assignments.json), [pending coordinator templates](../../eval/datasets/annotation-submission-templates.pending.json), and [selection preflight](selection.md). The manifest has no canonical text, and all assignments say `access_state: pending_source_access`. Distribute assigned rows only after C and B/D provide the approved text-access path.

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

D's primary annotation and independent review are separate submissions. D cannot serve as the independent reviewer of D's own primary work. Complete D-012 only after D's assigned canonical rows are accessible, D's primary submissions are actually made, and separate human reviewers have submitted their reviews. No labels or review records are inferred from the manifest metadata.
