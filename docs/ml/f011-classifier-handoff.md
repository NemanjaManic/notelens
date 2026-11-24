# C's F-011 classifier health contribution

**Owner:** Sara / C. **Feature:** `specs/003-classification`.

## C-012 local candidate, 2026-11-19

Sara approved the owner-local implementation. The classifier now accepts the
server-side `NOTELENS_CLASSIFIER_MOCK_FAILURE` setting in mock mode. For an
admitted, authenticated and validated classification request, the configured
profile returns one frozen `ErrorEnvelope` with the original request ID, a
static English message and `retryable=true`.

| Profile | Status | Error code |
| --- | --- | --- |
| `timeout` | 504 | `timeout` |
| `rate_limit` | 429 | `rate_limit` |
| `provider_unavailable` | 503 | `provider_unavailable` |

Unset gives the ordinary mock response. A valid profile allows ordinary health
responses, including the separately selected `NOTELENS_CLASSIFIER_MOCK_READINESS=not_ready`
profile. An unknown or empty failure value gives readiness 503 and a business
503 `configuration_required`, with no configuration value echoed. The response
is synthetic and immediate, with no provider calls, timers or automatic retries.

The working copy at `50ee841` passed **102 classifier tests** on Python 3.13.7,
including all three new profiles over Uvicorn loopback HTTP. Tests verified
correlation, validation precedence and process shutdown with closed ports.
The Starlette deprecation warning was treated as an error. Installed Python
bindings passed **153/153 payload outcomes**, **22/22 simulated correlation
outcomes** and all **29 exports**. The offline lock check passed.

The five-file patch `.cache/review/c012-classifier-mock-failures-7aa6c32.patch`
was checked and replayed on an isolated archive of `7aa6c321e7c40c364d234467adbecbab0d06a497`.
Its SHA-256 is `177cf9b45d8ff7c2bfa41dcc4c0ec44c681aba92dec945e4badf452777c18e67`.
The replay used the checkpoint's original lock and passed **84 classifier tests**
with one existing Starlette TestClient deprecation warning. The patch includes
the service and its tests. The independent split, training and TestClient changes
are outside that patch.

In the reply supplied by Sara on 2026-11-19, B confirmed the profile names and
`retryable=true` and reported adding all three authenticated business probes.
B also reported verifying readiness 503 and liveness 200 in the same process.
B requested the published C commit SHA for the coordinated run.

Sara authorized publication of the five-file contribution. The remote
branch `member-c/checkpoint-classifier-mock-failures` was verified at
`4080f9b3c41a0dba70238929e765d9ce535910eb`, with parent
`7aa6c321e7c40c364d234467adbecbab0d06a497`. The committed files matched
the isolated preflight, which passed 84 classifier tests and the
installed binding checks. [Published commit](https://github.com/NemanjaManic/notelens/commit/4080f9b3c41a0dba70238929e765d9ce535910eb)

## B verification and C-012 closure, 2026-11-19

B's F-011 verification plan, supplied by Sara, records C-012 as closed.
B used the exact published C commit above in an isolated coordinated run.
All 63 classifier HTTP cases passed, including authenticated timeout 504,
rate limit 429, provider unavailable 503 and readiness 503 with liveness
200 in the same process. The business probes also verified the expected
error codes, `retryable=true` and admitted request-ID correlation. B
reported 84 classifier tests and 51 checker self-tests passing.

B recorded 209 passed, zero failed and two blocked cases in that all-service
run. Both blockers concerned RAG and extraction readiness. The report
checksum recorded by B is
`0f90e243da860ead0fb17adda581e8843f21a07db40e8d17291488335d4bcd31`.
This closure records B's documented run and the match to the published C
commit. The raw report is retained in B's checkout.

The subsequent [published foundation record](https://github.com/NemanjaManic/notelens/blob/1ac8bfe9cf3ea9853c417ffe3f86ed7a1a15b6f8/specs/000-foundation/tasks.md)
records F-011 as complete with 213/213 mock HTTP checks passing and zero
blockers. F-014 remains open.

## Resume handoff, 2026-11-19

- **Working branch:** `member-c/classification` at `50ee841177494a0b4eb30c1f994cb455d55d8b5e`, where C-009 is complete. C-001 is recorded in `093e547` and the [source audit](data-audit.md). Keep C's working branch for its separate audit, contract review and provisional work.
- **Shared interim base:** `origin/main` at `7aa6c321e7c40c364d234467adbecbab0d06a497`, tree `74ab9bdb1f064b9e049decd0cfbf7a4ebd6f7129`. Its classifier subtree exactly matches C's published health commit `49c84181ccca348cae1bd65be4c29328341ea25c`. F-010, F-011 and F-014 are open. [PR #4](https://github.com/NemanjaManic/notelens/pull/4)

| Scope | Verification | Result |
| --- | --- | --- |
| Exact interim classifier snapshot | `uv sync --offline --locked --directory services/classifier`, then `python -B -m pytest services/classifier/tests -q -p no:cacheprovider` in an isolated Python 3.13.7 environment | 77 passed, including loopback mock health. One Starlette TestClient deprecation warning. |
| Exact interim Python bindings | `python -B scripts/project/check_bindings.py` in the same isolated environment | 153/153 payload outcomes, 22/22 simulated correlation outcomes and 29 exports passed. |
| C working copy | `python -B -m pytest services/classifier/tests -q -p no:cacheprovider -W error::starlette.exceptions.StarletteDeprecationWarning`; `python -B -m unittest discover -s data/mtsamples/tests -q` on Python 3.13.7 | 95 classifier tests and 8 audit tests passed. The classifier suite includes synthetic draft split and training-isolation checks. |
| Authorized local data artifacts | `python -B data/mtsamples/audit.py --check` on 3.13.7 and `python -B data/mtsamples/draft_splits.py --check` on 3.11.9 | Audit and provisional manifest verified without rewriting them. The initial split check on 3.13.7 failed byte comparison. The draft records Python and Unicode versions, so use the generating runtime for the exact-byte check. |
| Spec Kit | Pinned `uv --system-certs tool run --from 'git+https://github.com/github/spec-kit.git@v1.3.3' specify version`; official PowerShell resolver with `-PathsOnly -Json` and `-RequireTasks -IncludeTasks -Json` | CLI 1.3.3. The resolver selected C's feature with persistence disabled. Requirements checklist 16/16 checked. Extension configuration absent. |

The shared checkpoint commit records 204 passing health cases and six blocked cases. The checks above cover the classifier and bindings. B's shared checker still lists `classifier-not-ready` as blocked even though the published classifier supports it. B can register `NOTELENS_CLASSIFIER_MOCK_READINESS=not_ready` in the checker and exercise its 503 readiness and 200 liveness.

C-002 awaits F-014 and the split review. C-003 follows the C-002 freeze. C-010
awaits D-003 development-only assignments. The existing exploratory result remains
[provisional](experiments/draft-baseline-v1.md).

## Original local verification, 2026-11-17

**Date:** 2026-11-17. **Owner:** Sara / C. **Prepared by:** coding agent assisting C.
**Status at the time:** owner-local implementation and checks. B's checker package was `60b2b27986649e230f90723693c4e05b88e8891a`;
the shared F-004 package it builds on imported classifier `df842f928d8b856aa404afa00893415511ab1cd1`.
C's branch subsequently published the TestClient fix `9c736d4` and C-009 `50ee841`.

## Implemented mock health

`services/classifier/src/notelens_classifier/main.py` adds frozen validated
`GET /health/live` and `GET /health/ready`. In configured mock mode liveness
returns 200 `alive`; readiness returns 200 `ok`, null model version/reason. Set
`NOTELENS_CLASSIFIER_MOCK_READINESS=not_ready` to receive 503 `not_ready` with a
safe static reason, while liveness remains 200. This synthetic switch changes health
reporting only. Unknown readiness values or classification scenarios are not ready;
settings are never echoed. Live mode is not ready because live inference is absent.
Unrecognized/unset modes fail closed; no silent fallback to mock is introduced.

Health ignores incoming request IDs. When a token is configured, missing/wrong or
duplicate Authorization is rejected in either order with 401, one Bearer challenge,
`unauthorized`, `retryable=false` and a fresh canonical diagnostic UUID matching
the envelope and response header. Successful health responses and health 503 have
no request ID. Without a token only direct loopback mock health is admitted; remote
or non-mock no-token health is denied. Business request-ID admission and correlation
are unchanged. Health has no model or provider call.

## Actual verification

On Windows with Python 3.13.7, uv 0.13.7 and the local locked environment containing
the optional training group, the following was run from `services/classifier`:

```powershell
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$trainingPython = Join-Path $env:TEMP 'notelens-c-training-py313/Scripts/python.exe'
& $trainingPython -B -m pytest -q -W error::starlette.exceptions.StarletteDeprecationWarning
& $trainingPython -B ../../scripts/project/check_bindings.py
```

Results: **95 tests passed**, including synthetic health, all four classifier
scenarios, invalid request/duplicate headers, error handling, privacy and separate
draft training/split tests. Bindings: **153/153 payload outcomes, 22/22 simulated
exchanges**, 29 exports and strict number/JSON negatives passed. Tests initially
failed before implementation because health endpoints were absent; no warnings were
suppressed. The owner-local real-loopback tests started three Uvicorn processes:
healthy and not-ready profiles plus an authenticated profile. They exercised health
200/503/401, duplicate Authorization in both orders, fresh IDs, frozen validation,
business POST behavior and cleanup; all owned processes stopped and ports closed.
These are mock and synthetic tests, not B's full shared F-011 matrix or real inference.
