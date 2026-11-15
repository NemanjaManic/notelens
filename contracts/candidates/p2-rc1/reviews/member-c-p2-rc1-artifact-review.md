# C Review of p2-rc1

**Review date:** 2026-11-12

**Reviewer:** Coding agent assisting C; human confirmation pending.

**Reviewed commit:** `4ad602712bb23df6077cb252e1dd18b8cf8b9288`

**Candidate:** `p2-rc1`

**Manifest SHA-256:** `45a74a22a2ccb3f581edc74acc212f0cc94f54f9de1590b6bdd541013b84f0b5`

The candidate addresses most of C's requested behavior. I support the classification states and score rules, skipped-execution metadata, language-validation boundary, request correlation, and proposed scaffold responsibilities.

I request two changes before final acceptance:

1. **Explicit finite-score validation.** Direct calls to `CandidateContracts.validate()` accepted Python results containing `NaN` and positive/negative infinity as decision scores, and `NaN` as a probability score. The strict JSON file reader rejects these values, but in-memory payload validation does not. Please add an explicit finite-number check and negative tests, and preserve this requirement in the generated-binding/service validation handoff.

2. **Health authentication failures.** Both health endpoints declare `ServiceToken` authentication, but their OpenAPI responses omit 401. Please define the authentication-failure response and its correlation behavior, since health calls do not require `X-Request-ID`. C needs an agreed response shape before implementing these endpoints.

A smaller test-portability issue: `test_validator_runs_outside_repository` initially failed because `.cache` did not exist in the fresh extracted copy. It passed after the directory was created during the suite. Please make this test create its required directory or use a temporary directory.

## Verification performed

- All 33 manifest file hashes matched.
- Deterministic regeneration passed.
- All 139 payload outcomes and 10 simulated correlation outcomes passed.
- All 46 tests passed on the subsequent run.
- `--require-freeze` correctly rejected the candidate with `CANDIDATE_NOT_CANONICAL`.

These checks ran on Windows with Python 3.11.9, the three pinned direct validation dependencies, and Node.js v24.20.0. This was not a reproduction of B's locked Python 3.13 environment. No actual HTTP service, generated bindings, model or provider was tested.

The candidate correctly uses `status`; the earlier `state` field in my illustrative JSON fragments was a drafting error.

Please provide the revised candidate commit and manifest hash after addressing these points. This review does not approve revised bytes automatically or complete F-003. C's scaffold contribution still follows the agreed freeze, F-009 bindings and authorized task scope; C-009 and C-002 retain their existing prerequisites.
