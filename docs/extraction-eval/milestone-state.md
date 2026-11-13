# Member D local milestone state

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
