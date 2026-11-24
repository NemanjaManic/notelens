# Proposed D-011 source-grounded semantic review protocol

Status: prepared for explicit coordinator adoption and eligible completed reviews.
No new human review, independent agreement or semantic risk result is claimed.

## Inputs and review

The private packet contains each exact canonical source, question and complete
saved answer, including citations, warnings, state and identity. Source and answer
objects are hashed. Case aliases conceal fixture labels; automatic proxy results,
gold answer labels and other reviewers' ratings are withheld from the live review
form. Canonical source IDs/provenance remain available for identity checking.

Use the existing d-answer-review-rubric-v1 and d-answer-review-form-v2 dimensions:
source support, required facts, extra facts, uncertainty/context, evidence gaps,
scope/safety and clarity/English. Rate each 0, 1, 2 or U. Every 0, 1 or U needs a
reason and minimum correction tied to the source/claim. Preserve the original
rating before adjudication. The accepted seven-case D-008 pilot is supplied as
historical calibration material; its original scores and limited mock scope do
not become new provider-backed reviews.

An eligible reviewer must explicitly disclose identity, completion date,
AI assistance, prior exposure, authorship and preparation involvement. Source
review is distinct from review of the generated answer. An agent draft or an
ineligible/self-authored review cannot fill the independent risk criterion.
Reviewers must not see one another's scores before submission. The implementation
checks declarations and hashes; it cannot independently prove human authorship.

## Proposed risk mapping

For emitted answers, correctness requires all seven dimensions = 2, no critical
error and no unresolved adjudication. This intentionally strict mapping is a
proposal requiring adoption before use. U is unresolved, never silently pass/fail.
Correctness is evaluated against the full source and question; a literal quote
alone is not proof of relevance, completeness or preserved context.

Risk = incorrect emitted answers / all emitted answers. Correct abstentions,
false abstentions, answerability and coverage are reported separately. Provider
errors are technical failures, not answers or correct rejections; their source
answerability still needs an explicit reference/review judgment. The review form
cannot relabel a technical failure as an abstention to improve a metric.

No reported risk is produced until every required case is reviewed under the
adopted protocol. Critical errors and false abstentions remain explicit even
when the emitted-answer risk looks low. This protocol does not assert clinical
validation or waive the existing exact-F1, app or final-measurement gates.

A zero observed error rate is not a demonstrated risk upper bound of 5%. Report
sample counts and uncertainty: with zero errors, the one-sided 95% binomial upper
bound is 1 - 0.05^(1/n); at least 59 independent answered cases are needed for
that bound to be <= 0.05. This is uncertainty context, not a new retroactively
invented release threshold or a claim of independent sampling in the small pilot.

## Read-only scoring

`notelens_eval.semantic_risk.score_reviewed_packet` binds the immutable packet,
the returned forms and an explicit protocol adoption record. It refuses changed
identities/hashes/outcomes, leaves risk unset for incomplete/ineligible feedback
and reuses the existing answer-risk evaluator after validation. Synthetic unit
tests are implementation checks only, not actual human-review evidence.

Run against the exact returned private form, without any model call:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.semantic_risk --packet C:\private-review\packet.private.json --reviews C:\private-review\returned-form.json --decision eval/reports/development/d011-semantic-protocol-adoption-v1.json --output C:\private-review\score.json
```

Exit 2 means reviews or adoption are pending and risk remains null. Exit 0 means
the declarations and pinned data passed protocol checks; inspect the actual risk,
coverage and error counts rather than interpreting the exit code as a quality pass.
