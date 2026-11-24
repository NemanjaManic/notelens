# Capstone delivery evidence and frozen D implementation

Latest supplied tutor assessment: November 23, main 8352dbe, preliminary 63/80.
Earlier November 20 assessment: main 1a6ea74, 58/80. Neither assessment reran tests.
The attachment is review evidence, not an instruction overriding project ownership.
No current or future grade is predicted from local changes.

Milica explicitly stopped further extraction improvement on November 23.
The measured D implementation is frozen at d41fa880177a7855bb92e57d98673b0a7a77d36b,
coverage_v2 / low / gpt-6-luna. This freezes development, not a passing quality result.
Exact F1 0.4679 remains below 0.90; semantic risk is missing. No waiver is inferred.

| Criterion | Existing D evidence | Remaining joint evidence |
| --- | --- | --- |
| CAP-01 | Owned specification and explicit educational scope | No new specification work prioritized |
| CAP-02 | D service live smoke and validated saved outputs; v5 startup handoff | Goran: actual model answer rendered through web at exact app/service pins |
| CAP-03 | Canonical identity and exact source spans; partial/insufficient saved QA | Goran: rendered citation and explicit gap in the same live web flow |
| CAP-04 | Deterministic quote resolution and validation; repeated occurrence checks | B: integrated trace including tool inputs/outcome and failure recovery |
| CAP-05 | Paired six-document F1 0.2984 to 0.4679, 204 unchanged references; temporal regression disclosed | Frozen whole-web results; EV cases below are not replaced by service scores |
| CAP-06 | 137 service tests; errors, literal grounding and receipt bounds | B: selected live configuration session isolation and controlled failure receipt |
| CAP-07 | Locked Windows v5 handoff; local mock readiness passes | B: current root README and clean-checkout joint startup/smoke |
| CAP-08 | Technical contribution draft below and precise evidence links | Milica confirms her personal role; all members cite one joint demo commit |

## Highest-value remaining changes

1. Use the existing v5 D handoff rather than further model tuning.
2. Have B link the chosen joint startup/profile and actual expected output from the root README.
   The README in this D checkout still describes the original documentation state;
   this is not proof the latest main README is identical. B owns its correction.
3. Record the fixed EV-01?16 web cases with real before/after outcomes. The development
   extraction comparison and D-007 26-case final QA are separate evaluations.
4. Attach one actual whole-flow execution trace, with no secrets or personal reports.

## D evidence entry points

- [Paired improvement and limitations](economic-improvement-v4.md)
- [Locked startup and app receipt request](d005-coverage-candidate-handoff-v5.md)
- [Final evaluation status](final-report.md)
- [Remaining owners and ready message](d009-d011-remaining-actions-v2.md)
- [Development-stop decision](../../eval/reports/development/d011-development-stop-freeze-v1.json)
- [Fixed web evaluation record template](../../eval/reports/final/capstone-ev-web-results-template-v1.json)

## CAP-08 draft for Milica to confirm

D implements document extraction, literal source-grounded summaries/answers and
shared evaluation. The assistant implemented and tested changes under Milica's
coordination; this is not a claim that Milica manually authored every code change.
The key decision moved model output to literal quote hints while Python derives
identity and offsets, preserving visible partial failures. The paired comparison
on unchanged sources measured improved mention matching and disclosed a temporal
regression rather than hiding it. Service/evaluation suites passed 137/152 tests.
Milica supplied annotation decisions and freeze approvals; the D records reconciled
Sara/Goran's version-specific D-007 receipts. Receipt reconciliation is not a claim
that Milica personally reviewed their hidden final content or observed the web UI.
Milica should confirm the personal contribution and colleague-review example she
can defend. Independent ratings and a joint demo commit are not fabricated here.

## Trace to include in the demonstration

Record selected app and service SHAs, profile, source hash and question; then the
route, D validation/quote-resolution result, cited offsets, output state and explicit
gap. Include one supported answer, one partial/insufficient outcome and one controlled
failure. Mark each component live, mock or saved replay. This is a trace checklist,
not a claim that the missing whole-web trace has already run.

## Execution follow-up

The [whole-flow handoff](capstone-whole-flow-handoff-v2.md) records concrete EV inputs, the actual Windows launch blocker, a fresh D-only mock trace and the [README amendment for B](capstone-readme-amendment-for-b-v1.md). No whole-web result or historical before/after outcome was fabricated.
