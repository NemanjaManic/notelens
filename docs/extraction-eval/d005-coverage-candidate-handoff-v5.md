# D-005 coverage candidate handoff

Date: 2026-11-23. Candidate only; Goran app acceptance and D-011 quality remain open.

Use service commit `d41fa880177a7855bb92e57d98673b0a7a77d36b`, Python 3.13.7
and the committed `services/extraction/uv.lock`. Preserve the separate B mock
checkout pinned at `e61140d`. A previous receipt for `c7d0797` or `8ef63edd`
does not verify this new configuration. Do not reuse or reset an old live receipt.

Explicit server-side selection fields:

```json
{
  "model": "gpt-6-luna",
  "input_format": "messages",
  "output_format": "quote_hints",
  "prompt_profile": "coverage_v2",
  "reasoning_effort": "low"
}
```

These fields are a configuration excerpt, not a runnable approved spending policy.
The reviewed policy also requires operator, model access, scope, request/token/cost
bounds, timeout <= 60 seconds, zero automatic retries and a new exclusive receipt.
The completed development comparison does not provide a fresh app-call allowance.
Keep `OPENAI_API_KEY` and `NOTELENS_SERVICE_TOKEN` in the server process only.

Extraction uses `extract-quotes-v2.txt` / `d-quote-hints-prompts-v2`; answers use
`answer-quotes-v1.txt` / `d-quote-hints-prompts-v1`. An early source-based abstention
can have a null prompt version. The public quote-hint-built output version remains
`d-quote-hints-v2`. Exact file hashes are in the machine-readable handoff.
The provider returned the alias `gpt-6-luna`; no dated immutable model snapshot is claimed.

## Locked Windows startup

From a clean checkout at the service SHA above, using the existing approved
Windows setup:

```powershell
python -m venv services/extraction/.bootstrap
./services/extraction/.bootstrap/Scripts/python.exe -m pip install uv==0.13.7
./services/extraction/.bootstrap/Scripts/uv.exe sync --locked --directory services/extraction --python 3.13.7
```

For default mock inspection, no provider credentials or call policy are needed:

```powershell
$env:NOTELENS_MODE = 'mock'
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve --port 8003
```

For a separately approved configured live process, after private environment
setup and policy review:

```powershell
$env:NOTELENS_MODE = 'live'
$env:NOTELENS_EXTRACTION_PROVIDER_POLICY = 'C:\approved-execution\reviewed-app-policy.json'
./services/extraction/.venv/Scripts/python.exe -m notelens_extraction.cli serve --port 8003
```

Startup claims an exclusive receipt; health/readiness alone does not generate
answers. This handoff did not start a new live server or create an app receipt.
The locked dependency environment was already present for the local verification;
fresh installation on another host is an instruction, not a claimed executed check.

## Review findings and required app receipt

The paired six-document comparison improves exact F1 from 0.2984 to 0.4679 and
valid returns from 4/6 to 6/6. Four candidate extractions remain explicitly partial.
Temporal labels regress from 25/31 to 24/31 on identically matched mentions.
Quality acceptance fails; independent semantic answer risk remains missing.
All six synthetic QA outputs validate; one repeats the same sentence twice.
See [the measured report](economic-improvement-v4.md).

Goran's receipt should identify app SHA, this service SHA, model/profile/prompt
pins, startup profile, exact requests or replay hashes, and each failing step.
Check document identity, exact citation highlights including repeated/non-BMP
text, partial gaps and insufficient versus out-of-scope outcomes. Keep default
mock, saved-output replay and any newly authorized live generation distinguished.
The private candidate package includes six saved synthetic request/response pairs
for inspection; no provider call is needed to read them. It includes no final
cases, extraction gold labels, active policy or credentials.

Original D-004 receipt and the completed smoke review remain unchanged.
The new development execution receipt is separately referenced by the v4 plan
and execution report. Neither establishes deployment or joint final acceptance.
