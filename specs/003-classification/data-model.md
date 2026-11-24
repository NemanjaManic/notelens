# Data Model: Python Classification

**Owner**: C. **Status**: Shared records frozen through F-003/F-009; owned training/data entities remain design proposals.

## Shared records

Use [contracts/v1](../../contracts/v1/README.md) as the frozen canonical boundary.
- `PreparedDocument` is defined once in `contracts/v1/schema.json#/$defs/PreparedDocument`.
- `ClassificationRequest` is defined once in `contracts/v1/schema.json#/$defs/ClassificationRequest`.
- `ClassificationResult` is defined once in `contracts/v1/schema.json#/$defs/ClassificationResult`.
- `ErrorEnvelope` is defined once in `contracts/v1/schema.json#/$defs/ErrorEnvelope`.
Do not introduce a second hand-maintained language schema. B's generated bindings are
available in `contracts/generated/python`; C's local scaffold consumes their TypedDicts
and runtime validators. Schema/behavior changes still require B's shared review process.

## Owned entities and states

| Entity | Attributes and relationships | Validation/lifecycle |
| --- | --- | --- |
| Dataset release | Source checksum/version, local input, upstream conditions, schema and before/after class counts. | Audit before redistribution; exact source-label mapping is a required measured output. |
| Document/group manifest | Stable doc/group IDs, label, exact/near-duplicate method and conflict/exclusion reason. | One group in one split only; no hidden metadata predictors. |
| Model artifact | Training-only fitted preprocessing, estimator, label mapping, versions and uncertainty policy. | Development selection -> frozen -> locked final measurement. |
| Model card | Support, macro/per-class metrics, confusion matrix, error analysis and confidence/OOD limitations. | Report actual results and source versions, not planned thresholds. |

## Invariants

- Canonical text is unchanged downstream; SHA256 and doc_id bind document results.
- Source spans use code points and exact quote slices; English declarations do not prove language.
- Assertion, temporality and subject remain distinct. ICD only quotes a source code.
- Claim/source identifiers must resolve without cross-document or mixed-result collisions.
- User submissions and document-bound cache/history expire in memory within 60 minutes;
  permitted public training/corpus/benchmark fixtures have separately reviewed provenance.
- Schema checks and semantic support checks are different acceptance measures.

## Configuration and measured values

Approved limits are 2,097,152 PDF bytes, 100,000 Unicode code points and at most 60 minutes
from preparation. Exact live budgets/models/timeouts/retries/history/rates remain approval
gates; unset configuration disables dependent live behavior. Data distribution, split/duplicate
criteria and substantive thresholds require measured outputs and recorded decisions.
