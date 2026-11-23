# NoteLens extraction service

Member D's service uses the frozen 1.0.0 Python contract package. Default mock
startup accepts canonical English document requests and produces literal,
document-grounded extraction, summary and document-answer examples. Configured
provider startup uses the explicit server-side execution policy described below.
Missing live configuration returns `configuration_required`.

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

Trial preflight can call `OpenAITrialProvider.prepare` with the built-in request
and `generation_instructions(operation)[0]` to compute the exact outgoing
payload without sending it. Record its `request_sha256`, a reviewed upper
bound on all billable input tokens for that payload, and reviewed standard
input and output token rates. The output ceiling comes from the same payload.

`openai_transport.trial_provider` connects those reviewed bounds to HTTPS.
It uses the full worst-case reservation, including for timeouts and HTTP
errors, and permits at most three distinct approved requests within USD 0.10.
The current adapter prepares only two operations. Use one stable receipt
path for the approved trial across processes and restarts. The transport
claims that path exclusively before it can send and does not resume a
previous trial. The receipt contains no credential, input, or output.

To execute the approved one-time smoke after configuring the server-side
`OPENAI_API_KEY`, run from the repository root:

```powershell
./services/extraction/.venv/Scripts/python.exe services/extraction/scripts/run_synthetic_live_trial.py
```

The runner accepts no document or question arguments. It rechecks both approved
payload hashes before sending, uses the two recorded input bounds and 512-token
output limit, and creates the fixed receipt before the first provider call. A
failed or interrupted run consumes the receipt and cannot be resumed or retried.

## Configured provider over HTTP

The HTTP service can use `OpenAIResponsesProvider` for canonical document requests,
including app-issued document UUIDs. The existing synthetic trial retains its
exact two-request boundary. Default startup uses the mock provider.

An operator supplies a completed copy of
`fixtures/provider-policy.template.json` through the server-side
`NOTELENS_EXTRACTION_PROVIDER_POLICY` environment variable. The policy declares
the approver, operator, execution scope, accessible model, reviewed input/output
rates, remaining approved balance, token and call ceilings, timeout and zero
retries. Review the fixed input bound against the exact payloads. Admission uses
the reviewed UTF-8 request byte count plus 1,024 framing tokens. The policy
reserves its full input/output ceiling before every network attempt, including
failed and timed-out attempts. The approved balance must cover the intended
requests at their worst-case cost.

Configure `OPENAI_API_KEY` and the private `NOTELENS_SERVICE_TOKEN` in the server
process. Then start from the repository root after the locked service-local
dependency setup.

On this Windows workstation, a key may instead be handed to the authorized local
operator as an encrypted SecureString CLIXML file under
`services/extraction/.local-secrets/openai-key.xml`. The directory is ignored by
Git. Enter the key with `Read-Host -AsSecureString` and pipe that value directly
to `Export-Clixml`; do not put the literal key in a command, chat, documentation,
source file or log. Windows protects the exported SecureString for the same user
and computer. The server process must explicitly import/decrypt it into its
private `OPENAI_API_KEY` environment before provider startup; the service does
not automatically load CLIXML or a dotenv file. Key storage itself does not run
the trial, prove model access, claim a new receipt or alter the existing cap.

```powershell
$env:NOTELENS_MODE = 'live'
$env:NOTELENS_EXTRACTION_PROVIDER_POLICY = 'C:\approved-execution\provider-policy.json'
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve --port 8003
```

The receipt path is relative to the policy file. Startup claims it exclusively.
Preserve it after shutdown, failure or restart, and reconcile that execution
before authorizing another receipt. The original `.trial-receipt-2026-11-20`
remains part of its earlier execution. The template has no activation approval
or selected model/budget. Missing or invalid settings yield an unconfigured
provider. Authenticated readiness reports the configured model after valid setup.

The service applies the frozen schema, document identity, exact-span and
component-provenance validation to every returned result. Send B the reviewed
service commit, lockfile, startup policy identity and private verification
receipt after source review. The existing B mock runner is pinned to its mock
handoff. B's provider-backed app check needs the reviewed configured service.

### Prepared compatibility trial and internal error diagnostics

An operator policy may select `"input_format": "messages"` for a canonical request
encoded as a user message with an `input_text` block. Omit it or use `"text"` for
the existing string input. Unknown formats fail before claiming a receipt.
The consumed original trial stays archived at its recorded request hashes and
must not be restarted. Changed formats/prompts need newly reviewed payload pins
and execution authorization.

Non-200 responses retain bounded allowlisted operator metadata through
`ServiceError.provider_diagnostics`. Free-text messages and unknown values are
discarded. Diagnostics are not in the public error envelope. No retry is added.
See the [D-004/D-005 completion package](../../docs/extraction-eval/d004-d005-completion-v2.md)
for the prepared but unapproved trial and pending provider-output review.

The later [reviewed v3 handoff](../../docs/extraction-eval/d005-reviewed-handoff-v3.md)
supersedes that pending status: JSON mode now has an explicit JSON instruction
in the user input, source-derived code-point hints are provided and unique exact
quote alignment fails closed on ambiguity. Duplicate keys/nonfinite numbers are
rejected before alignment. The final synthetic extraction and answer passed
unchanged, with zero coordinate adjustments. Further app calls require a reviewed
bounded policy; the consumed original trial must not be rerun.

### Strict quote-hint candidate

The optional operator-policy field `"output_format": "quote_hints"` selects a
small strict provider schema instead of asking the model to emit the full wire
contract. The server builds identities, provenance, citation offsets and
displayed text from source quotes; the public API contract is unchanged.
Unresolvable candidates produce explicit incomplete/failed extraction outcomes,
and a failed summary preserves independently valid extraction. Omit the field
or use `"contract"` to retain the earlier behavior.

The [improvement report](../../docs/extraction-eval/extraction-improvement-v2.md)
pins the candidate, fresh/replayed sample scopes, counts and limitations. The
new candidate improves exact mention matching but does not clear the 0.90 F1
quality gate. Any new app/provider execution still needs a reviewed bounded
policy; the known cumulative reservation is close to the current USD 0.10 cap.
