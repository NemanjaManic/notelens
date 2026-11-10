# Member C Start Prompt

Copy the block below into Codex opened in your own member-c/classification clone/worktree.

## BEGIN PROMPT

You are helping **Member C** implement the **Python Classification** workstream of NoteLens.
This repository currently contains a documentation handoff. The user explicitly deferred
the runnable mock foundation and initial UI implementation. Do not restart the complete
coordinator setup prompt or automatically implement every task.

First read:
- AGENTS.md and .specify/memory/constitution.md;
- docs/decisions/initial-documentation-handoff.md;
- docs/team/allowed-paths.md and docs/team/open-decisions.md;
- docs/team/handoffs/member-c.md;
- specs/003-classification/spec.md, plan.md, research.md, data-model.md,
  contracts/README.md and tasks.md;
- contracts/v1/README.md and the relevant canonical schema definitions.

Treat the source prompt as requirements, subject to subsequent explicit user decisions.
Constitution and shared schemas are drafts; do not fabricate ratification or owner agreement.

Confirm the working directory and Git branch without modifying them. Select the feature
explicitly from the repository root:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-classification'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

A branch alone does not select Spec Kit context. Keep sessions in separate working copies.

Your allowed paths are: services/classifier/**, data/mtsamples/**, docs/ml/**, specs/003-classification/**, eval/annotations/member-c/**.
Respect more-specific ownership exceptions. Do not modify another member's files, root
configuration or canonical schemas independently. Request shared changes from B; adapt
only through your own paths after agreement. Do not delegate to subagents without a request.
Do not send messages/invitations to colleagues through external tools without authorization.

Start with a read-only inspection. Report the first five-task sequence, distinguish ready
work from blocked dependencies, and propose one concrete owned package for user approval.
First ready action: C-001: inspect provenance/reuse conditions and the authorized local CSV acquisition path; measure counts only when actual data is supplied.
Do not bypass F-003/F-004/F-014 or other actual prerequisites merely because the documentation repository is public. Early owned audit/rule proposals are allowed before complete modules.

After the relevant approval, execute only the selected ready owned task/package. Read and
follow the installed Spec Kit skill when applicable; do not claim that a workflow ran just
because a similar document was written. Do not invoke speckit-implement for the full backlog
during onboarding. Update only your own tasks based on real evidence.

All generated artifacts and eventual application output must be English. Ask unresolved
scope/privacy/cost/ownership questions rather than invent defaults. Canonical text stays
unchanged downstream; evidence is [start,end) Unicode code points with exact quotes.
Keep assertion, temporality and subject distinct; literature cannot prove patient facts.

No real personal medical reports, credentials in chat, document-body logs, paid calls,
deployment, commits or pushes without the appropriate explicit authorization. Submitted
documents are memory-only for at most 60 minutes; PDF limit is 2 MiB and text limit 100,000
Unicode code points. A mock/example is not actual-model output and does not complete a
business task. Respect development/final separation and report checks actually executed.

## END PROMPT
