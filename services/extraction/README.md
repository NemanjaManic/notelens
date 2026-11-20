# NoteLens extraction service

Member D's key-free mock scaffold uses the frozen 1.0.0 Python contract package.
It accepts canonical English document requests and produces literal, document-grounded
extraction, summary and document-answer examples. It is not a general medical extractor
or an activated live provider. Non-mock mode fails with configuration_required.

From the repository root, after service-local locked setup:

```powershell
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve
```

Endpoints: `GET /health/live`, `GET /health/ready`, `POST /v1/extract` (includes
independent summary outcome), and `POST /v1/document-answer`. Business POSTs require
one canonical UUID `X-Request-ID`; health requests use fresh diagnostic IDs on 401.
The CLI binds to loopback port 8003 by default without HTTP access logs. An exposed
service requires a server-side bearer token.

For the F-011 readiness check, start the service with `NOTELENS_MODE=mock` and
`NOTELENS_EXTRACTION_MOCK_NOT_READY=1`. With no service token configured, loopback
requests to `/health/ready` receive HTTP 503 with `status: not_ready`,
`mode: mock`, and `reason: mock_not_ready`. `/health/live` returns HTTP 200 with
`status: alive`. Unset `NOTELENS_EXTRACTION_MOCK_NOT_READY` and restart the
process to restore mock readiness.

The service uses `notelens_contracts.v1.validate_record` for runtime validation.
`services/extraction/uv.lock` declares the local generated package; no shared schema
is copied into D's source. The deterministic catalog preserves separate occurrences,
assertion and procedure status, and supported findings across section failures.

[Setup, demos, tests and limits](../../docs/extraction-eval/integration.md),
[shared dependency requests](../../docs/extraction-eval/milestone-requests.md).

## Offline OpenAI Responses trial

The `OpenAITrialProvider` adapter can be injected into the extraction service
for the exact built-in synthetic extraction request and the question
"Does the patient report cough?" It supplies the frozen output contract from
the installed contracts package and sends at most one request per operation.
The service applies its normal contract, citation and evidence checks to the
returned JSON.

The adapter ships with offline tests and has no environment-selected transport.
Activation requires an explicitly supplied synchronous transport that enforces
the approved aggregate budget, request count, timeouts and no retries. A
per-response output token limit alone cannot enforce a dollar cap. The default
service configuration continues to fail closed for live generation.
