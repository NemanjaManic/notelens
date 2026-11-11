# NoteLens extraction service

Runnable local **mock/provisional** Member D slice. It reads the B-owned draft
contract directly; frozen shared integration, real data and live configuration are
still pending. No approved provider/model was found, so non-mock mode fails closed.

From the repository root, after service-local locked setup:

```powershell
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve
```

Endpoints: `GET /health`, `POST /v1/extract` (includes summary), and
`POST /v1/document-answer`. The CLI uses loopback port 8003 by default and produces
no HTTP access logs. Set the agreed server-side token for exposed-service auth.

[Setup, demos, tests and limits](../../docs/extraction-eval/integration.md),
[shared dependency requests](../../docs/extraction-eval/milestone-requests.md).
