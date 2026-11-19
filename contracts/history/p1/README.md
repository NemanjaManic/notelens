# Contract v1 Proposal

**Status**: DRAFT, not frozen. **Owner**: B. **Required reviewers**: A/B/C/D.
The approved planning package proposes shared records, not service implementations.
B must collect owner feedback and record agreement before the contract freeze.

## Source of truth

[JSON Schema](schema.json) is the proposed canonical definition set.
[OpenAPI](openapi.json) references it without maintaining a second model definition.
The formats are JSON Schema Draft 2020-12 and OpenAPI 3.1.1.
The wire version 1.0.0 is proposed, not ratified. Bindings and representative fixtures
are later B-owned generated deliverables; do not maintain divergent TypeScript/Python models.

## Operations

| Operation | Producer | Input | Output |
| --- | --- | --- | --- |
| `POST /v1/classify` on classifier | C | ClassificationRequest | ClassificationResult |
| `POST /v1/extract` on extraction | D | ExtractionRequest | ExtractionResult |
| `POST /v1/document-answer` on extraction | D | DocumentQuestionRequest | AnswerResult |
| `POST /v1/retrieve` on rag | A | RetrievalRequest | RetrievalResult |
| `POST /v1/literature-answer` on rag | A | LiteratureAnswerRequest | AnswerResult |

Proposed configurable local ports: web 3000, A 8001, C 8002, D 8003.
These loopback origins are not deployed URLs. B prepares documents and checks session
ownership/expiry before forwarding canonical text. A receives questions and optional
concepts/soft specialty hints, not documents to ingest into its corpus.

## Canonicalization proposal: nfc-lf-v1

1. Reject malformed text/surrogate code points; do not hash replacement-garbled input.
2. Remove at most one leading U+FEFF; replace CRLF and CR with LF; normalize NFC.
3. Preserve other whitespace and case. Reject empty/whitespace-only content.
4. Reject more than 100,000 Unicode code points; never truncate.
5. SHA256-hash exact canonical UTF-8 bytes without a BOM; encode lowercase hexadecimal.
6. Assign an opaque per-submission doc_id. The hash is not an access token or session key.

Downstream modules never normalize/trim/repair canonical text.
B rejects stale doc_id/digest combinations. Browser string indices are UTF-16 code units;
Python indices use code points for valid scalar text. B must convert indices explicitly.

## Validation beyond the schema

Require half-open spans [start,end), 0 <= start < end <= code-point text length,
and exact quote equality. Foundation examples must include an emoji before evidence and
the second of two equal passages. JSON Schema does not verify slices, digests, source
semantics, English compliance or foreign-key relationships; runtime checks must do so.

Claim/source IDs are unique within a result; every source_id resolves to an included source.
A document_fact claim needs selected-document evidence; literature never proves a patient's
condition. Validate semantic support separately from quote existence. Document/literature
routes contain matching source kinds. Mixed may return only the supported portion with
partial evidence and warnings. Route none has no claims/sources and insufficient evidence.
Language en is a declaration, not proof that text is English.

Extraction assertion: confirmed|suspected|negated. Temporality: current|historical|unknown.
Subject: patient|family|other|unknown. ICD is optional and must quote an actual source code.
Empty items are valid; they do not prove the report lacks medical content.

Classification uses five confirmed display labels; C audits exact source mapping separately.
Supported requires one category and one score per category; other states have null category.
Validate category uniqueness. Probability scores lie in [0,1]; decision scores may be signed
and unbounded. Score kind, model version and confidence_note are mandatory; calibration
and clinical certainty must not be implied.

## Errors and partial results

Evidence insufficiency normally returns a valid 200 result, not a provider-error success.
A retrieval error result must contain ErrorDetail; a transport failure uses ErrorEnvelope.
Both remain distinct from a correct semantic rejection. B retains independently supported
document content when A fails. Safe English errors contain no secrets, bodies or traces.

| Outcome | Proposed status |
| --- | --- |
| Invalid request | 400 or 422 |
| Missing/invalid service token | 401 |
| Missing, expired or other-session document | Identical safe 404 document_unavailable |
| Oversized input | 413 |
| Unsupported file | 415 |
| Local/provider rate limit | 429 |
| Invalid upstream record | 502 |
| Provider/configuration/budget unavailable | 503 |
| Bounded request deadline exceeded | 504 |

Timeout, retry, history and rate-limit values require later approval; no values are assumed.
Server configuration controls mock/live mode. A browser cannot enable paid calls.
Exposed services require server-to-server authentication; key-free loopback mocks must
never become unauthenticated public services.

## Retention

User-approved on 2026-11-10: submitted documents stay in application server memory only,
for at most 60 minutes from preparation, deleted on expiry or restart. PDF limit:
2 MiB (2,097,152 bytes); text limit: 100,000 Unicode code points. Reject rather than truncate.

B removes document-bound results/history/cache entries on expiry, so text cannot be
resurrected. Do not persist submissions in indexes, logs, disk caches, static generation
or evaluation artifacts. Built-in public/synthetic fixtures and separately authorized
benchmark data are distinct from user submissions. Services process forwarded documents
without retaining request bodies. Recheck expiry before storing/displaying in-flight output.
Use a controlled clock to test expiry rather than waiting an hour.

Third-party retention/data-use terms require review before live activation. This local
application policy does not promise control over a provider's data retention.

## Review and freeze

Resolve field/enum/canonicalization proposals with all owners. B then records agreement,
version, fixtures, generated bindings and checks for mock objects and actual HTTP payloads.
Negative fixtures must fail for the intended schema or semantic reason.
This proposal does not claim those fixture/validator/binding implementations already exist.
