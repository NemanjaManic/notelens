# Reviewed D-004/D-005 service handoff — 2026-11-23

## Result and scope

D-owned D-004 extraction and D-005 summary/document-answer implementation and
bounded synthetic live verification are complete. Service SHA:
`c7d0797a86061c643b0f23e6d56f8caa9e7a6813`.
All 112 service tests pass. Saved final live Responses replay through both
authenticated HTTP routes returned 200 without another provider call.

The provider's diagnostic message established the HTTP 400 cause: JSON object
mode required the word JSON in the input message; the prior separate instructions
did not satisfy that observed validation. The corrected user input contains an
explicit JSON instruction. Input-derived code-point line hints, conservative
time/subject instructions and explicit root/component version rules address
subsequent validation failures. No reference/annotation labels entered requests.

The private adapter can align invalid coordinates only when the quoted string
occurs exactly once; valid repeated-quote positions are preserved and ambiguous
or absent quotes fail. It never changes claims, identities or labels. The final
two real model results needed **zero coordinate adjustments** and passed unchanged.
Earlier failed responses remain preserved and are not counted as successful.

Agent semantic review confirmed five source-supported extraction mentions,
including negation, suspicion, family subject and the historical performed
procedure; five supported English summary claims; and one complete cough answer
with an exact selected-document citation. Unstated time/subject remains unknown.
This is agent review of a single synthetic document/question, not independent
human evaluation or broad quality measurement.

## Pins and receipts

- Model: `gpt-6-luna`; input format `messages`; output ceiling 2,048 tokens.
- Extraction prompt SHA-256: `d724ae9868b6f1df49195649e96ecea57f0db9143ce1c69bc0596125ab74586f`.
- Answer prompt SHA-256: `ad99f61436f97a058ab6f3fb0c713fda31100abee8f6b0333e84487289dd0bfa`.
- Service uv.lock SHA-256: `626b44bcd33a7f2acb782a13b0339949a80adf255a79893bbff94e287cb0dec4`.
- Generated contract SHA-256: `707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78`.
- [Reviewed receipt](../../eval/reports/development/d004-d005-provider-review-v3.json)
  SHA-256: `c96bcd3aba9c30041602012745f1bc48f25681d67e0ffec31fa2af59f715c1ff`.
- [Machine-readable handoff](../../eval/reports/development/d005-reviewed-service-handoff-v3.json).
- Private package: `Predaja-NoteLens/D-005/D005-reviewed-synthetic-service-handoff-v3.zip`.
  SHA-256: `e3ae6b924d80d122afa3b88fa23830bd220a9dc81bb66cfabcdacfe20182ecaf`.

Six deliberate diagnostic/revision-verification calls were made under Milica's
new continuation request; automatic network retries were zero. Known cumulative
worst-case reservations are USD 0.0215100, within the retained USD 0.10 cap.
This is not billed spending; actual usage is retained in successful responses.
All earlier receipts and failure history are preserved. No final QA was accessed.

## Locked Windows startup

Use a clean service checkout at the SHA above, Python 3.13.7 and the committed
lockfile. Retain B's separate e61140d mock checkout. Fresh dependency setup:

```powershell
python -m venv services/extraction/.bootstrap
./services/extraction/.bootstrap/Scripts/python.exe -m pip install uv==0.13.7
./services/extraction/.bootstrap/Scripts/uv.exe sync --locked --directory services/extraction --python 3.13.7
```

These are fresh-machine handoff instructions; the already-locked local environment
was used for today's tests. Configure OPENAI_API_KEY and NOTELENS_SERVICE_TOKEN
privately in the approved server process. Use an explicitly reviewed app policy
with model gpt-6-luna, input_format messages, zero retries, current rates, approved
call/token/budget limits and a new exclusive receipt. Do not reuse/reset receipts.
The consumed diagnostic continuation does not grant new app-generation calls.

```powershell
$env:NOTELENS_MODE = 'live'
$env:NOTELENS_EXTRACTION_PROVIDER_POLICY = 'C:\approved-execution\reviewed-app-policy.json'
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve --port 8003
```

Startup claims a receipt. Keep credentials server-side; readiness does not invoke
generation. No active app policy, key, service token or deployment is supplied by
this handoff. App policy/account setup must be reviewed before actual new calls.

## Message ready for Goran

Hi Goran,

D-004 and the D-owned D-005 provider-output review are complete for the synthetic
smoke. The reviewed service SHA is c7d0797a86061c643b0f23e6d56f8caa9e7a6813,
using gpt-6-luna and the prompt/contract/lockfile pins above. Both final raw outputs
passed validation unchanged; I reviewed five extraction items, five summary claims
and the document answer for source support, identity, exact citations and English.
All 112 service tests and both saved-live-response HTTP replays passed.

The locked Windows startup, receipt reference, findings and private package
checksum are above. Please repeat the app checks for document identity, exact
citation highlights, partial gaps and insufficient versus out-of-scope outcomes.
The two smoke results do not verify all those states. Any fresh app generation
needs a separately bounded execution policy; deployment acceptance and unseen
final measurement remain pending.

Thanks,
Milica

This message/package has been prepared locally, not sent to Goran by the agent.
