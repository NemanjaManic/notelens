# Single CQ-01 V2 Trial: Validated Public Probe

Owner: Nemanja (A). Prepared: 2026-11-17. Executed: 2026-11-18.
Code checkpoint: ed5b302. Status: one approved actual probe validated and cached.

Nemanja separately approved one public CQ-01 probe of the
[v2 evidence-selection prompt](evidence-selection.md) on 2026-11-18. The
[proposal](selection-trial-proposal.json) records that exact approval. One fresh
count and one generation request produced a structurally valid full-coverage
assessment with exact Python-resolved quotes. See the [actual result](selection-trial-results.json).
The two previous v1 attempts remain halted. No additional generation or other
question is authorized by the consumed one-attempt approval.

## Scope approved for the one actual execution

| Item | Approved value |
| --- | --- |
| Question/model | CQ-01 only; gpt-6-luna |
| New attempts | At most one fresh input count and one generation attempt |
| Input ceiling | 20,000 provider-counted input tokens; reject excess before generation |
| Maximum output | 2,048 tokens |
| Reasoning/timeout | none; 30 seconds per request |
| Automatic retries | Zero, including SDK retries; halt after failure |
| Cumulative reference-price allowance | USD 0.02, including both earlier retained reservations |
| Provider settings | service_tier=default, store=false, no tools/history, truncation=disabled |

The exact approved scope is
`31a4334ed974edfb0b84a88d0a8a4b77c0ab1a38fe94834b2ce09fbc3e1b4bc7`.
It binds the complete native request fingerprint
`80446125fd83c4f4da7af137a4a24c2bae4e77f5bef548303367d221c7d13861`,
the v2 prompt/catalog, parameters, source versions, mode and both historical
ledger anchors. Approval, explicit --execute, the exact cumulative budget and a
separate assessment activation flag gated this request. The flag was enabled
only for its execution process and restored afterward; the actual .env was not
edited. The actual assessment activation setting is false again.

## Accounting and execution

The latest v1 retry ledger already includes both earlier attempts. Its cumulative
USD 0.0027622 reservation is carried forward once; the first ledger's reservation
is not added again. The original and retry SHA-256 anchors are respectively:

- `4d078067ef2df168281ebe8aa99f3bd59b933cdeea792c62cb8e53415092db05`
- `1b04e28fdc04723930820f1d2b04d670951eea7d65e01f84badca3329de96299`

At the recorded standard reference prices, the maximum new reservation under the
input/output ceilings is USD 0.003024, giving USD 0.0057862 combined. These are
reference-price calculations, not verified billing or an account-wide spending
control. The failed earlier requests are not assumed free. Applicable standard
rates were rechecked on 2026-11-18 and matched the recorded rates. See the
[OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6-luna).

The approved execution freshly counted 11,029 input tokens for the exact new
prompt/input/schema, enforced the input ceiling and persisted the reservation
before generation. Response usage matched that count and reported 204 output
tokens, 11,233 total. The checked SDK path validated the pricing tier, native
completion/JSON/usage, evidence-ID selection and exact Python-resolved quotes.

The fixed new directory is services/rag/.cache/selection-trial-cq01-v2, ignored by
Git. Its selection-trial-usage-v2 ledger records the prior ancestry and cumulative
amounts. Locks are acquired in original-trial, retry, then new-trial order. Old
files are read and verified, never reset or rewritten. Missing/changed history,
scope drift, stale locks, corrupt caches and inconsistent accounting fail closed.
Confirmed cached results are read without another provider call; failed or
incomplete attempts block further generation. A simulated failure to persist the
final halt flag also left the reserved attempt blocking another provider call.
Manual deletion/editing of state is not an approved retry mechanism.

## Safe local inspection

From this checkout with prepared public artifacts and both retained histories:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.selection_trial
```

Default inspection needs no key and makes no remote counting/generation calls.
The uv --offline flag controls dependency resolution; the default CLI inspection
path prevents provider calls. The approved scope's one generation attempt is now
consumed. Default inspection describes
the configured scope, not a renewed allowance. A confirmed result can only be
replayed from its hash-verified cache; missing/corrupt confirmed caches fail
closed. There is no count-only action or continuation to CQ-02/CQ-08. Fresh
clones lack the ignored execution histories and result cache; copying, deleting
or editing state is not new execution approval.

## Actual checks and limitations

All 38 new tests and the full 623-test RAG suite passed on Windows/Python 3.13.5
(17.17 seconds for the final full run):

```powershell
& services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

The actual SDK uses MockTransport in tests. Checks cover fresh consent and old
approval rejection, single-question admission, token/allowance gates, exactly-once
carry-forward, all three locks, on-disk reservation before generation, v2 quote
resolution, failed or incomplete attempts, cache integrity, prepared-request drift,
and write-failure blocking. Offline wheel build and isolated packaged inspection
with explicit repository context passed; the packaged pending gate also rejected
execution without provider creation. V1 prepared requests remain byte-identical.

One initial focused run had an existing generation-failure halt-state assertion
fail (83 passed, one failed). The same case passed in isolation and the unchanged
runtime passed a repeated 84-test focused run. Its cause was not established.
The old regression now also checks its expected provider error code, and the
separate deterministic halt-write fault test verifies no extra provider call.
The final full 623-test run passed; these observations do not establish a cause
or claim a runtime repair for the earlier transient failure.

The [preparation-time preflight record](selection-trial-preflight.json) confirms both old
ledgers are byte-identical, their cumulative amount is counted once, no new
trial directory was created and pending execution was rejected. There were zero
real key loads, provider creations or provider requests during that guard.
Those preparation observations remain a historical snapshot. The later actual
execution and cache verification are recorded separately below. The actual .env,
shared contracts, mock HTTP routes and other owners' source remain unchanged.
A-004/A-009 and their actual shared prerequisites remain incomplete.

## Actual result, 2026-11-18

All 623 offline tests passed again immediately before the approved execution
(18.57 seconds); no runtime source, prompt, schema or validation predicate was
changed for the run. The CLI was invoked once with --execute --budget-usd 0.02,
exited 0 and reported coverage=full with cache_hit=false. There was one fresh
count and one generation attempt, zero automatic retries, and no CQ-02/CQ-08 call.
The inputs were saved public retrieval candidates; this probe did not perform a
new query embedding or vector search, nor test an end-to-end shared HTTP route.

Both supplied requirements were supported, with four evidence references over
three distinct canonical spans from two sources. Python supplied all quote text
and offsets, and every quote exactly matched its original passage slice. Agent
review of all selected spans found that they explicitly cover systolic pressure
during heartbeats and diastolic pressure between beats. This is an agent review
of one public development question, not independent team/clinical acceptance or
a general quality benchmark. semantic_support_independently_verified and
wire_mapping_applied remain false in the saved decision.

The new reservation is USD 0.0021269; the retained cumulative reservation including
both earlier attempts is USD 0.0048891. Reported usage gives USD 0.0012049 at the
recorded standard reference prices. Actual billing, cache-price details and the
earlier failed requests' charges were not inspected. Reservations were not refunded.

The validated public result is stored in the ignored result cache. Re-reading it
with no key/activation and provider creation forbidden returned cache_hit=true,
made zero provider calls and left all three ledgers and the cached bytes unchanged.
The two earlier ledgers remain halted; this new ledger has one confirmed attempt,
halted=false and no remaining new attempt in its scope. Both other question IDs
were rejected and all original/retry paths remained blocked. No lock remains.
The [result record](selection-trial-results.json) stores hashes, usage and evidence
references without redistributing the raw provider response or quote bodies.

The subsequent approved [coverage trial](coverage-trial.md) produced validated
CQ-02 partial and CQ-08 missing-evidence decisions while preserving this ledger
and carrying its inclusive reservation once. This single-question runner still
cannot admit those IDs. Real literature answer generation and shared HTTP
integration remain outside both increments. The coverage trial is a distinct,
consumed scope; neither runner grants an additional provider attempt.

The scoped speckit-implement workflow used specs/001-rag and the official
PowerShell prerequisite resolver with nonpersistent context. No extension hooks
were present; existing task IDs/checkboxes and dependency gates are unchanged.

| Checklist | Total | Checked | Unchecked | Status |
| --- | ---: | ---: | ---: | --- |
| requirements.md | 16 | 16 | 0 | PASS |
