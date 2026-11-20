# Annotation Sample Selection Readiness

**Owner:** D. **Status:** preparation checklist only. Actual D-002 selection is blocked
until C publishes the permitted C-002 canonical document/group/split manifest and the
team confirms source access. No real document IDs or assignments are recorded here.

The selector and its synthetic demonstration are documented in
[annotation tooling](annotation-tooling.md). This page records the handoff checks required
before running it on a real source manifest.

## C-002 handoff preflight

Do not run actual selection until each item below is resolved against C's published
manifest and the team's access decision:

- [ ] C identifies the exact manifest version and provides canonical `doc_id`,
  `group_id`, specialty, validation/test split, canonical text digest and permission
  status for each candidate.
- [ ] C and D agree how those source fields map into the selector's provisional input;
  the adapter is not a replacement for C's published split format.
- [ ] B/D confirm how permitted canonical text is accessed and how dataset IDs map to
  submission IDs. Redistribution and retention permissions are explicit.
- [ ] The selector's existing checks pass for unique IDs, group/split separation,
  duplicate hashes, consistent group specialty, permission flags and requested counts.
- [ ] D reviews the proposed approximately 40-document balance, keeps dev/final groups
  disjoint, aligns validation/test with C where feasible, and reports infeasible targets
  instead of silently changing them.
- [ ] C's pre-selection primary and review material stays development-only. The team
  decides final-set access before assignment freeze.
- [ ] The selection seed, source-manifest version/digest, exact selected IDs, split
  counts and unresolved exceptions are recorded before D-003 assignments are published.

Until the required source, permission and split inputs exist, these are readiness checks
only. They do not constitute selection, access approval or assignment.
