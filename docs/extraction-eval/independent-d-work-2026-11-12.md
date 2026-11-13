# Five independent Member D deliverables

Date: 2026-11-12. These are local D-scope increments prepared without A/C data,
B-owned contract changes, a provider choice or colleague review.

## 1. Full synthetic HTTP evaluation

`eval/src/notelens_eval/http_suite.py` runs extraction and document-answer requests
for all 24 synthetic documents and 48 questions through a temporary, authenticated
loopback service in mock mode. Provider inputs contain only each public request;
reference facts/gaps remain in the post-call evaluator. Its JSON and Markdown outputs
go to ignored `eval/reports/local/http-suite/`. The report separates HTTP/technical
failures from evaluator-detected misses. It makes the existing functional mock visible
through the actual transport path, but does not exercise A, B orchestration or C.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.http_suite --output eval/reports/local/http-suite
```

The completed local run sent 72 requests: 72 HTTP 200 responses, 0 technical failures,
72/72 matching request IDs, 72 schema-valid records, and 0 schema/evidence validation
errors. The scorer reports mock-catalog misses separately; it is not a real-model quality
result. Outputs are generated locally and ignored with other run outputs.

## 2. Annotation draft linter

`notelens_eval.annotations lint` checks one draft's assignment identity, role, document
hash, completion flag, mention/evidence offsets, context enums and source-present ICD
evidence. It surfaces unresolved questions and unsupported assertion/procedure states
without normalizing them into accepted contract values. The synthetic input is
`eval/fixtures/annotation-lint-synthetic-v1.json`. Output contains IDs and issue codes,
not document text. A pass is structural readiness only, not proof of completeness.

## 3. Independent review comparison

`notelens_eval.review` compares primary and secondary submissions using exact mention
type and offsets. It reports unmatched mentions, per-attribute agreement over matched
mentions, evidence-span equality and explicit disagreements. It never adjudicates or
generates labels. The sample at `eval/fixtures/review-comparison-synthetic-v1.json`
contains one designed assertion disagreement.

## 4. Human answer review rubric and form

`answer-review-rubric.md` defines a seven-dimension draft rating scale, blind independent
review guidance, outcome flags, error handling and a calibration proposal. The blank
machine-readable form is `eval/fixtures/answer-review-template-v1.json`. No review,
calibration round, reviewer assignment, acceptance threshold or clinical judgment has
been invented. D-008's human calibration portion remains open.

## 5. Benchmark reference coverage profile

`evaluate_suite` and its Markdown report now show counts by QA evidence state, answerable
questions, required facts, expected gaps, entity type, unresolved attributes and group.
This helps the team spot benchmark imbalance before reading model scores. It is reference
coverage accounting, not a prediction-quality metric.

## What remains dependent on the team

C-002 still needs an approved, permitted, group-separated document manifest before real
annotation selection. B still needs to freeze shared contracts and supply integration
fixtures/bindings. A/B still need to provide the cross-service QA corpus and runtime.
The rubric still needs human calibration; real annotations and adjudication require
assignments and independent submissions. Model/provider comparisons and substantive
threshold selection require the appropriate approved references and operating policy.

These increments prepare D's tools and reviewer-facing artifacts. They do not mark the
parent backlog stories complete while those requirements remain open.
