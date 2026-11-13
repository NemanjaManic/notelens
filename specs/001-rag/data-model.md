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
| Prepared corpus artifact (A-002) | Selected topic records, cleaned summaries and stable passages linked to the source snapshot; preparation version, counts and checksums. | Owner-local standard-library pipeline; no API/schema freeze is required to prepare data. Extraction, cleaning and passage increments require their applicable approvals. |
| Passage/index manifest | Stable topic/passage IDs, source text, embedding model/dimensions and index version. | A changed space requires a distinct index build. |
| Relevance proposal | Question, source reference, necessary unique topics/passages and answerability. | D owns canonical development/final QA; A submits proposals, never indexes QA. |
| Retrieval experiment | Frozen settings, development dataset version, ranking/evidence/rejection metrics and costs. | Only development chooses settings; final questions remain held out. |

## Invariants

The original A-002 extraction artifact is UTF-8 JSONL with original logical
`full-summary` HTML, topic identity/title/URL/language, source creation date,
available synonyms, groups and per-topic source attribution/digests. It contains
no site records or evaluation references. The small prepared-corpus manifest
records source/selection/extractor identity, artifact size/checksum and measured
counts. It remains unchanged as the extraction record; its cleaning and passage
counts remain null rather than being rewritten retrospectively.

The separate cleaned artifact retains every original field and adds
`cleaned_summary` and `cleaning` (version, plain-text format, UTF-8 text SHA-256,
table/image/comment counts). The cleaning manifest records 401 cleaned topics,
input manifest/artifact digests, cleaner/script identity, output size/checksum,
and affected topic IDs for tables and omissions. Passage count remains null.
Plain text preserves headings, paragraphs, lists and table cell/row order;
cells are separated by ` | ` and rows by newlines. Lists within a cell retain
`- ` markers on that row, with cell whitespace collapsed. Original HTML remains
available for inspection. Image tags/comments are omitted and counted, without
fetching or inferring image content. HTML character references are decoded once.
No case-folding, stemming, deduplication, translation or medical rewriting occurs.
These are A-owned local formats and do not change the shared API contract.
Original HTML and cleaned plain text must not be inserted as trusted HTML in a UI;
render the cleaned field as text.

The separate passage artifact now contains 617 records over 401 topics. Each
record has topic ID/title/URL/language, creation date, synonyms/groups/source
provenance, a stable `passage_id`, cleaning version, topic-text SHA-256,
`chunking` configuration, `start`, `end`, actual `overlap_code_points` and `text`.
Offsets are half-open Unicode code points in the unchanged `cleaned_summary`;
`text` equals that exact slice. Original HTML and review QA are not copied into
passage records. Source block parsing verifies positions against canonical text;
it does not replace the canonical field with newly normalized text.

Passage IDs hash the configuration/version, complete carried topic metadata,
topic-text digest and offsets, including a topic-ID prefix. Repeated text at
different positions has distinct IDs. The passage manifest links its input
manifest/artifact, script digest, measured counts/checksums and a corpus version
derived from input/output identities and policy. These are local preparation
records, not frozen API bindings, an embedding/index version or retrieval scores.
See [the candidate policy](../../docs/rag/chunking.md). Historical cleaning counts
remain unchanged; actual passage counts live in the new passage manifest.

- Canonical text is unchanged downstream; SHA256 and doc_id bind document results.
- Source spans use code points and exact quote slices; English declarations do not prove language.
- Assertion, temporality and subject remain distinct. ICD only quotes a source code.
- Claim/source identifiers must resolve without cross-document or mixed-result collisions.
- User submissions and document-bound cache/history expire in memory within 60 minutes;
  permitted public training/corpus/benchmark fixtures have separately reviewed provenance.
- Schema checks and semantic support checks are different acceptance measures.

## Configuration and measured values

The owner-local service reader now exposes immutable PreparedCorpus/PreparedPassage
records with lookups by passage and topic ID. It verifies the prepared artifacts and
reuses their exact text/offsets/identities; it does not reconstruct canonical text.
Specialty tags come from the snapshot's explicit selected-topic mapping, including
the approved overrides, and do not create a hard retrieval filter. Optional startup
loading is server-controlled. These are internal preparation records, not additions
to shared API schemas or evidence of a built embedding/index pipeline.

Approved limits are 2,097,152 PDF bytes, 100,000 Unicode code points and at most 60 minutes
from preparation. Exact live budgets/models/timeouts/retries/history/rates remain approval
gates; unset configuration disables dependent live behavior. Data distribution, split/duplicate
criteria and substantive thresholds require measured outputs and recorded decisions.
