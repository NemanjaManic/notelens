# Data Model: Complete Frontend and Integration

**Owner**: B. **Status**: proposal pending cross-owner review.

## Shared records

Use [contracts/v1](../../contracts/v1/README.md) as the only proposed canonical boundary.
- `PreparedDocument` is defined once in `contracts/v1/schema.json#/$defs/PreparedDocument`.
- `ClassificationResult` is defined once in `contracts/v1/schema.json#/$defs/ClassificationResult`.
- `ExtractionResult` is defined once in `contracts/v1/schema.json#/$defs/ExtractionResult`.
- `DocumentQuestionRequest` is defined once in `contracts/v1/schema.json#/$defs/DocumentQuestionRequest`.
- `RetrievalRequest` is defined once in `contracts/v1/schema.json#/$defs/RetrievalRequest`.
- `AnswerResult` is defined once in `contracts/v1/schema.json#/$defs/AnswerResult`.
- `ErrorEnvelope` is defined once in `contracts/v1/schema.json#/$defs/ErrorEnvelope`.
Do not introduce a second hand-maintained language schema. Generated bindings are a
future B-owned contract-freeze deliverable.

## Owned entities and states

| Entity | Attributes and relationships | Validation/lifecycle |
| --- | --- | --- |
| Document session | Opaque session/document IDs, canonical document, created_at/expires_at, processing state and owned results. | Prepared -> processing -> ready/partial/error -> expired/deleted; never renew beyond 60 minutes. |
| UI state | English loading/empty/error/unsupported/insufficient/mock/live status. | Unknown/expired/other-session document gets the same safe unavailable result. |
| Claim graph | Module-local source/claim IDs, namespaced in mixed output, selected doc hash and route. | Preserve links; reject stale outputs; do not let ID collisions attach a claim to another source. |
| Operational configuration | Approved limits, live-mode flag, timeout/retry/history/rate policies, budget and service origins. | Unconfigured live execution fails closed; exact values need later approval. |

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
