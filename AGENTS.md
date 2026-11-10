# NoteLens Agent Instructions

## Authority and scope

Read `prompts/NoteLens_Codex_SpecKit_prompt_00.md` for relevant project requirements and
`.specify/memory/constitution.md` for project principles. Subsequent explicit user decisions
take precedence. Source-plan precedence is confirmed prompt decisions, prompt technical
corrections, improvement proposal, then original plan. Source PDFs are absent; do not claim
to have read them. Keep the supplied prompt unchanged unless the user explicitly requests
a correction.

This repository is a four-person SITA AI Bootcamp capstone. Member A creates the GitHub
repository; B still owns the complete frontend and shared integration. Use A/B/C/D except
where the user has supplied identities. Never invent collaborators or GitHub handles.

Current preparation is documentation only. The user approved sharing this documentation
base and explicitly deferred runnable mocks/UI on 2026-11-10; read
[the handoff decision](docs/decisions/initial-documentation-handoff.md).
A generated spec or guide does not complete implementation. The runnable foundation
checkpoint has not been reached. From this documentation handoff onward, enforce
[the allowed-path matrix](docs/team/allowed-paths.md). New unlisted shared root files need
ownership review by B, not a self-assigned owner.

The current coordinator approval covers README/handoffs/working-copy instructions and the
initial documentation commit/push. It is not a standing cross-owner implementation grant.
Each member can begin owned inspection/proposals in a separate branch, but must preserve
actual task dependencies. Do not invoke the full original setup/implementation prompt.

## Approvals and reporting

- Obtain explicit user approval before a new change package. Do not ask again for work
  already covered by that approval. If unclear whether a proposed action is covered, ask.
- Ask unresolved functionality, privacy, cost, or ownership questions. Do not invent
  defaults, experimental results, reviewer acceptance, capacity, or budgets.
- Work on independent approved parts while an answer is pending.
- Do not commit, push, publish, deploy, activate paid calls, add paid services, or send
  collaborator invitations without explicit authorization for that action.
- Do not delegate to subagents unless the user explicitly requests delegation.
- Report actual commands/checks and their limitations. Distinguish agent review from
  human/team approval, mock checks from module checks, and offline checks from live checks.

## Language and product boundaries

All application surfaces and project artifacts MUST be English, including generated
answers, summaries, errors, notices, documentation, identifiers, and comments. Chat with
the user may remain Serbian. Support English public/synthetic medical text and text-based
PDFs; do not silently translate unsupported input. Display demo/not-a-doctor/no-real-personal-
reports notices.

No OCR, speech, translation, LLM/NER model training, new diagnosis generation, treatment
recommendations, user accounts, complex agent frameworks, or credentialed clinical datasets
are approved for the MVP. ICD is optional and may only copy codes explicitly in the source.
Final delivery is **2026-11-24**. Do not silently move the deadline.

## Ownership and architecture

A: Python RAG, knowledge corpus, retrieval, literature answers.
B: complete TypeScript frontend/integration, canonical document preparation, shared
contracts, infrastructure, deployment, security, root configuration and global Spec Kit files.
C: Python classification, MTSamples cleaning and split/model manifests.
D: Python extraction/summarization/document answers, annotation coordination, shared evaluation.

Each Python service has its own dependencies and lockfile. B owns root package/workspace
configuration and shared lockfiles. D may own a local evaluation package manifest.
Never run repository-wide formatting that changes another owner's files.
Member-specific annotation paths override D's parent ownership; annotators never edit
each other's primary or review files.

All ingestion, chunking, embedding calls, vector-store access, retrieval and literature
answer generation remain in A's Python service. D handles document-grounded generation.
B uses thin service clients and preserves claim provenance for mixed responses.

## Spec Kit workflow

The project integration is pinned to **Spec Kit 1.3.3** with Codex skills. On the preparation
machine the bare global `specify` reported 1.0.13; other members' installs are not assumed.
Use the verified, pinned entry point:

```powershell
uv --system-certs tool run --from 'git+https://github.com/github/spec-kit.git@v1.3.3' specify version
```

Run installed skills as agent workflows, not shell executables. Read each relevant
`.agents/skills/speckit-*/SKILL.md`, follow its instructions and official resolver scripts,
and report the actual workflow used. Resolve templates at execution time; never substitute
a similar handwritten document for an executed workflow.

One constitution precedes separate feature specifications and later plans/tasks.
Only one feature is processed per `speckit-specify` invocation. Use exact feature paths:

| Member | Feature |
| --- | --- |
| Shared foundation, coordinated by B | `specs/000-foundation` |
| A | `specs/001-rag` |
| B | `specs/002-platform` |
| C | `specs/003-classification` |
| D | `specs/004-extraction-evaluation` |

A Git branch does not choose the feature. After feature creation, select existing feature
context explicitly in each separate working copy. Example for A, from the repository root:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/001-rag
export SPECIFY_FEATURE_NO_PERSIST=1
```

All four members confirmed Windows. PowerShell is the primary documented path; Git Bash
calls the committed PowerShell scripts through powershell.exe. See the exact
[working-copy commands](docs/team/working-copies.md) and member-specific handoffs.
No Bash variants of Spec Kit scripts or Linux/macOS support are claimed.
The specify workflow records its selected feature in ignored,
per-checkout `.specify/feature.json`; feature creation and later read-only selection are
different operations. Never run four active sessions in one checkout.

Keep standard task IDs/checkboxes and stable F/A/B/C/D aliases in future backlogs.
Specs do not replace plans, tasks, contracts, tests or handoffs. Never invent npm scripts
or report the foundation checkpoint before a runnable, checked mock foundation exists.

## Evidence, data and verification

Canonical text is prepared once and never altered downstream. Evidence uses half-open
Unicode code-point offsets [start, end), with exact canonical quotes. Explicitly convert
browser UTF-16 indices; cover non-BMP characters and repeated text. Assertion, temporality
and subject are separate. Literature cannot prove a patient-specific condition.

Use canonical contracts and shared fixtures once agreed. Propose shared changes to B
instead of independently editing shared schemas. Low literature retrieval scores must not
block document-supported answers; classification is a soft retrieval signal, not a hard
filter or clinical diagnosis. Return partial supported mixed answers and explicit gaps.

Keep duplicate groups within one data split. Fit learned transformations on training data;
choose thresholds/models/prompts on development data. Lock final tests until frozen
measurement. Keep evaluation QA out of the retrieval index. Measure topic recall over
unique topics. Do not claim semantic support merely because a quote or topic URL exists.

Run relevant deterministic checks after changes. Do not write implementation-mirroring
tests for simple documentation. Substantive metric thresholds are not yet agreed;
structural/quote-offset acceptance is 100% on the defined suite. Never fabricate a pass.

## Secrets and external actions

Keep API keys server-side; never request secret values in chat. Do not log document bodies.
Never commit large raw datasets/indexes or local credentials. License/reuse reviews are
required before redistributing third-party data. Public repository visibility is approved;
publishing files requires separate push authorization.

Submitted documents may be kept only in server memory for at most 60 minutes, deleted on
expiry or restart, as explicitly approved by the user on 2026-11-10. Built-in public examples
may remain versioned. Do not persist submitted content to disk or shared caches.

The user also approved a 2 MiB (2,097,152 bytes) PDF limit and 100,000 Unicode code points
per document on 2026-11-10. Reject excess input; never silently truncate it.

No exact API spending cap, provider activation, hosting accounts, remaining session controls,
or operational limits have been approved. Record open decisions and ask
before dependent implementation. Mocks and routine checks must be key-free. Live paid CI
is off by default. Do not assume serverless filesystem persistence or co-hosting of all
Python services within the web application.
