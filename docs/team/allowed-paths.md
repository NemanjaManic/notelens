# Allowed Paths and Ownership

**Status**: Ownership guidance for the documentation handoff, 2026-11-10.
The runnable foundation checkpoint is pending and explicitly deferred.
The initial coordinator prepared this approved documentation package across paths.
From this handoff onward, each contributor changes only their owned paths. The most specific
row wins. Shared-file requests go to the named owner and do not authorize direct edits.

| Path | Owner | Responsibility |
| --- | --- | --- |
| `apps/web/**` | B | Complete frontend, document preparation, orchestration, session isolation, service clients. |
| `services/rag/**` | A | Python corpus ingestion, retrieval, embeddings, vector adapters, literature answers, local tests and lockfile. |
| `services/classifier/**` | C | Python dataset/model training and inference, local tests and lockfile. |
| `services/extraction/**` | D | Python extraction, summarization, document answers, local tests and lockfile. |
| `data/mtsamples/**` | C | Acquisition scripts, provenance, cleaning, split/manifests; do not commit large raw files. |
| `data/knowledge/**` | A | Corpus scripts, attribution and version manifests; do not commit large indexes. |
| `eval/**` | D | Shared benchmark, evaluation runner, scoring, adjudication and reports; member annotations are exceptions. |
| `contracts/**` | B | Canonical contracts, generated bindings, shared fixtures and shared version changes. |
| `infra/**` | B | Deployment and infrastructure. |
| `.github/**` | B | CI, review routing and repository workflow configuration. |
| `scripts/project/**` | B | Local startup, integration and ownership checks. |
| `docs/team/**` | B | Coordination, ownership, handoffs and start prompts. |
| `docs/decisions/**` | B | Accepted cross-module decisions and documented change requests. |
| `docs/rag/**` | A | RAG documentation and experiments. |
| `docs/platform/**` | B | Frontend, orchestration, deployment and security documentation. |
| `docs/ml/**` | C | Dataset, classification experiments and model documentation. |
| `docs/extraction-eval/**` | D | Extraction, annotation and evaluation documentation. |
| `specs/000-foundation/**` | B | Shared foundation specification, plan and tasks. |
| `specs/001-rag/**` | A | RAG specification, plan and tasks. |
| `specs/002-platform/**` | B | Platform specification, plan and tasks. |
| `specs/003-classification/**` | C | Classification specification, plan and tasks. |
| `specs/004-extraction-evaluation/**` | D | Extraction/evaluation specification, plan and tasks. |
| `eval/annotations/member-a/**` | A | A's primary annotations and separately stored secondary reviews only. |
| `eval/annotations/member-b/**` | B | B's primary annotations and separately stored secondary reviews only. |
| `eval/annotations/member-c/**` | C | C's primary annotations and separately stored secondary reviews only. |
| `eval/annotations/member-d/**` | D | D's primary annotations and separately stored secondary reviews only. |
| Root README/AGENTS, package manifests, workspace/build configuration, shared lockfile, `.env.example` | B | Shared project configuration and documentation. |
| `.specify/**`, `.agents/skills/**`, shared `.codex/**` integration files | B | Global Spec Kit constitution, templates, integration and version maintenance. |
| `prompts/NoteLens_Codex_SpecKit_prompt_00.md` | B, explicit user approval required | Preserve the supplied requirements input; do not rewrite it during setup. |

A is the GitHub repository creator. This does not change B's ownership of shared files.
A/C/D maintain their own service dependencies and lockfiles. D may maintain a local
evaluation package manifest; shared JavaScript lockfile changes go through B.

## Shared change requests

1. Record the proposed change, reason, affected contracts/paths, owners and consumers.
2. Obtain agreement from affected owners and required user approval for scope/cost/privacy.
3. B updates canonical contracts, fixtures and version; module owners adapt via their own PRs.
4. Record checks, compatibility and replacement of mocks with real adapters.

Do not directly edit another member's annotation or review file. D adjudicates separate
member submissions into canonical references under D-owned paths.

## Review and checkpoint

No real colleague handles are available. CODEOWNERS and enforced PR-scope checks are
later foundation deliverables, not implemented by this matrix. Do not insert fictional
handles. CODEOWNERS requests review; branch protection is needed to enforce approvals.
File ownership reduces conflicts but cannot guarantee their absence.

All four working copies now branch from the same documentation base as described in
[working copies](working-copies.md). This permits independent inspection/proposals.
Later business work still requires its actual dependencies and the reviewed runnable
foundation base. Frozen contracts, mocks and runtime checks are not implied by this package.
