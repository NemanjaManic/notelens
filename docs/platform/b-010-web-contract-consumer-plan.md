# B-010: Scoped Web Contract-Consumer Suite Plan

**Prepared:** 2026-11-17. **Owner/story:** B / US1.
**Feature/task:** `specs/002-platform/T001` / B-010, distinct from foundation F-010.
**Status:** approved implementation completed for the scoped B-010 consumer; see execution below.
**Baseline:** `e84856d9aa2d8fea82b40305a63af2db2438e5ec` on
`member-b/task-f-004-web-workspace`.
**Ready dependencies:** foundation F-003/T004 and F-004/T006 are technically complete.
**Unchanged gates:** F-010, F-011 and F-014 remain pending.

This document supplements the existing platform [spec](../../specs/002-platform/spec.md),
[plan](../../specs/002-platform/plan.md) and [T001](../../specs/002-platform/tasks.md).
The initial approval covered this plan; the user subsequently approved its scoped
implementation. Preserve all existing drafts, frozen/generated contracts, A/C/D
source/tests/locks, and existing feature artifacts. No commit, push or message sending.

## Summary and current state

Deliver a small, reusable web consumer boundary plus tests showing that the web accepts
verified synthetic results and exposes a safe rejection outcome for malformed or
mismatched results. Use the generated `@notelens/contracts/v1` runtime and types.
The consumer must not become a second schema, Python business implementation or HTTP
client/router. Later B-003 clients and B-002 views can use this boundary.

F-009 already checks 153 shared wire payloads and 22 simulated exchanges per runtime.
F-004 checks installed web bindings, web build/render and 30 real module HTTP cases.
F-012 checks 54 Python/TypeScript Unicode cases. B-010 must add web consumption behavior,
not replay those suites under a new feature name or count them as new tests.

The current web source contains the starter page and mock configuration/status helper.
There is no `contracts.test.ts` or reusable result consumer. The web package has no
Vitest dependency or test script. Node v24.22.1, TypeScript 7.0.2 and the generated local
package are already installed. F-012 already uses Node's test runner and type stripping.

## Technical context and research decisions

**Runner decision:** use `node:test` and `node:assert/strict`, with explicit NodeNext
test typechecking through the existing local TypeScript compiler. Reuse the successful
F-012 execution style. Node type stripping does not perform typechecking or implement
tsconfig path aliases, so use erasable TypeScript, explicit relative `.ts` imports and
`import type`. See the official [Node TypeScript documentation](https://nodejs.org/docs/latest-v24.x/api/typescript.html),
[test runner](https://nodejs.org/docs/latest-v24.x/api/test.html) and
[TypeScript noEmit option](https://www.typescriptlang.org/tsconfig/noEmit.html).

No Vitest, tsx, browser runner, new npm script or package/lock change is needed for
this bounded suite. Replace T001's planned Vitest verification command with the actual
Node coordinator only during separately approved implementation. Other tasks' future
test commands remain their own deliverables; do not claim those tools are installed.

**Validation decision:** call generated async `validateRecord` for native values,
`validateJson` for JSON text and `validateExchange` for synthetic business exchanges.
Use generated record/context/error types directly. Do not parse JSON with `JSON.parse`
before the strict generated JSON validator, serialize native NaN/Infinity before
validation, coerce values, alter text or repair identity/evidence.

**Fixture decision:** load the frozen documents, payloads, references and transport
fixtures read-only. Use fresh in-memory clones for mutations. The fixture index is
`contracts/v1/fixtures/manifest.json`; there is no `catalog.json`. Select stable
fixture/case IDs rather than copying medical payloads into a second fixture bundle.

**Integration decision:** expose and run this suite through a standalone web-owned
coordinator. Keep existing shared startup, CI workflow/guard bodies and scaffold
commands unchanged in this package. Run existing shared regressions separately after
the source-inventory update. Required application CI wiring belongs to B-006; the
current F-010 workflow does not become evidence that this new suite ran in hosted CI.

## Proposed implementation scope

| B-owned path | Intended change |
| --- | --- |
| `apps/web/src/lib/contracts/consumer.ts` | Thin record/exchange consumption boundary and safe typed outcomes. No fetch, service algorithm or UI page. |
| `apps/web/tests/contracts.test.ts` | Consumer-level positive, negative, preservation and safe-diagnostic cases. |
| `apps/web/tests/tsconfig.contracts.json` | NodeNext/noEmit test typecheck including the consumer module; no Next config change. |
| `apps/web/scripts/check-contracts.mjs` | CWD-independent typecheck/test coordinator, origin/source checks and metadata-only evidence. |
| `docs/platform/interface-review.md` | Append current findings, commands and coverage; retain the historical P1 review unchanged. |
| `specs/002-platform/tasks.md` | T001's real verification command and actual scoped evidence; checkbox only when its consumer acceptance passes. |
| `scripts/project/scaffold_inputs.json` | Explicitly allow the new B source/test/config files and pin the approved task-document change. Preserve all prior pins/snapshots. |
| This plan | Append actual execution and review limits after implementation. |

The proposed package is eight paths; determine exact Git scope during implementation
review. No root/web package manifest, root npm lock, Python dependency/lock, frozen
schema/runtime/fixture, A/C/D file, application page or existing draft edit is proposed.
No ownership-policy, workflow, F-011 checker or global Spec Kit regeneration is needed.

## Constitution check before and after design

| Gate | Design assessment |
| --- | --- |
| B ownership and independent scope | Pass: platform consumer/tests/docs plus the existing B inventory. |
| Frozen contracts and generated bindings | Pass: import/use only; no competing schema or wire definition. |
| Canonical identity/evidence/provenance | Pass: validate against selected context and preserve accepted fields unchanged. |
| English and educational boundaries | Pass: fixed English notices; no diagnosis, treatment or clinical-language claims. |
| Privacy and configuration | Pass: synthetic fixtures only, no logging bodies/tokens and no persistence or provider activation. |
| Honest gates and evidence | Pass: fixture consumer checks are distinct from HTTP, browser UI, model quality and human acceptance. |
| Feature context and preservation | Pass: explicit platform resolver context, existing artifacts preserved, no persistent feature selection. |

No exception is proposed. The confirmed retention/upload limits and 2026-11-24
delivery remain unchanged. No latency, retry, history, rate, budget or model policy
is introduced. Operational decisions remain with their dependent tasks.

## Internal consumer model

These are local TypeScript application outcomes, not additions to `contracts/v1`.

| Input/output | Meaning and invariant |
| --- | --- |
| Record input | One expected generated result definition, explicit native/JSON representation, and selected prepared-document context where required. |
| Exchange input | Known business operation, HTTP status, raw request/response header lists and response JSON; expected record/path/status come from frozen OpenAPI metadata. |
| Accepted outcome | Validated typed record, with existing mode, status, identity, sources, claims, versions and warnings preserved. |
| Service-error outcome | Valid frozen error/exchange; retain code, retryable and diagnostic correlation, with a fixed English notice. Do not expose the upstream error message. |
| Rejected outcome | No accepted result; stable local rejection code, fixed English notice and safe diagnostic rule IDs. No raw body, token or thrown-message echo. |

A record consumer handles classification, extraction, retrieval and answers, including
already-composed answer fixtures. An exchange consumer additionally checks the five
frozen business operations: classify, extract, document-answer, retrieve and
literature-answer. A small operation-to-contract/path/status lookup references the
frozen OpenAPI; it does not decide which service to call or generate a mixed answer.
Undocumented statuses or a success/error body in the wrong channel are rejected.

Keep the boundary pure and asynchronous. It neither performs HTTP nor stores global
document/result state. Successful document-bearing records require the caller's
selected canonical document, not a context reconstructed from the incoming result.
Validate that context; missing/stale/wrong identity must not silently pass. Pure
literature records do not acquire patient-specific document evidence by implication.

For error responses, validate ErrorEnvelope and the exchange without requiring a
rejected/invalid document to pass PreparedDocument validation. Preserve the frozen
400 admission rules for missing/malformed/duplicate business IDs, valid-ID correlation
and raw header duplicates. Do not collapse headers into an object before validation.
Preserve retryability; this boundary does not retry or impose an application policy.

The current consumer is mock-only. Valid live/mixed-mode records used as fixture data
must not be accepted as mock output. Keep route `mixed` distinct from mode `mixed`:
a precomposed answer with document/literature sources and all-mock provenance can
still have route `mixed` and mode `mock`. ErrorEnvelope has no invented mode field.

Insufficient evidence, clarification, an empty extraction and legitimate partial
results remain valid outcomes where the frozen contracts allow them. Do not convert
them into transport failures or erase their gaps/provenance. Component/source IDs
are preserved; namespacing/composition and request routing remain B-003 work.

## Case matrix and acceptance

Enumerate stable case IDs before implementation. Require every declared case to run;
report actual case counts and outcomes, not a count invented by this plan.

| Area | Required consumer checks |
| --- | --- |
| Definitions and context | Valid records for all four result types; wrong result definition, missing context, stale doc_id, wrong digest and corrupted canonical context rejected. |
| Classification | Supported, uncertain and both unsupported execution forms; preserve score_kind, versions and limitations. Do not interpret scores as diagnoses or calibrated certainty. |
| Extraction/summary | Preserve independent extraction/summary success/failure and valid partial/empty outcomes. Retain assertion including `unknown`, temporality, subject and procedure status. |
| Evidence | Preserve non-BMP/repeated evidence; reject bad offsets/quotes, wrong source identity and unsupported reference changes using the frozen validators/reference context. No new highlighter. |
| Retrieval | Preserve sufficient/insufficient state, passages, versions and score note. No retrieval, threshold selection or hard specialty filter. |
| Answers | Document/literature, already-composed mixed sufficient/partial, none and clarification; preserve independent retrieval_provenance and explicit gaps without inventing generation components. |
| Provenance negatives | Reject dangling/cross-kind sources, component/claim mismatches, wrong patient/literature linkage, forbidden mode changes and invalid mixed relationships. |
| Strict input | Malformed/duplicate-key JSON, overflow/non-finite input, unknown version, extra/missing fields and invalid enums fail. Native values are not sanitized through JSON serialization. |
| Transport | Correct success/error records and request-ID correlation; missing/duplicate/mismatched response IDs, incorrect disposition and undocumented status/body combinations fail. |
| Diagnostics and mutation | Invalid responses yield fixed English rejection notices with no payload/credential/exception marker. Frozen input/reference objects and all accepted identifiers/fields stay unchanged. |

Use actual exported consumer functions in these tests. Directly testing only the
generated validators repeats F-009 and does not complete B-010. Include fault probes
showing that bypassing validation, dropping selected-document context, ignoring
correlation or removing provenance checks causes the consumer suite to fail.

"Fail visibly" here means an observable rejected consumer state with a safe English
notice, asserted by the tests and reported through case IDs/rules. This does not
claim browser/report-panel rendering; that presentation acceptance remains B-002.
Do not mark B-002 or another product task complete from this suite.

Synthetic evidence/reference checks do not prove clinical support, English detection
or actual classification/extraction/retrieval quality. Health 200/503 and health-auth
coverage remain F-011; do not extend its partial matrix or misuse its 401-only frozen
exchange-validator branch in this consumer suite.

## Runner, evidence and regression approach

The Node coordinator resolves paths from its own file location. It first checks the
installed generated-package origin/schema and frozen hashes, then typechecks and
executes the explicit test file with the existing Node executable/compiler. No package
download, Python service, browser, provider, corpus or index is needed for this suite.
Run only with the installed toolchain; never use npm exec to fetch an absent runner.

Declare complete case IDs and bind results to a fresh run nonce and current consumer,
test, runner/config and frozen-input hashes. Clear stale success at run start. Missing,
duplicated, failed, skipped, cancelled, validator-only substitute or stale case evidence
must not yield a passing report. A successful compiler run alone is not a suite pass.

Save logs/reports under ignored `.cache/review/b010-contracts/` with owned-path checks.
Reports contain case IDs, outcome/rule metadata, versions, source/artifact hashes and
typecheck/test exits, not document bodies, full records, raw headers or environments.
Use safe scalar/digest assertions so test failures do not dump a medical fixture.
Expected service errors and rejected negative inputs are different from a failed test.

Register only the new B source/test/config files in the current scaffold inventory.
Keep existing B snapshots, frozen/owner pins, prior verification entries and allowable
generated outputs intact. Refresh the shared source-bound receipt after that change;
the existing runner still has its current checks and does not automatically gain a
B-010 case count or hosted CI claim. Record the new standalone result separately.

The known F-010 dependency audit finding on A's `chromadb==1.5.9` remains open. B-010
does not require a green advisory scan or change that dependency. Keep F-010/F-011/
F-014 pending and distinguish regression passes from the known dependency failure.

## Implementation sequence and planned commands

After separate implementation approval, using scoped `speckit-implement` on platform
T001 only:

1. Snapshot all working files/drafts, protected/owner bytes and the real index. Confirm
   Node/local TypeScript/package origins and the existing 16/16 quality gate.
2. Enumerate the case IDs/expected outcomes and read-only fixture references. Implement
   the bounded consumer and its tests without service calls or application pages.
3. Add test-only NodeNext configuration and the no-install Node coordinator. Verify
   strict rejection, safe error outcomes, field preservation and failed evidence paths.
4. Write `docs/platform/interface-review.md` against frozen v1.0.0, noting stale draft
   references in older platform artifacts without rewriting the freeze or other tasks.
5. Register the approved sources and update only T001's verification/evidence. Check
   B-010 only when its actual consumer acceptance passes; all other markers stay as-is.
6. Execute the suite, failure probes, shared/F-012 regressions and scoped preservation
   review. Prepare exact Git scope before any separately authorized commit/push.

These commands are proposed deliverables; the new files do not exist in this planning
change. From the repository root after implementation:

```powershell
node node_modules/typescript/bin/tsc --noEmit --project apps/web/tests/tsconfig.contracts.json
node --experimental-strip-types --test apps/web/tests/contracts.test.ts
node apps/web/scripts/check-contracts.mjs
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_scaffold_checks.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scaffold.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_unicode.py
```

The coordinator is the package's normal verification command, combining typecheck
and runtime checks; direct commands are diagnostic. Verify invocation from another
working directory and avoid unnecessary repeat full runs after unchanged sources pass.

## Completion and downstream boundaries

B-010 requires actual web-consumer positives/negatives, current installed bindings,
test typecheck, complete fresh case evidence, proven safe rejection/no mutation, and
passing relevant regressions with preserved ownership/frozen records. No predicted
test count or fabricated acceptance is recorded by this plan.

B-004 sessions, B-001 real input/preparation and B-002 report UI retain their F-014/
B-010 dependencies. B-003 owns HTTP clients, routing/composition and history. B-005
owns replacing mocks with real modules; B-006 owns full application CI. F-005's shared
mock startup still requires F-011. No one of these tasks is implemented or closed here.

## Actual planning workflow and preservation

Applied the installed [speckit-plan skill](../../.agents/skills/speckit-plan/SKILL.md)
as a scoped platform T001 supplement under the repository's pinned Spec Kit 1.3.3
integration. Research, internal model and validation details are consolidated here;
existing platform plan/research/data-model/contracts/quickstart/tasks stay untouched.
No feature creation, task regeneration, subagent or global CLI install was used.

Executed the official Windows scripts with explicit feature selection:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/002-platform'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
$env:SPECIFY_INIT_DIR = 'D:/Work/SITA/Capstone'
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/setup-plan.ps1 -Json
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks -Template plan-template
```

Setup found the existing platform plan and skipped template copying. The official
resolver returned the platform paths and composed template; it did not change the Git
branch. The existing checklist is 16/16 checked; pre/post extension hooks are absent.
No persistent `.specify/feature.json` was created. Node/TypeScript version probes and
read-only source/interface inspection informed this plan; no new suite or install ran.

Planning evidence is under ignored `.cache/review/b010-plan/`. The preservation audit
passed: only this new project plan was added; all 318 existing files and 16 drafts,
72 protected files and 57 owner files remain unchanged. Local links, source inventory,
the existing scaffold receipt and feature-state preservation were checked. The actual
index is unchanged and empty; HEAD/upstream remain at `e84856d`. Existing implementation
suites were not rerun for this documentation change. B-010/F-010/F-011/F-014 stay
unchecked. No application/runtime, contract, dependency, service, commit or push change
is part of this planning package.

## Approved implementation execution (2026-11-17)

Applied the installed `speckit-implement` workflow to platform T001 only. The official
PowerShell prerequisite resolver selected `specs/002-platform` with RequireTasks /
IncludeTasks and nonpersistent selection. The existing quality checklist remains
16/16; no pre/post extension hooks are registered. The original backlog, other tasks,
frozen contracts and owner boundaries are preserved.

Implemented the eight-path scope above. The interface-review path already contained a
historical P1 review; its original bytes are retained as a prefix to the new review. The consumer uses generated validators/types
for native/strict JSON records and raw-header business exchanges, with safe local
outcomes. There is no service/client/page/package/lock/CI workflow change. T001 uses
the actual standalone Node/noEmit coordinator instead of a nonexistent Vitest command.

Local consumer verification passed: 221/221 cases, no failures/skips/cancellations/
todo; TypeScript noEmit passed. Four consumer fault mutations and sixteen evidence
fault probes were detected. See [interface review](interface-review.md) for exact
coverage, the frozen business diagnostic-ID freshness gap enforced at the consumer,
and the distinction between consumer acceptance and browser/product acceptance.

Shared verification passed: B 165 / A 319 / C 51 / D 59 tests, all 30 HTTP cases,
web typecheck/build/bindings/config/render and protected/generated checks. All twelve
HTTP processes stopped and ports closed. `check_scaffold.py` accepted the resulting
source-bound receipt. F-012 independently passed 54/54 cross-language Unicode cases.
The standalone consumer coordinator also passed from a different working directory.

The isolated eight-file candidate passed local ownership and staged secret checks;
these are agent/local checks, not human approval. The checker detects a config copy
from the unchanged Unicode config, so its declaration includes that read-only source
without adding it to the eight changed files. The real index remains empty/unchanged.

Preservation verified 315 unchanged baseline files, all 16 excluded drafts, 72
protected files and 57 imported owner files. Only four approved baseline paths
(this plan, historical review appendix, platform tasks and inventory) changed, plus
the four new consumer/test/runner/config files. All previous inventory snapshots,
owner/frozen pins and provenance entries were preserved. The historical review's
original bytes remain an exact prefix. Only T001 was checked; no other task changed.
HEAD/upstream remain `e84856d`. Detailed hashes and scoped evidence are in ignored
`.cache/review/b010-implementation/`; fresh standalone results are in
`.cache/review/b010-contracts/`. The final source-bound shared receipt was refreshed
after the appended review's approved inventory pin was finalized.
F-010/F-011/F-014 remain pending, including the known A chromadb audit finding.
No commit, push, merge or message sending is part of this implementation.
