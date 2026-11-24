# D-009 final run attempts and remaining work (2026-11-24)

Status: **D-009 is not formally complete.** No run saved all 26 cases and the official
freeze-based scorer was not run; attempt 9 was measured with a branch-level structural
scorer (results below). This record lists what was executed so
work can resume without repeating it. It contains identifiers, counts and hashes only;
no final question, document or reference text.

Operator for attempts 2-9: the repository user acting with Milica's delegated
authority. All runs used the pinned runtime package (manifest SHA-256
`bbba7cc5...fbda`, ZIP SHA-256 `a96ebf78...24f7`) and the bounded B runner with the
Windows job watchdog. Every attempt used a new UUID; no UUID or receipt was reused.
Outputs are stored privately under `%LOCALAPPDATA%\NoteLens\Restricted\D009\<run-id>`.

## Attempts

| # | Run ID | App | Saved cases | Stop point and cause | A reserved USD |
| --- | --- | --- | --- | --- | --- |
| 1 | `7a59879d` | `870599f` | 0/26 | F-DOC-01: D extraction provider request rejected; HTTP status not retained | 0 |
| 2 | `f6873748` | `423ca75` | 0/26 | Preflight `app_checkout_mismatch`: app worktree had untracked files | 0 |
| 3 | `4012142f` | `423ca75` | 0/26 | Startup: launcher set A paid-operation flags to `1`; A requires `true` | 0 |
| 4 | `81197e16` | `423ca75` | 17/26 | F-MIX-01: A support response failed validation; zero-retry halt | 0.0191 |
| 5 | `51545633` | `423ca75` | 11/26 | F-LIT-03: A question-parts response failed validation; zero-retry halt | 0.0045 |
| 6 | `db05e81e` | `423ca75` | 9/26 | F-LIT-01: A question-parts content check failed (outside first retry scope) | 0.0003 |
| 7 | `1e87d6c3` | `423ca75` | 22/26 | F-MIX-06: A `out_of_scope` abstention halted A; runner rejected the `unsupported` literature branch | 0.0301 |
| 8 | `8f7ba571` | `506a593` | 10/26 | F-LIT-02: transient `provider_unavailable` (OpenAI) | 0.0024 |
| 9 | `22d812cb` | `506a593` | 22/26 | F-MIX-07: D extraction `source_analysis_unavailable`; all 14 A requests completed | 0.0327 |

All attempts stopped every listener and drained the job. D's provider receipt files
contain only their label line, so **D call counts and D spend are unknown**; reconcile
total spend from the OpenAI usage page. Additional spend: one 15-token key check and a
development-only diagnosis (27 question-parts calls on the nine A development
proposals in `docs/rag/qa-proposals.json`; all 27 passed every invariant).

## Changes made after the first final attempts (must be disclosed in any report)

These are post-hoc reliability changes made after final cases were executed. Model,
prompts, retrieval, corpus, index and D extraction were not changed.

1. **A launcher** `services/rag/src/notelens_rag/final_runtime.py` (uncommitted on
   branch `rag`; SHA-256 `dc29396c...c1e` at run 9):
   - one separately reserved re-attempt per generation stage after an invalid
     response, a failed content check, or a transient `provider_unavailable`
     (1 s pause); a second failure halts; timeout, rate limit, budget,
     authentication and configuration failures still halt immediately;
   - failed operations record an `error_code` in the A receipt;
   - `out_of_scope`, `needs_clarification` and `unsupported_language` are recorded as
     `completed_abstained` requests, are never re-attempted and do not halt A;
   - policy `automatic_retries` is now `1`; `APP_SHA` is `506a593...`.
   Tests: new retry/abstention tests added, the old zero-retry test updated; the full
   RAG suite passed. Template policy updated accordingly.
2. **B runner** `scripts/project/run_bounded_evaluation.py`: a literature branch with
   kind `unsupported` is accepted as an explicit gap; unavailable/invalid branches
   still stop the run. Local commit `506a593` on
   `member-d/d009-attempt-closure-7a59879d` (not pushed; B review required). The B
   operator check that injects a 503 still expects a stop; it was not re-run.
3. **D extraction**: a matching live re-attempt was drafted and reverted. It conflicts
   with D's explicit zero-retry design (13 D tests) and the approved D budget
   (32 calls x USD 0.0155584 reservation fills the USD 0.50 cap).

## Scoring inputs received

Sara's restricted scoring package (README, binder script, `qa-structure-references.json`,
`retrieval-references.json`) matched its `SHA256SUMS.txt`. The binder was run for
attempts 4 and 5 only; outputs are in the private scoring folder.

## Measured results for attempt 9 (`22d812cb`)

Scored offline against Sara's references bound to this run (binder output SHA-256
`559044f1...b520`; run receipt SHA-256 `b6767ba5...cecf`; retrieval references
SHA-256 `7522ab71...3e47`). This used a branch-level structural scorer that applies the
`eval/src/notelens_eval/final_qa.py` checks to each accepted branch record, because
mixed answers are saved as separate document and literature branches rather than one
AnswerResult. It is **not** the official `notelens_eval.run --profile final
--require-freeze` pipeline; no final freeze was approved or materialized. Zero new
provider calls were made by scoring.

| Measure | Result |
| --- | --- |
| Cases executed | 22/26 (4 technical errors: F-MIX-07, F-MIX-08, F-OOS-01, F-OOS-02 not executed) |
| Accepted branch records schema-valid | 27/27 |
| Accepted branch records with literal evidence valid (document code-point spans; literature excerpt in pinned passage) | 27/27 |
| Literature branches returned as explicit `unsupported` gap | 1 (F-MIX-06) |
| Answer route matches reference (executed cases) | 17/22; mismatches F-DOC-07, F-DOC-08, F-LIT-07, F-MIX-01, F-MIX-06 |
| Evidence state matches reference (executed cases) | 16/22; all six executed mixed cases returned `partial` where `sufficient` was expected |
| Retrieval, cited-source proxy: any required topic cited | 12/15 cases with targets (0.80) |
| Retrieval, cited-source proxy: mean required passage-group coverage | 0.80 over 15 cases |

The retrieval rows are a proxy computed from cited literature sources, not
`topic_recall@5`; ranked retrieval lists were not saved. Literal validity and
route/state agreement do not establish semantic correctness. Final extraction F1 and
independent semantic answer risk remain unmeasured, as previously approved.

## Remaining work to close D-009

1. Decide on D: accept D's single-attempt failures as measured, or approve a D live
   re-attempt (update the 13 tests, raise the D per-run cap) and run again.
2. Choose the run to score under a rule stated before scoring (for example the first
   run after the final code freeze), and report every attempt above.
3. Write a converter from saved web answers to the evaluator's QA and retrieval
   prediction formats. Saved outputs contain cited sources, not the ranked top-5
   passages, so `topic_recall@5` needs either a disclosed cited-source proxy or a
   runner change that saves ranked retrieval.
4. Bind Sara's references to the chosen run, materialize and approve the final freeze,
   run `notelens_eval.run --profile final --require-freeze`, and write
   `docs/extraction-eval/final-report.md`.
5. Commit/push the A launcher changes, get B review of the runner commit, commit the
   preserved failed-attempt record (currently in a git stash), and update T013.
