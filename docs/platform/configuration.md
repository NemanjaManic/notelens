# B-004 memory sessions and guarded configuration

Owner: B. Platform task: T002 / B-004, **complete for the key-free mock**.
Current branch base: `cde4dd6ab2da6be5937521c97b4875e97fdc496c`.

## Approved browser session policy

The user approved the local mock defaults on 2026-11-20. Sessions live in one
web process and expire after 30 minutes of inactivity or 60 minutes from
issuance. Successful opens, reads, stores and document deletions count as
activity. Passive ownership checks and failed actions leave the idle deadline
alone. Session expiry, explicit close and restart clear the document references.
Each document also has its own deadline of 60 minutes from preparation start.
The approved input limits are 2,097,152 PDF bytes and 100,000 Unicode code points.

The process admits up to 32 active sessions and 10 new sessions per rolling
minute. Each session has three document slots, including one in-flight
preparation. A failed or cancelled preparation releases its reservation.
Rate-limited creation returns `429` and `Retry-After` in seconds. At capacity,
creation returns `503`. Existing owners can keep using or close their own session.

`POST /api/session` explicitly opens or reuses a session. `DELETE /api/session`
revokes the capability and expires the cookie. Both return `204` on success.
Set `NOTELENS_SESSION_ORIGIN` to the exact browser origin, including its port
when applicable. The routes reject missing or mismatched request origins with
`403`, and fail closed if configuration is missing or the execution mode is
unavailable. They use `Cache-Control: no-store` and an opaque host-only
`__Host-notelens-session` cookie with `Secure`, `HttpOnly` and `SameSite=Strict`.
Tabs in one browser context share the cookie. Ownership comes from the cookie
and the process store. A document ID alone does not confer ownership.

B-004 stores zero chat turns and makes no upstream calls or automatic retries.
B-001 owns uploads. B-003 owns chat history and upstream timeout policy.

## Key-free verification

From the repository root, `node apps/web/scripts/check-sessions.mjs` runs
TypeScript noEmit and 39 synthetic cases. The browser scenarios reported 32
passing assertions in Chrome across seven phases. The built Next app was used
for the session route smoke. A standalone loopback server ran the same route
handler and memory store with synthetic fixtures and a controlled clock. Tests
covered two browser contexts, cookie handling, cross-origin rejection, idle and
absolute deadlines, explicit revocation, process restart, and admission limits.

To repeat, build with `npm.cmd run build` in mock mode. Start the Next app on
`127.0.0.1:48317` with `NOTELENS_MODE=mock` and
`NOTELENS_SESSION_ORIGIN=http://localhost:48317`. Start
`node apps/web/tests/session-browser-server.mjs 48316` separately. Use the
bundled Chrome DevTools CLI to open each page with `new_page` and
`--isolatedContext`, then run `evaluate_script --pageId <id> --sourcePath
<absolute path to apps/web/tests/session-browser.scenarios.js> --format function`.
Use fresh Chrome contexts for each run.

| Phase | Browser URL | Context |
| --- | --- | --- |
| Next smoke | `http://localhost:48317/?role=next` | Next |
| Owner access | `http://localhost:48316/?role=owner` | Owner |
| Second session | `http://localhost:48316/?role=other` | Other |
| Cross-origin rejection | `http://127.0.0.1:48316/?role=foreign` | Foreign |
| Expiry and close | `http://localhost:48316/?role=expiry` | Owner |
| Restart on the same port after stopping the fixture server | `http://localhost:48316/?role=restart` | Owner |
| Admission limits | `http://localhost:48316/?role=limits` | Owner |

The web checks verify the ratified constitution digest already recorded in the
foundation inventory. The F-014 publication SHA is recorded in the
[checkpoint](../team/foundation-checkpoint.md).

## Early work before F-014

The 2026-11-17 increment was based on
`e12791c45f584b5cf35a9ba74f98520abc1cba14`.

The user explicitly approved implementing this bounded early B-004 package before
F-014. This exception permits only the B-owned, independently tested memory/config
core. It preserves the existing F-014 dependency for full B-004 acceptance. It does
not complete, waive or publish F-014, F-010, F-011 or B-004, authorize other platform
tasks, alter frozen contracts or grant edits to A/C/D. No commit/push is authorized.

## Early scope and design

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

## Early workflow and verification

Used the installed speckit-implement workflow for platform T002 only. Official
PowerShell prerequisite resolution used SPECIFY_FEATURE_DIRECTORY=specs/002-platform
and SPECIFY_FEATURE_NO_PERSIST=1 with RequireTasks/IncludeTasks. The existing quality
checklist is 16/16; no extension hooks are registered. Existing specs/plans/model and
open decisions informed this bounded implementation; no regeneration or delegation.

The early coordinator check used NodeNext/noEmit and ran 28 synthetic Node tests,
requiring complete passing counts, no skips/cancellations/todo, fresh process output,
a fresh nonce and unchanged source/protected hashes. It saves metadata only under
ignored `.cache/review/b004-sessions/`. The noEmit web tsconfig explicitly permits
`.ts` imports so Node type stripping and the web compiler resolve the same module.
No package, dependency or lock changes are needed. Tests cover independent sessions,
uniform failures, input/output copies, deletion, concurrency, deadlines, delayed
timers, invalid context, text limits and instance recreation as simulated restart.
An actual deployed-process restart/browser authentication flow is not tested here.

The early run and preservation evidence was recorded under ignored
`.cache/review/b004-early/`.

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
case IDs as well as its complete counts. Mutation evidence and the early nine-file
commit scope were recorded under ignored `.cache/review/b004-commit-scope/`.
