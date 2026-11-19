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

The service uses `notelens_contracts.v1.validate_record` for runtime validation.
`services/extraction/uv.lock` declares the local generated package; no shared schema
is copied into D's source. The deterministic catalog preserves separate occurrences,
assertion and procedure status, and supported findings across section failures.

[Setup, demos, tests and limits](../../docs/extraction-eval/integration.md),
[shared dependency requests](../../docs/extraction-eval/milestone-requests.md).
