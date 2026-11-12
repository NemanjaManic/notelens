# Member C status and required team handoffs

**Prepared:** 2026-11-11

**Workstream:** C — MTSamples preparation, classification, evaluation and inference

**Audience:** A, B and D

**Delivery deadline:** 2026-11-24

**My immediate implementation dependency is the shared foundation coordinated by B.**
I have completed C-001 locally and prepared my interface feedback. To proceed with C-009,
I need frozen contracts and the runnable scaffold. To proceed with C-002 and then training,
I additionally need the reviewed, published foundation base. My annotation work separately
requires D's assignments, which depend on the split manifests I will deliver first.

This report reflects the current local backlogs and supplied review documents. It does
not assert the status of unpublished work in other members' working copies. Please provide
reviewable artifacts and check results for any prerequisite already completed elsewhere.

## 1. What I have completed

- **C-001 — Local acquisition and dataset audit:** 4,999 source rows, 40 source categories,
  1,338 rows in the five target categories, and 1,329 after removing nine empty target texts.
- Exact source-label mapping, source checksum, provenance/reuse review and a repeatable
  audit script are recorded. Raw and derived CSVs remain local and Git-ignored.
- Preliminary inspection found **46 exact duplicate groups with conflicting target labels,
  covering 92 rows**. This subset is not ready for training; near duplicates and benchmark
  exclusions remain C-002 work.
- Eight synthetic audit tests and real-source regeneration checks passed. These are data
  audit checks, not trained-model, HTTP or shared-contract test results.
- My [response to B](member-c-response-to-b.md) covers canonical text, classification states,
  scores, errors, language handling, scaffold ownership and deployment boundaries.

Evidence: [data audit](data-audit.md), [source manifest](../../data/mtsamples/manifests/source.json)
and [C task backlog](../../specs/003-classification/tasks.md). There are no frozen splits,
trained models, model-quality measurements or implemented classification endpoint yet.

## 2. What B must complete to unblock me

The following are existing dependency gates, not requests for B to implement my classifier.

| Priority / deliverable | What I need from B | Evidence that the gate is satisfied | What it unlocks |
| --- | --- | --- | --- |
| **1. Review decisions and fixtures — F-008** | Resolve C-related interface questions with me; prepare shared positive/negative fixtures and validators. Collect A/D feedback for their interfaces. | Versioned fixtures and executed structural/semantic checks, including invalid hashes, invalid category sets and Unicode cases. | The F-003 freeze. |
| **2. Contract freeze — F-003** | Record actual owner agreement on schema version, request/result fields, classification states/scores, canonicalization and error mappings. | Canonical `contracts/v1` plus `docs/decisions/contract-freeze.md` and passing freeze checks. A draft document alone is insufficient. | One of C-009's two direct prerequisites. |
| **3. Generated bindings — F-009** | Produce shared Python/TypeScript bindings from the frozen schema. | Generated files under `contracts/generated/**`, reproducible generation and compatible shared fixtures. | F-004; avoids a separate handwritten classifier schema. |
| **4. Scaffold — F-004, with F-011 health/readiness** | Coordinate a runnable, key-free foundation with independent service environments, dependency locks, mock behavior and verified Windows commands. Resolve who edits each service before implementation. | Actual installs/startup and checks; frozen bindings available to the classifier project. | F-004 completes the other direct C-009 prerequisite. F-011 contributes to the later runnable checkpoint. |
| **5. Reviewed publication — F-014** | Complete the foundation's startup/smoke, Unicode, ownership, handoff and acceptance gates; publish the reviewed base after explicit commit/push authorization. | Recorded checkpoint, real checks, actual shared commit available to the team and correct working-copy instructions. | C-002, once I also complete C-009; C-003 training follows C-002. |

F-014 requires the full dependency chain in the [foundation backlog](../../specs/000-foundation/tasks.md),
including F-007. A branch name, illustrative JSON or B-only local work does not replace a
reviewed shared base. Publication approval must not be inferred from this report.

### Decisions B and C need to close first

- `uncertain` versus `unsupported`, including when five scores or empty scores are returned.
- Unique category coverage, score order/meaning, and any probability-sum validation tolerance.
- Malformed request, unavailable model and unexpected failure mappings. My proposed 500
  mapping needs B's canonical OpenAPI review; it is not already adopted.
- Common language-validation responsibility and behavior; confidence is not a language detector.
- Classifier scaffold ownership and shared startup integration.

**My proposed scaffold arrangement:** I create the classifier's service files, dependencies,
lockfile and local tests under `services/classifier/**`; B coordinates F-004/F-011 and owns
root configuration, shared contracts and startup. B should record the agreed arrangement.
My scaffold contribution belongs to foundation delivery; it must not depend on C-009,
because C-009 itself requires the scaffold. This remains a proposal, not a task reassignment
or an authorization to edit another owner's files.

## 3. What D must provide, and when

**D's annotations do not block my initial model training.** C-003 depends on C-002,
not C-010. The annotation dependency applies to my annotation task and later final-task gate.

| Timing | D's deliverable | What I need to receive |
| --- | --- | --- |
| Before assignments | D-001 annotation guidance | Entity definitions, assertion/temporality/subject rules, exact code-point evidence rules, repeated-mention handling and separate review instructions. |
| After I deliver C-002 splits | D-002 selection, then D-003 assignments | Frozen document/group IDs, dev/final designations, my primary assignments and separately allocated secondary reviews, permitted source access, submission format and my exact paths. |
| During annotation | Clarification and adjudication process | A way to record uncertain cases without editing another member's submission. D owns canonical adjudication. |
| During shared evaluation planning | Evaluation coordination | Agree the interface for my versioned classification outputs and metric reports; set substantive acceptance thresholds after development measurements and team review. |

D-002 explicitly depends on C-002. Therefore, D cannot finalize assignments from the current
inspection subset. I must first provide the frozen group-disjoint splits. Before model
selection, my assignments must be development-only; final-reference exposure must not become
feedback for choosing models or thresholds. The planning target is ten primary documents
per member, with independent secondary review of at least ten documents across the team.
Those targets are not actual assignments yet.

C-010 becomes ready after D-003. C-008 requires both C-007 and C-010, plus the documented
model-selection freeze. Independent human review must not be claimed from generated output.

## 4. What I need from A and the team

A's complete RAG implementation, embeddings and vector index are **not direct prerequisites
for my classifier training**. A does need to provide interface feedback and the agreed
foundation contribution so B can complete the common checkpoint.

For integration, A/B should preserve specialty as an optional soft hint: no hard filtering,
default specialty forced from an uncertain result, or interpretation as a clinical diagnosis.
The team must review substantive acceptance criteria after measured development results.
Hosting/accounts, operational controls and paid activation remain later decisions; they do
not require buying a service to run the planned local classifier baselines.

## 5. My next steps after each handoff

| Gate received | My next task |
| --- | --- |
| F-003 and F-004, including the generated bindings required by the scaffold | **C-009:** implement and run classifier contract-consumer checks. |
| C-009 completed and F-014 available; C-001 is already complete | **C-002:** group exact/near duplicates, exclude conflicting groups, verify split feasibility, and freeze seeded train/validation/test manifests. |
| C-002 completed | **C-003:** majority and TF-IDF/Logistic Regression baselines; then **C-004:** controlled XGBoost comparison. |
| Development comparisons completed | **C-005:** uncertainty policy and metrics/limitations; **C-006:** packaged inference; **C-007:** startup and integration evidence for B/D. |
| D-003 assignments available | **C-010:** development-only annotations and separate reviews in my owned paths. This can proceed alongside other ready C tasks. |
| C-007 and C-010 completed, with model/configuration selection frozen | **C-008:** locked final measurement and model card; no final-test tuning. |

While waiting, I can continue owned inspection, answer interface questions, and prepare
duplicate-handling and experiment-design proposals within approved scope. These proposals
do not complete C-002, authorize training early, or change the dependency graph.

## 6. Requested team response

Please respond with the following so I can verify readiness and continue the next eligible task:

1. **B:** accepted or revised C interface proposals, recorded scaffold responsibilities,
   current F-003/F-009/F-004 status, and links to artifacts/check results.
2. **B:** the actual reviewed foundation commit and checkpoint when F-014 is completed.
3. **D:** annotation guidance now, followed by assignment details after my C-002 handoff;
   confirm that my pre-selection exposure will remain development-only.
4. **A/B:** confirmation of the soft-specialty-hint behavior during interface agreement.

If any dependency needs to change, record an explicit reviewed change with the responsible
owners. I will not silently bypass a gate or mark a task complete from documentation alone.
No new delivery promises, approved operational limits or team acceptance are inferred here.
