# Annotation Sample Selection Readiness

**Owner:** D. **Status:** The user accepted and froze the D-002 selection on 2026-11-20. Distribution remains pending the approved canonical-text access route.

## C-002 source and preflight

The restricted handoff declares source version `c002-d002-development-v1`, canonicalization `nfc-lf-v1`, kind `permitted_benchmark`, and annotation permission for each manifest row. The manifest SHA-256 is `e8596143168c2631eebb60ba080f996d0f9a13efa6d236ceae1de35eaa2769c6`; it matches the separately supplied checksum.

D's read-only preflight reported 185 unique groups, all in C's `validation` split, with no structural or capacity issues for 40 selected groups and ten secondary reviews. The selector produced a deterministic selection using seed `20261120`: 40 development groups, eight from each of the five specialties, ten primary assignments per member and ten separate reviewer assignments. No test/final documents were present in this manifest. Following user acceptance, the output status is `frozen_pending_source_access`, `human_reviewed: false`, and `access_state: pending_source_access` for all assignments.

The frozen manifest and pending templates are [the assignment manifest](../../eval/datasets/annotation-assignments.json) and [the coordinator-held templates](../../eval/datasets/annotation-submission-templates.pending.json). The user accepted the selection proposal. These contain IDs, group IDs, specialties and hashes, not canonical document text. Do not distribute rows until the approved access route is confirmed. The handoff folder contained no canonical text files, and the manifest has no embedded `canonical_text`.

## Remaining checks before D-002 freeze and D-003 release

- [x] Verify the supplied manifest bytes against the SHA-256 and source version.
- [x] Validate candidate IDs, duplicate groups, split labels, specialties, permissions and requested allocation capacity with D's preflight.
- [x] Generate and retain the seeded, development-only 40-group proposal and its separate pending templates.
- [ ] C and B/D provide the approved route for annotators to retrieve only their assigned canonical rows and verify each `text_sha256` under `nfc-lf-v1`.
- [x] Freeze the selected development groups and assignment seed after the user's acceptance; no test/final rows were selected.
- [x] User accepted the specialty balance, reviewer allocation and workflow proposal on 2026-11-20.

The candidate selection is frozen. Annotator distribution and source-text review remain pending the approved access route. This does not constitute completed annotation or independent review.
