# NoteLens: Codex Setup Prompt for Spec Kit and Four Independent Workstreams

Copy the content between **BEGIN PROMPT** and **END PROMPT** into Codex, opened in the project directory. The initial session prepares the project and its task backlogs. Four team members then implement their workstreams in separate working copies.

---

## BEGIN PROMPT

You are the technical coordinator for **NoteLens**. Prepare a new project using the official **GitHub Spec Kit** and **Spec-Driven Development (SDD)**. Enable four people to implement their modules independently against shared contracts, with minimal overlap in file changes.

In this session, produce specifications, plans, executable task backlogs, contracts, fixtures, mock implementations, and a minimal runnable foundation. Leave the four business modules for their respective team members. Use actual Spec Kit workflows rather than merely creating documents that resemble their outputs. Do not delegate to subagents unless the user explicitly requests delegation.

## 1. Confirmed Decisions and Source Precedence

These decisions are confirmed. Do not ask the team to decide them again.

| Item | Confirmed decision |
| --- | --- |
| Project status | The application and GitHub repository are being created from scratch. |
| Delivery deadline | **November 24, 2026.** This supersedes the November 27 deadline in the original documents. |
| Application language | **The entire application must be in English.** |
| Prompt and project artifacts | Write all specifications, plans, tasks, documentation, handoff prompts, comments, and identifiers in English. |
| Frontend and application integration | TypeScript. Member B owns the complete frontend and integration layer. |
| RAG | **Python.** Member A owns a Python RAG service. |
| Classification | Python. Member C owns training and classification inference. |
| Extraction | Python. Member D owns extraction and summarization. |
| API budget | A small budget exists; its exact amount has not been specified. |
| ICD codes | Optional for the MVP. Do not infer or generate codes from diagnoses. |
| Main dataset | MTSamples / Medical Transcriptions, restricted to the five specialties below. |
| Manual annotation | Approved: 30–50 documents. Use 40 as the planning target, shared across all four members. |
| Plan precedence | The improvement proposal takes precedence over the original plan, subject to the corrections and subsequent decisions in this prompt. |
| Metric regressions | A regression may be accepted through documented team review. Never conceal it or lower a threshold merely to make a check pass. |

### Team responsibilities

| Member | Workstream |
| --- | --- |
| A | Python RAG, knowledge corpus, retrieval, and retrieval evaluation contributions. |
| B | Complete frontend, TypeScript integration/orchestration, deployment, infrastructure, and security. |
| C | Classification dataset preparation, ML training, evaluation, and Python inference service. |
| D | Python entity extraction and summarization, annotation coordination, and the shared evaluation framework. |

Use A/B/C/D until actual names and GitHub handles are provided. Never invent identities.

If available, read both provided source PDFs completely: the original capstone project plan and the improvement proposal. Identify them by their contents; their filenames may use an earlier project name and may be in Serbian. All newly produced content must use NoteLens and be in English. This prompt includes the confirmed decisions needed to prepare the project even when the PDFs are unavailable.

Apply this precedence:

1. Confirmed decisions in this prompt, including the updated deadline and Python RAG requirement.
2. Technical corrections explicitly listed in this prompt.
3. The improvement proposal.
4. The original plan.

Use current official documentation to verify tool/API facts. Do not silently change business requirements because a tool suggests another architecture.

If a new unresolved conflict affects functionality, privacy, cost, or ownership, identify the conflicting requirements and ask a focused question. Continue independent work while awaiting the answer. Resolve routine implementation details using evidence and record the decision. Never invent credentials, experimental results, completed checks, budgets, or team capacity.

### English-language acceptance requirement

English is mandatory for every application surface: navigation, forms, buttons, placeholders, upload instructions, onboarding text, tooltips, loading and empty states, errors, validation messages, warnings, privacy notices, chat responses, generated summaries, entity labels, source explanations, and demo content. English medical documents and English questions are the supported MVP inputs.

LLM prompts must explicitly request English outputs. Define and test behavior for unsupported input languages; never silently present non-English output as a compliant result. Add an English-language review to the UI and generation acceptance checklist. Also keep README files, API documentation, schemas, evaluation rubrics, and team handoff instructions in English.

## 2. Product Scope

NoteLens is an educational demonstration that helps users understand English medical reports. The primary demo uses built-in public examples. A user may also supply permitted public or synthetic text or a text-based PDF.

The application must:

1. Prepare canonical document text.
2. Predict a supported medical specialty, with an explicit uncertain/unsupported outcome where appropriate.
3. Extract diagnoses, symptoms, and procedures with assertion status, temporality, and supporting document passages.
4. Generate a short, understandable English summary with traceable evidence.
5. Answer document questions from the document and medical-concept questions from a curated MedlinePlus corpus.
6. Show sources for claims and state clearly when evidence is insufficient.

Keep assertion and temporality distinct. For example, use `assertion` for confirmed/suspected/negated and `temporality` for current/historical/unknown. This preserves combinations such as a historically confirmed condition. Do not attribute family history to the patient; define a `subject` field if needed.

Patient-specific statements require evidence from the selected document. General literature does not prove that the patient has a condition. Specialty classification is a document label, not a diagnosis. A classification mistake must not permanently exclude relevant retrieval sources: use the category as a soft signal, not a mandatory filter.

The frontend must include document viewing, classification, extracted items with passage highlighting, a summary, chat, source attribution, claim provenance, and clear processing/error/insufficient-evidence states. Use visible English notices explaining that this is a demonstration, it does not replace a doctor, and users should not upload real personal medical reports.

Document-only and literature-only evidence must remain distinguishable. Questions needing both use a `mixed` route and retain the provenance of each claim.

Keep OCR, speech, translation, LLM/NER model training, new diagnosis generation, treatment recommendations, user-account systems, and complex agent frameworks outside the MVP unless explicitly requested.

## 3. Data Sources and Dataset Splits

### Main documents and classification labels: MTSamples

Source: [Medical Transcriptions](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions).

Target specialties:

- Cardiovascular / Pulmonary
- Orthopedic
- Gastroenterology
- Neurology
- Urology

Verify exact source labels and record their mapping. Produce actual counts before and after cleaning; do not copy numbers from the PDFs and present them as measured results.

Member C owns acquisition, provenance, the version/checksum manifest, deterministic cleaning, and split manifests. Review the dataset release license and upstream reuse conditions before redistribution, and record attribution. If Kaggle authentication is required, support a manually supplied local CSV without asking users to paste credentials into chat.

Remove empty texts. Detect and group identical and near-duplicate documents before splitting, using a documented method. A document group must not appear in more than one split. Record conflicting labels within the five specialties and exclude those cases from the initial single-label benchmark with an explanation. Do not merge broad labels such as Surgery into organ-system specialties.

Fit vectorizers, feature selection, and learned transformations on training data only. Do not use label-revealing metadata as hidden predictors. Publish separate train/validation/test manifests with a seed and group IDs, using feasible stratified proportions. Select models, thresholds, prompts, and retrieval settings on development/validation data. Keep the final test set locked until final measurement.

### RAG knowledge corpus: MedlinePlus

Source: [MedlinePlus XML](https://medlineplus.gov/xml.html).

Use English Health Topic summaries and relevant metadata for the selected subjects. Preserve a snapshot date, `topic_id`, URL, title, synonyms, and attribution. Review [content reuse guidance](https://medlineplus.gov/about/using/usingcontent/). Do not automatically ingest every outbound link or licensed encyclopedia/drug monograph.

Keep the corpus small and inspectable. Report measured topic and chunk counts. Member A owns the corpus and its ingestion pipeline in Python.

### Retrieval evaluation questions: MedQuAD

Source: [MedQuAD](https://github.com/abachaa/MedQuAD), primarily `4_MPlus_Health_Topics_QA`.

Check questions against content actually present in the selected corpus snapshot. An original topic URL does not establish that a downloaded summary contains the answer. Preserve original references and human-reviewed relevant topics/passages. Keep evaluation questions and reference answers out of the retrieval index. Compute topic-level recall over unique topics rather than counting multiple chunks from the same topic.

### Optional supplementary extraction data

[Augmented Clinical Notes](https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes) is optional after the core MVP works. Do not make it a blocking dependency. If used, review provenance/licenses, select the appropriate `full_note`, identify generated JSON summaries as silver references, and report results separately from MTSamples. Do not assume the classifier transfers reliably to this different distribution.

Do not introduce MIMIC or another credentialed dataset into this MVP.

## 4. Architecture and Contract-First Foundation

### Proposed runtime boundaries

| Component | Language / starting framework | Owner |
| --- | --- | --- |
| Complete UI and application integration | Next.js + TypeScript | B |
| RAG service | Python + a small FastAPI API | A |
| Classifier training and inference service | Python, scikit-learn/XGBoost, FastAPI | C |
| Extraction and summarization service | Python + FastAPI | D |
| Shared evaluation runner | Promptfoo with adapters calling the agreed APIs | D |

**RAG ingestion, chunking, embedding calls, vector-store access, retrieval, optional reranking, and retrieval-grounded answer generation belong in Python.** TypeScript may contain a thin HTTP client for the RAG service; it must not reimplement RAG logic. A's service produces literature-grounded English answers with citations. D's service handles document-grounded question answering alongside extraction and summarization. B routes requests and presents their results; for mixed answers, define a contract that preserves the claim/source links from both services.

Verify this architecture with a short feasibility check before freezing the plan. Avoid a mandatory ONNX export. Keep each Python service small rather than introducing an elaborate distributed platform.

Gemini, Chroma, and Vercel are starting candidates from the documents. Verify current availability, SDK support, runtime limits, Python hosting, persistence, and costs using official sources. Do not assume three Python services automatically deploy inside the same Vercel application, or that serverless local files persist. Propose the smallest viable hosting arrangement and record the reasoning. Ask before an alternative introduces a new paid service or changes the agreed scope.

Specifications and mocks must work without real API keys. Exact budget and hosting accounts remain open configuration decisions. Record them and ask before enabling paid calls/deployment, without blocking the local foundation. Do not invent an approved monetary cap. Include configurable limits, usage tracking, and live paid CI checks disabled by default.

Use narrow adapters for LLMs, embeddings, vector stores, and service clients. Support a key-free mock mode. Changing embedding models requires reindexing and an index version; never mix incompatible embedding spaces. Include caching, timeouts, bounded retries, and explicit behavior for HTTP 429 and provider outages.

### Shared contracts

Before parallel business implementation, B collects A/C/D proposals and freezes `contracts/v1`. Canonical JSON Schema/OpenAPI definitions, examples, and an error envelope are the source of truth. Generate language bindings where practical. Avoid conflicting hand-maintained TypeScript/Python schemas. Verify that mocks and actual HTTP payloads satisfy the same contracts.

Specify at least:

| Contract | Required content |
| --- | --- |
| `PreparedDocument` | `schema_version`, `doc_id`, canonical `text`, `text_sha256`, source metadata. |
| `ClassificationResult` | Category or explicit uncertain/unsupported state, scores, model version, and the meaning/limitations of confidence. Raw scores are not proof of calibration. |
| `ExtractionResult` | Items with entity ID, type, text/name, assertion, temporality, evidence; summary with evidence links; version. ICD is optional and may only reproduce a code present in the source. |
| `RetrievalRequest` / `RetrievalResult` | Question, optional extracted concept names, passages with topic/passage IDs, URL, text, score, retriever version, and sufficient/insufficient/error state. |
| `AnswerResult` | English answer, claim-to-source links, sources, `document/literature/mixed/none` route, evidence state, warnings. Do not invent numeric clinical certainty. |
| Shared errors | Unsupported file, validation failure, timeout, rate limit, provider unavailable, insufficient evidence. |

Document preparation creates canonical text once; downstream modules must not alter it. Define `evidence.start` and `evidence.end` as half-open `[start, end)` Unicode code-point offsets. The quote must exactly equal that canonical-text slice. Provide Python and TypeScript examples covering an emoji/non-BMP character and repeated passages. JavaScript UTF-16 indices must not be treated as code-point indices. Define explicit UI conversion, deterministic normalization, and hashing.

A low retrieval score blocks unsupported literature claims, but must not block a document-grounded answer. Select retriever-specific thresholds on validation data. A score is not a probability of truth. For mixed answers, return the supported portion and identify missing evidence rather than inventing a complete answer.

## 5. File Ownership and Git Workflow

Create a monorepo with these ownership boundaries. Adjust details only where necessary for verified feasibility while preserving one owner per path.

| Path | Owner and responsibility |
| --- | --- |
| `apps/web/**` | B: complete UI, document preparation/upload, API routes, routing, session isolation, service integration. |
| `services/rag/**` | A: Python ingestion, retrieval, embeddings, vector-store adapters, local tests, experiments, its Python dependencies and lockfile. |
| `services/classifier/**` | C: Python training/inference, local tests, its Python dependencies and lockfile. |
| `services/extraction/**` | D: Python extraction/summarization, local tests, its Python dependencies and lockfile. |
| `data/mtsamples/**` | C: scripts, manifests, split IDs; large raw files ignored by Git. |
| `data/knowledge/**` | A: corpus scripts/manifests; large indexes ignored by Git. |
| `eval/**` | D: benchmark, Promptfoo runner, scoring, reports, except member-specific annotation paths below. |
| `contracts/**` | B: canonical schemas, generated bindings, shared fixtures. |
| `infra/**`, `.github/**`, `scripts/project/**` | B: deployment, CI, local startup, integration checks. |
| `docs/team/**`, `docs/decisions/**` | B: coordination and accepted cross-module decisions. |
| `docs/rag/**` | A. |
| `docs/platform/**` | B. |
| `docs/ml/**` | C. |
| `docs/extraction-eval/**` | D. |
| `specs/000-foundation/**` | B. |
| `specs/001-rag/**` | A. |
| `specs/002-platform/**` | B. |
| `specs/003-classification/**` | C. |
| `specs/004-extraction-evaluation/**` | D. |
| `eval/annotations/member-a/**` | A; explicit exception to D's parent-directory ownership. |
| `eval/annotations/member-b/**` | B; explicit exception. |
| `eval/annotations/member-c/**` | C; explicit exception. |
| `eval/annotations/member-d/**` | D. |

B alone maintains root README/AGENTS files, root package-manager configuration and lockfile, workspace definitions, `.env.example`, shared build configuration, and global Spec Kit constitution/templates/integration files. A, C, and D maintain separate Python projects and lockfiles inside their services. D may maintain a local evaluation package manifest; changes to a shared JavaScript lockfile go through B. Avoid repository-wide formatting that modifies another member's files.

The initial coordinator session may create all empty modules, specifications, initial backlogs, and handoff documents. After the foundation checkpoint, each member changes only owned paths. Propose shared-contract changes through a documented request; B updates the canonical schema, fixtures, and version after agreement. Consumers adapt through their own PRs.

Generate root and local `AGENTS.md` guidance, an allowed-path matrix, and a simple CI check for declared PR scope. Prepare CODEOWNERS without fabricated GitHub handles and document how to insert the real ones. Explain that CODEOWNERS requests review; branch protection is needed to enforce approvals. State that file ownership reduces conflicts but cannot guarantee their absence.

Everyone branches from the same foundation checkpoint. Each person uses a separate clone or worktree and their own branch. Explicitly select the correct Spec Kit feature using the installed version's mechanism rather than assuming Git branch names select it. If supported, document `SPECIFY_FEATURE_DIRECTORY` and `SPECIFY_FEATURE_NO_PERSIST` for relevant execution contexts. Do not overwrite another session's `.specify/feature.json` or run four active sessions in the same checkout.

Provide actual Bash and PowerShell commands for working-copy creation and feature selection. Do not invent a remote URL or account. Document remote repository creation/connection without publishing the project during this preparation session.

Every feature owns its own `tasks.md`. Avoid a shared task file that all four members constantly edit. Generate a combined status by reading separate task files, or let B maintain it. Cross-feature task links express dependencies. Creating a spec or mock does not complete its business-implementation task.

## 6. Spec Kit Workflow and Required Artifacts

Inspect the directory, Git state, runtimes, and installed Spec Kit. Configure the official Codex integration according to current documentation and pin a verified version. Preserve existing work if the directory is unexpectedly nonempty. Do not use force-overwrite flags.

Official references:

- [Spec Kit repository](https://github.com/github/spec-kit)
- [Codex integration](https://github.github.io/spec-kit/integrations/codex.html)
- [SDD quickstart](https://github.com/github/spec-kit/blob/main/docs/quickstart.md)

Verify command names against the installed integration. At preparation time, Codex documentation uses skills such as `$speckit-constitution`, `$speckit-specify`, `$speckit-clarify`, `$speckit-plan`, `$speckit-tasks`, `$speckit-analyze`, and `$speckit-implement`; versions may differ. Agent skill invocations are not shell executables. Never claim a skill ran when only a similar document was written. If the environment cannot execute a required step, report the exact limitation and smallest necessary next action.

Proceed in this order:

1. Establish one project constitution: confirmed scope, English-only application/artifacts, Python RAG/classification/extraction, ownership, contract-first development, traceable evidence, isolated work, test-set protection, cost controls, and November 24 deadline.
2. Create a foundation specification covering the shared product, architecture, contracts, ownership, mocks, and integration smoke scenario.
3. Create four separate feature specifications: `001-rag`, `002-platform`, `003-classification`, `004-extraction-evaluation`.
4. Clarify material unresolved decisions, then create plans and the installed workflow's research/data-model/contracts/quickstart artifacts as appropriate.
5. Generate tasks for each feature. Analyze consistency within features and across interfaces, ownership, and dependencies.
6. Use checklist stages where appropriate. Do not claim reviewer acceptance without review.
7. Implement only the foundation scaffold: contracts, representative fixtures, mock adapters, health endpoint stubs, and a minimal mock UI/end-to-end smoke path. Use the installed Spec Kit implementation workflow for this foundation when available. Leave actual ML/RAG/LLM business implementation to the team.
8. Create four separate English start prompts that activate the right feature and implement only that member's workstream in later sessions.

Preserve standard Spec Kit task checkbox/ID syntax. Add stable global aliases such as `F-xxx`, `A-xxx`, `B-xxx`, `C-xxx`, `D-xxx` where local task IDs repeat between features. Use `[P]` only for tasks that genuinely satisfy the installed workflow's parallelism rules.

Each executable task must include:

- One owner and a user-story reference.
- A concrete deliverable and allowed file paths.
- Dependencies identified by feature and task ID.
- Acceptance criteria and a real verification command.
- A definition of done distinguishing mock checks, actual-module checks, and live-provider checks.

After creating the scaffold, verify that documented commands exist. Do not invent npm scripts.

Create an English handoff document for each member with their first five ready tasks, input/output contracts, mock examples, file boundaries, feature-activation command, and local checks. Their start prompt must read constitution/AGENTS/spec/plan/tasks, stay inside owned paths, and request shared-contract changes rather than modifying shared files independently.

## 7. Required Task Backlogs

Expand the following seed tasks into executable Spec Kit tasks. Do not leave them as generic epic titles.

### Foundation — coordinated by B

- **F-001:** Verify and initialize the official Spec Kit Codex integration and constitution.
- **F-002:** Record confirmed decisions, MVP scope, updated deadline, Python service boundaries, ownership, and feature specifications.
- **F-003:** Define and validate `contracts/v1`, positive/negative fixtures, Unicode offsets, and shared errors.
- **F-004:** Scaffold the three independent Python services and TypeScript application with standalone mock inputs/outputs and initial dependencies.
- **F-005:** Provide local startup, health stubs, and an English mock end-to-end smoke path without secrets.
- **F-006:** Complete four plans, task backlogs, handoffs, start prompts, and ownership/feature-context checks.
- **F-007:** Document the foundation checkpoint and branching procedure. If committing is unavailable, identify the exact prepared files and command; never fabricate a commit hash.

### A — Python RAG

- **A-001:** Acquire and version the permitted MedlinePlus snapshot and topic manifest. Corpus preparation can begin after the initial specification.
- **A-002:** Implement Python parsing/cleaning, stable topic IDs, metadata, attribution, and chunking with local fixture tests.
- **A-003:** Implement Python embedding/vector-store adapters, batched ingestion, caching, and index versioning.
- **A-004:** Implement an embedding-only retrieval baseline returning contract-compliant passages through a Python FastAPI endpoint.
- **A-005:** Add a lexical/hybrid retrieval variant and compare it on the same validation questions. Reranking is optional if its measured benefit fits the deadline and budget.
- **A-006:** Use concepts from questions and extraction without requiring ICD codes or hard-filtering by predicted specialty.
- **A-007:** Propose single-source and multi-source questions/references to D. Write personal annotations only under `eval/annotations/member-a/**`.
- **A-008:** Measure retrieval and rejection behavior. Test contracts, timeouts, empty corpora, and provider failures. Deliver the stable API/client examples to B and evaluation outputs to D without editing their implementations.
- **A-009:** Implement literature-grounded English answer generation inside the Python RAG service, with claim-linked citations, insufficient-evidence behavior, and contract-compliant outputs. The TypeScript application only calls this API and displays its results.

### B — complete frontend, integration, deployment, security

- **B-001:** Build the complete English demo-document/text/PDF input flow and canonical-text display; validate type/size and explicitly handle unsupported scanned PDFs.
- **B-002:** Build classification, entity, summary, source-highlighting, and chat interfaces using mocks from the beginning. Cover English loading, empty, validation, error, and insufficient-evidence states.
- **B-003:** Implement server-side TypeScript HTTP clients for the Python RAG/classifier/extraction services, `document/literature/mixed/none` routing, and controlled history/state. A user/session must not access another session's `doc_id`.
- **B-004:** Implement configuration, secret handling, timeouts/retries, redacted logs, caching, and configurable spending limits.
- **B-005:** Connect actual Python services through small separate PRs after their contract checks pass; keep RAG algorithms in A's Python service.
- **B-006:** Add CI, ownership-scope checks, secret/dependency checks, and agreed integration checks. Live evaluation requires explicit triggering.
- **B-007:** Provide local/cloud runbooks, health/readiness, persistence, service authentication, and a viable deployment of the application plus Python services. Record real deployment URLs only after actual deployment.
- **B-008:** Test document/retrieved-text prompt injection, XSS, oversized files, unauthorized document IDs, accidental document logging, and abuse/rate limits. If URL fetching exists, use an allowlist and prevent SSRF; do not introduce arbitrary browsing.
- **B-009:** Finish the full English frontend, attribution, notices, readable errors, and demo rehearsal. Label mock outputs clearly so they cannot be mistaken for live results.

### C — Python ML classification

- **C-001:** Acquire and audit the dataset, provenance/license, schema, and class distribution.
- **C-002:** Detect duplicate groups, identify conflicting labels, and publish reproducible train/validation/test manifests.
- **C-003:** Train a TF-IDF + Logistic Regression baseline; include a majority baseline and class support for context.
- **C-004:** Compare XGBoost against the baseline through controlled validation experiments. Add embeddings + XGBoost only if time/cost permit. Keep the better simpler model when appropriate; never manipulate the benchmark to make XGBoost win.
- **C-005:** Report macro-F1, per-class precision/recall/F1, confusion matrix, error analysis, and confidence/out-of-distribution limitations.
- **C-006:** Package the complete preprocessing/inference pipeline, label mapping, model version, deterministic inference, and contract-compliant Python FastAPI endpoint. ONNX export is not required.
- **C-007:** Deliver contract/smoke checks, non-sensitive examples, B's service-start instructions, and D's evaluation integration instructions.
- **C-008:** Complete personal annotations under `member-c`; after model selection, run the locked final test and record actual results in an English model card.

### D — Python extraction, summarization, shared evaluation

- **D-001:** Define entities, assertion/temporality rules, annotation instructions, schema proposals, and extraction mocks without waiting for complete ML/RAG implementations.
- **D-002:** Select 40 representative documents using C's published manifests, approximately balanced across specialties. Separate extraction development and final evaluation by document/group. Where feasible, align development with ML validation and final evaluation with ML test documents. Publish and freeze assignment IDs.
- **D-003:** Assign 10 primary documents per member using separate member paths. Add independent secondary review for at least 10 documents; annotators must not edit the same file. Adjudicate disagreements and generate the canonical reference set. Call it human-reviewed rather than clinically validated without expert confirmation.
- **D-004:** Implement Python LLM extraction against the schema, assertion/temporality, evidence spans, output validation, and bounded repair/retry. Do not infer diagnoses absent from the report.
- **D-005:** Generate English evidence-linked summaries and document-grounded answers in Python. Separately verify whether cited passages support extracted items, summary claims, and document answers. Quote existence alone does not establish semantic support.
- **D-006:** Build the shared Promptfoo runner using API adapters, versioned datasets, deterministic scorers, and separate offline/smoke/live profiles. Module owners supply local tests and outputs; D maintains the shared runner.
- **D-007:** Assemble approximately 80 QA cases with separate development/final portions, including around 30 multi-source questions, around 10 questions lacking an answer in the required source, and out-of-scope questions. Publish exact counts, categories, relevant topic/passage IDs, and relevance criteria. Multiple diagnoses do not automatically make every corresponding topic necessary for every question.
- **D-008:** Define LLM-as-judge rubrics, human-review calibration, and entity-evidence support checks. Record model/prompt versions and disagreements. The judge must not be the only quality measure.
- **D-009:** Produce an English evaluation report with measured results, baseline comparisons, cost, limitations, and frozen final configurations. Consolidate results without independently editing A/C implementations.

## 8. Evaluation and Demonstration Acceptance

Always report sample counts and input/model/prompt/index versions.

| Area | Required measurements |
| --- | --- |
| Classification | Macro-F1, per-class recall/F1, confusion matrix, baseline comparison, leakage checks. |
| Extraction | Schema validity, exact quote/offset validity, entity precision/recall/F1 with predefined exact/relaxed matching, assertion and temporality accuracy, unsupported-item rate. |
| Summaries and answers | Source-relative correctness, groundedness, completeness, citation correctness, English output compliance. |
| Retrieval | Unique-topic Recall@5, MRR, and all-required-topics@5: the fraction of questions for which all annotated necessary topics appear in the top five. |
| Evidence coverage | Whether retrieved passages actually contain the required evidence, beyond merely finding a topic URL. |
| Abstention | Answer rate on answerable questions, correct rejection of unanswerable questions, error risk versus coverage. A system that always refuses must not pass on abstention alone. |
| Security | All defined injection, secrets, logging, isolation, and upload checks; passing the finite suite is not proof of universal security. |

Report single-source and multi-source retrieval results separately. Flag questions requiring more than five topics. Do not count multiple chunks of one topic as multiple relevant topics. Do not call `coverage@5` an independent metric if its formula is identical to Recall@5.

Plan human review of approximately 40 generated answers, 10 per member, plus at least 20 entity-evidence pairs. This is separate from initial document annotation. Use development examples for judge calibration. Review final answers for reporting without tuning final prompts against the same held-out set. Handle repeated mentions with explicit matching rules.

Use the stronger model only when supported by results. If XGBoost does not beat the baseline, explain and retain the better model; the team may accept a documented change to the original demo criterion rather than leak test information.

### Technical corrections that override the PDFs

1. MedlinePlus Connect does not validate clinical correctness of suggested ICD codes. A missing mapping does not prove an invalid code. ICD lookup is not an MVP dependency.
2. Retrieval scores are not clinical confidence estimates.
3. Choose thresholds on development/validation data, never the final test.
4. Low RAG scores must not block document-supported answers.
5. Coverage defined as the fraction of relevant topics retrieved is recall. Measure retrieval of all required annotated topics separately.
6. Generated silver summaries do not automatically provide span-level/entity/status ground truth.

Require 100% structural validity and quote/offset consistency on the defined acceptance suite. The team sets substantive extraction/retrieval/answer thresholds after the first development measurement, targeted for **November 14, 2026** under the revised schedule. Create named configuration entries and an acceptance process without inventing agreed numeric values.

Routine CI uses deterministic unit/contract checks and a small mock/smoke suite. Live evaluation uses caching and a controlled budget. Run the complete final benchmark on a frozen version; repeat only with a new version and documented reason. For regressions, record old/new results, sample counts, judge limitations, and the team's acceptance decision.

## 9. Revised Schedule and Dependencies

**Final delivery is November 24, 2026.** Adapt work to the actual execution date without silently moving this deadline. If it has already passed, ask for the new deadline.

| Phase | Target dates in 2026 | Exit condition |
| --- | --- | --- |
| 0 — foundation | November 9–10 | Confirm contracts, Spec Kit foundation, ownership, Python service/deployment feasibility, mocks, and four executable backlogs. |
| 1 — parallel implementation | November 11–14 | Independent modules work with mocks; data splits and initial annotations exist; first development measurement and threshold decisions are complete. |
| 2 — integration | November 15–18 | Actual modules are connected, the complete flow works, and human review has started; security checks already exist. |
| 3 — validation and deployment | November 19–21 | Development improvements, review, abstention/security/cost checks, and a deployment rehearsal are complete. |
| 4 — freeze and final checks | November 22–23 | Freeze configuration, run locked final evaluation, finish the report, rehearse the demo, and preserve contingency time. |
| Delivery | **November 24** | Submit the reviewed application and supporting artifacts. |

Do not invent available hours or promise a delivery velocity. Identify the critical path and MVP/should/could priorities. Optional reranking, alternative datasets, ONNX, and ICD integration must not block the core product.

Foundation/contracts are the shared prerequisite for parallel implementation. Before they are finalized, A can inspect the corpus, C can audit data, D can draft annotation rules, and B can prepare the UI within owned paths. After the checkpoint, each module must pass local checks without complete implementations of the others. Do not schedule all of D behind A/C or all of the frontend behind backend completion. Document when mocks are replaced by real adapters.

## 10. Completion Criteria for This Initial Codex Session

Finish when the actual foundation scaffold, required specifications, and all four task backlogs are created and checked, or when a clearly described external limitation prevents completion. Do not stop after a generic plan. Leave the full business implementation for the four workstreams.

Conclude in English with:

1. Confirmed decisions and specific remaining blockers.
2. Installed Spec Kit version and actual workflow invocations used.
3. The member/path/feature/initial-task ownership table.
4. Links to created specifications, plans, task files, contracts, handoffs, and four start prompts.
5. Actual local mock-start and verification commands.
6. Results of executed checks, clearly separating unexecuted live checks.
7. Instructions for four independent working copies and correct feature activation.
8. Each member's next concrete actions.

The preparation succeeds when every member can open their own working copy, run their English start prompt, read their feature's `tasks.md`, and begin a ready task without waiting for the other modules or modifying their files.

## END PROMPT

---

## Reference Sources

- [GitHub Spec Kit](https://github.com/github/spec-kit)
- [Spec Kit Codex integration](https://github.github.io/spec-kit/integrations/codex.html)
- [Spec Kit quickstart](https://github.com/github/spec-kit/blob/main/docs/quickstart.md)
- [Spec Kit core reference](https://github.com/github/spec-kit/blob/main/docs/reference/core.md)
- [MTSamples / Medical Transcriptions](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions)
- [MedlinePlus XML](https://medlineplus.gov/xml.html)
- [MedlinePlus content reuse](https://medlineplus.gov/about/using/usingcontent/)
- [MedQuAD](https://github.com/abachaa/MedQuAD)
- [Augmented Clinical Notes](https://huggingface.co/datasets/AGBonnet/augmented-clinical-notes)
- [MedlinePlus Connect web service](https://medlineplus.gov/medlineplus-connect/web-service/)

Project requirements come from the two source plans and the team's subsequent confirmed decisions. Additional implementation details are a proposed delivery approach. Codex must verify current versions and practical feasibility before executing them.
