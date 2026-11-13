# Current classifier handoff after F-003/F-009

Human owner confirmations are recorded and canonical v1.0.0 is frozen. The shared
Python package now exists at contracts/generated/python and exports TypedDicts and
validate_json/validate_record/validate_exchange from notelens_contracts.v1. These are
not Pydantic BaseModel classes; use explicit runtime validation at the HTTP boundary.
See [the checked binding guide](../../contracts/generated/README.md) and
[the current handoff](frozen-contracts-handoff.md). C (Sara) owns the next mock scaffold
contribution after this checked package is published; B has edited no classifier files.
C-009 still requires completed F-004; C-002 retains its reviewed published F-014 gate.

The original approved scaffold requirements below remain historical design details.
Their earlier pending-freeze/package statements are superseded by this current section;
the service implementation commands below are still planned and have not been run by B.

# Classifier Scaffold Brief: P2 RC1

**Prepared:** 2026-11-12. **Coordinator:** B. **Implementation owner:** C.
**Status:** precise proposed F-004/F-011 contribution, pending candidate approval and
actual F-003/F-009 deliverables. This document does not start C's implementation or
complete C-009, F-004, F-011, F-014, or any classifier business task.

**Candidate revision:** `p2-rc1`, revision 2 (2026-11-13). Review the exact new manifest
and commit; C's revision-1 agent review did not provide final human acceptance.

Review with the [executable candidate](../../contracts/candidates/p2-rc1/README.md).
The candidate's schema/API and complete examples define the proposed service wire shape;
P1 remains canonical until actual owner approval. The current classifier is not built.

## Ownership and dependencies

C creates only `services/classifier/**`: source, mock behavior, local tests, its own
Python manifest/lock, and generated-package dependency declaration. B owns shared/root
configuration, contracts, bindings, startup/shutdown and integration tests. A/D create
their own service contributions. No cross-owner implementation is authorized here.

The scaffold contribution is part of F-004/F-011; it does not depend on C-009, because
C-009 consumes the completed frozen-contract scaffold. Before implementation begins,
record actual candidate agreement, F-003 freeze, F-009 package location/import checks,
and the authorized owner-specific package. After F-004, C can run C-009. C-002 still
requires C-009 and the reviewed published F-014 checkpoint; training follows its gates.

Implement the scaffold portion under F-004 first. The health/readiness portion is
F-011 and follows F-004's checkpoint; this combined brief does not reverse that order.

## Proposed package/import arrangement for F-009

B's later F-009 deliverable must provide an installable `notelens-contracts` Python
package at `contracts/generated/python`, exporting frozen models from
`notelens_contracts.v1`. At minimum C imports PreparedDocument, ClassificationRequest,
ClassificationResult, ErrorDetail, ErrorEnvelope, LivenessResult and HealthResult.
Generate these from the single frozen schema; do not handwrite a competing schema.

In C's future service manifest, use a local path dependency on that generated package,
resolved relative to `services/classifier` as `../../contracts/generated/python`.
B verifies package installation and fixture compatibility during F-009 before C locks
service dependencies. These package/module names are concrete candidate handoff choices,
not a claim that the package exists today. C selects and verifies compatible Python/
FastAPI/Uvicorn/test versions in its own environment. No version is silently inherited
from A's Python 3.14.2 preparation or B's Python 3.13.7 tooling.

F-009 runtime validation must reject NaN, positive infinity and negative infinity for
Python objects in memory, including classification decision/probability scores, before
serialization. JSON Schema's number type and JSON-file parsing alone do not enforce this
on every language runtime. Reproduce the candidate's native-number tests against generated
bindings and the service boundary. Preserve valid finite decision scores without adding
probability bounds; probability scores remain in [0,1]. Keep strict JSON handling for
nonstandard constants and overflowed numeric literals. This is an explicit F-009 acceptance
requirement, not a claim that bindings were generated or tested here.

## Service entry point and endpoints

Proposed importable app: `src/notelens_classifier/main.py`, exporting `app` as
`notelens_classifier.main:app`, with the project configured to install its src package.
The service listens on configurable loopback origin `http://127.0.0.1:8002` locally.
No public listener, deployment, paid API, model download, corpus or trained artifact is
required for the mock scaffold. Keep inputs and results transient, without body logging.

| Endpoint | Required behavior |
| --- | --- |
| POST /v1/classify | Validate headers and frozen request/document contracts, digest and canonical invariants; return the selected deterministic mock scenario or the agreed real-mode configuration failure. |
| GET /health/live | 200 LivenessResult means the process is alive; it does not assert inference/model readiness. No business request-ID header is required. |
| GET /health/ready | 200 HealthResult with status ok when ready for the explicitly configured mode; 503 HealthResult/status not_ready with a safe reason otherwise. This health-specific payload is documented in the candidate API. |

Both health endpoints return 401 ErrorEnvelope for missing/invalid authentication where
service authentication is enabled: code unauthorized, retryable false, a safe English
message, WWW-Authenticate: Bearer, and a newly generated canonical diagnostic UUID shared
by the response X-Request-ID header and body request_id. Ignore all incoming health
X-Request-ID values, including malformed/duplicate IDs; do not echo them or reject them
with 400. No request ID is required for health 200/503 responses. Preserve the loopback-only
key-free mock exception; this proposal does not create an unauthenticated public endpoint.

Proposed server-only configuration: `NOTELENS_CLASSIFIER_MODE=mock` and
`NOTELENS_CLASSIFIER_MOCK_SCENARIO=supported` (or uncertain, unsupported_skipped,
unsupported_performed). These are candidate configuration names for the scaffold; the
browser cannot enable real execution. Choose scenarios through server configuration or
test dependency injection, not untrusted document instructions. Mocks have no provider key.

Clone the selected valid fixture shape and bind doc_id/hash to the actual prepared input;
do not return a fixed fixture document ID for unrelated input. Preserve mode mock and
truthful synthetic notes/versions. A scenario simulating performed classification does
not imply that a real classifier ran. Real mode without a usable pipeline returns
503/configuration_required and not-ready status, never silent mock predictions.

Unsupported scenarios are synthetic only. Until an explicit reviewed/evaluated scope
policy exists, real accepted English input takes the supported/uncertain path. Do not
classify scope from low confidence, keyword absence, D's extraction or hidden labels.

## Validation, correlation and failure ownership

- Keep canonical text unchanged, verify exact UTF-8 digest, and echo input identity.
  Reject empty/invalid/version/digest input with 422, excess canonical length with 413;
  malformed JSON with 400. B checks PDF bytes/file types and session authorization.
- Require one canonical lowercase UUID X-Request-ID for business calls. Preserve/echo
  valid IDs on success and failure; error-envelope ID matches the response header.
  Reject missing/malformed/duplicate incoming IDs before classification with
  400/validation_failure, generating a new safe diagnostic UUID only for that error.
- Apply the candidate's 401/429/500/503 mappings when their actual cause applies. Do not
  invent numeric controls. Exposed services require server-only authentication; the
  key-free exception is loopback mock development only, never an unauthenticated public service.
- B handles malformed/mismatched upstream results as 502, and its outgoing deadline as
  504. C stops unnecessary work before inference when cancellation is known, releases
  references at completion, and documents any synchronous work it cannot interrupt.
  B never attaches a late result to an expired/different document. Runtime bounds,
  cancellation tests and retention guarantees need actual integration decisions.
- C validates the admitted document's accepted language-policy record. B owns the actual
  common language method; no classifier-confidence language detector or silent translation.
- No submitted documents in logs, training files, indexes, disk caches or evaluation artifacts.
  Demo fixtures are synthetic and separate. The 60-minute maximum does not permit C to
  create a separate retained document store or unbounded in-flight processing.

## Required local tests and evidence

C creates the following future test targets:

- `tests/test_contract.py`: supported and uncertain with five scores; unsupported mock
  skipped/processed; ordered/unique finite scores; nullable skipped model/score fields;
  canonical digest/version, empty/oversized/non-BMP input; frozen shared examples.
- `tests/test_http.py`: valid and invalid/missing/duplicate header handling, matching
  response/envelope IDs, safe status mappings and dynamic input doc_id/hash binding.
- `tests/test_health.py`: liveness/readiness separation, mock-ready without a real model,
  real missing-model not-ready/configuration failure, no fallback or model download;
  authenticated-mode 401 envelope/challenge/fresh-ID behavior with absent, valid,
  malformed and duplicate incoming IDs.
- `tests/test_privacy.py`: no submitted text or credential leakage in errors/logs, and
  no storage side effects in mock processing.

B separately owns deliberate malformed-upstream, mismatched/stale/late-result integration
tests. C's valid scenario fixture must not be corrupted to simulate a B integration fault.
No mock/HTTP pass completes model training, uncertainty measurement or final evaluation.

## Planned Windows commands: not available or verified yet

These commands become executable only after F-009 and C's approved scaffold create the
package, importable app, dependencies and named tests. They have **not** been run here.
Use the agreed uv executable, Python interpreter, and C's locked service environment.

```powershell
uv sync --locked --directory services/classifier
uv run --locked --offline --directory services/classifier python -m pytest tests/test_contract.py tests/test_http.py tests/test_health.py tests/test_privacy.py
$env:NOTELENS_CLASSIFIER_MODE = 'mock'
$env:NOTELENS_CLASSIFIER_MOCK_SCENARIO = 'supported'
uv run --locked --offline --directory services/classifier python -m uvicorn notelens_classifier.main:app --host 127.0.0.1 --port 8002
```

In a second PowerShell session after startup, planned health checks are:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8002/health/live
Invoke-RestMethod -Uri http://127.0.0.1:8002/health/ready
```

B's shared startup will supervise owned processes and clean shutdown once implemented.
C's completion handoff must include actual Windows interpreter/package versions, lock
and binding version, executed commands/results, mock versus real status, and remaining
limitations. B then checks shared startup and mock HTTP integration. No fabricated
passing commands, runtime capacity, ready model or published commit is accepted.
