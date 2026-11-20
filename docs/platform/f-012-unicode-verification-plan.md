# F-012: B-Owned Unicode Verification Plan

**Prepared:** 2026-11-16. **Owner:** B. **Task:** foundation T008 / F-012, US2.
**Status:** implemented and technically verified on 2026-11-16 after the user's separate
F-012 implementation approval. T008 is checked for this bounded verification deliverable.
The earlier planning instruction alone did not authorize implementation. No new install,
commit or push is part of this execution.
**Dependencies:** technically completed F-004/T006 and completed F-008/T003.
**Requirements:** foundation FR-005/FR-006/FR-007 and SC-003.

This is a bounded supplement to the existing foundation plan/task, not regenerated
Spec Kit feature artifacts or an executed `speckit-plan` output. The recording workflow
uses scoped `speckit-implement` for T006 and respects the supplied prompt and frozen
contracts. [F-004 evidence and review limits](../team/f-004-technical-completion.md)
identify the actual shared source baseline, `8282a73`, and outstanding acceptance gates.

## Intended outcome

Provide an executable Python/TypeScript verification suite proving that the defined
public/synthetic examples produce identical NFC/LF canonical strings and UTF-8 SHA256
values, preserve exact half-open code-point spans, and convert explicitly to browser
UTF-16 slice indices. Invalid raw UTF-16 offsets, wrong quotes/digests/identity and
downstream text mutation must fail on the specified cases.

Use the frozen packages as the record/semantic authority. Do not edit schemas, fixtures,
generated packages or historical contracts. Exact quote validation is not proof of
clinical support or of which repeated occurrence the UI intended to select.

## Existing evidence and missing increment

The existing 155-case canonical suite, 153-case installed binding suite and historical
repeated/non-BMP regression already exercise contract validity. The canonical `offset`
fixture contains a supplementary-plane emoji and two occurrences of `No chest pain.`.
The last occurrence is code points `[47,61)` and UTF-16 units `[48,62)`.

The missing deliverable at planning time was a dedicated, current-canonical, cross-runtime
entry point and web test suite; this increment now supplies it. Reuse current fixtures
and current generated validators; do not
promote a historical P2 candidate or claim that the old regression alone completed F-012.
Current `apps/web/tsconfig.json` includes `src`, not tests; a test-only typecheck must
explicitly cover the planned TypeScript suite without changing production configuration.

The B tooling environment does not declare `notelens-contracts` as an installed dependency.
For the new coordinator, load the unchanged generated package from the explicit
`contracts/generated/python/src` path and assert its origin/schema against this checkout.
Label this as generated-source validation; F-004's separate service binding checks remain
the installed-package evidence. The TypeScript suite uses the existing frozen workspace
package. Do not borrow an owner environment or silently add a tooling dependency.

## Approved owned file scope

| Path | Role |
| --- | --- |
| `scripts/project/check_unicode.py` | Key-free coordinator; independent Python reference using standard library NFC/hash operations and current frozen validators; run the TypeScript checks and compare machine-readable results. Resolve paths from the script. |
| `apps/web/tests/canonical-text.test.ts` | Node test-runner suite for the defined examples, exact occurrence selection and code-point/UTF-16 round trips. This is the task's existing path, to be extended later by B-001 rather than duplicated. |
| `apps/web/tests/fixtures/unicode-vectors.json` | B-owned raw/synthetic test vectors and explicit expected outputs; these are test inputs, not replacement wire contracts or changes to frozen fixtures. |
| `apps/web/tests/tsconfig.unicode.json` | Test-only TypeScript check using installed tooling/types; no application build or new test framework required. |
| `apps/web/tests/helpers/unicode-reference.ts` | Pure test-local code-point/UTF-16 conversion and preparation demonstration; no production ingestion/highlighting entry point. |
| `scripts/project/scaffold_inputs.json` | Explicit allowlisting of any later approved executable test files and new baseline hashes; leave owner/frozen/B snapshot pins intact. |
| `docs/platform/f-012-unicode-verification-plan.md` | Append actual commands/results and limitations after implementation. |
| `specs/000-foundation/tasks.md` | Add actual F-012 evidence and check T008 only after acceptance passes. |

Frozen `contracts/**` paths named by the broad task are read-only for this increment.
A/C/D source, manifests/locks, evaluation/annotation files and user drafts are outside
the change scope. Root/web package manifests and lockfiles stay unchanged under this
proposed no-new-dependency approach. A different runner/dependency choice requires an
explicitly reviewed B-owned scope extension, not an unrecorded install.

## Cases and acceptance checks

| Case family | Required assertion |
| --- | --- |
| Unchanged canonical fixtures | Consume current `offset`, `history` and procedure examples; compare literal text, frozen digest, identity and accepted validation. No downstream normalization. |
| NFC and LF demonstrations | Test-local raw CRLF, lone CR and LF examples and a decomposed-accent English synthetic example produce the explicitly expected LF/NFC string; preparation is idempotent. Preserve ordinary spaces and line breaks; add no trimming, BOM stripping or whitespace-collapse policy. |
| UTF-8 digest | Python `hashlib` and Node crypto agree on exact UTF-8 bytes; canonical fixture digests stay fixed. A digest of altered text or UTF-16 bytes does not stand in for the canonical digest. |
| Supplementary characters | Count Unicode scalar/code points rather than UTF-16 units or grapheme clusters. Check positions before/after the existing emoji and reject unpaired surrogate text via frozen validators. |
| Conversion boundaries | Round-trip valid code-point/UTF-16 boundaries; reject a UTF-16 index inside a surrogate pair rather than rounding or silently repairing it. |
| Repeated text | Assert the exact selected second occurrence and explicit converted `[48,62)` slice, not merely quote existence or first-match search. The first occurrence may be valid evidence in its own right; failing the test's requested occurrence is distinct from contract quote validity. |
| Span boundaries | Cover start/end boundaries and invalid negative, empty/reversed/out-of-range intervals. A raw UTF-16 pair passed as code points fails the appropriate frozen diagnostic. |
| Mutation and identity | Wrong digest, wrong quote, changed downstream text and mismatched `doc_id`/hash are rejected; compare precise diagnostics where the frozen suites define them. |
| Existing clinical metadata | Where complete history/procedure/ICD fixture records are exercised, retain assertion, temporality, subject, procedure status and source-only ICD unchanged; span verification introduces no clinical inference. |
| Retention/output discipline | Only built-in/public/synthetic fixtures; no user input, provider/model/index, body logging or document persistence. Generated test reports stay in ignored `.cache/review/`. |

Keep the Python and TypeScript calculations independent, and assert literal expected
values so agreement between two implementations cannot hide a shared mistake. Do not
derive all expected spans through the conversion function being tested. Language-policy
metadata comes from frozen synthetic fixtures; this suite does not detect English or
authorize real language-validation behavior.

## Implementation sequence after separate approval (executed)

1. Select `specs/000-foundation` using the official resolver and scoped implementation
   workflow; inspect hooks/checklists and preserve the current work/draft snapshot.
2. Define the small case inventory and explicit expected texts/digests/spans in owned
   test vectors, reusing frozen cases where possible. Add no shared wire-field changes.
3. Implement test-local TypeScript checks and independent Python reference/coordinator.
   Use current canonical generated validators rather than historical helper contracts.
4. Compile the dedicated test tsconfig and run the cross-runtime check with no new
   dependencies, service launches or external network access. Include negative cases.
5. Extend only the approved executable-file inventory, refresh stale verification
   evidence, verify all frozen/imported bytes and preserved drafts, then record observed
   counts and limitations. Mark T008 only when the defined suite is 100% correct.

Installed Node v24.22.1 executed `--experimental-strip-types --test` successfully.
TypeScript 7.0.2 typechecked the dedicated test configuration with existing Node types.
No new test-framework package was installed. Later UI/browser tests may extend this
suite under their own scope.

## Executed verification entry points

From the repository root:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_unicode.py
if ($LASTEXITCODE -ne 0) { throw 'Unicode verification failed.' }
node node_modules/typescript/bin/tsc --noEmit --project apps/web/tests/tsconfig.unicode.json
node --experimental-strip-types --test apps/web/tests/canonical-text.test.ts
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_contracts.py --require-freeze
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/generate_contracts.py --check
```

The coordinator also passed when invoked from a separate working directory, with its
child commands run from an ignored run directory. Fixture/runtime paths come from the
script location and TypeScript module URLs; report interchange uses explicit UTF-8.
Acceptance is 100% of the defined structural/hash/span cases, reported by case/count;
no clinical or semantic support threshold is invented. No service test count may be
relabeled as F-012 evidence. Any failure stops completion; contracts are not relaxed.

## Gate and product boundaries

F-012 does not require F-011, F-005 or F-014, so the bounded B work can proceed once
separately authorized. F-005 still requires F-004/F-011/F-012; B-010 is a separate web
record-consumer task; B-001 production input preparation and B-002 report highlighting
retain B-010/F-014/B-004 dependencies. No upload/PDF parser, session store, report UI,
real language detector, provider call, clinical inference or service algorithm is added.

F-010, F-006, F-013, F-007 and F-014 retain the foundation graph. Human/team acceptance
must be recorded separately, including outstanding D shared-commit review clarity.
Completing this bounded F-012 suite does not complete any of those gates or close A/C/D
tasks. No commit, push or colleague message is part of this execution. Delivery remains
2026-11-24.

## Observed F-012 results (2026-11-16)

The executed scoped `speckit-implement` workflow used the official PowerShell prerequisite
resolver with `SPECIFY_FEATURE_DIRECTORY=specs/000-foundation` and
`SPECIFY_FEATURE_NO_PERSIST=1`. The requirements checklist was 16/16 checked, with no
extension hooks. Only foundation T008 is newly checked in this increment; no template,
feature context, constitution or other owner's task was regenerated or completed.

The suite has 54 named cases: seven preparation examples, three unchanged canonical
documents, four clinical-metadata fixtures, five exact spans, six boundary round trips,
nine invalid index values, two surrogate-helper negatives and 18 frozen-diagnostic
negatives. Python and TypeScript independently calculate and assert literal expectations;
the Node runner passed 54 tests without failures, skips or cancellations. The dedicated
test-only TypeScript check passed. A joined emoji/variation-selector example verifies
code-point counting across a multi-code-point grapheme, in addition to non-BMP UTF-16 units.

Additional memory-only probes rejected a wrong second-occurrence expectation, wrong
UTF-8 digest expectation and an incorrectly empty diagnostic expectation. A separate
coordinator replay with deliberately corrupted Python output ran the real Node suite
and failed at the cross-runtime comparison; it left no successful latest receipt.
A subsequent valid run from a different working directory passed 54/54 and created new
evidence. No production/frozen/owner file was mutated by these probes.

The coordinator records only case IDs, public fixture hashes, counts, coordinates,
diagnostic rules and source/runtime provenance. No canonical text or request body is
written to its reports. Every run has a fresh directory and nonce; all results must
agree, the TypeScript command must exit 0 and the frozen/suite inputs must remain
unchanged before a successful `latest.json` pointer is written. Failed runs remove
the old pointer. Failure messages expose only a bounded case/stage identifier or
exception class. This is finite verification tooling, not a service or OS firewall.

Local reports: `.cache/review/f012-unicode/latest.json` identifies the current
`run-*/report.json`, with Python/TypeScript metadata reports and command logs alongside.
The source/draft snapshot and independent negative probes are under
`.cache/review/f012-implementation/`. These ignored artifacts are not distributed
acceptance receipts; a new checkout must rerun the source entry point.

The implementation parent is `f4173b87d304eb36b9d016c5685484ad9539c1e6`.
After allowlisting the five new executable/test inputs and updating only T008's task
document hash, the full existing scaffold runner was rerun (18:50:27-18:52:15 UTC).
All 15 steps passed: B 80 tests, A/C/D 319/51/59 tests, canonical freeze/generation,
installed bindings, web typecheck/build/render and 30 real module HTTP cases, with all
12 processes stopped and ports closed. The default scaffold verifier then returned 0.
Its separate scope remains F-004; the 54-case report above supplies F-012 evidence.
Current shared working-source fingerprint:
`1c90ca4b054ee761ab8d9199d9c2415afa5200d955f8001ee1968a3930b6cb78`.
The existing C/D TestClient warnings remain unsuppressed. These local F-012 changes
are uncommitted/unpushed, and F-014 remains pending.
