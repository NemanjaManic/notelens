# Member D: Standalone Work Update

**Date:** 2026-11-15. **Scope:** D-owned local and synthetic work that does not require
C's real annotation manifest, A's corpus, B's shared runtime, a paid provider or human
reviewers.

## Completed work

1. **Checked annotation practice examples.** The structural checker passed on 16
   synthetic documents, 18 mentions and 37 mention/evidence/code spans. This does not
   establish semantic support or clinical validity.
2. **Ran the complete evaluation test package.** `python -m pytest tests -q` from `eval`
   passed: **36 tests**.
3. **Ran the complete extraction service test package.** `python -m pytest tests -q` from
   `services/extraction` passed: **59 tests**. One upstream Starlette/httpx deprecation
   warning remains.
4. **Regenerated the current synthetic development evaluation** with the existing
   `d-extraction-qa-synthetic-v2` references: **24 documents, 48 questions, 72 schema-valid
   outputs and 0 technical errors**. The reference digest was
   `7f568febed116050dbd300678cfdcd5198349b6b4da7d3f83dd57d00cb5bb2e1`. Local outputs are
   under ignored `eval/reports/local/synthetic-v4-2026-11-15/`.
5. **Summarized the synthetic mock failures.** Exact entity counts were TP=14, FP=0,
   FN=15 (recall 0.4828 on this authored fixture). Required literal facts were complete
   for 35/48 questions; all four literal completeness checks passed for 10/48; 1/26
   expected gap mentions appeared in answer text or warnings; no unexpected source quotes
   were found in 48/48. Failure records: 25 undisclosed-gap, 15 missing-entity, 11 QA-state
   and 13 missing-required-fact records (categories can overlap). These are narrow mock
   diagnostics, not model-quality, clinical, or acceptance-threshold results.
6. **Checked the answer-review tooling without fabricating a review.** The integrity suite
   passed **7 tests**. Summarizing the blank template reported one blank record, zero
   completed reviews and zero invalid records. No human review or calibration is claimed.
7. **Prepared the D-002 source-selection preflight** in [selection.md](selection.md).
   It lists the C-002 manifest, field mapping, permission, split-integrity and freeze
   evidence needed before real selection. It records no real IDs or assignment decisions.

## Remaining dependencies

- Actual D-002 selection still needs C's published permitted canonical group/split
  manifest and an agreed source-access policy.
- Real assignments, primary annotations and independent reviews require frozen selection
  and actual reviewer participation.
- Cross-module QA still requires A's corpus and agreed A/C interfaces; coordinated
  F-004/F-014 acceptance remains with B and the service owners.
- Live evaluation, reviewer calibration, and substantive thresholds remain unperformed
  pending their respective team decisions and human inputs.

No shared contracts, other owners' files, real annotations, final-set references, provider
calls or paid services were changed or used.
