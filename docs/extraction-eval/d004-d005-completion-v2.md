# D-004 and D-005 completion package — 2026-11-23

## Prepared service

Service SHA: `30fa30b372489c2a03c1579cf27081f629992bc4`.
All 107 service tests passed on Windows/Python 3.13.7, including simulated HTTP
provider checks. These are offline tests. The sole warning is the existing
Starlette/httpx test-client deprecation.

Provider failures now retain HTTP status and allowlisted error type/code/parameter
in operator-only exception diagnostics. Raw upstream error text, headers and
unknown fields are discarded. Public API error envelopes remain unchanged.
This fixes lost failure evidence, not the unproven HTTP 400 root cause.

The provider/policy now support explicit `input_format: messages`; default text
input and both original 512-token trial hashes remain unchanged. The
[Responses reference](https://developers.openai.com/api/reference/resources/responses/methods/create)
allows both forms. An explicit user input_text message is a compatibility
hypothesis, not a verified live fix.

## Next trial: prepared, not approved or executed

The [exact proposal](../../eval/reports/development/d004-message-input-trial-proposal-v2.json)
pins both new payloads, prompts, contract and lockfile. Synthetic payloads are
private under `Predaja-NoteLens/D-004/D004-message-input-proposal-v2`.

- Same demo document, cough question and gpt-6-luna model.
- Explicit user input_text message; output ceiling 2,048 tokens per call.
- At most two new calls: extraction with summary, then document answer.
- Zero retries/repairs; stop at the first provider or validation failure.
- New exclusive receipt; preserve every old receipt and reserve before sending.
- New exact worst-case reservation USD 0.0043707.
- Known cumulative worst-case reservation USD 0.0100161, within USD 0.10.

The [model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
lists standard input/output rates USD 0.10/0.50 per million tokens, reviewed
2026-11-23. The bounds apply to that standard/default route. They are not actual
billing or an audit of undisclosed executions. Review changed rates/accounting
before sending. The old approval has zero calls remaining; the new proposal has
`approved: false`. No key was loaded or provider call made during preparation.

After explicit new authorization, the agent checks pins, loads the existing
encrypted key only into the authorized child process, reserves the limits and
executes each operation at most once. Save envelopes, usage and validated output
privately, or record the exact failing operation/service SHA and sanitized error.
Do not retry incomplete/failed responses. A larger ceiling does not guarantee success.

## Output review and D-005 handoff

After real outputs exist, D checks extraction mentions, assertion/temporality/
subject/procedure status; summary and answer support, completeness and English;
document IDs/hashes, exact citations and Unicode code-point spans; provenance,
explicit gaps, usage and receipts. The
[handoff candidate](../../eval/reports/development/d005-service-handoff-candidate-v2.json)
already pins service/model/prompts/contract/lockfile. Successful receipt and
semantic findings remain null until verified outputs exist.

Two synthetic outputs prove only their own behavior. Broader quality remains
D-011; sufficient/partial/insufficient/out-of-scope app cases currently have
offline coverage, not verified provider results. Send the completed reviewed
handoff to Goran for app acceptance. Any extra provider calls by the app need a
separately bounded approval; these two calls do not fund additional app execution.
Deployment and unseen-final measurement remain pending.

## Locked Windows startup

Use the service SHA above and committed lockfile. Retain B's separate e61140d
mock checkout. Fresh setup from the approved D checkout:

```powershell
python -m venv services/extraction/.bootstrap
./services/extraction/.bootstrap/Scripts/python.exe -m pip install uv==0.13.7
./services/extraction/.bootstrap/Scripts/uv.exe sync --locked --directory services/extraction --python 3.13.7
```

The existing environment passed tests; a fresh installation was not repeated.
For a later authorized app check, use a separate reviewed server-side policy with
an exclusive receipt, input_format messages, model, rates and remaining call/
token/budget limits. Load OPENAI_API_KEY and NOTELENS_SERVICE_TOKEN privately;
never use credential literals in commands or chat. Then:

```powershell
$env:NOTELENS_MODE = 'live'
$env:NOTELENS_EXTRACTION_PROVIDER_POLICY = 'C:\approved-execution\reviewed-provider-policy.json'
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve --port 8003
```

No active policy or service token is committed. Startup claims a receipt; do not
restart with a new receipt to reset the budget. Readiness does not prove generation.

Milica's next action is explicit approval for the exact new trial above. The
agent handles execution, result verification and D-005 handoff preparation.
Goran owns the app recheck. No API key resend or repeated setup confirmation is needed.
