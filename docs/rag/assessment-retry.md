# Single CQ-01 Assessment Retry: Prepared, Execution Not Approved

Owner: Nemanja (A). Prepared: 2026-11-17.
Code checkpoint: cb0d9c2ec92a3caa8f377478d7b764e4ff30f26c.

Nemanja approved preparing one controlled retry and local checks, without provider
calls. The [retry proposal](assessment-retry-proposal.json) still has
execution_approved=false and approval=null. Preparation does not reopen the old
three-question trial. The first CQ-01 failure remains undiagnosed retrospectively;
the new diagnostics will locate rejected conditions in any future response.

## Proposed execution scope

| Item | Value pending a separate execution decision |
| --- | --- |
| Question | CQ-01 only; no CQ-02/CQ-08 continuation |
| Model/input | Same gpt-6-luna prompt, structured schema, saved candidates and requested parts |
| Maximum new attempts | One, with a fresh input count before generation |
| Input/output limits | 20,000 input tokens; 2,048 maximum output tokens |
| Reasoning/timeout | none; 30 seconds |
| Automatic retries | Zero, including SDK retries |
| Cumulative reference-price allowance | USD 0.02, including the original retained reservation |
| Provider settings | service_tier=default, store=false, no tools/history, truncation=disabled |

The new approval must bind scope
`13139aecb51365d4aa0fb2945320fd637541222abe8469a6f455807683708964`.
The old approval cannot authorize this scope. Execution also needs the separate
assessment activation flag, a server-side key and an exact cumulative budget
argument. The actual .env was not edited and the flag was not activated.

## Preserved accounting and state

The original services/rag/.cache/assessment-trial/usage.json remains halted and
byte-identical, with SHA-256
`4d078067ef2df168281ebe8aa99f3bd59b933cdeea792c62cb8e53415092db05`.
Its USD 0.0013811 reservation remains counted. Confirmed usage of zero does not
establish that the original request was free; actual billing was not inspected.

A separately authorized attempt would use the fixed ignored directory
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
invoice, account-wide spending control or a fresh price verification. Recheck
the applicable model/rates before a separately authorized actual execution.

## Available now: key-free inspection

From this checkout with its original public artifacts and retained local history:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.assessment_retry
```

Default inspection does not load the key, create a provider client, count input
remotely or generate. Fresh clones lack the ignored original history and cannot
execute this retry without that verified history. The uv --offline switch controls
dependency resolution; the CLI's default inspection path prevents provider calls.
Even explicit --execute remains blocked by the pending proposal. There is no
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
request bytes. A separate [actual-history guard check](assessment-retry-preflight.json)
blocked the new unapproved attempt and all original case IDs without loading a key
or creating a provider client. The new retry directory was not created. No paid
or free provider requests were made during preparation.

The scoped speckit-implement workflow selected specs/001-rag using the official
PowerShell resolver with nonpersistent context. The requirements checklist had
16 checked and zero unchecked entries; no extension hooks were present. Existing
task IDs, checkboxes and actual shared dependencies remain unchanged.

This does not produce an actual validated model assessment, semantic-quality
measurement, literature answer or live HTTP route. A-004/A-009 and shared gates
remain incomplete. Next is a separate owner decision on this one execution;
any further attempt or other question needs its own reviewed scope.
