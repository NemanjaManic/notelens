# NoteLens Constitution

**Status**: Draft for user review. Confirmed source requirements remain binding
independently of this draft's ratification status.

## Core Principles

### I. Educational Scope and English Language

NoteLens MUST help users understand English medical reports as an educational demonstration.
Every application surface, generated response, prompt, identifier, comment, specification,
evaluation artifact, and handoff MUST be in English. English documents and questions are the
supported MVP inputs. Unsupported languages MUST receive an explicit English outcome rather
than silently passing as supported. Visible notices MUST explain that this demonstration
does not replace a doctor and that users must not upload real personal medical reports.
Built-in public examples are the primary demo; permitted public or synthetic text and
text-based PDFs are additional inputs.

### II. Independent Ownership and Isolated Work

A owns RAG; B owns the entire frontend, orchestration, infrastructure, security, and shared
contracts; C owns classification; D owns extraction, summarization, document-grounded
answers, annotation coordination, and shared evaluation. A creates the repository; that
administrative role does not transfer B's module responsibilities to A. Do not invent names
or GitHub handles.

Each workstream MUST have separate owned paths, specifications, plans, and task files.
The approved initial coordinator session MAY prepare documentation and empty foundations
across those boundaries. After the foundation checkpoint, contributors MUST use separate
clones/worktrees and branches, and change only owned paths. Shared changes go through the
responsible owner. Member annotation paths override parent ownership. Ownership reduces
conflicts but cannot guarantee their absence.

### III. Contract-First Boundaries

Before parallel business implementation, B MUST collect A/C/D proposals and coordinate the
freeze of canonical, versioned contracts for documents, classification, extraction,
retrieval, answers, provenance, and errors. Generated language bindings SHOULD be used where
practical; divergent hand-maintained definitions MUST NOT become competing sources of truth.
Mocks and real payloads MUST satisfy the same contracts. Changes require a documented
proposal, agreement, owner-maintained schema/fixture/version updates, and consumer updates.

The approved boundaries are a TypeScript application/integration layer and three small
Python services. All ingestion, chunking, embeddings, index access, retrieval, and
literature-grounded generation belong to A's Python service. D's Python service owns
extraction, summarization, and document-grounded answers. B orchestrates and displays their
outputs, preserving claim-to-source links when combining supported portions.

### IV. Canonical Text and Traceable Claims

Preparation MUST produce canonical text once, with document identity and digest.
Downstream modules MUST NOT alter it. Evidence offsets MUST be Unicode code-point,
half-open intervals [start, end), and quotes MUST exactly match the canonical slice.
Cross-language checks MUST cover non-BMP characters and repeated passages; browser
highlighting MUST explicitly convert code-point offsets to native string indices.

Patient-specific claims MUST have document support; literature MUST NOT establish a
patient's condition. Assertion, temporality, and subject MUST remain distinct, including
historically confirmed conditions and family history. Citations MUST be checked for
semantic support as well as existence. Specialty is a document label, not a diagnosis.
ICD codes are optional and MUST only reproduce codes explicitly present in the source.

### V. Evidence-Aware Answers and Honest Uncertainty

Document, literature, mixed, and unsupported routes MUST remain distinguishable.
Missing evidence MUST be reported explicitly. Low retrieval scores MUST block unsupported
literature claims without blocking supported document answers. Mixed responses MUST return
supported portions and identify gaps. Specialty MAY be a soft retrieval signal; it MUST NOT
permanently exclude relevant sources. Retrieval scores MUST NOT be presented as
probabilities of clinical truth. Classification MUST expose uncertain/unsupported outcomes
and explain score meaning and calibration limitations. Do not invent diagnoses,
treatment recommendations, or numeric clinical certainty.

### VI. Reproducible Data and Protected Evaluation

C MUST own MTSamples provenance, license/reuse review, deterministic cleaning, exact
five-specialty mapping, measured counts, duplicate grouping, and seeded split manifests.
Remove empty texts. Keep identical/near-duplicate groups within one split. Report conflicting
labels within the target specialties and exclude those groups from the initial single-label
benchmark. Fit learned transformations only on training data. Do not use label-revealing
metadata as hidden predictors or merge broad Surgery labels into organ-system specialties.

A MUST own a small, versioned, attributable English MedlinePlus Health Topic corpus.
Review reuse conditions before redistribution. Keep evaluation questions and references
out of the index; topic URLs alone do not establish passage-level answerability. Select
models, prompts, thresholds, and retrieval settings on development/validation data.
Keep final tests locked until measuring frozen final configurations.

### VII. Measured Acceptance and Human Review

Always report sample counts and input/model/prompt/index versions. Measure classification
against baselines, per-class performance, and leakage; extraction validity, evidence support,
entity matching, assertion, temporality, and unsupported items; summaries/answers for
correctness, groundedness, completeness, citations, and English compliance; and rejection
versus answer coverage. Retrieval MUST measure unique-topic Recall@5, MRR, and
all-required-topics@5, separating single-source and multi-source cases. Repeated chunks
MUST NOT inflate topic recall.

Require 100% structural and exact quote/offset validity on the defined acceptance suite.
Leave substantive quality thresholds unset until the first development measurement and
documented team decision, targeted for 2026-11-14. Always-refusing systems MUST NOT pass on
rejection alone. Plan 40 primary annotated documents, independent secondary review of at
least 10, approximately 80 QA cases, approximately 40 generated-answer reviews, and at least
20 entity-evidence pair reviews. Do not call human-reviewed material clinically validated
without expert confirmation. Calibrate LLM judging against human review; it MUST NOT be the
sole measure. Regressions require old/new measurements and documented team acceptance.
Do not lower thresholds or conceal regressions to make checks pass.

### VIII. Privacy, Isolation, and Security

Secret values and document bodies MUST NOT enter repository history or ordinary logs.
Keep secrets server-side. Scope document access to its user/session; knowing a document ID
MUST NOT grant another session access. Treat inputs and retrieved passages as untrusted,
including embedded instructions. Address upload type/size limits, scanned PDFs,
prompt injection, XSS, unauthorized document IDs, accidental document logging, rate limits,
and abuse. Do not introduce arbitrary URL browsing. If approved URL fetching exists,
require an allowlist and SSRF protections. Surface unagreed retention, session lifetimes,
operational limits, and account choices before dependent implementation or deployment.

### IX. Key-Free Development and Controlled Spending

Specifications, contracts, mocks, and the local foundation MUST work without real API keys.
Narrow adapters MUST isolate LLMs, embeddings, vector stores, and service clients. Real
providers require caching, timeouts, bounded retries, rate-limit/outage behavior,
usage tracking, and configurable spending controls. Changing embedding spaces requires
reindexing and a new index version. Live paid CI MUST be disabled by default.

No exact monetary cap or hosting account is approved. Paid calls, new paid services, and
deployment require explicit authorization before activation. Do not assume serverless
local-file persistence or that all Python services run inside the web deployment.

### X. Real Workflows and Reviewable Stages

Use installed official Spec Kit skills and resolver scripts; record actual invocations
and versions. Distinguish specifications, mocks, real module checks, and live checks.
Generated checklists MUST NOT be reported as human reviewer acceptance. Preserve standard
task checkbox/ID syntax and stable cross-feature aliases. Each future executable task MUST
have one owner, a user story, paths, dependencies, acceptance criteria, a real verification
command, and separate mock/module/live completion conditions. Mocks do not complete
business implementation.

Each new change package in this user-led setup requires explicit user approval.
Approval remains valid for necessary work inside that package; do not ask for it repeatedly.
Ask unresolved functionality, privacy, cost, or ownership questions rather than guessing.
Do not delegate to subagents without an explicit request. Never fabricate checks, results,
commits, deployments, identities, budgets, or team capacity.

## Product and Delivery Constraints

- Final delivery is **2026-11-24**, superseding 2026-11-27. Do not silently move it
  or invent available working hours.
- Foundation: 2026-11-09 through 2026-11-10; parallel implementation: 2026-11-11 through
  2026-11-14; integration: 2026-11-15 through 2026-11-18; validation/deployment rehearsal:
  2026-11-19 through 2026-11-21; freeze/final checks: 2026-11-22 through 2026-11-23.
- Include document preparation, five-specialty classification, evidence-linked
  diagnoses/symptoms/procedures, summaries, document/literature/mixed questions, and sources.
- Target specialties: Cardiovascular / Pulmonary, Orthopedic, Gastroenterology,
  Neurology, Urology. Exact source-label mapping awaits C's measured audit.
- Exclude OCR, speech, translation, LLM/NER model training, new diagnosis generation,
  treatment recommendations, user accounts, and complex agent frameworks.
- Optional reranking, augmented clinical notes, ONNX, and ICD integration MUST NOT block
  the core. Do not introduce MIMIC or another credentialed dataset.

## Workflow and Quality Gates

1. Establish the constitution, then foundation and four workstream specifications.
   Clarify material gaps before the relevant plans; generate separate plans/tasks
   and analyze interfaces.
2. Verify service/hosting feasibility using official sources before freezing plans.
   Gemini, Chroma, and Vercel are candidates, not commitments or proven deployments.
3. Freeze contracts and provide key-free fixtures, stubs, and a minimal mock flow before
   the foundation checkpoint. Leave business RAG/ML/LLM implementation to the team.
4. Before the checkpoint, A may inspect corpus sources, C may audit data, D may draft
   annotation guidance, and B may prepare the UI within owned paths. Do not serialize
   frontend/evaluation behind complete backends. Track replacement of mocks.
5. After the checkpoint, use separate working copies and explicitly select the feature.
   Concurrent sessions MUST NOT overwrite a shared checkout's feature state.
6. Routine checks are deterministic and key-free. Live evaluation requires explicit
   triggering and budget control. Repeat final runs only for a new version and a
   documented reason. Passing a finite security suite is not proof of universal security.

## Governance

Confirmed decisions in `prompts/NoteLens_Codex_SpecKit_prompt_00.md` and subsequent explicit
user decisions are authoritative. Source precedence is: confirmed prompt decisions,
prompt technical corrections, improvement proposal, original plan. The two source PDFs
are absent from this checkout; do not claim they were read. This constitution organizes
requirements and MUST NOT silently override them.

B owns constitution maintenance and accepted cross-module decisions after the checkpoint.
Amendments require a documented proposal, affected-owner review, explicit approval of
changed requirements, a version decision, and migration/consumer impact where applicable.
Use semantic versioning: major for incompatible governance changes, minor for new
principles, patch for non-semantic clarification. Reviews MUST record compliance and
unresolved exceptions. Review routing does not replace branch protection.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): pending user review | **Last Amended**: 2026-11-10
