# Early B-004: memory sessions and guarded configuration

Owner: B. Date: 2026-11-17. Platform task: T002 / B-004, **pending**.
Base: `e12791c45f584b5cf35a9ba74f98520abc1cba14`.

## Approved F-014 execution-order exception

The user explicitly approved implementing this bounded early B-004 package before
F-014. This exception permits only the B-owned, independently tested memory/config
core. It preserves the existing F-014 dependency for full B-004 acceptance. It does
not complete, waive or publish F-014, F-010, F-011 or B-004, authorize other platform
tasks, alter frozen contracts or grant edits to A/C/D. No commit/push is authorized.

## Scope and design

`MemorySessions` is a server-only, single-process core with no disk, cache, browser,
network, logging or provider adapter. Random 256-bit capabilities identify sessions
and preparation tickets. Call `beginDocument` before preparing a document; its fixed
deadline includes preparation and validation time. Only generated-runtime-validated
PreparedDocument snapshots can enter the store. Text is never normalized downstream.

Documents expire absolutely after 3,600,000 milliseconds. Reads and rejected duplicate
writes do not renew the deadline. Timers clear idle document references; reads and
writes independently reject expired entries if timer execution is delayed. Cleanup
callbacks run when the Node event loop can execute; this is not a hard real-time
physical-memory erasure guarantee. Sessions contain only private copies and reads
return new copies. Cross-session, unknown and expired lookups return the same fixed
English unavailable outcome. Explicit deletion/endSession/dispose cancels timers
and removes references. Each process/store starts empty; no recovery is attempted.
Clock regression or invalid clock values dispose the store and fail closed.

The clock/scheduler seam exists for deterministic tests. Production callers should
use the default monotonic clock and unref'd Node timers. This class is not connected
to an endpoint. It does not establish browser ownership by itself: future server
routes must derive the capability from a protected server-issued browser session,
never trust a submitted owner ID or expose another session's capability. B-001 must
create a fresh document identity per submission and start the preparation ticket
before handling submitted content. Duplicate active document identities are rejected
within one session; expired tickets cannot be reused.

Only approved constants exist: 60-minute document retention, 2,097,152 PDF bytes and
100,000 Unicode code points. The core enforces the text limit; PDF parsing/byte
admission belong to B-001. All non-mock modes fail closed even when keys are present.
No history, retry, request rate, session-count/lifetime, timeout or spending defaults
are invented. Empty session maps contain opaque capabilities only and remain until
explicit end/dispose; capacity/abuse policies need approval before exposing routes.
No analysis/answer/history storage is included. Future document-bound results must
share the document's absolute deadline and teardown before integration acceptance.

## Workflow and verification

Used the installed speckit-implement workflow for platform T002 only. Official
PowerShell prerequisite resolution used SPECIFY_FEATURE_DIRECTORY=specs/002-platform
and SPECIFY_FEATURE_NO_PERSIST=1 with RequireTasks/IncludeTasks. The existing quality
checklist is 16/16; no extension hooks are registered. Existing specs/plans/model and
open decisions informed this bounded implementation; no regeneration or delegation.

Run with the existing installed toolchain:

```powershell
node apps/web/scripts/check-sessions.mjs
```

The coordinator typechecks with NodeNext/noEmit and runs 28 synthetic Node tests,
requiring complete passing counts, no skips/cancellations/todo, fresh process output,
a fresh nonce and unchanged source/protected hashes. It saves metadata only under
ignored `.cache/review/b004-sessions/`. The noEmit web tsconfig explicitly permits
`.ts` imports so Node type stripping and the web compiler resolve the same module.
No package, dependency or lock changes are needed. Tests cover independent sessions,
uniform failures, input/output copies, deletion, concurrency, deadlines, delayed
timers, invalid context, text limits and instance recreation as simulated restart.
An actual deployed-process restart/browser authentication flow is not tested here.

Full B-004 remains pending F-014, approved remaining operational policies and browser
transport/integration acceptance. F-010/F-011/F-014 stay unchecked; the earlier A
chromadb advisory remains open. Existing drafts, generated/frozen files and A/C/D
files must remain unchanged. Final run and preservation evidence is recorded under
ignored `.cache/review/b004-early/` after checks finish.

## Retention review follow-up

The two test gaps R1/R2 identified in the early-package review were corrected within
the same nine-file scope. Idle-expiry coverage now ends the session after the timer
fires, without first reading or storing the expired document; a stale retained entry
would still require cancellation at teardown. Validation-expiry coverage starts a
valid store operation, crosses its absolute deadline while validation awaits, leaves
timers unfired and requires the unavailable outcome. Neither test relies on a later
document lookup to perform lazy expiry.

Both original mutations are now detected independently: disabling idle callback
cleanup fails only the idle-removal case, and removing the post-validation deadline
guard fails only the new validation-expiry case. Each isolated mutant runs all 28
cases with 27 passing and its expected regression failing. The unmodified source
passes all 28 and noEmit typechecking. Session/config implementation and frozen
contracts are unchanged by these fixes. The coordinator requires both retention
case IDs as well as its complete counts. Fresh mutation evidence and the refreshed
nine-file commit scope are under `.cache/review/b004-commit-scope/`; no commit or
push has occurred. B-004/F-010/F-011/F-014 remain pending.
