# Documentation Handoff Checkpoint

**Date**: 2026-11-10. **Scope**: documentation/task sharing only.
**Authority**: [explicit user scope decision](../decisions/initial-documentation-handoff.md).

## Contents

README, original prompt, pinned Spec Kit integration, constitution draft, five specifications,
five plans/backlogs, shared draft schemas, owner guidance and four handoff/start-prompt pairs.
The original prompt is not rewritten. Shared schemas remain draft and reviewer acceptance
is not invented. Full runnable-foundation tasks remain open.

The first root commit of origin/main is this initial documentation base:
`git rev-list --max-parents=0 origin/main`. Member branches start there as documented in
[working copies](working-copies.md). The actual commit SHA is obtained from Git after the
commit exists, never fabricated in advance.

## Publication conditions

Publication completes only when the actual authorized commit/push succeeds and GitHub's
main SHA matches the local commit. If push fails, report that limitation and preserve local
work. Do not claim the remote is ready merely because these instructions are written.

## Validation scope

Check Markdown links, member paths/feature commands, declared task references, schema/OAS
structure, unchanged prompt and official assets, and staged-file secrets/unwanted local state.
Validate a fresh checkout after publication, including PowerShell and Git Bash feature
selection. These checks do not test an application: no runtime exists in this release.

## Explicitly deferred

No UI, mock services/startup, generated bindings, trained models, corpus acquisition,
real extraction/generation, shared runtime smoke, benchmark or deployment is included.
No actual service-start command exists yet. Later foundation completion needs the original
checks and a separate base; this document does not close F-003/F-004/F-005/F-006/F-007/F-014.
