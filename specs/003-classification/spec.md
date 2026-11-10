# Feature Specification: Reproducible Five-Specialty Classification

**Feature Branch**: Not created; feature selection is independent of Git branches.

**Feature Directory**: `specs/003-classification`

**Owner**: C

**Created**: 2026-11-10

**Status**: Draft for user review

**Input**: User description: "Classify permitted English medical documents into the five agreed specialties or an explicit uncertain/unsupported outcome, using leakage-resistant data splits, honest model comparisons and versioned reproducible results."

**Governing requirements**: [Constitution](../../.specify/memory/constitution.md) and
[source prompt](../../prompts/NoteLens_Codex_SpecKit_prompt_00.md). Implementation choices
belong to the later plan and must preserve the confirmed boundaries.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a Specialty With Its Limits (Priority: P1)

As a user, I can see the supported specialty of a report or an explicit uncertain/unsupported
outcome, together with scores and limitations that do not imply a clinical diagnosis.

**Why this priority**: A useful document label must not misrepresent uncertainty.

**Independent Test**: Use standalone permitted example inputs and agreed-record fixtures to
inspect the specialty/state, score meaning and model version without real RAG/extraction/UI.

**Acceptance Scenarios**:

1. **Given** a supported English report, **When** classification succeeds, **Then** the
   result uses the agreed label mapping and identifies the model version.
2. **Given** input below the chosen development-derived acceptance rule or outside scope,
   **When** classification is evaluated, **Then** the agreed uncertain/unsupported policy
   is applied without claiming reliable detection of every unfamiliar input.
3. **Given** a specialty prediction, **When** other modules consume it, **Then** it is
   documented as a soft retrieval signal and never a diagnosis or mandatory source filter.

---

### User Story 2 - Trust the Data Split and Comparison (Priority: P1)

As an evaluator, I can inspect dataset provenance, actual class counts, cleaning decisions,
grouped splits and development comparisons without leakage from duplicate reports.

**Why this priority**: A strong score on contaminated data would be misleading.

**Independent Test**: Reproduce cleaning/group assignments and split manifests from an
authorized local source, then inspect split intersections, conflicting-label exclusions
and development-only model/threshold selection.

**Acceptance Scenarios**:

1. **Given** identical/near-duplicate documents, **When** splits are generated,
   **Then** every group belongs to at most one split.
2. **Given** a group with conflicting target-specialty labels, **When** the initial
   single-label benchmark is assembled, **Then** it is reported and excluded.
3. **Given** development model selection, **When** a more complex candidate performs worse,
   **Then** the better simpler candidate may be retained and the comparison is reported.
4. **Given** label-revealing metadata, **When** training inputs are prepared,
   **Then** it is not used as a hidden predictor.

---

### User Story 3 - Reproduce and Integrate a Frozen Model (Priority: P2)

As a team member, I can run reproducible inference and consume an agreed result while final
measurement stays separate from experimentation.

**Why this priority**: Packaging and frozen evaluation make the model usable by B and D.

**Independent Test**: Run the packaged inference on fixed examples, check deterministic
results/version/labels, and inspect development/final evaluation provenance.

**Acceptance Scenarios**:

1. **Given** the same packaged model and input, **When** inference is repeated,
   **Then** the documented deterministic result remains consistent.
2. **Given** frozen model selection, **When** the locked final test is run,
   **Then** actual metrics, sample counts and limitations enter the English model card.
3. **Given** no trained model yet, **When** integration proceeds,
   **Then** C supplies clearly identified mocks without claiming training is complete.

### Edge Cases

- Missing local data, acquisition requiring authentication, absent license/provenance.
- Empty texts, rare classes, impossible stratification or conflicting duplicate labels.
- Broad source categories such as Surgery that must not be relabeled as target specialties.
- Out-of-scope/non-English inputs, tiny notes or distribution shift from another dataset.
- Uncalibrated scores, tied/low scores, changed label mapping or incompatible model artifacts.
- Failed inference, missing artifact/version or accidental final-test access.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Own MTSamples acquisition/audit, provenance, release/upstream reuse review,
  attribution, version/checksum manifest, deterministic cleaning and measured distributions.
- **FR-002**: Support a manually supplied local CSV if authenticated acquisition is required.
  Never request credentials in chat or redistribute data before reuse review.
- **FR-003**: Restrict the benchmark to Cardiovascular / Pulmonary, Orthopedic,
  Gastroenterology, Neurology and Urology; verify exact source labels and publish their mapping.
- **FR-004**: Measure counts before/after cleaning; remove empty texts and report exclusions.
  Do not reuse unmeasured counts from source plans or merge broad labels into target labels.
- **FR-005**: Detect identical/near-duplicate groups before splitting using a documented
  reproducible method; keep each group within one split.
- **FR-006**: Identify conflicting target-specialty labels in a group, report them and
  exclude those cases from the initial single-label benchmark.
- **FR-007**: Publish separate seeded train/validation/test manifests with document/group
  IDs and feasible stratified proportions; document feasibility constraints.
- **FR-008**: Fit all learned transformations only on training data; do not use
  label-revealing metadata as hidden predictors.
- **FR-009**: Supply a majority baseline and a strong simple baseline, and compare the
  required candidate from the source prompt under controlled validation conditions.
  Optional higher-cost variants depend on time/cost and MUST NOT block core classification.
- **FR-010**: Report macro-F1, per-class precision/recall/F1, class support, confusion matrix,
  error analysis and baseline comparison. Retain the better simpler model when appropriate.
- **FR-011**: Select model, score thresholds and uncertain/unsupported behavior on
  development/validation data. Keep final tests locked until the frozen final measurement.
- **FR-012**: Explain score meaning, confidence/calibration limitations and distribution
  shift; raw scores are not proof of calibration or clinical truth.
- **FR-013**: Package preprocessing and inference together with model version, label mapping
  and deterministic behavior; satisfy B's canonical result/error definitions.
- **FR-014**: Return a supported category or explicit uncertain/unsupported outcome with
  scores and version. Do not invent diagnoses or claim universal unfamiliar-input detection.
- **FR-015**: Do not alter prepared canonical text or require ICD codes. Classification
  mistakes MUST NOT permanently exclude downstream retrieval sources.
- **FR-016**: Deliver local contract/smoke checks, permitted non-sensitive examples,
  startup instructions to B and evaluation integration instructions to D.
- **FR-017**: Publish stable split/group IDs so D can select annotation documents before
  all final models are complete; do not make all evaluation wait for final classification.
- **FR-018**: Complete assigned annotations and separate independent reviews only under
  member-c paths; D coordinates assignments and canonical reference adjudication.
- **FR-019**: After model selection, run the locked final test and report actual results,
  versions, sample counts and limitations in an English model card.
- **FR-020**: Compare changes honestly; regressions or changes to original demo expectations
  require documented team review, not test leakage or benchmark manipulation.
- **FR-021**: Optional supplementary datasets MUST be separately reported; do not assume
  reliable transfer to a different document distribution. Credentialed clinical datasets
  and mandatory export formats outside the prompt MUST NOT be introduced.

### Key Entities *(include if feature involves data)*

- **Source release**: Dataset version/checksum, provenance, license/reuse review and attribution.
- **Clean document/group**: Stable IDs, source/clean text references, labels and exclusion reasons.
- **Split manifest**: Seed, feasible proportions and train/validation/test group assignments.
- **Model experiment**: Candidate/preprocessing versions, development measurements and selection reason.
- **Classification result**: Specialty or uncertain/unsupported state, scores, version and limitations.
- **Model card**: Actual development/final metrics, support, error analysis and limits.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The audit reports actual before/after counts, exact mapping for all five
  target labels, exclusion reasons and a versioned source manifest.
- **SC-002**: No published document group appears in more than one split; every conflicting
  target-label group is reported/excluded from the initial single-label benchmark.
- **SC-003**: Development reports include all required metrics, support, baseline/candidate
  comparisons and recorded selection reasons without locked-final-test selection.
- **SC-004**: All classification outputs in the defined structural suite satisfy agreed
  records, label mapping, version and explicit uncertain/unsupported handling.
- **SC-005**: Packaged inference is reproducible on fixed versioned examples, and B/D can
  consume its documented mock/real interface independently of other completed modules.
- **SC-006**: Frozen final results appear with actual sample counts, versions and limitations;
  no numeric quality threshold is claimed agreed before measured team review.

## Assumptions

- Target labels are confirmed; exact source strings/counts, grouping parameters and split
  proportions require C's audit and published evidence.
- Model candidates are confirmed by source prompt sections 4 and 7C; the implementation
  plan must preserve the required comparisons without forcing a more complex model to win.
- B's contract freeze and D's assignment/evaluation coordination are cross-workstream
  dependencies, not permission to edit their files.
- Data, training, inference and final evaluation are not implemented by this specification.