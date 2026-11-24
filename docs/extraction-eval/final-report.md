# D-009 final measured delivery report

Date: 2026-11-24. **D-009 evaluation execution and reporting completed. Quality
limitations remain explicit; this is not a quality-gate pass.**

The complete fixed 26-case workload finished once after the confirmed B budget
fix. The selected result is attempt 13, the first pass on that repaired candidate;
it is not a combination of earlier results or the best of repeated unchanged runs.

## Frozen execution and measured results

- Run UUID: `7e0e606d-4e99-4f38-96bf-632f126dd3a6`.
- App/D candidate: `b5e09ea746aab812882bfc38963ff3ef1cfd80f8` (based on main `ebe37dbd217483a152d1c33e70e0ff9fe034a1fc`, plus the disclosed A/B/D fixes).
- A operational launcher SHA-256: `553f1141840610f0cabaa90509c27bcda0adbeccf6523d078eab92160a5f3772`.
- C-008 startup manifest: `affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32`.
- Receipt SHA-256: `2702e05532acc17baf8fb5f4b37b2b3c02e73ffcfed792c4c366b249c0258072`.
- [Execution freeze and artifact hashes](../../eval/config/d009-attempt13-execution-freeze-v1.json).
- [Aggregate results, ranks and cost evidence](../../eval/reports/final/d009-attempt-13-summary-v1.json).

| Measure | Result |
| --- | --- |
| Fixed runtime cases saved and completed | 26/26 |
| Technical errors | 0 |
| Canonical source documents | 16/16 |
| Accepted answer branches with valid schema | 28/28 |
| Accepted branches with exact literal citations | 28/28 |
| Explicit unsupported literature branches | 4 |
| Answer route agreement | 20/26 |
| Evidence-state agreement | 15/26 |
| End-to-end topic Recall@5 (15 positive-reference cases) | 0.7333 |
| End-to-end topic MRR@5 | 0.7333 |
| All-required-topics@5 | 0.7333 |
| Required passage-group coverage@5 | 0.7333 |
| Secondary: Recall@5 only where retrieval actually ran | 1.0000 (11 positive cases) |
| Final extraction F1 | Unmeasured |
| Independent semantic answer risk | Unmeasured |

Four model scope abstentions produced no ranked retrieval. They remain empty
predictions on the primary full 15-case relevance denominator; they are not
dropped to obtain the secondary attempted-only score. The primary end-to-end
Recall@5 of 0.7333 is below the recorded 0.90 criterion. The route/state mismatches
and abstentions remain measured limitations. The four unsupported branches are
not described as correct answers merely because the pipeline completed.

Ranked metrics use actual retained passage/topic identifiers and the existing
`notelens_eval.retrieval_metrics.evaluate_retrieval` implementation. The separately
reported cited-source proxy is not substituted for ranked Recall@5. Structural
citation checks establish exact text/identity, not semantic entailment or clinical
correctness. Extraction F1 lacks separate final annotations; independent semantic
risk lacks eligible independent ratings. Earlier D-011 quality exceptions remain
visible. No threshold was lowered or missing metric replaced with a passing value.

## Confirmed cause and repairs

The reproducible 22/26 stop was in B's global run budget. A legitimate unsupported
literature outcome was accepted by the runner but set the shared web budget's
stopped flag. The next extraction was blocked before any D provider dispatch and
appeared as `source_analysis_unavailable`. Attempt 12's durable D ledger proves
there was no new D call for that failed source. The fix continues only after an
explicit unsupported literature branch; invalid/unavailable outcomes and budget
violations still stop. A regression failed before the fix and passed after it;
the real built-app local-double check verified the next unique extraction.

A separate A diagnosis caught `ready` question decomposition with empty parts.
After the already bounded retry, the new optional fallback preserves the original
complete question as one requirement. Support and citation validation still apply;
abstentions, timeouts and budget failures do not use that fallback. This selected
run used the fallback **0 times**, so its successful
completion must not be attributed to observed fallback use. Safe error frames and
ranked source IDs are retained without question/passage bodies in the A ledger.

D now has explicit, policy-gated structural re-generation (up to three), with zero
network retries. Default live behavior remains one attempt. Reservations use the
existing conservative serialized-UTF-8-plus-framing upper bound, retain the original
64000-token admission ceiling, and enforce both the 64-call and USD 0.50 limits.
The durable journal fsyncs each reservation before dispatch and retains provider
IDs, usage and uncertain reservations. No prompt, model, canonical text, frozen
reference or citation validation was weakened. This run used 0 D structural
re-attempts; the observed stop removal is explained by the confirmed B fix.

## Cost, shutdown and historical attempts

| Component | Calls | Reserved USD | Conservative usage calculation USD |
| --- | --- | ---: | ---: |
| D | 32 generations | 0.2429121750 | 0.0105853 |
| A | 40 generations, 12 embeddings, 40 free counts | 0.02846490900 | 0.02003987150 |
| Combined | This run only | 0.27137708400 | 0.03062517150 |

Usage calculations apply the approved conservative rates, not a verified provider
invoice. Historical D spend remains unreconciled; a fresh run ledger does not reset
or reconcile cumulative account usage. All provider attempts remain reserved.
The Windows job drained and all four listeners closed. No deadline fired.

The [first nine attempts](../rag/d009-run-attempts-2026-11-24.md) remain preserved.
[Attempt 10](d009-attempt-10-7c1e46b5-ae55-4fa0-acf0-0ca0297b0963.md) saved nine records
(eight completed and one unavailable); its precise A failure was not retained.
[Attempt 11](../../eval/reports/final/d009-attempt-11-summary-v1.json) saved 18 cases;
[attempt 12](../../eval/reports/final/d009-attempt-12-summary-v1.json) saved 22 and
exposed the B stop-after-gap defect. Separate paid diagnostic requests are disclosed
in the private receipts: one query embedding, two bounded A diagnostic runs, and
one D extraction. These diagnostic outputs are not used as final predictions.

This is a repeated protected-workload evaluation after post-hoc reliability fixes,
not a pristine unseen first measurement. All model/prompt/reference pins and
operator policies are recorded. The official all-component freeze CLI was not run;
the delivered protocol is branch structural scoring plus the existing ranked
retrieval scorer. No extraction or independent semantic acceptance is implied.

## Verification and delivery state

- D: 145 offline tests passed, including explicit retry limits, no network retries,
  exact cost/call guards, and durable pre-dispatch reservations.
- A: the 836-test full suite passed before the source-only rank trace addition;
  all 35 focused final-runtime tests passed after that addition.
- B: all five budget regressions and the locked web build passed. Counted local
  services verified continuation after a real unsupported response while preserving
  first-error stops, ceilings, source reuse and single-use startup receipts.
- Six D scorer regressions passed, including run-identity mismatch, repeated hashes,
  missing-rank denominator preservation, and unavailable-versus-unsupported outcomes.
- The full saved-output checksum inventory and all 16 document bindings verified.

Code and evidence are delivered through the team-reviewed main-integration PRs
[#55](https://github.com/NemanjaManic/notelens/pull/55),
[#56](https://github.com/NemanjaManic/notelens/pull/56), and
[#57](https://github.com/NemanjaManic/notelens/pull/57). The global handoff check still encounters an existing
C-owned `specs/003-classification/tasks.md T011` dependency-format error; it was not
changed under the delegated A/B/D scope. Raw inputs, outputs, indices, model bundles,
gold references, credentials and native receipts remain private.
