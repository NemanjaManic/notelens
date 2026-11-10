# Data Model: Python RAG

**Owner**: A. **Status**: proposal pending cross-owner review.

## Shared records

Use [contracts/v1](../../contracts/v1/README.md) as the only proposed canonical boundary.
- `RetrievalRequest` is defined once in `contracts/v1/schema.json#/$defs/RetrievalRequest`.
- `RetrievalResult` is defined once in `contracts/v1/schema.json#/$defs/RetrievalResult`.
- `LiteratureAnswerRequest` is defined once in `contracts/v1/schema.json#/$defs/LiteratureAnswerRequest`.
- `AnswerResult` is defined once in `contracts/v1/schema.json#/$defs/AnswerResult`.
- `ErrorEnvelope` is defined once in `contracts/v1/schema.json#/$defs/ErrorEnvelope`.
Do not introduce a second hand-maintained language schema. Generated bindings are a
future B-owned contract-freeze deliverable.

## Owned entities and states

| Entity | Attributes and relationships | Validation/lifecycle |
| --- | --- | --- |
| Corpus snapshot | Snapshot date, checksums, topic IDs, language, titles, URLs, synonyms and attribution. | Source/licensing review before redistribution; counts measured after acquisition. |
| Passage/index manifest | Stable topic/passage IDs, source text, embedding model/dimensions and index version. | A changed space requires a distinct index build. |
| Relevance proposal | Question, source reference, necessary unique topics/passages and answerability. | D owns canonical development/final QA; A submits proposals, never indexes QA. |
| Retrieval experiment | Frozen settings, development dataset version, ranking/evidence/rejection metrics and costs. | Only development chooses settings; final questions remain held out. |

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
