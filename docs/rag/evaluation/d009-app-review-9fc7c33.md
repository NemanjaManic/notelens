# A review status for the B final runtime candidate

**Historical candidate review**: The source findings below concern `9fc7c33`
and its then-missing whole-stack watchdog. Goran subsequently supplied the tested
watchdog pin `d846dcfee5a066dc180a59dbf0c1ed8888809f38`; the
[v3 reconciliation](../d009-watchdog-reconciliation-v3.md) records A's exact-source
inspection and active launcher/policy checksums. The earlier open watchdog finding
does not describe that newer managed runner. Final execution/scoring is separate.

Prepared: 2026-11-24. Scope: independent A-side review of app candidate
`9fc7c333ca74971768e1df13ed6238798c48e90e`.

**Status: partial exact-source review; joint runtime acceptance is blocked on
the absolute run watchdog and remaining execution-policy checks.**

The supplied `D009-B-final-runtime-preflight-9fc7c33.json` reports 73 passing
Chrome assertions in a key-free mock profile and a separate synthetic counted
rehearsal of 26 cases. Its recorded service counts are 16 extraction requests,
16 document answers and 16 literature answers, with one extraction per source
across report reopens and citation visits and overflow rejected before dispatch.
These are B-supplied results, not checks independently rerun by this reviewer.
The supplied file explicitly leaves final execution and the proposed operator
unauthorized and live readiness/model access unverified.

## Verification limitation

The normal executor failed before creating a process with
`setup refresh had errors`. An escalated read-only source inspection then
remained pending and was aborted before returning output. A subsequent minimal
normal `git cat-file -t 9fc7c333ca74971768e1df13ed6238798c48e90e` failed with the
same setup error. Consequently this review has not verified local availability
of the exact Git object, inspected its source, or executed candidate checks.
An agent review of an older checkout would not establish acceptance of this SHA.

## Exact-source findings relayed by the primary reviewing agent

The primary agent subsequently fetched the exact candidate using
`git fetch --no-tags origin 9fc7c333ca74971768e1df13ed6238798c48e90e`, without
changing the current branch, and inspected candidate source with `git show`.
The findings below are attributed to that primary-agent source inspection;
this subagent has not independently executed the candidate test suite.

- The candidate live client uses the configured evaluation timeout and permits
  live provider records for generation services through `consumeExchange` /
  `consumeRecord`. The old checkout's mock-only consumer is not a blocker that
  can be carried forward to this candidate.
- RAG bearer configuration matches A's `NOTELENS_RAG_SERVICE_TOKEN` interface.
- `start_bounded_web` verifies the three service health records in live mode,
  checks service/model pins, uses separate service tokens and starts the web
  process with the bounded profile and limits. Startup readiness is bounded
  to 35 seconds; this is separate from the whole-run deadline.
- **Blocking runtime-control finding:** the inspected
  `scripts/project/start_bounded_evaluation.py` validates the approved policy,
  writes a startup receipt and starts the bounded web process, then waits with
  `while stack.processes['web'].poll() is None: time.sleep(0.25)`. That loop
  has no 60-minute absolute deadline. The proposed whole-run hard stop requires
  a separately identified and tested external controller or a B-owned launcher
  correction. A's own service deadline cannot prove a whole-system deadline.

No statement here converts B's synthetic/browser evidence into live-provider
acceptance or authorizes final execution. Per-case stop-on-first-error behavior,
attempt receipts and exact call multiplicity still require the remaining
controller/source review and key-free verification.

## Required exact-candidate review

1. Complete exact-candidate inspection of case dispatch, budgets and receipts;
   Git identity, the bounded launcher and live-mode client have the primary-agent
   source findings recorded above.
2. Demonstrate authenticated health/readiness without provider calls and
   cancellation/stop behavior in the selected executable profile.
3. Bind A admission hashes to the exact UTF-8 literature question payload sent
   by B, including any mixed-query splitting; whole-case question hashes are not
   interchangeable with branch-payload hashes.
4. Verify the 120-second web timeout against A's proposed 15-second provider
   operation limit. Seven provider operations can consume 105 seconds before
   local overhead. This arithmetic is not an executed timeout demonstration.
5. Verify that the final profile enforces one attempt per operation, no hidden
   repair/retry/judge calls, no extra retrieve request, no re-extraction on
   rendering and a 60-minute absolute watchdog with durable usage receipts.
6. Verify D's actual generation/counting multiplicity and input/output limits
   from its pinned provider profile; 32 app operations alone do not establish
   32 provider calls.

The proposed operator must confirm approved model access and authenticated live
service readiness before a team decision authorizes final execution. No secret
value or final scoring reference is needed for this source/interface review.

The user's expedited target is 15:00 on 2026-11-24. This is not evidence of a
tutor-confirmed submission cutoff, and completion before that time is not claimed.

No provider calls, final-case access, commit, push, deployment, shared-file edit
or independently rerun browser pass occurred in this review attempt.
