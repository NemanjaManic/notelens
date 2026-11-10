# Data Model: Shared Foundation

**Owner**: B. **Status**: proposal pending cross-owner review.

## Shared records

Use [contracts/v1](../../contracts/v1/README.md) as the only proposed canonical boundary.
- `PreparedDocument` is defined once in `contracts/v1/schema.json#/$defs/PreparedDocument`.
- `ClassificationResult` is defined once in `contracts/v1/schema.json#/$defs/ClassificationResult`.
- `ExtractionResult` is defined once in `contracts/v1/schema.json#/$defs/ExtractionResult`.
- `RetrievalRequest` is defined once in `contracts/v1/schema.json#/$defs/RetrievalRequest`.
- `RetrievalResult` is defined once in `contracts/v1/schema.json#/$defs/RetrievalResult`.
- `AnswerResult` is defined once in `contracts/v1/schema.json#/$defs/AnswerResult`.
- `ErrorEnvelope` is defined once in `contracts/v1/schema.json#/$defs/ErrorEnvelope`.
Do not introduce a second hand-maintained language schema. Generated bindings are a
future B-owned contract-freeze deliverable.

## Owned entities and states

| Entity | Attributes and relationships | Validation/lifecycle |
| --- | --- | --- |
| Contract proposal | Version, schema definitions, source meanings, safe errors, consumer review status. | Draft -> owner-reviewed -> frozen; only B publishes canonical changes. |
| Foundation fixture | Permitted synthetic/public text, expected record, intended negative-check reason. | Never confuse with trained/live outputs or real clinical ground truth. |
| Checkpoint | Artifact inventory, executed mock checks, actual branch/commit state and handoffs. | Unreached until runnable checks and prerequisites pass. |
| Member handoff | Owned paths, exact feature, first five task sequence, examples and commands. | Produced after commands actually exist; no invented npm scripts. |

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
