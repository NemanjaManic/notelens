# Research: Python Extraction and Shared Evaluation

**Owner**: D. **Checked**: 2026-11-10. **Status**: proposed design, not experiment results.

Primary source details and retrieval limitations are recorded in the
[shared feasibility review](../../docs/decisions/technical-feasibility.md).

## Entity semantics

- **Decision**: Keep assertion, temporality and subject separate; validate exact spans and independent semantic support.
- **Rationale**: Historical confirmation and family history must not become current patient diagnoses.
- **Alternatives considered**: Generated silver summaries are not entity/status/span ground truth.

## Annotation targets

- **Decision**: 40 documents, 10 primary per member, independent review of at least 10; actual IDs after C manifests.
- **Rationale**: Separate submission paths prevent collisions; D adjudicates.
- **Alternatives considered**: Do not fabricate assignments or claim clinical validation without an expert.

## Test-lock roles

- **Decision**: Before model selection C's primary annotations use development documents; final references must not expose selection feedback to C.
- **Rationale**: Preserves ML test protection while letting D build final extraction references.
- **Alternatives considered**: If actual manifests make assignment infeasible, seek team review before freezing IDs.

## Evaluation targets

- **Decision**: Approximately 80 QA, around 30 multi-source and 10 lacking answers; exact category counts/overlap definitions after review.
- **Rationale**: Necessary topics are question-specific, and source passages must contain evidence.
- **Alternatives considered**: Do not index questions or let an always-refusing system pass.

## Judge/human review

- **Decision**: Approximately 40 generated-answer reviews, 10 per member, plus at least 20 entity-evidence pairs; calibrate on development only.
- **Rationale**: The judge is not the only quality measure; final reviews are for reporting.
- **Alternatives considered**: Do not tune final prompts on the same final reviewed examples.


## Activation and empirical gates

No source facts are inferred from unreadable data pages. Acquisition audits decide actual
counts, permitted redistribution, duplicate/split feasibility and topic/QA evidence.
No live model ID, account quota, price, timeout/retry/rate policy or quality threshold is
silently chosen. Local mocks need none of those paid/live settings.
This design is complete for local preparation; deployment and live-provider configuration
must remain blocked until the corresponding owner/user approval and actual checks.
