# Data Model: Python Extraction and Shared Evaluation

**Owner**: D. **Status**: proposal pending cross-owner review.

## Shared records

Use [contracts/v1](../../contracts/v1/README.md) as the only proposed canonical boundary.
- `PreparedDocument` is defined once in `contracts/v1/schema.json#/$defs/PreparedDocument`.
- `ExtractionRequest` is defined once in `contracts/v1/schema.json#/$defs/ExtractionRequest`.
- `ExtractionResult` is defined once in `contracts/v1/schema.json#/$defs/ExtractionResult`.
- `DocumentQuestionRequest` is defined once in `contracts/v1/schema.json#/$defs/DocumentQuestionRequest`.
- `AnswerResult` is defined once in `contracts/v1/schema.json#/$defs/AnswerResult`.
- `ErrorEnvelope` is defined once in `contracts/v1/schema.json#/$defs/ErrorEnvelope`.
Do not introduce a second hand-maintained language schema. Generated bindings are a
future B-owned contract-freeze deliverable.

## Owned entities and states

| Entity | Attributes and relationships | Validation/lifecycle |
| --- | --- | --- |
| Annotation assignment | Document/group/split ID, primary member, distinct secondary reviewer, immutable submission references. | Draft -> feasibility-reviewed -> frozen -> annotated -> adjudicated. |
| Reference set | Exact/relaxed matching rules, entity assertion/temporality/subject, evidence and adjudication version. | Group-separated development/final material; distinguish human review from clinical validation. |
| QA case | Required source kinds, necessary unique topics/passages, answerability and possibly overlapping categories. | Candidate -> snapshot-reviewed -> development/final frozen; QA never enters index. |
| Evaluation run | Input/model/prompt/index versions, counts, deterministic scores, calibrated reviews, costs and limitations. | Mock/offline/live separated; final repeat needs new version and documented reason. |
| Threshold decision | Named metric entries initially unset, first development measurement and recorded team acceptance. | Target 2026-11-14; never lower thresholds merely to pass. |

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
