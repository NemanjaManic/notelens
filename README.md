# NoteLens

SITA AI Bootcamp capstone for understanding English medical reports with traceable evidence.
Final delivery: **November 24, 2026**.

## Current state

This is the initial **documentation and team handoff** release. It includes Spec Kit
integration, specifications, plans, separate task backlogs and draft interface contracts.
There is no runnable web application, mock service, trained model or live AI integration yet.
The user explicitly [deferred the runnable mock foundation](docs/decisions/initial-documentation-handoff.md).

The product is an educational demonstration, does not replace a doctor, and must not accept
real personal medical reports. The planned inputs are English public/synthetic text,
text-based PDFs and built-in public examples. All application artifacts/output must be English.

## Start here

1. Read [the handoff decision](docs/decisions/initial-documentation-handoff.md) and
   [root agent rules](AGENTS.md).
2. Follow [Windows working-copy instructions](docs/team/working-copies.md). Each person
   uses their own clone or worktree and branch; a Git branch alone does not select a feature.
3. Open your own working copy in Codex and use only your member's English start prompt.
4. Review your feature's spec/plan/tasks, identify ready work and approve a concrete package
   before changes. Frozen contracts and the runnable foundation still gate business integration.

| Member | Workstream | Feature | Handoff | Start prompt |
| --- | --- | --- | --- | --- |
| A | Python RAG | [001-rag](specs/001-rag/tasks.md) | [Guide](docs/team/handoffs/member-a.md) | [Prompt](docs/team/start-prompts/member-a.md) |
| B | Frontend and Integration | [002-platform](specs/002-platform/tasks.md) | [Guide](docs/team/handoffs/member-b.md) | [Prompt](docs/team/start-prompts/member-b.md) |
| C | Python Classification | [003-classification](specs/003-classification/tasks.md) | [Guide](docs/team/handoffs/member-c.md) | [Prompt](docs/team/start-prompts/member-c.md) |
| D | Extraction and Evaluation | [004-extraction-evaluation](specs/004-extraction-evaluation/tasks.md) | [Guide](docs/team/handoffs/member-d.md) | [Prompt](docs/team/start-prompts/member-d.md) |

Member A creates/owns the GitHub repository. Member B still owns the entire frontend,
shared contracts, integration, infrastructure and security. No colleague identities are invented.
The user will send collaborator invitations.

## Shared documents

- [Original requirements prompt](prompts/NoteLens_Codex_SpecKit_prompt_00.md), preserved unchanged.
- [Constitution draft](.specify/memory/constitution.md), pending ratification.
- [Ownership matrix](docs/team/allowed-paths.md).
- [Foundation backlog](specs/000-foundation/tasks.md).
- [Draft contracts](contracts/v1/README.md), not frozen.
- [Open decisions](docs/team/open-decisions.md).
- [Preparation record](docs/team/preparation-status.md) and [planning record](docs/team/planning-status.md).
- [Documentation checkpoint](docs/team/documentation-checkpoint.md).

## What can start now

A can inspect permitted knowledge sources; C can audit data provenance/acquisition;
D can draft annotation/evidence rules; B can review shared interfaces and coordinate feedback.
The handoffs show the first five-task sequence and explicitly label blocked implementation
work. Those sequences are not claims that five business tasks per member are ready today.

There are no npm scripts, service startup commands or runtime smoke tests available yet.
Do not run future test commands from tasks.md before their prerequisite creates the files
and dependencies. Do not call speckit-implement for the entire backlog during onboarding.

## Privacy and limits already approved

Submitted documents may be kept only in application server memory for at most 60 minutes,
deleted on expiry/restart. PDFs are limited to 2 MiB (2,097,152 bytes); canonical text to
100,000 Unicode code points. Reject oversized input rather than truncating it.
Built-in public examples may remain versioned. These are requirements, not implemented checks.

## Tooling

The repo-local Codex skills and PowerShell scripts come from verified Spec Kit **1.3.3**.
They are committed so each clone gets the same workflow. Do not rerun specify init over them.
Use the pinned entry point when the CLI is needed:

```powershell
uv --system-certs tool run --from 'git+https://github.com/github/spec-kit.git@v1.3.3' specify version
```

Git, Codex and PowerShell are needed for onboarding; uv/Python are needed when running the
pinned CLI or later Python checks. Package installation, real provider setup and deployment
remain separately approved tasks. No API key is needed to read/validate the feature context.

## Contribution boundaries

Change owned paths only; propose shared changes to B. Keep separate service dependencies/
locks and avoid repository-wide formatting. Ownership currently relies on the documented
process; CI scope enforcement, populated CODEOWNERS and branch protection are future work.
No project code license has been selected.
