# Member B Interface Review - C Review Copy

**Prepared by B**: 2026-11-11. **C update**: 2026-11-11.
**Ownership**: B retains the original guide; this C-owned review copy contains proposed C-related amendments.
**Contract status**: DRAFT; version 1.0.0 is proposed, not frozen.
**Team acceptance**: pending. C feedback is incorporated below as proposals; no B acceptance, A/D agreement or contract freeze is claimed.

This guide explains B's job and the current interface proposal. It is not a second
schema, an implemented API, a completed foundation, or a record of clinical validation.
The original B document describes a package on `member-b/task-contract-review`.
This review copy is stored under C-owned `docs/ml/` for B to consider and incorporate.
It does not complete F-008, F-003, F-009, F-004, B-010 or C-009.
See the [full C response](member-c-response-to-b.md) and [C status/dependency report](member-c-status-and-dependencies.md).

## 1. Read the project as a complete user journey

NoteLens is an educational demonstration for understanding English medical reports.
Built-in public examples are the primary demo. Permitted public/synthetic text and
text-based PDFs are additional inputs. Final delivery remains **2026-11-24**.
The application must display demo, not-a-doctor, and no-real-personal-report notices.

1. **B accepts input.** Validate supported input, reject excess/unsupported content,
   and explain empty or scanned PDFs in English. No OCR or translation is in scope.
2. **B prepares the document once.** Produce canonical text, an opaque submission ID,
   its SHA256 digest, and source metadata; associate it with its session in memory.
3. **C classifies the document.** Return a specialty or uncertain/unsupported outcome.
4. **D extracts and summarizes.** Return findings, their source passages, and a short
   evidence-linked summary. C and D receive the same unchanged prepared text.
5. **B displays the analysis.** Show text, specialty, findings, summary, versions,
   evidence, and explicit processing/empty/partial/error states. Do not hide D's
   supported output merely because C is uncertain or another component fails.
6. **B routes a question.** D answers document questions; A answers literature questions.
   Mixed questions need both contributions with their source meanings preserved.
7. **B displays supported claims.** Link each claim to its sources and show evidence
   gaps. A general literature statement cannot establish a patient-specific fact.
8. **B expires the submission.** Remove document-bound content, results, history, and
   caches no later than 60 minutes from preparation, or earlier on process loss.

The shared foundation remains a documentation handoff without a runnable web application,
service implementations, service mocks or generated bindings. C has since completed the
local C-001 dataset audit, with working audit commands and checks; these are not application
runtime or classifier-service checks.
See the [handoff decision](../decisions/initial-documentation-handoff.md).
The original source PDFs are absent; this review uses the supplied requirements prompt
and repository documents, not a claimed reading of those PDFs.

## 2. B's responsibilities and boundaries

| Area | B's deliverable | Dependencies and responsibility boundary |
| --- | --- | --- |
| Shared contracts | Coordinate proposals, examples, checks, agreement, version freeze, and generated bindings. | A/C/D review what their services consume/produce; B maintains the canonical files after agreement. |
| Document preparation | Input validation, PDF text preparation in memory, canonical text, ID/hash, and source metadata. | No downstream text normalization; parser choice and unsupported-language handling still need implementation decisions. |
| Full frontend | Input, document viewer, specialty, findings, summary, chat, sources, notices, and all English states. | Begin against agreed mocks; show mock origin visibly. |
| Integration | Server-side HTTP clients, routing, document/request association, partial results, and claim/source preservation. | A owns retrieval and literature generation; D owns extraction, summaries, and document generation. |
| Sessions and configuration | Session ownership, absolute expiry, bounded history, secrets, safe errors/logs, and guarded live mode. | Keep approved privacy limits; resolve remaining controls before dependent implementation. |
| Security and CI | Deterministic contract/scope/integration checks and defined upload, isolation, injection, XSS, secrets, and logging checks. | A finite passing suite is not a claim of universal security; live paid CI stays off by default. |
| Runtime and deployment | Local startup, readiness, service authentication, approved hosting/runbooks, and rehearsal evidence. | Hosting, accounts, provider retention, budget, and operational limits are not approved by this review. |
| Evaluation participation | B's assigned annotations and independent reviews, plus generated-output review contributions. | D publishes assignments and adjudicates; B only edits B's own annotation/review paths. |

The proposed app uses Next.js/TypeScript with three independent Python/FastAPI services.
C owns model training/inference and MTSamples preparation. A owns all corpus ingestion,
chunking, embeddings, vector-store access, retrieval, and literature answers. D owns
extraction, summaries, document answers, annotation coordination, and shared evaluation.

The annotation target is 40 primary documents across the team, planned as ten per member.
Assignment IDs and dev/final portions must come from D. Approximately ten generated-answer
reviews per member are a separate planning target, not already assigned/completed work.
Do not select models/prompts/thresholds using locked final references.

Use the [allowed-path matrix](../team/allowed-paths.md). Current ownership applies even
before the runnable checkpoint: B's coordinator role is not a cross-owner editing grant.

## 3. How to read the shared contract files

The [contract README](../../contracts/v1/README.md) explains the intended behavior.
The [JSON Schema](../../contracts/v1/schema.json) is the proposed structural source of
truth. [OpenAPI](../../contracts/v1/openapi.json) maps HTTP operations to those same
definitions. There are currently 22 schema definitions and five proposed POST operations.
Both JSON files parse; this alone does not validate their schemas or API behavior.

| Layer | What it can establish | What requires more work |
| --- | --- | --- |
| JSON Schema | Fields, types, required values, enums, and defined conditional rules. | Cross-record IDs, exact quotes, hashes, source support, and whether text is English. |
| OpenAPI | Operation paths, request/response references, proposed statuses, and bearer authentication declaration. | Working endpoints, enforced authentication, transport behavior, and runtime compatibility. |
| Exact-text/relationship checks | Digest equality, valid code-point spans, exact canonical quotes, unique IDs, resolved citations, and matching document context. | Whether a quoted passage actually supports the meaning of a claim. |
| Source-support review | Whether findings/claims preserve source meaning, assertion, temporality, and subject. | Human/team acceptance and measured quality still require actual review/evaluation. |

The wire version and canonicalization version are contract fields. Model, prompt,
retriever, and index versions describe how outputs were produced. One does not replace
another. Generated TypeScript/Python bindings are future derived artifacts, not a reason
to maintain competing handwritten schemas in the services.

### 3.1 Operations B integrates

| Service owner / operation | Request | Response and B's responsibility |
| --- | --- | --- |
| C: `POST /v1/classify` | `ClassificationRequest`: schema version and prepared document. | `ClassificationResult`: validate ID/hash, specialty state, category, score kind/meaning, and model version; display limitations. |
| D: `POST /v1/extract` | `ExtractionRequest`: schema version and the same prepared document. | `ExtractionResult`: validate document association, findings, spans, summary claims/sources, and versions; render exact evidence. |
| D: `POST /v1/document-answer` | `DocumentQuestionRequest`: schema version, prepared document, question, optional history. | `AnswerResult`: preserve document citations and associate the response with the original request/document. |
| A: `POST /v1/retrieve` | `RetrievalRequest`: schema version, question, optional concepts and specialty hint. | `RetrievalResult`: passages, score explanation, versions, and sufficient/insufficient/error state. Relevant to retrieval inspection/evaluation; not a command for B to implement RAG. |
| A: `POST /v1/literature-answer` | `LiteratureAnswerRequest`: currently the same definition as `RetrievalRequest`. | `AnswerResult`: A performs literature-grounded generation; B checks/presents claim-source relationships. |

Proposed configurable local origins are web 3000, A 8001, C 8002, and D 8003. These are
local proposals, not deployments. The five operations describe internal service APIs;
browser-facing upload/session/chat routes are not yet specified by this OpenAPI proposal.

B's server checks session ownership and expiry before forwarding a document. A receives
questions/concept hints; user submissions must not be ingested into A's literature index.
Specialty is a soft retrieval hint, so an incorrect category cannot exclude relevant topics.

### 3.2 Canonical text, identities, and expiry

The proposed `nfc-lf-v1` preparation is:

1. Reject malformed Unicode/surrogate code points.
2. Remove at most one leading U+FEFF, convert CRLF/CR to LF, and normalize to NFC.
3. Preserve other whitespace and case; reject empty/whitespace-only content.
4. Reject more than 100,000 Unicode code points; do not truncate.
5. Hash exact canonical UTF-8 bytes without a BOM; use lowercase SHA256 hexadecimal.
6. Assign an opaque per-submission `doc_id` and bind access to its session.

The digest identifies text; neither a digest nor a document ID grants access. C/D must
not trim, normalize, or repair canonical text. B must reject stale or mismatched results.
The PDF byte limit is **2,097,152 bytes**; it is independent of the canonical-text limit.

Submitted content stays in server memory only, for at most 60 minutes from preparation.
Do not renew that absolute lifetime through activity. No submission bodies in logs,
filesystem/static caches, browser localStorage, indexes, or evaluation artifacts. Public
built-in examples are distinct from submissions. Delete related results/history/cache
entries on expiry/restart, and recheck expiry before accepting in-flight results.
Unknown, expired, and other-session IDs share the safe `404 document_unavailable` outcome.
Third-party retention needs its own live-activation review.

### 3.3 Extraction, classification, and answer meanings

- Extraction `type`: diagnosis, symptom, or procedure. Optional ICD may only copy an
  explicitly present source code with evidence; it is not required for the core flow.
- `assertion`: confirmed, suspected, or negated. `temporality`: current, historical,
  or unknown. `subject`: patient, family, other, or unknown. Keep these independent.
- A historically confirmed condition remains confirmed and historical. A family member's
  condition must not become a patient condition. Missing context must not be invented.
- Empty extraction items are structurally valid; they do not establish an absence of
  medical content. Entity IDs and source/claim IDs need relationship checks.
- Classification `supported` needs one of the five categories and five scores, one per
  category. `uncertain`/`unsupported` require a null category. Category uniqueness is
  an additional check. Probability scores lie in [0,1]; decision scores may be signed
  and unbounded. Neither is clinical certainty or proof of calibration.
- `AnswerResult` carries English text, claims, sources, evidence state, route, warnings,
  mode, and versions. Each claim links to included sources through `source_ids`.
- Document/literature routes retain their source kinds. A sufficient mixed answer needs
  both kinds; a partial mixed answer may retain only the supported portion and state gaps.
  Route `none` has insufficient evidence and empty claims/sources.
- When B combines outputs, namespace colliding claim/source IDs and rewrite links together.
  Validate the combined record. B preserves supported service content without generating
  new medical conclusions. The routing/combination mechanism still needs an agreed design.

### 3.4 C update: measured data and proposed classifier behavior

**Measured C-001 status:** the supplied local CSV contains 4,999 rows; 1,338 belong to the
five target specialties and 1,329 remain after removing nine empty target transcriptions.
Counts are Cardiovascular / Pulmonary 371, Orthopedic 355, Gastroenterology 224, Neurology
223 and Urology 156. The exact source labels each have a leading space; no enum changes
or broad-label merges are needed. See [C's data audit](data-audit.md).

There are 46 preliminary exact duplicate groups with conflicting target labels, covering
92 rows. The current subset is not a frozen benchmark. C-002 must handle near duplicates,
exclude conflicting groups and establish reproducible group-disjoint splits. Eight
synthetic audit tests and source-regeneration checks passed; no model/API checks ran.

**C proposals for B's agreement:**

- Preserve canonical input text and return its original ID/hash. Derive model features
  internally; do not alter or repair the document. Fit learned preprocessing on train only.
- `supported`: selected category and exactly five finite scores, one per target category.
  `uncertain`: null category and all five computed scores. `unsupported`: null category,
  with empty scores if inference was skipped or five scores if it ran; explain the reason.
- Low confidence alone means uncertainty, not proof of unsupported input. Select thresholds
  on development data. Probability scores are not clinical certainty or proven calibration.
- Use an error envelope for malformed requests, model/configuration failures and runtime
  failures. Missing model artifacts must not trigger mock fallback or a successful
  uncertain result. C proposes 400 for malformed JSON, 422 for invalid fields/hash/empty
  text, 413 for oversized text, and 503 for unavailable model configuration.
- C proposes 500 / `internal_error` for unexpected classifier failures. B must review the
  missing 500 entry in the canonical API. The local API already includes 502; B should use
  it when rejecting an invalid upstream classifier result. Full mappings are in C's response.
- C proposes common language validation at B's preparation boundary, with rejected
  non-English input using `unsupported_language` and proposed HTTP 422. The detection
  method is unresolved; `language: en` and classifier confidence are not language checks.
- C proposes creating the classifier scaffold, health/readiness, tests and local dependency
  lockfile in its own service paths. B coordinates F-004/F-011, shared contracts and startup.
  Record this ownership before execution. The foundation scaffold contribution precedes
  C-009, which depends on the scaffold; do not introduce a circular dependency.
- Exposed classifier services use the agreed server-to-server authentication; local key-free
  mocks stay on loopback. No submitted text is retained in service logs or files. Hosting,
  operational limits and deployment remain separate unresolved gates.

No A/D interface choices are adopted by this C update. C's category remains a soft retrieval
hint; uncertain or failed classification must not suppress independent supported outputs.

## 4. Worked synthetic exchange

All examples below are **documentation illustrations**. No classifier, extractor,
retriever, model, or provider ran. `mode: mock` describes invented protocol examples,
not an implemented mock service. Example version strings are fixture identifiers.
The source deliberately repeats and contradicts statements to exercise evidence handling;
it is not a realistic clinical narrative. No patient identity or clinical interpretation
is implied. Assertion is illustrated; subject and temporality stay unknown where unstated.

### 4.1 PreparedDocument produced by B

```json
{
  "schema_version": "1.0.0",
  "doc_id": "illustrative-document",
  "text": "Demo \ud83e\ude7a\nNo chest pain.\nChest pain is suspected.\nNo chest pain.",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "canonicalization_version": "nfc-lf-v1",
  "source": {"kind": "synthetic_text", "name": "Illustrative handoff text"},
  "language": "en"
}
```

JSON escapes encode one U+1FA7A character, not two document characters. The decoded text
has 61 code points and 62 UTF-16 code units. It matches the synthetic text in B's handoff.

| Passage | Code-point interval [start,end) | Browser UTF-16 interval [start,end) |
| --- | --- | --- |
| First `No chest pain.` | [7,21) | [8,22) |
| `Chest pain is suspected.` | [22,46) | [23,47) |
| Second `No chest pain.` | [47,61) | [48,62) |

For the second denial, the wire evidence is `start: 47, end: 61`. B converts it to
UTF-16 indices 48 and 62 to slice/highlight in JavaScript. Sending 48 and 62 as wire
offsets is invalid. Finding only the first matching quote also loses the intended occurrence.

### 4.2 Request construction for all five operations

The Python fragment shows object construction only; it makes no HTTP requests. Here,
`prepared_document` means the parsed JSON object above. Required fields are included;
no session token or live-provider configuration belongs in these document records.

```python
classification_request = {"schema_version": "1.0.0", "document": prepared_document}
extraction_request = {"schema_version": "1.0.0", "document": prepared_document}
document_question_request = {
    "schema_version": "1.0.0",
    "document": prepared_document,
    "question": "What statements about chest pain appear in this text?",
    "history": [],
}
retrieval_request = {
    "schema_version": "1.0.0",
    "question": "What does suspected mean in this synthetic example?",
    "concepts": ["suspected"],
    "specialty_hint": None,
}
literature_answer_request = dict(retrieval_request)
```

History is optional in D's question request; A's current question shape has no history
field. How follow-up questions are contextualized is review question R-04 below.

### 4.3 ClassificationResult from C

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "doc_id": "illustrative-document",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "status": "uncertain",
  "category": null,
  "scores": [],
  "score_kind": "decision_score",
  "confidence_note": "Synthetic fixture; no classifier ran and no scores were measured.",
  "model_version": "mock-classifier-v0"
}
```

B shows uncertainty and the limitation note, rather than selecting a default specialty.
A supported example in the later fixture suite must cover all five unique categories:
Cardiovascular / Pulmonary, Orthopedic, Gastroenterology, Neurology, and Urology.
C has completed the exact source-label audit: the five labels map to the proposed enum
after removing surrounding source-label whitespace. The measured uncertainty policy is
still pending development experiments. This legacy empty-score mock is illustrative;
C proposes retaining all five computed scores for real uncertain outcomes. See section 3.4.

### 4.4 ExtractionResult from D

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "doc_id": "illustrative-document",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "items": [
    {
      "entity_id": "suspected-mention",
      "type": "symptom",
      "name": "Chest pain",
      "assertion": "suspected",
      "temporality": "unknown",
      "subject": "unknown",
      "evidence": [{"start": 22, "end": 46, "quote": "Chest pain is suspected."}]
    },
    {
      "entity_id": "second-denial",
      "type": "symptom",
      "name": "Chest pain",
      "assertion": "negated",
      "temporality": "unknown",
      "subject": "unknown",
      "evidence": [{"start": 47, "end": 61, "quote": "No chest pain."}]
    }
  ],
  "summary": {
    "language": "en",
    "text": "The text includes suspected chest pain and a separate denial of chest pain.",
    "claims": [
      {"claim_id": "summary-suspected", "text": "The text states that chest pain is suspected.", "scope": "document_fact", "source_ids": ["doc-suspected"]},
      {"claim_id": "summary-denial", "text": "The text also contains a denial of chest pain.", "scope": "document_fact", "source_ids": ["doc-second-denial"]}
    ],
    "sources": [
      {
        "source_id": "doc-suspected", "kind": "document", "doc_id": "illustrative-document",
        "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
        "evidence": {"start": 22, "end": 46, "quote": "Chest pain is suspected."}
      },
      {
        "source_id": "doc-second-denial", "kind": "document", "doc_id": "illustrative-document",
        "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
        "evidence": {"start": 47, "end": 61, "quote": "No chest pain."}
      }
    ],
    "evidence_state": "sufficient",
    "warnings": ["Artificial offset exercise; conflicting statements are reported without clinical reconciliation."]
  },
  "extractor_version": "mock-extractor-v0",
  "prompt_version": "mock-extraction-prompt-v0"
}
```

This is deliberately not an exhaustive extraction reference: the first repeated denial
is omitted. D's mention/grouping rules need review. Sufficient summary evidence here
supports only the narrow statement that both phrases occur; it does not resolve their
clinical meaning or claim completeness of extraction.

### 4.5 RetrievalResult from A: insufficient evidence

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "state": "insufficient",
  "passages": [],
  "retriever_version": "mock-retriever-v0",
  "index_version": "mock-index-v0",
  "score_note": "Synthetic empty retrieval; no corpus was searched and no score was measured."
}
```

A sufficient result instead includes passages with `source_id`, `kind: literature`,
`topic_id`, `passage_id`, `title`, HTTPS `url`, `text`, `snapshot_date`, and `score`.
The retrieval result also retains its versions and score note. The score's interpretation
and sufficiency threshold must come from A's measured development policy, not a B default.
An error-state retrieval result requires `error`; sufficient/insufficient results must
not contain that error field under the current schema.

### 4.6 AnswerResult: document-supported answer

For the document question in section 4.2, D could return this narrow supported response:

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "language": "en",
  "text": "The text states that chest pain is suspected and also contains a denial of chest pain.",
  "claims": [
    {"claim_id": "answer-suspected", "text": "The text states that chest pain is suspected.", "scope": "document_fact", "source_ids": ["doc-suspected"]},
    {"claim_id": "answer-denial", "text": "The text also contains a denial of chest pain.", "scope": "document_fact", "source_ids": ["doc-second-denial"]}
  ],
  "sources": [
    {
      "source_id": "doc-suspected", "kind": "document", "doc_id": "illustrative-document",
      "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
      "evidence": {"start": 22, "end": 46, "quote": "Chest pain is suspected."}
    },
    {
      "source_id": "doc-second-denial", "kind": "document", "doc_id": "illustrative-document",
      "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
      "evidence": {"start": 47, "end": 61, "quote": "No chest pain."}
    }
  ],
  "evidence_state": "sufficient",
  "warnings": ["Artificial example; no clinical reconciliation is inferred."],
  "route": "document",
  "answer_version": "mock-document-answer-v0",
  "prompt_version": "mock-document-prompt-v0"
}
```

### 4.7 AnswerResult: literature-source shape

This protocol-only illustration uses an intentionally non-resolving `.invalid` URL.
The passage, topic/passage IDs, and date are synthetic fixture metadata, not fetched
MedlinePlus content, an actual corpus snapshot, or real clinical evidence. The date is
the example's preparation date. Do not display this as an authentic literature citation.

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "language": "en",
  "text": "In this synthetic passage, suspected expresses uncertainty.",
  "claims": [
    {"claim_id": "fixture-meaning", "text": "In this synthetic passage, suspected expresses uncertainty.", "scope": "general_information", "source_ids": ["fixture-literature-source"]}
  ],
  "sources": [
    {
      "source_id": "fixture-literature-source",
      "kind": "literature",
      "topic_id": "synthetic-topic",
      "passage_id": "synthetic-passage",
      "title": "Synthetic terminology fixture",
      "url": "https://example.invalid/notelens/fixture-topic",
      "text": "In this synthetic passage, suspected expresses uncertainty.",
      "snapshot_date": "2026-11-11"
    }
  ],
  "evidence_state": "sufficient",
  "warnings": ["Protocol illustration only; this source is synthetic and was not retrieved."],
  "route": "literature",
  "answer_version": "mock-literature-answer-v0",
  "prompt_version": "mock-literature-prompt-v0"
}
```

For a sufficient mixed illustration, combine the document and synthetic-literature claims
and their sources, preserve the warnings, set `route: mixed`, and use a combined version
identifier. That is a future composition check, not a service called in this review.

### 4.8 AnswerResult: partial mixed answer

For "What does the text say about chest pain, and what general explanation does the
literature provide?", D may support the document portion while A returns section 4.5.
This example preserves both supported document statements and explicitly states the gaps:

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "language": "en",
  "text": "One passage says chest pain is suspected. Another passage denies chest pain. A general literature explanation is unavailable; the document statements are not clinically reconciled.",
  "claims": [
    {"claim_id": "d:answer-suspected", "text": "One passage says chest pain is suspected.", "scope": "document_fact", "source_ids": ["d:doc-suspected"]},
    {"claim_id": "d:answer-denial", "text": "Another passage denies chest pain.", "scope": "document_fact", "source_ids": ["d:doc-second-denial"]}
  ],
  "sources": [
    {
      "source_id": "d:doc-suspected", "kind": "document", "doc_id": "illustrative-document",
      "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
      "evidence": {"start": 22, "end": 46, "quote": "Chest pain is suspected."}
    },
    {
      "source_id": "d:doc-second-denial", "kind": "document", "doc_id": "illustrative-document",
      "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
      "evidence": {"start": 47, "end": 61, "quote": "No chest pain."}
    }
  ],
  "evidence_state": "partial",
  "warnings": ["No supporting literature passage was returned.", "Artificial example; conflicting document statements remain unresolved."],
  "route": "mixed",
  "answer_version": "mock-combined-answer-v0",
  "prompt_version": "mock-combination-fixture-v0"
}
```

The prefix illustrates consistent ID rewriting, not an agreed namespace format. No
literature source is invented to fill the gap. An outage would require an availability
warning rather than pretending that a successful search found no evidence.

### 4.9 AnswerResult: no supported answer

For a question about an unstated procedure with no supporting literature result:

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "language": "en",
  "text": "The available sources do not support an answer to this question.",
  "claims": [],
  "sources": [],
  "evidence_state": "insufficient",
  "warnings": ["Synthetic unsupported-question example."],
  "route": "none",
  "answer_version": "mock-no-answer-v0",
  "prompt_version": "mock-no-answer-prompt-v0"
}
```

### 4.10 Operational failure: ErrorEnvelope

```json
{
  "schema_version": "1.0.0",
  "request_id": "illustrative-request",
  "error": {
    "code": "timeout",
    "message": "The requested service did not respond in time.",
    "retryable": true
  }
}
```

This illustrates the error shape; it does not configure a deadline or retry count.
`retryable` does not permit unbounded retries. Keep messages in safe English without
document bodies, secrets, stack traces, or upstream response dumps.

| Situation | Proposed HTTP behavior | Application behavior |
| --- | --- | --- |
| Valid but insufficient evidence | Normally 200 with a domain result. | Explain the gap; do not equate it with provider failure. |
| Invalid request | 400 or 422. | Show safe validation guidance; exact mapping needs agreement. |
| Missing/invalid service token | 401. | Treat exposed service access as unauthorized; tokens stay server-side. |
| Unknown/expired/other-session document | Same safe 404 `document_unavailable`. | Require a permitted resubmission; disclose no other-session content. |
| Oversized / unsupported file | 413 / 415. | Reject rather than truncate or attempt OCR. |
| Local/provider rate limit | 429. | Show a bounded recovery state using approved controls. |
| Invalid upstream record | 502. | Do not render malformed data as valid analysis. |
| Provider/configuration/budget unavailable | 503. | Retain independently supported results; keep live execution guarded. |
| Request deadline exceeded | 504. | Show timeout; bounded retry policy remains an open decision. |

## 5. Questions to resolve with the team

These are review requests, not adopted changes. No messages have been sent to teammates.
B can discuss them using this guide and record the actual responses. All agreement
statuses remain pending; B's agent review is not owner approval.

| ID | Question / reason | Responsible reviewers | Proposed next action | Agreement |
| --- | --- | --- | --- | --- |
| R-01 | Can all services consume the proposed canonical document unchanged, including NFC/LF, non-BMP text, repeated spans, and exact UTF-8 hashing? | A/B/C/D; C/D consume documents. | Confirm the preparation rule and shared examples before freeze; record any required schema/behavior changes. | C design response available; runtime checks and owner agreement pending |
| R-02 | Can C return five unique category scores for supported results, with explicit score meaning and uncertain/unsupported behavior? | B/C | Confirm payload cases and label meanings; leave empirical thresholds to C's development measurements. | C state/score proposal in section 3.4; B/C agreement pending |
| R-03 | Does D need additional extraction/summary fields or rules for repeated mentions, contradictory statements, history, family context, and source-present ICD? | B/D | Review mention grouping and support rules; add historical/family/ICD positives and negatives in F-008 after agreement where required. | Pending |
| R-04 | D accepts optional history, but A's current request has no history. How will literature and mixed follow-up questions obtain sufficient context? | A/B/D | Agree explicit context/routing behavior before B-003; propose a contract change only if needed, with privacy implications reviewed. | Pending |
| R-05 | AnswerResult has no top-level doc_id/hash. How does B reject an old answer after a document switch or expiry, including insufficient answers with no document sources? | A/B/D | Review server-side request-context association and whether additional wire identity is needed. Do not invent fields in examples. | Pending |
| R-06 | What does A's retrieval score mean, and how are sufficient/insufficient/error outcomes surfaced without suppressing document support? | A/B/D | Agree state semantics and partial-answer examples; select numeric thresholds only after development measurement. | Pending |
| R-07 | What namespaces and version conventions should combined results use, and how is displayed answer text kept aligned with its claims? | A/B/D | Agree a deterministic composition approach preserving supported portions, citations, versions, and warnings; no new B-side medical generation. | Pending |
| R-08 | Which exact status/error mappings apply? The README allows 400 or 422 and describes 502, while the API proposal must also describe the intended mapping consistently. | A/B/C/D | Walk through malformed requests, malformed upstream results, rate limits, timeouts, and configuration errors; propose changes before freeze. | C error-mapping proposal available; shared mapping pending |
| R-09 | Which session/history/question/operational controls are needed, and how is unsupported English-language input/output identified? | B with A/D and user | Obtain decisions before dependent implementation; no invented limits, language detector, or live defaults. | C language/privacy boundary proposal available; method/limits pending |
| R-10 | Who creates each Python mock scaffold? F-004/F-011 list B editing service paths, but current ownership restricts those paths to A/C/D. | A/B/C/D and user if cross-owner work is requested | Prefer owner-created service scaffolds coordinated by B, or seek explicit bounded authorization; preserve task dependencies. | C proposes owner-created classifier scaffold; coordination pending |
| R-11 | How will exposed services authenticate, and what approved host/budget/provider-retention arrangement can preserve memory-only submissions? | B with A/C/D and user | Resolve at the dependent activation/deployment gates; keep key-free loopback mocks local and live mode disabled. | C boundary proposal available; deployment/auth configuration pending |

When feedback arrives, record the reviewer alias, reviewed proposal version/changes,
decision date, accepted changes or remaining objections, and actual check evidence.
Do not fill in consent, ratification, thresholds, or reviewer names from inference.
The existing [open-decision register](../team/open-decisions.md) remains authoritative
for pending decisions; this table is B's discussion guide, not a silent replacement.

## 6. Branch workflow and the next packages

The user selected **task -> B integration -> main**. Both local branches were created
from the clean documentation base in this package:

| Branch | Role / current state |
| --- | --- |
| `main` | Shared reviewed base; unchanged by this package. |
| `member-b/platform` | B's integration branch, created from main. No task changes merged yet. |
| `member-b/task-contract-review` | Current task branch, created from member-b/platform; holds this local document. |

Future task branches start from the latest B integration branch. Complete and check each
task before merging it back; prepare focused B-to-main PRs promptly for shared prerequisites.
Unfinished work stays on task branches. A/C/D need the reviewed shared foundation in main,
not only on B's branch. Commit/push/merge/publication actions need their own authorization.
Git branch ancestry is established by commits, not by slash-separated names. Avoid a
task name under `member-b/platform/`, which conflicts with the existing integration ref.

Branch names do not choose Spec Kit context. Use `specs/000-foundation` for foundation
work and `specs/002-platform` for platform work, with `SPECIFY_FEATURE_NO_PERSIST=1`.
Follow the committed [working-copy guide](../team/working-copies.md); use separate working
copies for concurrent sessions. This guide records a B-specific branch preference without
rewriting the team runbook or changing another member's workflow.

### 6.1 Dependency order

Read the [foundation backlog](../../specs/000-foundation/tasks.md) and
[platform backlog](../../specs/002-platform/tasks.md). Alias order differs from local
task numbering; for example F-008 is foundation T003 and F-003 is foundation T004.

| Order | Deliverable | Actual gate / completion evidence |
| --- | --- | --- |
| Now | Review this documentation and obtain team feedback. | No service implementation or tooling installation needed. Writing this guide does not complete B-010. |
| Next proposed package | Approve local tooling setup, then implement F-008 positive/negative fixtures and validators. | F-002 already exists. Create the B-owned tooling environment and execute structural/exact-text/relationship checks. Team discussion can continue while checks are prepared. |
| F-003 | Incorporate reviewed changes and record the contract freeze. | F-008 checks and actual A/B/C/D agreement; a draft file is insufficient. |
| F-009 | Generate shared bindings. | Frozen schema; reproducible generation and shared fixture compatibility. |
| F-004 / F-011 | Web workspace plus coordinated service mocks, health/readiness, and safe failure responses. | F-003/F-009 and resolved scaffold ownership; actual dependency locks/builds and key-free checks. |
| F-012 / F-005 / F-010 | Cross-language Unicode checks, startup/mock flow, and foundation CI/scope checks. | Actual scaffolds; executed fixture, health, startup/shutdown, smoke, and scope checks. |
| F-006 / F-013 / F-007 / F-014 | Verified handoffs, real user/team acceptance, checkpoint inventory, and authorized publication. | Preserve listed dependencies; the current documentation commit is not F-014. |
| B-010 | Web consumer suite and interface review against frozen generated bindings. | F-003 and F-004. This document supplies only preparatory review material. |
| B-004 | Sessions, retention, isolation, guarded configuration. | B-010 and F-014; remaining relevant controls approved before implementation. |
| B-001 / B-002 | Document input and complete report panels using mocks. | B-010, F-014, and B-004. These tasks can progress independently when ready. |
| B-003 | Thin clients, question routing, source-preserving combination, and bounded state. | B-001/B-002 plus resolved applicable review/configuration questions. |
| Later platform work | B-008 security, B-006 CI, B-005 real integrations, B-007 deployment, B-009 rehearsal. | Follow each task's explicit dependencies and separate live/deployment approvals. |

B-011 annotations become ready after D-003 assignments; they are not held behind the
entire web implementation. A can inspect corpus sources, C can audit data, and D can
draft annotation rules before complete modules exist. B-005 is an aggregate task: replace
each mock independently when that module's prerequisites pass, and close the task only
after all required integrations/checks pass. Do not infer completion from fixture outputs.

### 6.2 Original B-machine setup facts and deferred checks

These are B's reported local observations from the original document, not observations
about C's machine or checks repeated for this review copy.

This checkout has Node v24.19.0, npm.cmd 11.17.0, and Python 3.13.7. `uv` was not found
on PATH. The PowerShell execution-policy inspection showed LocalMachine Restricted with
no process/user override; direct committed-script and npm.ps1 invocation was blocked in
the planning inspection. `npm.cmd --version` works. Python's default console output could
not print the example emoji; escaped/ASCII output worked. These are local observations,
not package compatibility, application-build, or cross-language runtime results.

The user chose to defer installation and policy adjustment. This package changes neither.
The next implementation package should resolve tooling, verify the pinned Spec Kit 1.3.3
entry point, and run the actual read-only feature resolver with the chosen feature context.
Do not change permanent execution policy as an unreviewed shortcut.

F-008's future command is `uv run --directory scripts/project python check_contracts.py`.
Neither that validator nor its environment exists yet. No schema-validator installation,
HTTP/module tests, browser tests, startup smoke, paid/provider checks, or deployments
are part of this documentation package. No Spec Kit generation/implementation workflow
was invoked; this is ordinary approved documentation preparation.

For this document, check JSON syntax, compare fields/operations to the proposal, calculate
the synthetic digest/spans, verify local links, and inspect the diff. Full JSON Schema
validation, positive/negative acceptance fixtures, actual HTTP payload checks, Python/
TypeScript agreement, and human/source-support acceptance remain separate future checks.

### 6.3 Original B-document check record (2026-11-11)

The following record is retained from B's supplied document. It describes the original
examples and B's original working-copy state, not new checks or the Git state of this C copy.

Used `python -B -` with an inline standard-library inspection script; no test runner,
dependencies, persistent validation script, or service process was introduced.

- Parsed all nine JSON examples and checked required/allowed fields plus selected
  const/enum/reference relationships against the existing schema definitions.
- Parsed and evaluated the request-construction fragment using only the prepared
  synthetic object and `dict`; checked all five operation request references against
  OpenAPI. The fragment constructs dictionaries and makes no network calls.
- Recomputed the synthetic SHA256 and three code-point/UTF-16 intervals; checked all
  eight evidence occurrences, document identities/digests, unique claim/source IDs,
  and citation resolution in the examples.
- Resolved all nine relative Markdown file links and checked final newline/trailing
  whitespace. These checks passed for the worked examples, not for a runtime system.
- Inspected `git status --short`, `git branch --show-current`, and the document diff.
  The intended final state is one untracked document on the contract-review task branch;
  no files are staged and no commit, merge, or push has been performed.

This was agent documentation review. It does not establish full JSON Schema/OpenAPI
validity, English compliance of future generated outputs, semantic/clinical validation,
human/team acceptance, implemented session security, or any mock/module/live test pass.

### 6.4 C's required next handoffs

B must resolve C's proposals and complete the F-003 freeze, F-009 bindings and coordinated
F-004 scaffold before C-009's actual consumer checks can run. C-002 additionally depends
on C-009 and F-014's reviewed publication, not merely the original documentation commit.
C-003 training then follows C-002. These gates remain unchanged by this copy.

D can prepare annotation guidance now. D-002 selection requires C-002 splits; D-003 then
assigns C's development-only primary annotations and separate reviews. C's initial training
does not depend on C-010 annotations; the C-008 final-task gate does. A's completed RAG model
is not a direct prerequisite for C's training, although A participates in the shared foundation.

See [C's status and dependency report](member-c-status-and-dependencies.md) for exact
requested artifacts and the next task each handoff unlocks. No source CSVs are redistributed
by these documents, and no commit, push, deployment or teammate message is authorized here.

Original supplied B-document SHA-256: `4511453853084296437c82bcc12d3bbb65df7b5c89cc0ef328d9a21e5e2fdb9f`.
