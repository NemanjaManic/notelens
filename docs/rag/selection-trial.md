# Single CQ-01 V2 Trial: Prepared, Execution Approval Pending

Owner: Nemanja (A). Date: 2026-11-17. Code checkpoint: ed5b302.
Status: local preparation approved; no new provider request or execution approval.

This prepares one public CQ-01 probe of the [v2 evidence-selection prompt](evidence-selection.md).
The [proposal](selection-trial-proposal.json) has execution_approved=false and
approval=null. The two previous v1 attempts remain halted. The old approvals do
not authorize this new prompt, schema, evidence catalog or request.

## Proposed scope for a separate execution decision

| Item | Proposed value |
| --- | --- |
| Question/model | CQ-01 only; gpt-6-luna |
| New attempts | At most one fresh input count and one generation attempt |
| Input ceiling | 20,000 provider-counted input tokens; reject excess before generation |
| Maximum output | 2,048 tokens |
| Reasoning/timeout | none; 30 seconds per request |
| Automatic retries | Zero, including SDK retries; halt after failure |
| Cumulative reference-price allowance | USD 0.02, including both earlier retained reservations |
| Provider settings | service_tier=default, store=false, no tools/history, truncation=disabled |

The exact proposed scope is
`31a4334ed974edfb0b84a88d0a8a4b77c0ab1a38fe94834b2ce09fbc3e1b4bc7`.
It binds the complete native request fingerprint
`80446125fd83c4f4da7af137a4a24c2bae4e77f5bef548303367d221c7d13861`,
the v2 prompt/catalog, parameters, source versions, mode and both historical
ledger anchors. Fresh approval, explicit --execute, the exact cumulative budget,
a separate assessment activation flag and a server-side key are all required.

## Accounting and execution

The latest v1 retry ledger already includes both earlier attempts. Its cumulative
USD 0.0027622 reservation is carried forward once; the first ledger's reservation
is not added again. The original and retry SHA-256 anchors are respectively:

- `4d078067ef2df168281ebe8aa99f3bd59b933cdeea792c62cb8e53415092db05`
- `1b04e28fdc04723930820f1d2b04d670951eea7d65e01f84badca3329de96299`

At the recorded standard reference prices, the maximum new reservation under the
input/output ceilings is USD 0.003024, giving USD 0.0057862 combined. These are
reference-price calculations, not verified billing or an account-wide spending
control. The failed earlier requests are not assumed free. Recheck applicable
rates before a separately authorized actual execution.

The larger v2 input has not been counted remotely. An approved execution would
obtain a fresh count for its exact prompt/input/schema, enforce the input ceiling,
then atomically persist input-plus-maximum-output reservation before generation.
The same checked SDK path validates the pricing tier, completion/refusal/JSON,
usage, evidence-ID selection and exact Python-resolved quotes.

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
path prevents provider calls. Even explicit execution is blocked by the pending
proposal. There is no count-only action or continuation to CQ-02/CQ-08. Fresh
clones cannot execute without the exact verified ignored historical ledgers.

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

The [actual preflight record](selection-trial-preflight.json) confirms both old
ledgers are byte-identical, their cumulative amount is counted once, no new
trial directory was created and pending execution was rejected. There were zero
real key loads, provider creations or provider requests during that guard.
The actual .env, shared contracts, mock HTTP routes and other owners' files are
unchanged. No real v2 assessment, semantic-quality metric or literature answer
was produced. A-004/A-009 and their actual shared prerequisites remain incomplete.

The scoped speckit-implement workflow used specs/001-rag and the official
PowerShell prerequisite resolver with nonpersistent context. No extension hooks
were present; existing task IDs/checkboxes and dependency gates are unchanged.

| Checklist | Total | Checked | Unchecked | Status |
| --- | ---: | ---: | ---: | --- |
| requirements.md | 16 | 16 | 0 | PASS |
