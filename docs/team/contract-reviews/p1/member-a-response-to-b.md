# RAG Interface Review — Nemanja (A), Agent-Assisted

**Reviewer:** A's coding agent for Nemanja
**Date:** 2026-11-11
**Proposal P1:** Draft contract `1.0.0`, `contracts/v1/schema.json`,
`contracts/v1/openapi.json` and the contract README at commit `e7bc839c0632`,
reviewed using B's interface-review guide dated 2026-11-11.

This reviewer, date and proposal apply to every item below. Statuses express the
agent's technical assessment; human/team acceptance and contract freeze remain pending.

The proposed fields generally cover stateless literature questions, retrieval
results and cited literature answers. The following changes and decisions should
be addressed before freezing the interfaces.

| Reference | Status | Feedback |
| --- | --- | --- |
| Request formats / R-01 | **agreed** | `schema_version`, `question`, optional `concepts` and nullable/optional `specialty_hint` cover standalone RAG requests. A does not need a prepared patient document. Specialty must remain a soft signal, and questions or document-derived content must never enter the literature index. A cannot confirm C/D's document-consumption behavior on their behalf. |
| Literature sources and claims | **agreed** | Topic/passage IDs, title, HTTPS URL, passage text and snapshot date cover basic citations. A's answers must contain `general_information` claims linked to literature sources. Literature must not establish patient-specific facts. Returned passage text will require the later preparation stage; the currently extracted HTML is not a finished API passage. |
| Evidence outcomes / R-06 | **agreed** | Insufficient evidence is a valid domain outcome, distinct from a technical failure. Unsupported claims must be withheld. A's insufficient or failed result must not suppress independently supported document answers from D. Numeric sufficiency thresholds remain subject to development measurements. |
| Score interpretation / R-06 | **change requested** | Document score direction and comparison rules. I propose that higher returned `score` means better rank, with the metric/transformation explained in `score_note`. Scores should be compared only within the applicable retriever/version, never interpreted as clinical confidence. This needs agreement; no numeric thresholds are proposed here. |
| RAG provenance / R-07 | **change requested** | `/retrieve` exposes retriever/index versions, but `/literature-answer` returns `AnswerResult`, which lacks that provenance. A literature answer must expose—or resolve through a documented immutable manifest—the corpus selection/preparation version, index version and retriever version. Suggested structured fields are `corpus_version`, `index_version` and `retriever_version`. An explicit immutable mapping from `answer_version` is an alternative. `snapshot_date` alone cannot distinguish different selections or preparation pipelines from the same download. |
| Follow-up context / R-04 | **still unresolved** | A's request currently contains no history. It supports self-contained questions, but an ambiguous follow-up such as “What causes it?” needs an agreed context mechanism. Prefer keeping A stateless. B/D/A must agree whether routing supplies a self-contained literature question, explicit context, or requests clarification. Do not silently assume that `concepts` always resolves the ambiguity or add unrestricted history. |
| Request association / R-05 | **change requested** | Specify correlation for successful responses as well as errors. A server-generated request ID propagated and echoed through an agreed HTTP header would suffice without adding patient-document fields to A's body. B must bind it to the originating session, selected document/version and question, then reject stale responses after a document switch or expiry—including answers with empty sources. |
| Mixed composition / R-07 | **still unresolved** | B must preserve supported claim text, consistently namespace colliding IDs and rewrite citation references together. The exact composition/version convention remains open. Also decide how mixed mock/live components are represented: the current single `mode` cannot describe component origins separately. A combined result must not conceal mock contributions under a `live` label. |
| HTTP errors / R-08 | **change requested** | Define when retrieval `state: error` is used versus a non-2xx `ErrorEnvelope`; otherwise consumers have two ambiguous failure channels. My preference is non-2xx envelopes for operational failures and 200 for completed searches with sufficient/insufficient evidence. Resolve 400 versus 422, document **500 with `internal_error`**, and specify the error code for malformed upstream responses at 502. Missing index/configuration should produce an explicit configuration failure rather than fabricated index-version metadata. |
| Validation and controls / R-09, R-11 | **still unresolved** | Agree behavior for whitespace-only questions, unsupported languages, follow-up/history bounds and question-size limits. The approved document limits must not automatically become question limits. Timeouts, retries, rate controls, provider activation/budget, hosting and provider retention remain unapproved. Server-side authentication and configuration-controlled mock/live mode are acceptable principles, not implemented guarantees. |
| Scaffold ownership / R-10 | **change requested** | Prefer an A-created RAG scaffold and service dependencies/lockfile, coordinated by B against agreed contracts. B owns shared contracts, generated bindings and integration. Clarify F-004/F-011 accordingly, or obtain explicit bounded authorization before cross-owner edits. |

**Current evidence:** A has implemented local extraction of 401 selected MedlinePlus
topics. Nineteen extraction tests passed, and all extracted records were compared
with the source XML. Retrieval, literature generation, HTTP endpoints and
shared-contract consumer tests are not implemented yet.

The preceding review was read-only; this file records that feedback only. It does
not change canonical contracts, complete A-010 or authorize a contract freeze.
