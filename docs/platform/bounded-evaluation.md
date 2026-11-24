# Bounded whole-web evaluation

## Key-free dry run

From the repository root, use the locked Windows setup from the
[Windows readiness runbook](deployment.md) and build the production app.

```powershell
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_bounded_evaluation.py
if ($LASTEXITCODE -ne 0) { throw 'Bounded evaluation dry run failed.' }
```

The checker uses versioned synthetic fixtures and three authenticated local HTTP
doubles. It exercises the app's document submission, fitted-classifier response,
report, question and citation paths with live-shaped D and RAG responses. The
normal scenario exercises two unique sources, concurrent report requests,
reopens, a duplicate source in another session and a cited answer. Fresh
scenarios exhaust each HTTP ceiling and verify no excess request reaches a
service. An injected retryable HTTP 503 verifies that the queued literature
branch and subsequent answer attempts stay unsent. The dry run also checks the
single-use startup receipt and shuts down its owned listeners.

## Provider-backed profile

Use the operator-approved config only after the team approves the system and
reference freeze and the complete provider execution scope. Keep it in the
approved restricted run directory. The local JSON has these required fields:

- `approved` set to true and a stable `run_id`.
- `services.rag`, `services.extraction` and `services.classifier`, each with the
  approved loopback `port` and expected `model_version`.
- `http_limits` with explicit nonnegative integer ceilings for `extract`,
  `document-answer` and `literature-answer`.
- `http_timeout_ms` with the approved time limit for a single web-to-service
  request, bounded by the one-hour document lifetime.

Start the pinned, independently bounded service instances. Set the three
service authentication tokens server-side using `NOTELENS_RAG_SERVICE_TOKEN`,
`NOTELENS_SERVICE_TOKEN` and `NOTELENS_CLASSIFIER_SERVICE_TOKEN`. Run the launcher
against the approved config:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/start_bounded_evaluation.py $approvedConfig
```

The launcher checks authenticated live readiness and the three expected model
versions, then starts one web process on loopback with its own labelled profile.
It claims the run once in the restricted config directory and preserves the
startup receipt even when startup fails. Preserve that receipt and the upstream
provider receipts when recording the outcome.

The app serializes D and RAG exchanges. It reserves an attempt before dispatch,
uses separate operation ceilings, and stops further dispatch after a failed
exchange or an attempt to exceed a ceiling. Partial and insufficient evidence
records can still be valid exchanges. Local classifier requests do not consume
the provider ceilings.

Extraction is attempted at most once per canonical text SHA-256 in the run.
The owning session's active document entry stores the in-flight and completed
result, so reopens, question turns and citation links reuse it. Use the original
document ID and owning session for other questions on that source. Resubmitting
the same source under a new ID cannot launch another extraction or access the
original session's result. Session expiry or deletion removes the report result.

These are app-to-service HTTP ceilings. D and RAG must independently enforce the
approved provider-call, token, cost and retry limits inside their services. A RAG
HTTP request can make several completion or embedding calls. The dry run verifies
the web dispatch controls and supplies no provider-spend or final-case evidence.
