# Partial and Missing Evidence: Actual V2 Probes

Owner: Nemanja (A). Date: 2026-11-18.

Nemanja authorized continued A-owned work, including these two public probes
under the existing cumulative USD 0.02 assessment allowance. The scoped
[proposal](coverage-trial-proposal.json) records that authorization; it does not
reset or add to the allowance. Both attempts completed successfully. The
[result record](coverage-trial-results.json) contains usage, hashes and evidence
references without raw provider responses or quote bodies.

## Observed behavior

| Public development case | Actual coverage | Input / output tokens | Evidence behavior |
| --- | --- | --- | --- |
| CQ-02: COVID-19 cause and contagiousness duration | partial | 13,165 / 213 | SARS-CoV-2 supported by one exact quote; no duration borrowed from RSV. |
| CQ-08: Trigeminal neuralgia incidence in Serbia in 2025 | none | 5,277 / 173 | No supplied passage supports the requested new-case rate; no evidence reference fabricated. |

Together with the earlier [CQ-01 result](selection-trial-results.json), the v2
path now has one actual full, one partial and one missing-evidence example.
These are public development probes with supplied requested parts and saved
retrieval candidates. They did not run a new embedding or vector search.
Agent inspection of the selected COVID-19 quote and all five CQ-08 candidates
agreed with these limited decisions. This is not independent team/clinical
acceptance, held-out evaluation or a general quality benchmark.

The model selects offered evidence IDs. Python resolves them to immutable
passage slices, then checks the original support rules and exact Unicode
offsets. V2 prompt/catalog/configuration and the v1 snapshots were unchanged.
The saved semantic_support_independently_verified and wire_mapping_applied
flags remain false. No final answer or live shared HTTP route is claimed.

## Execution and cumulative accounting

The runner admits CQ-02 first and CQ-08 only after a confirmed CQ-02 result.
Each invocation explicitly selects one question. There is no automatic loop,
retry or continuation after a failure. Both invocations exited 0, with one fresh
input count and one generation attempt each. Input counts matched response
usage; max input was 20,000 tokens, max output 2,048, reasoning none, timeout
30 seconds, SDK retries zero, store false and service tier default.

The latest inclusive historical reservation was carried forward once. Reference
prices were rechecked on 2026-11-18. The two new results account for USD 0.0020372
in reported-usage reference costs and USD 0.0038922 in reservations. Including
all retained assessment history, confirmed reference usage is USD 0.0032421 and
reserved reference cost is USD 0.0087813, below the cumulative USD 0.02 limit.
Actual invoice, cache pricing and earlier failed-request charges were not
inspected. No reservation was refunded.

Original v1, retry v1, prior CQ-01 v2 and new coverage state have separate
directories. Locks are acquired in that order. Missing/changed history, corrupt
caches, source/request drift, wrong order, incomplete attempts and inconsistent
accounting block further generation. The original two ledgers remain halted.
The new two-attempt scope is consumed, even though halted is false. Deleting or
editing a ledger is not authorization to repeat it. The real .env was unchanged
and activation was disabled again after each invocation.

## Local inspection and checks

With the prepared public corpus and retained local history in this checkout:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.coverage_trial
```

Default inspection prints scope metadata and makes no key/provider request.
The uv offline option controls dependency resolution; it is the CLI's default
inspection path that prevents API calls. Fresh clones lack the ignored execution
history and cached results. This command is not a new execution allowance.

All 36 new coverage tests and the full 659-test RAG suite passed on Windows with
Python 3.13.5 (26.20 seconds for the full run). SDK tests use MockTransport and
fixture credentials. They cover ordering, exactly-once historical carry, all four
locks, authorization/cap checks, disk reservation before generation, malformed
selections, cache integrity, source drift, stop-on-failure and halt-write failure.
Offline wheel build and isolated packaged preview/disabled-activation checks
passed before execution. No new dependencies were added.

After execution, both actual results were replayed with activation disabled,
key loading/provider creation/network forbidden: two cache hits, zero provider
calls. All four ledgers and all three validated result caches remained
byte-identical; unrelated question IDs were rejected and no lock remained.
The [preparation preflight](coverage-trial-preflight.json) remains a historical
snapshot of the earlier unapproved state, separate from the actual run record.

The scoped speckit-implement workflow used the official PowerShell resolver for
specs/001-rag with nonpersistent feature selection and no extension hooks.

| Checklist | Total | Checked | Unchecked | Status |
| --- | ---: | ---: | ---: | --- |
| requirements.md | 16 | 16 | 0 | PASS |

## Next boundary

A-004/A-009 remain open. Next work is A-owned answer composition from validated
support decisions, followed by actual transport integration and evaluation.
Automatic requested-part extraction for new questions is also unfinished.
The existing [partial-answer wire interpretation](answer-support-policy.md#frozen-interface-interpretation-requiring-confirmation)
is still a proposal: this increment does not settle it or alter shared contracts.
Current main remains the documentation handoff; F-014 is not claimed complete.
Independent owner-local preparation can continue under Nemanja's authorization.
