# Member C response to B's interface review

**Date:** 2026-11-11

**Responding workstream:** C — dataset preparation, classification training and inference

**Reviewed document:** *Member B Interface Review*, prepared 2026-11-11, proposed contract version 1.0.0

**Status:** C response prepared for forwarding and discussion. Proposed decisions below require B's agreement and recording before contract freeze; this document does not claim team approval or an implemented service.

## R-01 — Canonical document and identity

The proposed `PreparedDocument` is compatible with C's planned classifier. No additional
document fields are requested by C at this stage.

C will accept B's `nfc-lf-v1` canonical text unchanged, including non-BMP characters,
repeated text and preserved whitespace. C will check the SHA-256 of its exact UTF-8 bytes
and return the input `doc_id` and `text_sha256`. A mismatch must be rejected rather than
repaired. C will not trim, normalize, truncate or replace the canonical document.

Internal model feature extraction is separate from document preparation: tokenization
and vectorization may derive features without changing the document. Learned transformations
will be fitted on training data only and packaged with the model for inference.

Shared Unicode/digest fixtures and generated Python bindings are needed to verify this
behavior. Compatibility is currently a design assessment, not a runtime test result.

## R-02 — Categories, scores and classification states

The local audit confirms these exact mappings; each source string below begins with one space:

| Source label | Output category | Nonempty records |
| --- | --- | ---: |
| `" Cardiovascular / Pulmonary"` | Cardiovascular / Pulmonary | 371 |
| `" Orthopedic"` | Orthopedic | 355 |
| `" Gastroenterology"` | Gastroenterology | 224 |
| `" Neurology"` | Neurology | 223 |
| `" Urology"` | Urology | 156 |

No category enum change is needed. Surgery and other broad labels will not be mapped into
these categories. Classification is a document specialty label, not a diagnosis.

I propose the following behavior for B/C agreement:

| State | Meaning | Category and scores |
| --- | --- | --- |
| `supported` | The model completed classification and the result satisfies the development-selected acceptance policy. | One selected category and exactly five scores, one per category. |
| `uncertain` | Classification completed, but the result does not satisfy that policy. | `category: null`; retain all five computed scores. |
| `unsupported` | An agreed input-scope check identifies content outside supported classification scope. | `category: null`; empty scores if classification was skipped, otherwise all five computed scores. Explain the reason. |

Low confidence alone produces `uncertain`; it does not prove that an input is unsupported.
The scope-check method and its limitations remain to be agreed and evaluated. No universal
out-of-distribution or unsupported-language detection is claimed.

Scores must be finite and categories unique. Return them in the category order above for
deterministic fixtures. Probability scores must lie in [0,1]; any sum-to-one validator
needs an agreed numerical tolerance. Decision scores may be signed and must not be
displayed as percentages. `score_kind` must describe the actual model output.

Every result includes `model_version` and an English `confidence_note`. Model probabilities
are not clinical certainty and are not automatically calibrated. Model selection and
uncertainty thresholds will use development data only; no empirical threshold is set now.

The illustrative empty-score mock in B's document remains a documentation example. It
does not demonstrate real uncertainty behavior. Future fixtures should also include
supported results, real-shape uncertain results with five scores, and unsupported cases.

## R-08 — Proposed classifier error mapping

Operational failures must use `ErrorEnvelope`, not successful uncertain predictions.
The following is a proposal for the shared contract, not an implemented mapping:

| Condition | HTTP / existing error code | Responsibility |
| --- | --- | --- |
| Malformed JSON | 400 / `validation_failure` | C's HTTP boundary; safe message. |
| Invalid fields/version, empty text or digest mismatch | 422 / `validation_failure` | C validates the request and document consistency. |
| Text exceeds 100,000 code points | 413 / `validation_failure` | Reject without truncation. |
| Missing/invalid service credentials where required | 401 / `unauthorized` | C enforces the agreed server-to-server mechanism. |
| Missing or incompatible model artifact | 503 / `configuration_required` | Do not substitute mock output or an uncertainty result. |
| Agreed rate limit reached | 429 / `rate_limit` | Apply only after limits and recovery policy are agreed. |
| Classifier returns a malformed response to B | 502 / `internal_error` | B rejects the upstream payload; preserve independent D output. |
| B's classifier request deadline expires | 504 / `timeout` | B's service client; cancellation behavior and deadline need agreement. |
| Valid supported/uncertain/unsupported result | 200 / no error envelope | Domain result with truthful state and score meaning. |

Unexpected internal classifier exceptions also need a safe mapping. I propose 500 /
`internal_error`; 500 is not currently listed for `/v1/classify`, so B should review and
add it to the canonical API if accepted. C will not add a competing local contract.
The local OpenAPI proposal already lists 502; the remaining work is agreement and
consistency of behavior, not simply adding that status.

Validation/configuration failures should not trigger automatic retries. Transient failures
may be marked retryable only under the agreed bounded policy. No retry counts, request
deadlines or rate limits are selected by this response. All errors must be English and
omit request bodies, credentials, stack traces and unsafe upstream details.

Session ownership, expired-document 404 responses, PDF parsing and file-type rejection
remain B's responsibility. C receives prepared text, not uploaded PDF files.

## R-09 — Language, session and operational controls

I propose that B owns the common input-language validation step before dispatching the
same prepared document to C and D. An `en` field alone is not proof of English. The team
must choose and evaluate the validation method before this behavior is implemented.

Explicitly rejected non-English input should use the existing `unsupported_language`
error, with a proposed 422 mapping at that boundary; it must not be silently translated.
This should remain distinct from a structurally valid English document outside the
classifier's supported scope. C's confidence threshold is not a language detector.

C does not need chat history, user identity or session storage for classification. B
enforces session access and absolute expiry. C processes forwarded text transiently,
does not retain submitted documents after request processing and does not write them to
logs, model-training files, caches or evaluation datasets. The approved maximum retention
of 60 minutes is an upper bound, not permission for C to keep a separate document store.

Request concurrency, timeouts, cancellation, rate limits and deployment resource limits
still require coordination. No capacity or latency guarantee has been measured.

## R-10 — Scaffold ownership

I propose owner-created service scaffolds: C implements the classifier's mock service,
health/readiness behavior, local tests, package manifest and lockfile within
`services/classifier/**`. B coordinates F-004/F-011 and owns root configuration, shared
startup, contracts and generated bindings.

B should record this division in the foundation tasks before execution. C's foundation
scaffold contribution must be distinguished from C-009: the scaffold helps deliver F-004;
C-009 subsequently tests consumption of the frozen contracts in that scaffold. This
avoids treating C-009 as a prerequisite for the very scaffold it depends on.

Mock mode must be explicit and key-free. A real-mode service without a usable model must
not report model readiness or silently fall back to mock predictions. No cross-owner
file changes or completed foundation tasks are implied by this proposal.

## R-11 — Authentication and deployment

The proposed server-to-server bearer-token boundary is suitable for B/C review. Tokens
stay server-side; the browser calls B, not the classifier directly. C must enforce the
agreed authentication for exposed services and must never log credentials or document bodies.

Key-free development mocks remain local to loopback. Hosting, TLS/secret provisioning,
network exposure, operational limits and deployment approval are still unresolved. C's
planned TF-IDF/Logistic Regression and XGBoost work can run locally without paid inference
APIs. Optional embedding services are not activated or assumed by this response.

The proposed local classifier origin `http://127.0.0.1:8002` is configurable and is not
a deployment URL. No hosting account, budget or paid provider is approved here.

## R-03 through R-07 — C's boundaries and integration requirements

These questions primarily require B/D or A/B/D decisions. C is not approving decisions
on their behalf. C's relevant requirements are:

- **R-03:** C does not require extraction fields, inferred diagnoses or ICD codes to classify.
  D owns mention, assertion, temporality and evidence rules.
- **R-04:** The classifier does not need question history or literature follow-up context.
  C's request can remain a schema version plus prepared document.
- **R-05:** C already returns document identity and digest. B must reject a stale classifier
  result after a document switch or expiry, even when C's result is uncertain/unsupported.
  Answer identity changes remain an A/B/D decision.
- **R-06:** Specialty is an optional soft retrieval signal. Uncertain/unsupported C output
  must not force a default specialty, hard-filter A's corpus or suppress supported D output.
- **R-07:** C supplies its own model version; it must not be confused with the wire schema
  version or A/D generation versions. Combined answer composition remains with A/B/D.

## Current evidence and next dependencies

C-001 is complete locally: the supplied CSV has 4,999 rows; 1,338 belong to target
specialties, and removing nine empty target transcriptions leaves 1,329 records. Preliminary
exact-text inspection found 46 conflicting groups covering 92 rows. Near-duplicate grouping
and conflict exclusions are still required before freezing a benchmark.

Eight synthetic audit tests and actual-source regeneration checks passed. These are dataset
audit checks, not classifier contract, HTTP, accuracy or live-provider checks. No trained
model, split manifests or functioning classification endpoint exists yet. Detailed evidence
is in [data-audit.md](data-audit.md); earlier C proposals are in [interface-review.md](interface-review.md).

The next required handoffs are:

1. **B/C:** Resolve the proposed state/score and error rules, language boundary and scaffold
   ownership; B records the decisions and prepares positive/negative shared fixtures.
2. **B:** Complete F-003 contract freeze and F-009 generated bindings, then coordinate
   F-004/F-011 owner-created scaffolds and the runnable foundation.
3. **C:** Complete C-009 once F-003/F-004 are available. C-002 also requires F-014 before
   publishing frozen, group-disjoint train/validation/test manifests.
4. **D/C:** D assigns development annotation/review documents using the frozen manifests.
   C must not inspect final references for model selection; independent human review
   cannot be replaced by generated annotations.
5. **C:** Train the majority and TF-IDF/Logistic Regression baselines, compare XGBoost on
   development data, then package the selected model and provide integration evidence.
   Final-test measurement follows model-selection freeze and the remaining task gates.

The delivery date remains **2026-11-24**. This response does not change the deadline,
authorize publication/deployment, or mark remaining implementation tasks complete.
