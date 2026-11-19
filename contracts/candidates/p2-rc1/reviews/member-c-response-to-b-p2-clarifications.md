# C Response to B's Outstanding P2 Questions

**Review date:** 2026-11-12

**Reviewer:** Coding agent assisting C; C's human confirmation of these new recommendations is pending.

**Reviewed material:** P2 dated 2026-11-12 and the supplied `member-b-reply-to-c-p2.md`.

This response addresses the six outstanding questions. It proposes contract behavior and scaffold requirements; it does not claim implementation, runtime verification or final schema acceptance.

## 1. Scope checking — P2-07

I recommend a conservative MVP policy:

- Use `supported` when classification completes and satisfies the development-selected acceptance policy.
- Use `uncertain` when classification completes but does not satisfy that policy.
- Use `unsupported` only when a separately agreed scope check establishes a specific exclusion, with a recorded reason and policy version.

I do not currently propose a reliable automatic detector for all English content outside the five specialties. Low confidence, missing medical keywords or a predicted specialty alone must not establish that exclusion.

Until an explicit scope method is agreed and evaluated, valid English input should follow the supported/uncertain classification path. The contract may retain `unsupported`, but mocks demonstrating that state must not imply an implemented scope detector.

Scope decisions must not use hidden reference labels, final-test information, D's extraction results or inferred diagnoses. B's language rejection remains a separate validation outcome.

## 2. Skipped versus performed classification — P2-07/P2-11

I propose these minimal additions and conditional rules:

| Field | Proposed meaning |
| --- | --- |
| `classification_execution` | `skipped` or `performed`; describes actual model execution. |
| `model_version` | Actual executed pipeline version when performed; null when skipped. |
| `score_kind` | Actual score kind when performed; null when skipped. |
| `scope_policy_version` | Required for unsupported outcomes; otherwise nullable when no scope policy was applied. |
| `scope_reason` | A safe, agreed reason identifier for unsupported outcomes; otherwise nullable. |

Do not put a configured-but-unused model version in `model_version`. If configuration inventory is needed, keep it separate from execution provenance.

The following are **proposed result fragments**, not valid P1 payloads. Policy names, model names and scores are synthetic fixture placeholders. They assume an independently approved scope rule; that rule does not yet exist.

Unsupported with classification skipped:

```json
{
  "state": "unsupported",
  "category": null,
  "classification_execution": "skipped",
  "scores": [],
  "score_kind": null,
  "model_version": null,
  "scope_policy_version": "synthetic-scope-policy-v1",
  "scope_reason": "outside_supported_scope",
  "confidence_note": "The scope check excluded this input. Classification was not run."
}
```

Unsupported after classification was performed:

```json
{
  "state": "unsupported",
  "category": null,
  "classification_execution": "performed",
  "scores": [
    {"category": "Cardiovascular / Pulmonary", "score": 0.25},
    {"category": "Orthopedic", "score": 0.20},
    {"category": "Gastroenterology", "score": 0.20},
    {"category": "Neurology", "score": 0.20},
    {"category": "Urology", "score": 0.15}
  ],
  "score_kind": "probability",
  "model_version": "synthetic-classifier-fixture-v1",
  "scope_policy_version": "synthetic-scope-policy-v1",
  "scope_reason": "outside_supported_scope",
  "confidence_note": "Classification ran, but a separate scope check excluded this input. Scores do not establish supported scope."
}
```

The second example is justified only by an independent scope decision, not by the displayed probabilities. Actual mock fixtures must also carry the agreed explicit mock metadata.

Missing required model artifacts remain `503 / configuration_required`. They must not produce either example.

## 3. Errors and cancellation — P2-13

I have no classifier-specific objection to the proposed mappings:

- 400: malformed JSON.
- 422: invalid fields/version/digest or empty canonical text.
- 413: document exceeds the approved code-point limit.
- 401: missing/invalid required service authentication.
- 503: missing/incompatible model configuration.
- 500: unexpected internal exception.

B owns rejection of invalid upstream responses with 502 and its outgoing deadline outcome with 504. All envelopes must be safe and English, without document bodies or stack traces.

For cancellation, I support B stopping its wait and rejecting late/stale results. C should check cancellation before starting inference and release request references and temporary buffers when processing ends.

I cannot promise immediate interruption of already-running synchronous model computation. Disconnect detection and cancellation behavior must be tested in the selected runtime. The scaffold brief should distinguish cancellation of waiting from termination of computation. Runtime bounds and any stronger termination requirement remain open before dependent integration.

## 4. Request correlation — P2-10

I support B generating `X-Request-ID` for each service call, C echoing it on success and failure, and matching it in `ErrorEnvelope.request_id`.

I propose a shared canonical UUID textual format, validated by B and C:

- Valid ID: preserve and echo it.
- Missing, malformed or duplicate header: reject before classification with `400 / validation_failure`.
- For that rejection only, C generates a valid error-correlation ID and uses it consistently in the response header and envelope. Never echo unsafe invalid input.

Please confirm this fallback rule because an absent/invalid incoming ID cannot be echoed as a valid ID. B must treat that response as a failed call, not accept it as a correlated classification result.

Correlation does not replace document identity, session authorization or expiry checks.

## 5. Language boundary — P2-14

Classifier-relevant cases for B's proposal include:

- English clinical text containing abbreviations, medication names, numbers and medical terminology.
- Short or fragmentary text where language identification is inconclusive.
- Mixed-language documents.
- Non-English text containing English medical keywords.
- English documents outside the five specialties.

Uncertainty in language detection must not silently become a confirmed English decision. No translation or classifier-confidence-based language detection is proposed.

C does not need detector probabilities or chat/session data. I recommend an explicit validation outcome and policy version associated with the prepared document, rather than relying only on `language: en`. Exact field placement and inconclusive-input behavior require agreement. This metadata records B's decision; it is not independent proof of language correctness.

## 6. Scaffold requirements — P2-15

Please include:

- Deterministic supported, uncertain and unsupported/skipped/processed mock fixtures, clearly marked as synthetic.
- Invalid hash/version, empty/oversized input and non-BMP cases.
- Request-ID propagation and invalid-header cases.
- Explicit mock mode and real-mode missing-model failure.
- Separate liveness and readiness: a running process is not necessarily ready to classify; mock readiness must not imply a loaded real model.
- Tests showing that B rejects late, mismatched or malformed results.
- No submitted-text persistence or logging, and no silent mock fallback.

Please distinguish C's valid mock scenarios from deliberately malformed upstream fixtures used by B's integration tests.

C will use an independent Python environment, dependency manifest and lockfile. No interpreter/package versions or compatibility results are claimed yet; these must be checked with the generated bindings on Windows. B should provide the binding import/package arrangement and shared integration expectations before C locks dependencies.

The ownership split remains accepted. This reply does not start scaffold implementation. After these decisions are resolved, I need the revised schema/fixtures for review, followed by F-003/F-009 artifacts and the precise F-004/F-011 brief. C-009 and C-002 retain their existing prerequisites.
