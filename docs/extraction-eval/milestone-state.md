# Member D local milestone state

## Current completion checklist (2026-11-23; delivery 2026-11-24)

This section supersedes the historical status below. Closed parent tasks:
D-001, D-002, D-003, D-004, D-005, D-006, D-007, D-008, D-010, D-012 and D-013. D-011 is now closed as development with team-accepted limitations. D-009 remains open.
The tutor confirmed funding sufficiency for continuing the existing plan; less
than 10% of project budget is reportedly consumed. Milica subsequently authorized additional synthetic diagnostic calls to resolve
provider failures; six were executed with zero automatic retries and the retained
cumulative USD 0.10 cap. Following later explicit authorization for economical additional spending, the
coverage/low comparison brings known cumulative reservations to USD 0.2020124
under a locally announced USD 0.25 cap. These are bounds, not actual billing.
The original USD 0.10 trial receipt remains unchanged. See the
[funding record](../../eval/reports/development/d004-tutor-budget-confirmation-2026-11-23-v1.json).

| Order / task | Concrete remaining work | Responsible party / completion evidence |
| --- | --- | --- |
| Complete. D-004 | CLOSED D-owned implementation and bounded synthetic live verification: JSON-input rejection diagnosed and fixed; final extraction contains five supported mentions/statuses and a five-claim summary. Raw final output passed unchanged. All 112 service tests pass. | Receipt: eval/reports/development/d004-d005-provider-review-v3.json. Original receipts preserved. Broader quality remains D-011; this does not establish production/deployment acceptance. |
| Complete. D-005 | CLOSED D-owned implementation and provider-output review: final summary and cough answer reviewed for support, completeness, English and exact citations. Both saved-live-response HTTP replays passed without another provider call. Reviewed service SHA c7d0797; package/startup/pins ready. | Goran owns remaining app recheck of identity/highlights/partial/insufficient/out-of-scope. See docs/extraction-eval/d005-reviewed-handoff-v3.md. No message, app-call scope or deployment approval is inferred. |
| Complete. D-013 | CLOSED: Milica approved D013-freeze-candidate-v1; d013-development-reference-freeze-v1 is materialized. All 40 development references, 1,189 mentions, 1,320 evidence spans, 250 disposition IDs and 49 archive checksums verify. | Completed by Milica/D. Freeze receipt: eval/reports/development/d013-reference-freeze-receipt-v1.json. 153 tracked items are work for D, not a new 153-question user form. |
| Complete. D-007 | CLOSED: d007-final-reference-freeze-v1 records all 26 exact case versions/hashes and both sets of thirteen approved human reviews; 25 v1 plus F-DOC-06 v2, zero unresolved issues reported. Four supplied checksums and all receipt identity links verify. Final content remains restricted; D relied on custodian/reviewer attestations for hidden file bytes and spans. | Freeze receipt: eval/reports/development/d007-final-reference-freeze-receipt-v1.json. D-009 still requires explicit eligibility disposition for prior technical-note exposure of F-DOC-01/02/03 and joint system/configuration/execution approval. No final measurement authorized or executed. |
| Complete. D-008 | CLOSED in the approved limited mock development-pilot scope: 14 original ratings, seven paired cases, five entity-evidence items, unchanged initial agreement 43/49 (87.76%), six approved adjudication decisions and 30 verified final checksums. Original approximate-40/20 targets were not met; shortfalls of 26/15 are accepted and reported. | Milica approved all six decisions and reports team acceptance of limitations. Final report: eval/reports/development/d008-limited-pilot-final-v1.json. No new reviews are requested. |
| Complete with limitations. D-011 | Candidate d41fa880 / coverage_v2 / low: on six paired new development documents exact F1 improves 0.2984 to 0.4679; valid returns 4/6 to 6/6, with four partial candidate extractions. Common-mention temporal labels regress 25/31 to 24/31. Six synthetic QA outputs validate; semantic risk remains missing. 137 service and 152 eval tests pass. | Milica reports team agreement to development closure with accepted limitations. Quality acceptance remains not met; semantic risk remains unmeasured. Receipt: d011-team-accepted-closure-v1.json. |
| Open. D-009 | Full scope retained. Latest candidate, failed development acceptance, 26 identity pins, unapproved eligibility proposal, v5 app handoff and final scorer are prepared. Fresh mock contracts/transport and 152 eval tests pass. | Still requires D-011 quality/risk, Goran app receipt, eligibility disposition, approved joint freeze and restricted final references/outputs. Final execution/scoring not performed. See d009-d011-remaining-actions-v2.md. |

For B-005/B-009/B-007, Goran owns integration/demo/deployment acceptance. Milica
supplies reviewed D service evidence. B-007 additionally needs approved host/account/
costs and target TLS/auth/readiness/persistence/memory verification. These B tasks
are not D-owned implementation tasks.

Fresh production build, 160 key-free cases, integration TypeScript checking and
six verified successful hosted runs are already recorded. On an approved Windows
machine run default mock security, smoke, pinned D-005, readiness and Chrome first;
run indexed RAG separately. This machine's Application Control error 4551 requires
administrator resolution or another approved machine; no bypass or rerun pass is
claimed. See the [platform record](../../eval/reports/development/d009-platform-evidence-intake-v2.json).

## Historical 2026-11-11 checkpoint

Inspected 2026-11-11 on `member-d/extraction-evaluation`, starting at `e468d2f`.
The continuation request explicitly authorizes D implementation behind provisional
adapters while shared gates remain pending; no commit/push or external messages.

- Preserved existing uncommitted training checker, guide changes and C handoff.
- Reproduced 16 synthetic documents / 18 mentions / 37 span checks. The eight invalid
  cases previously existed only as inline experiments; persistent regression coverage
  is being added with the service tests, not retrospectively claimed as existing.
- Local Spec Kit integration is 1.3.3. Read scoped speckit-implement instructions;
  feature resolver ran with `SPECIFY_FEATURE_DIRECTORY=specs/004-extraction-evaluation`
  and `SPECIFY_FEATURE_NO_PERSIST=1`, using process-only PowerShell Bypass. Checklist:
  16 checked, zero unchecked; no before/after hook file exists. No global policy changed.
- No existing service/test package, frozen contract, generated binding, provider/model
  selection or C split manifest was present. Gemini is a candidate, not approval.
- uv was absent on PATH. Bootstrapped uv in the ignored extraction `.bootstrap`
  environment and used it for service-local lock/sync. Python 3.11.7 is available;
  3.13 was a proposal. No root configuration or shared schema changed.

## Implemented and verified

- Standalone FastAPI/CLI with mock extraction, literal English summary and document QA,
  current draft-schema validation, shared evidence primitives, request correlation,
  explicit mode/configuration and bounded repair diagnostics.
- 40 extraction/service regressions passed, including an actual loopback process/CLI
  test and eight persisted training-checker negatives; 8 eval/tooling tests passed.
  One Starlette TestClient dependency deprecation warning remains; tests passed.
- The original system-Python training command still reports 16/18/37. No third-party
  dependency is needed by that command after reusing the evidence primitive.
- Independent synthetic predictions and three document-QA cases evaluated. Entity
  counts are TP=4, FP=0, FN=1 (the catalog intentionally misses cough). These are
  synthetic/mock scoring demonstrations, not real-model or clinical results.
- Promptfoo 0.125.1 ran three cases against the actual temporary mock HTTP server:
  3 passed, 0 failed/errors. The initial bare CLI could not open its default database;
  the wrapper now keeps tool state in eval/.promptfoo and disables cache/telemetry/
  sharing/result persistence. Node's user-info sandbox restriction required escalation.
- Synthetic selection produced 20 proposal assignments and 30 pending templates;
  a separate test verifies the 40-document/10-primary-per-member algorithm. Merge CLI
  produced pending_adjudication from an empty synthetic bundle, without labels.
- GitHub read-only heads check still found main at e7bc839 and D's branch at e468d2f.
  No newer shared freeze or foundation was available there. No commit/push was made.

Actual commands: [integration](integration.md). Remaining requests:
[B/C/A/configuration](milestone-requests.md). Parent tasks stay partial where frozen
contracts, real data, actual human review or an approved live provider are required.
Draft schema compatibility is not a shared foundation freeze.

## Development freeze decision, November 23

Milica stopped further extraction improvements. Implementation d41fa880 / coverage_v2 / low is frozen for handoff. D-011 quality remains failed, independently reviewed risk is absent, and D-009 joint final execution remains pending. See [the capstone evidence map](capstone-delivery-evidence-map-v1.md). No quality waiver or final pass is inferred.

## Team-accepted D-011 closure

Milica reports team agreement to close D-011 as completed development with the disclosed limitations. This supersedes earlier statements that the parent task must remain open. Quality acceptance remains not met; thresholds and historical measurements are unchanged. D-009, deployment and joint final execution are not approved by this decision.

## PR 31 replay intake

Accepted bounded D-005 historical saved-response replay evidence at platform
0536cb56fdd1f99f9cc73110e28a90a22892cb01 / D service c7d0797. Hosted key-free
CI success was directly verified; local replay success is Goran-reported, not
a fresh D rerun. This does not validate frozen development service d41fa88 or
execute the 26-case final set. D-004 and D-owned D-005 are closed in that bounded
scope; full D-009 remains open. See d005-pr31-replay-review-v1.json.
