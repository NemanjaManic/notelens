# Research: Python Classification

**Owner**: C. **Checked**: 2026-11-10. **Status**: proposed design, not experiment results.

**2026-11-11 audit update**: [C-001 evidence](../../docs/ml/data-audit.md) now records the
supplied CSV checksum, measured mapping/counts and readable Kaggle/upstream reuse sources.
The historical unknowns below describe the original planning state; split parameters,
near-duplicate analysis and model experiments remain unexecuted.

Primary source details and retrieval limitations are recorded in the
[shared feasibility review](../../docs/decisions/technical-feasibility.md).

## Acquisition and reuse

- **Decision**: Support an authorized local CSV; audit release/upstream reuse terms before distribution.
- **Rationale**: Kaggle details were unreadable here; no counts/labels/license can be claimed measured.
- **Alternatives considered**: Do not request credentials in chat or introduce a credentialed dataset.

## Leakage control

- **Decision**: Exact/near-duplicate groups precede splits; conflicting target labels are excluded from the initial benchmark.
- **Rationale**: Avoid train/test overlap and misleading labels.
- **Alternatives considered**: Do not map broad Surgery categories into target specialties.

## Model selection

- **Decision**: Majority baseline, TF-IDF + Logistic Regression, controlled XGBoost comparison; retain the better simpler model.
- **Rationale**: Source prompt explicitly allows a documented change when XGBoost does not win.
- **Alternatives considered**: Do not tune on the final test or manipulate splits.

## Audit-derived parameters

- **Decision**: C documents grouping criteria, feasible split proportions and seed before publishing frozen manifests.
- **Rationale**: Actual class/group counts are unavailable until audit; use an evidence-based decision procedure.
- **Alternatives considered**: Do not invent measured counts or copy source-plan estimates.


## Activation and empirical gates

No source facts are inferred from unreadable data pages. Acquisition audits decide actual
counts, permitted redistribution, duplicate/split feasibility and topic/QA evidence.
No live model ID, account quota, price, timeout/retry/rate policy or quality threshold is
silently chosen. Local mocks need none of those paid/live settings.
This design is complete for local preparation; deployment and live-provider configuration
must remain blocked until the corresponding owner/user approval and actual checks.
