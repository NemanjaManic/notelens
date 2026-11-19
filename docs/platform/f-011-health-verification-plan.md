# F-011: B-Owned Health and Failure Verification Plan

**Prepared:** 2026-11-16. **Owner:** B. **Task:** foundation T007 / F-011, US1.
**Status:** the B-owned checker is implemented and exercised after the user's separate
implementation approval. Shared F-011 is incomplete; T007 and F-014 remain unchecked.
No A/C/D service edit, collaborator message, commit or push is part of this execution.
**Dependency:** technically completed F-004/T006. F-012 is also technically complete;
F-005 still depends on completed F-011 and F-012.

Planning baseline: [8a20f2c9b2128605d1863c9a722978657976cd91](https://github.com/NemanjaManic/notelens/commit/8a20f2c9b2128605d1863c9a722978657976cd91)
on `member-b/task-f-004-web-workspace`. This supplements the existing foundation
[plan](../../specs/000-foundation/plan.md) and [T007](../../specs/000-foundation/tasks.md),
not a regenerated Spec Kit feature plan. The official read-only PowerShell prerequisite
resolver selected `specs/000-foundation` with no persistent feature selection; checklist
status was 16/16 and no extension hooks exist. Implementation must use the scoped
`speckit-implement` workflow after separate approval.

## Intended checker and ownership boundary

Deliver `scripts/project/check_health.py --mode mock`: finite, key-free checks of actual
loopback HTTP health and safe failure behavior across the three independently installed
Python services. B owns the checker, process containment, wire validation and evidence.
A/C/D retain all service source, service tests, manifests and lockfiles. B will not add
health handlers, failure mappings or model logic to an owner's service.

The default command must evaluate all three services and return nonzero if any required
endpoint/case is missing, invalid, failed or unexercised. A diagnostic subset may be useful
while C is pending, but must be explicitly labeled incomplete for shared F-011 and must
not produce a successful full-gate receipt. Checker self-tests and fixture checks are
separate from real service HTTP results. No F-011 pass is claimed by this plan.

## Current source inspection and owner coordination

These are source-inspection findings, not new runtime health measurements. Imports remain
pinned in [scaffold_inputs.json](../../scripts/project/scaffold_inputs.json).

| Owner/source | Observed capability | Pending integration detail |
| --- | --- | --- |
| A / `24c2b6d96fc00c7e2ffe5dcd63be57d72dc406ac` | RAG has `/health/live`, `/health/ready`, optional service-token enforcement, and deterministic timeout/rate-limit/provider-unavailable/internal-error scenarios on both business routes. Mock readiness is conditional on absence of a corpus configuration error. | Verify actual health/auth matrix in B's new checker. Agree a synthetic, key-free not-ready trigger; do not load a real corpus or silently set live mode. |
| C / `df842f928d8b856aa404afa00893415511ab1cd1` | Classifier exposes `/v1/classify`; source explicitly defers health/readiness to F-011. Four classification outcomes exist, with validation/configuration errors and a safe unexpected-error boundary. | Sara owns adding health routes and their regressions. No public timeout/rate-limit/provider-outage scenario selector is present; ask C for a supported deterministic seam if those runtime cases are required. An HTTP 404 is missing coverage, not a pass or an optional endpoint. |
| D / `36ea2a1b59e382930daee7d088c883b0d103c619` | Extraction has health routes, corrected auth/ID behavior and `create_app(provider=..., token=...)`. Existing owner tests inject a scripted provider; timeout/connection exceptions are mapped by the service, and `ServiceError` can carry rate-limit failures. | CLI setup supplies no general failure-scenario selector. A B-owned inert provider can use the existing factory seam for real HTTP error-mapping checks, subject to owner review of that seam. Mock readiness currently depends only on provider mode; no distinct mock-not-ready switch is present. |

The pending questions are about owner-supported test configuration, not permission to
edit shared contracts. Resolve the exact unavailable/readiness and failure triggers with
the relevant owner before implementing those dependent runtime cases. Do not fabricate
a service response, monkeypatch its HTTP handler or activate a real provider to obtain
coverage. A plan can identify an unexercised case without pretending it passed.

No owner request is sent by this preparation. If an owner publishes a new commit, B must
review it separately before a separately authorized scoped import. Current import hashes
must not be silently replaced. The existing F-004 runner/verifier hardcodes owner test
counts 319/51/59; any approved owner update that adds tests also requires a reviewed update
to those B guards and their regressions. That owner-integration package is separate from
implementing the B checker against today's unchanged services.

## Frozen wire rules to enforce

Read the canonical [OpenAPI](../../contracts/v1/openapi.json),
[schema](../../contracts/v1/schema.json) and
[transport fixtures](../../contracts/v1/fixtures/transport-cases.json) unchanged.
Use `notelens_contracts.v1` runtime validation rather than duplicating wire definitions.
The tooling environment can load the exact generated Python source with origin/schema
checks, as F-012 does; label that correctly. Existing installed-package checks remain
separate. No new dependency is needed for standard-library HTTP and process coordination.

| Response | Required check |
| --- | --- |
| `GET /health/live`, 200 | `LivenessResult`, correct service identity, `status=alive`, `mode=mock`, nonempty version; no body/model/index/provider work. |
| `GET /health/ready`, 200 | `HealthResult`, correct service, `status=ok`, `mode=mock`, `model_version=null`, `reason=null`. |
| `GET /health/ready`, 503 | `HealthResult` with `status=not_ready` and a nonempty safe reason, not a business `ErrorEnvelope`. Any actual mock probe must still report `mode=mock`; use an owner-supported key-free unavailable condition. |
| Health authentication failure, 401 | `ErrorEnvelope`, `unauthorized`, `retryable=false`, exactly one canonical response UUID matching the envelope, one `WWW-Authenticate: Bearer` challenge; never echo any incoming health ID. |
| Business admission failure | Missing/malformed/duplicate IDs cause frozen 400 admission behavior before authentication; a valid business ID is echoed on ordinary business success/error paths. Keep this distinct from health. |
| Simulated business failures | Check timeout 504, rate-limit 429, provider-unavailable 503 and validation 400/422 against frozen envelopes and owner-supported scenarios. Health readiness 503 and business error 503 are different channels. |

Incoming health request IDs are optional and ignored, including malformed/duplicate
values. Health 200/503 responses do not require an ID. Do not add that requirement or
an invented mode field to an error envelope. If a health result carries an ID, ensure
it does not reuse an incoming ID; D may emit a fresh ID even on successful health calls.

**Important validator boundary:** current generated `validate_exchange` handles health
**401 authentication exchanges only**; passing health 200/503 to it yields
`HEALTH_AUTH_STATUS`. For 200/503, use the generated payload validators plus B's explicit
method/path/status/service/mode assertions from the frozen OpenAPI. Do not extend the
frozen runtime or misreport valid ID-free health responses as an owner defect.

For business probes, retain raw header lists and use the existing correlation validator.
Do not collapse duplicate Authorization or X-Request-ID fields into a dictionary before
checking them. Retryability must follow the frozen scenario/owner behavior: A's simulated
failures currently use false, while D's timeout/outage/rate-limit tests use true. Only
the health-auth 401 rule mandates false here; this task adds no application retry policy.

## B-owned implementation files proposed for later approval

| Path | B responsibility |
| --- | --- |
| `scripts/project/check_health.py` | `--mode mock` coordinator, raw loopback HTTP client, canonical validators, deterministic case IDs, scoped results and metadata-only evidence. Reject other modes before service startup. |
| `scripts/project/health_probe_app.py` | Only if required for existing factory seams: create the actual owner app with an inert test provider/settings. Never install replacement handlers or return fabricated health/error envelopes. |
| `scripts/project/tests/test_health.py` | Checker regressions using frozen positive/negative responses, raw header duplicates, missing coverage and owned-process cleanup; identify these as checker tests. |
| `scripts/project/scaffold_inputs.json` | Allowlist approved new B files and record task-document baseline changes; preserve current owner/frozen pins and original B input snapshot. |
| `docs/platform/f-011-health-verification-plan.md` | Append actual commands, per-service/case results, limitations and pending owner work. |
| `specs/000-foundation/tasks.md` | Record a scoped B checker delivery if appropriate, but check T007 only after the agreed full service matrix actually passes. |

Reuse the existing `scaffold_process.py` job containment without editing it unless a
reproduced issue requires a separately reviewed scope change. Keep the root/web packages,
all owner service files and locks, frozen/generated contracts, annotation/eval data and
the user's drafts untouched. No Node helper or new framework is necessary for this plan.
Do not regenerate unrelated feature artifacts or update another owner's task markers.

## Case matrix and execution approach

1. **Healthy mock profiles:** all three services, both health routes, no configured token
   on direct loopback and a configured synthetic test token with valid authentication.
   For each, exercise absent, canonical, malformed and duplicate incoming IDs. Health
   availability must not depend on a valid business request ID.
2. **Health denial profiles:** with a configured token, test missing/invalid credentials
   and duplicate Authorization in both valid-first and invalid-first orders. Vary the
   incoming IDs, including duplicate values, and confirm fresh diagnostic correlation
   and the exact challenge. Repeat a denial to detect a reused fixed diagnostic ID.
3. **Not-ready behavior:** validate the frozen 503 response shape in checker self-tests.
   Separately exercise actual service 503 via agreed mock-only factory/configuration
   seams where supported. The frozen `health-not-ready` fixture uses `mode=live`; it is
   offline validation data, not authorization to start live mode. Report any unavailable
   runtime seam explicitly; its evidence cannot be replaced by a fixture pass. Confirm
   the final required runtime matrix with owners before using it as a completion gate.
4. **Safe business failures:** use only the exact RAG synthetic question, C's canonical
   document request and D's built-in synthetic extraction/answer fixtures. Exercise the
   agreed timeout/rate/outage/validation paths through actual owner error mapping. D's
   inert injected provider may raise the existing exception/ServiceError types; it must
   not perform generation. No arbitrary input, raw reports, corpus or models are used.
5. **Checker negatives:** wrong service/mode, wrong 200/503 body type, malformed JSON,
   missing endpoint, absent/echoed/mismatched diagnostic IDs, missing/duplicate challenge,
   duplicate auth and incomplete case/process lists must not produce a full pass. A
   live-shaped response cannot satisfy an expected mock case. The known missing C routes
   must keep the default all-service result incomplete until an owned correction lands.

Enumerate stable case IDs before executing the implementation; report actual counts and
provenance rather than inventing a passing count in this plan. Group requests into finite
owned profile launches and check that each launched process exits and its port closes.
The existing 30-case F-004 HTTP result remains useful regression evidence but is not the
new health matrix. C-009, model readiness, real English detection and clinical support
are not completed by these probes.

## Process, configuration and evidence controls

Use each service's own existing environment/interpreter and frozen package. Launch actual
apps only on `127.0.0.1` ephemeral ports, with proxy-header trust and access logs disabled
through B's temporary Uvicorn command arguments. Use the existing Windows job helper so
timeouts/interruption stop only owned descendants; never scan/kill unrelated processes
or persistent services. This is finite verification, not F-005's shared dev supervisor.

Scrub inherited provider credentials, service settings, corpus/index selectors and Node
preloads; then set only explicit mock and synthetic test-token settings for each profile.
Never print the token or store the environment. Retain only public fixture inputs on the
wire; no submitted content is accepted or persisted. Check synthetic leakage markers
without writing response bodies or raw unsafe service diagnostics to the final report.
Use the existing loopback guard where applicable; do not describe it as an OS firewall.
Readiness checks must not invoke a model, provider, corpus loader or index.

Save case IDs, mode/service/version, status, diagnostic rules, source/runtime origins,
input/artifact hashes and owned-process cleanup records under ignored
`.cache/review/f011-health/`. Bind evidence to a fresh run nonce and current source;
clear stale success pointers at run start. Missing/failed/incomplete coverage must not
reuse an earlier receipt. Fixture-only and runtime cases need distinct provenance.
Harness deadlines are verification controls, not new latency SLOs, retries, rate limits,
history settings or provider budgets.

## Verification commands and completion gates

These commands now exist after separate implementation approval. Checker self-tests and
the frozen/generation checks pass; the all-service health command currently returns 1
for the documented incomplete matrix. From the repository root:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B -m unittest discover -s scripts/project/tests -p test_health.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_health.py --mode mock
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_contracts.py --require-freeze
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/generate_contracts.py --check
```

Also verify invocation from a different working directory and rejection of incomplete
case/process evidence. Refresh current source/runtime receipts and rerun relevant F-004
and F-012 regressions after executable inventory changes. Full T007 closure requires the
actual agreed all-service matrix, canonical health/error records, request-ID/auth rules,
zero provider/model calls and complete cleanup, with unresolved owner cases identified
rather than skipped into success. B can implement and test its checker while owner work
is pending; that does not complete shared F-011.

The initial planning-only change added this B-owned Markdown file. The separately
approved implementation adds the checker and its regressions, updates the executable
inventory and records partial B progress in T007 without checking it complete.
F-005 remains dependent on completed F-011; F-010 can progress independently. F-006,
F-013 human/team acceptance, F-007 checkpoint and F-014 publication retain their graph.
F-014 remains pending, and delivery remains 2026-11-24.

## B-owned implementation and observed checks (2026-11-16)

Implemented `scripts/project/check_health.py` and `scripts/project/tests/test_health.py`
against parent `8a20f2c9b2128605d1863c9a722978657976cd91`. No optional factory bootstrap
was added: the unavailable/failure seams requiring owner agreement remain unexercised.
The checker launches the existing owner apps through Uvicorn with explicit mock settings,
loopback binding, no trusted proxy headers and no access logs. No handler, provider or
service configuration file is replaced. No package/lockfile was changed or installed.

The finite case inventory has 210 unique IDs: 198 actual HTTP probes plus 12 explicit
owner-blocked cases. The supported HTTP run observed:

| Service | Passed HTTP cases | Failed HTTP cases | Blocked/unexercised cases |
| --- | --- | --- | --- |
| A / RAG | 74 | 0 | 1 not-ready trigger |
| C / classifier | 8 | 50 missing-health-endpoint cases | 1 not-ready and 3 failure triggers |
| D / extraction | 66 | 0 | 1 not-ready and 6 failure triggers |
| Total | 148 | 50 | 12 |

The 50 C outcomes are repeated matrix checks of its two absent health routes, not 50
distinct defects or a regression in its already verified F-004 scope. The default
checker exits **1** and writes `passed=false`, `complete=false`. It must not be described
as a full F-011 pass. All 10 launched service processes exited, their ports closed and
the coordinator's Windows jobs completed cleanup. No unrelated process was targeted.

All **31 checker self-tests passed**, covering ID-free health success, 503 HealthResult,
401 diagnostic/challenge rules, raw duplicate headers, business admission and validation,
no invalid document context on error envelopes, retryability differences, sensitive-output
diagnostics, missing/duplicate/fixture-only case evidence, process coverage/cleanup,
runtime package origins, disabled live mode and actual cleanup after a probe exception.
Checker fixtures are not counted among the 198 service HTTP probes.

The first HTTP attempt exposed a B-checker assumption that every installed contract
package lived in `site-packages`. RAG legitimately declares an editable dependency.
The B-only correction accepts that exact generated-source location only when editable
installation metadata declares it, and still requires the service's own interpreter,
metadata directory, source URL and schema. Wheel installs must resolve inside their
own environments. Four origin regression tests passed; no owner package was changed.
The earlier incomplete run remains in ignored history and is not the current result.

Validation uses the exact generated Python source in the B client, separately from the
service interpreter/install provenance recorded by each worker. Raw response/request
headers are preserved, 200/503 health bodies are checked without misusing the health-401
exchange validator, and only successful document-bearing business records receive the
prepared-document validation context. Error envelopes can therefore describe rejected
documents without requiring those documents to pass validation first.

Reports contain case IDs, outcomes, statuses, diagnostic rules and source/install/process
metadata, not document bodies or tokens. Service stdout/stderr is drained in bounded
memory and reduced to leak/traceback flags rather than saved raw. Workers use fresh run
IDs, and the parent verifies their expected case lists. The completeness check refuses
fixture-only results, pending owner capabilities and missing/duplicate process records.
The latest pointer explicitly carries the incomplete result; no stale success is reused.

Current evidence is identified by `.cache/review/f011-health/latest.json`, with per-run
`report.json`, worker/profile metadata and artifact hashes below it. The before snapshot
and preservation/regression audit are under `.cache/review/f011-implementation/`.
These are local ignored artifacts; another checkout must rerun the commands itself.
No new live-provider/model, corpus or index operation was activated; mock business outputs
remain deterministic fixtures. This is not an OS firewall or a clinical-quality result.

Outstanding next coordination remains unchanged: C owns the health endpoints and approved
failure triggers; A/C/D must confirm supported mock-not-ready triggers; D must confirm
the proposed existing-factory failure seam before those dependent probes are added.
An owner update requires a new reviewed commit and separately authorized scoped import.
The B checker is usable now, but shared F-011/F-005/F-014 stay open.

The final health run was also invoked from a separate working directory and returned the
same explicit incomplete counts. After the approved executable/task baseline update,
the full existing scaffold suite passed all 15 steps: **111 B tests** (the existing 80
plus 31 health-checker tests), A/C/D **319/51/59**, web checks and **30** module HTTP cases
with all **12** scaffold processes stopped. The default scaffold verifier returned 0.
F-012's dedicated cross-runtime suite and test typecheck passed **54/54** again.
These regression results do not replace the incomplete F-011 verdict above. Existing
C/D TestClient deprecation warnings remain visible and their service code is unchanged.

The execution used the scoped `speckit-implement` workflow, the official foundation
resolver with no persistent selection, 16/16 checked requirements and no pre/post hooks.
T007 and T014 remain unchecked. Prior successful scaffold evidence was archived under
`.cache/review/f011-implementation/previous-scaffold-run/` before a fresh receipt was
generated. Only the checker, its self-tests, this approved plan/execution document,
the T007 progress note and B's inventory/provenance record changed in this increment.
No dependency, frozen record, owner service or existing user draft changed, and no commit
or push was performed.

## Isolated D factory follow-up (2026-11-18)

The user authorized a bounded five-file B candidate after D confirmed its existing
`create_app(provider=..., token=...)` seam. The new B-owned `health_probe_app.py` supplies
an inert provider to that real factory; it does not replace routes or fabricate HTTP
responses. The owner import remains `36ea2a1b59e382930daee7d088c883b0d103c619`.

The isolated review's two promotion blockers are corrected in this candidate:

- The checker uses its normal repository ROOT and `.cache/review/f011-health` locations,
  launching the tracked `health_probe_app:create_app` factory. Provider trace paths must
  belong to the active run, and the new B helper is in the existing source inventory.
- The original matrix regression now checks the exact six remaining owner blockers.
  The original and new tests run together against the candidate checker. Negative traces
  (missing/malformed, wrong operation/scenario, extra/missing/reordered call, invalid
  repair or extra field) invalidate the relevant HTTP case records.

Three authenticated loopback profiles exercise both `/v1/extract` and
`/v1/document-answer`: timeout -> HTTP 504 / `timeout`; rate limit -> HTTP 429 /
`rate_limit`; connection failure -> HTTP 503 / `provider_unavailable`. Each requires
`retryable=true`, frozen envelope/exchange validation and correlated canonical UUIDs.
Safe traces prove one actual `generate` invocation per route (`extract`/`answer`, no
repair). Synthetic private exception details and fixture text must not enter responses
or service logs; trace files contain only scenario, operation and repair metadata.

### Candidate verification and limits

Executed in a separate local checkout under
`.cache/review/f011-d-factory-candidate/repository`, based on
`05c70c2508e84cdb64890e271376bca95aa7f785`. The working branch was not promoted.

- **49/49 checker tests** pass together, including 31 existing tests, ten ported
  extension tests and eight factory/trace regressions. Test subcases cover additional
  invalid trace variants without inflating the reported test-method count.
- Two full health runs, from the candidate root and another working directory, each
  record **154 passed / 50 failed / 6 blocked** over 210 unique cases. All six D probes
  pass; only those six case records differ from the retained 148/50/12 baseline.
- Both health runs correctly return **exit 1**, `passed=false`, `complete=false`.
  Each cleaned all **13** owned service processes and closed their ports.
- The existing scaffold runner passed all **15 steps**: **183 B tooling tests**,
  A/C/D **319/51/59**, frozen/generated checks, web typecheck/build/bindings/config/render
  and **30** real module HTTP cases, with all **12** scaffold processes stopped and
  ports closed. The read-only scaffold verifier also returned 0 on the same source.

Commands from the candidate root:

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'scripts/project'
$env:PYTHONDONTWRITEBYTECODE = '1'
& ./scripts/project/.venv/Scripts/python.exe -B -m unittest discover -s scripts/project/tests -p test_health.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_health.py --mode mock
# Expected exit 1 while the shared health gate is incomplete.
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_scaffold_checks.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scaffold.py
```

Candidate-only command receipts and exact five-file scope are retained under
`.cache/review/f011-d-factory-candidate/`. `health-commands.json` identifies both runs;
`result.json` binds final hashes, cleanup, runtime origins, scope/security checks and
preservation audit. The existing published baseline and earlier isolated receipts remain
unchanged. This is agent verification of key-free mocks, not human/team acceptance.

The offline tooling cache initially lacked a locked wheel. Verification instead used
copies of the already installed environments, with local editable paths and package
metadata rebound inside the candidate. No dependency or lockfile changed, and no network
installation was used. Existing C/D TestClient warnings and the separately pending A
`chromadb` dependency-audit finding remain unchanged; this is not a whole-CI green claim.

The remaining six owner blockers are A mock not-ready, C mock not-ready and its three
business failure triggers, and D mock not-ready. The 50 failures are the imported C
scaffold's known absent-health-route cases. D's mock readiness flag/reason remains an
unpublished proposal; no live-mode substitute or invented switch is used. Reported A/C
follow-ups have not been imported by this package.

F-011/T007 and F-014/T014 remain pending and unchecked. No task/spec/plan checkbox,
owner source/test/dependency/lockfile, frozen contract, fixture or existing draft is
changed. This candidate has not been promoted, merged, committed or pushed.
