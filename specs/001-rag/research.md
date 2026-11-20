# Research: Python RAG

**Owner**: A. **Checked**: 2026-11-10. **Status**: proposed design, not experiment results.

Primary source details and retrieval limitations are recorded in the
[shared feasibility review](../../docs/decisions/technical-feasibility.md).

## Corpus boundary

- **Decision**: English Health Topic summaries and relevant metadata only; measured snapshot/manifests before real ingestion.
- **Rationale**: A topic URL is not proof the selected summary answers a question.
- **Alternatives considered**: Do not follow all links or ingest licensed encyclopedia/drug content.

## Retrieval comparison

- **Decision**: Embedding-only baseline versus lexical/hybrid on the same validation cases; optional reranking only after measured benefit/cost review.
- **Rationale**: Avoid test-set selection and hidden specialty hard filters.
- **Alternatives considered**: Do not introduce complex agent frameworks.

## Generation placement

- **Decision**: Python owns embeddings, index access, retrieval and literature generation; B uses thin HTTP clients.
- **Rationale**: Confirmed workstream boundary.
- **Alternatives considered**: TypeScript RAG duplication violates the source prompt.

## Index compatibility

- **Decision**: Include embedding model/dimensions, preprocessing, corpus and retriever versions; reindex on space changes.
- **Rationale**: Prevents incompatible embeddings mixing.
- **Alternatives considered**: Reusing an incompatible index is prohibited.


## Activation and empirical gates

On 2026-11-14 the user selected OpenAI text-embedding-3-small with 1,536 dimensions
for the first embedding-only baseline and approved local Chroma. The public-corpus
preflight measured 207,790 tokens; its documented price-based estimate is USD 0.0041558.
The separately approved initial live step is capped at USD 0.10, covers the public
corpus and one small probe, uses batches up to 32 and a 30-second timeout, and has
no automatic retries. The key is kept in ignored services/rag/.env. These are
specific local approvals; they do not activate generation or deployment. See
[implementation and pricing sources](../../docs/rag/embeddings.md).

No source facts are inferred from unreadable data pages. Acquisition audits decide actual
counts, permitted redistribution, duplicate/split feasibility and topic/QA evidence.
No other live model ID, account quota, operational policy or quality threshold is
silently chosen. Local mocks need none of the paid/live settings.
This design is complete for local preparation; deployment and live-provider configuration
must remain blocked until the corresponding owner/user approval and actual checks.
