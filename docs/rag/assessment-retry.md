# Single CQ-01 Assessment Retry: Approved Attempt Halted

Owner: Nemanja (A). Prepared: 2026-11-17.
Code checkpoint: cb0d9c2ec92a3caa8f377478d7b764e4ff30f26c.

Nemanja approved preparation and then explicitly approved one actual CQ-01 retry
on 2026-11-17. The [retry proposal](assessment-retry-proposal.json) records that
exact scope. One fresh count and one generation attempt completed, but local
validation rejected the first quote in the first part with quote_mismatch. The
retry is halted; no additional attempt is approved. See the
[actual result](assessment-retry-results.json). The original three-question trial
remains halted and its first historical failure is still undiagnosed.

## Scope approved for the one attempt

| Item | Approved value |
| --- | --- |
| Question | CQ-01 only; no CQ-02/CQ-08 continuation |
| Model/input | Same gpt-6-luna prompt, structured schema, saved candidates and requested parts |
| Maximum new attempts | One, with a fresh input count before generation |
| Input/output limits | 20,000 input tokens; 2,048 maximum output tokens |
| Reasoning/timeout | none; 30 seconds |
| Automatic retries | Zero, including SDK retries |
| Cumulative reference-price allowance | USD 0.02, including the original retained reservation |
| Provider settings | service_tier=default, store=false, no tools/history, truncation=disabled |

The recorded approval binds scope
`13139aecb51365d4aa0fb2945320fd637541222abe8469a6f455807683708964`.
The old approval cannot authorize this scope. Execution also needs the separate
assessment activation flag, a server-side key and an exact cumulative budget
argument. The actual .env was not edited. The flag was enabled only for the
execution process and restored afterward; actual assessment activation is false.

## Preserved accounting and state

The original services/rag/.cache/assessment-trial/usage.json remains halted and
byte-identical, with SHA-256
`4d078067ef2df168281ebe8aa99f3bd59b933cdeea792c62cb8e53415092db05`.
Its USD 0.0013811 reservation remains counted. Confirmed usage of zero does not
establish that the original request was free; actual billing was not inspected.

This attempt used the fixed ignored directory
services/rag/.cache/assessment-retry-cq01-v1. Its assessment-retry-usage-v1 ledger
records the prior scope/hash/amounts and combines old usage with the new attempt.
The original trial's default accounting and three-case limit are unchanged.
Both runners share the original lock, and the retry also locks its own folder.
Changed/missing history, stale locks, corrupt caches and mismatched accounting
fail closed. Failed attempts retain reservations and halt; validated cached results
can be read without a new provider call. Deleting state to obtain another attempt
is not an approved operation.

At the original recorded reference rates, the maximum new reservation under the
input/output limits is USD 0.003024; including the old reservation gives
USD 0.0044051. These are reference-price ceilings for this configuration, not an
invoice or account-wide spending control. Official model rates were rechecked on
2026-11-17 before execution and matched the recorded standard input/output prices.
See the [OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Available now: key-free inspection

From this checkout with its original public artifacts and retained local history:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.assessment_retry
```

Default inspection does not load the key, create a provider client, count input
remotely or generate. Fresh clones lack the ignored original history and cannot
execute this retry without that verified history. The uv --offline switch controls
dependency resolution; the CLI's default inspection path prevents provider calls.
Even explicit --execute is now blocked by the saved halted state. There is no
count-only action or automatic continuation to the other two questions.

## Actual preparation checks

All 33 new retry tests and the full 539-test RAG suite passed on Windows/Python
3.13.5 (14.52 seconds for the final full run):

```powershell
& services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

Checks cover fresh consent, old approval rejection, activation/key/budget gates,
CQ-01 admission, cumulative budget rejection when a new request would fit alone,
reservation before generation, safe diagnostics, retained failures, both locks,
cache reuse, history tampering, and preserving the old trial's halted behavior.
Tests forbid real key loading, live-client creation and network access, using the
actual SDK through in-memory MockTransport responses.

The offline wheel build and isolated retry-module import passed. Comparing all
three prepared model requests against the pre-diagnostics baseline found identical
request bytes. A separate [preparation-time guard check](assessment-retry-preflight.json)
blocked the new unapproved attempt and all original case IDs without loading a key
or creating a provider client. The new retry directory was not created during
that preparation check. No paid or free provider requests were made during
preparation. The later actual execution is recorded separately below; the
preparation snapshot is not overwritten.

The scoped speckit-implement workflow selected specs/001-rag using the official
PowerShell resolver with nonpersistent context. The requirements checklist had
16 checked and zero unchecked entries; no extension hooks were present. Existing
task IDs, checkboxes and actual shared dependencies remain unchanged.

## Actual execution, 2026-11-17

All 539 offline tests passed again before execution (13.83 seconds). Runtime
source, prompt, structured-output schema, candidate inputs and validation rules
were unchanged. The approved CLI was invoked once with --execute --budget-usd
0.02, a 30-second timeout and zero automatic retries. There was one fresh input
count and one generation attempt for CQ-01; CQ-02/CQ-08 were not attempted.

The CLI exited 1 with invalid_assessment and this safe diagnostic:

```json
{
  "format_version": "rag-validation-diagnostic-v1",
  "stage": "assessment",
  "rule": "quote_mismatch",
  "path": "/assessment/parts/0/evidence/0/quote"
}
```

The quote was nonempty, referenced a known returned passage and had integer
offsets within its bounds, but differed from that exact text slice. This does
not distinguish incorrect quote wording from incorrect otherwise valid offsets.
The raw failed response and output usage were not retained, so no particular
text edit or offset correction is inferred. This later diagnostic also does not
establish the cause of the original historical failure.

The fresh count was 3,571 input tokens. The new retained reference-price
reservation is USD 0.0013811; the cumulative reservation including the first
attempt is USD 0.0027622 under the USD 0.02 allowance. Confirmed reference usage
remains zero because no assessment passed all checks. Actual billing was not
inspected; this does not imply the model request was free.

An offline guard with provider creation forbidden blocked this retry and both
other question IDs, as well as all original trial IDs. Neither ledger changed
during the guard. There are no active locks or validated result caches, and the
activation flag is false. No attempt was repeated. No validated semantic decision,
clinical-quality metric, literature answer or live HTTP route was produced.
A-004/A-009 and shared gates remain incomplete.

## Proposed next local package: citation selection

One candidate improvement is to give the model precomputed canonical evidence
options with stable identifiers. The model would select evidence identifiers and
assess support; Python would copy the corresponding exact quote and Unicode
offsets from its own unchanged source mapping. Unknown evidence identifiers would
be rejected. This removes both quote reproduction and character-position
generation from the model while preserving exact canonical evidence validation.
Semantic support and explicit gaps would still require their existing checks.

This changes the internal assessment prompt/schema and needs a separate local
change-package approval. It is proposed only; neither implementation nor another
provider attempt is authorized by the completed execution above.
