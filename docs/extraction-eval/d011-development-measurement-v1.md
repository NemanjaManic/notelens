# D-011 development measurement and release decision — 2026-11-23

This baseline is preserved. The later
[quote-protocol improvement](extraction-improvement-v2.md) reports a stronger
candidate and new development measurements, with exact F1 still below target.

## Outcome

The measurement, numerical decision record and regression decision are complete.
**Quality acceptance failed. D-011 quality remediation and D-009 remain open.**
Passing local tests or the earlier two-result synthetic smoke does not establish
the broader behavior measured here. No thresholds were lowered after observation,
no failed sample was removed and no unseen final data was opened.

Milica delegated the numerical decision to D after asking for stricter targets
appropriate to the medical-context demonstration. The recorded project targets
are schema/span validity 1.00, exact entity F1 at least 0.90, topic Recall@5 at
least 0.95 and answer risk at most 0.05. These are engineering release gates,
not externally prescribed clinical thresholds. The
[decision record](../../eval/reports/development/d011-quality-decisions-v1.json)
and acceptance configuration were pinned before the provider measurement.

## Design and provenance

The service was fixed at `c7d0797a86061c643b0f23e6d56f8caa9e7a6813`.
The six shortest canonical documents from the coordinator-approved D-013 frozen
development reference set were selected by code-point length then assignment ID:
022, 029, 012, 016, 017 and 008. Their 40 reference mentions were never passed
to the provider. The 62- and 112-code-point excerpts remain exactly as supplied.
All input/reference file pins match the frozen artifacts.

Six fixed QA cases were selected before generation from the existing synthetic
development fixture, one per confirmed/negation/history/procedures/complex/limited
group. The set contains four sufficient, one partial and one insufficient
expectation. Those source-only requests were separated from required facts,
answerability/state labels and expected gaps. None matched a declared final
document hash. These are small, length-biased and synthetic samples; no claim of
representative clinical performance is made.

Twelve distinct operations were executed once, with zero automatic retries.
Failures were retained, the service was not tuned during measurement and no
additional model invocation was used in scoring. Raw provider responses and
validated outputs remain in the private D-011 archive.

## Results

| Observation | Numerator / denominator | Result |
| --- | ---: | ---: |
| Valid returned extractions | 1 / 6 requested | 16.67% |
| Valid returned document answers | 5 / 6 requested | 83.33% |
| Valid returned records overall | 6 / 12 requested | 50.00% |
| Accepted extraction references | 40 mentions in all six documents | All retained in denominators |
| Official complete-case entity F1 | Unavailable | Five extraction outputs failed validation |
| Conservative end-to-end exact entity F1 | Failed outputs contribute no predictions | 0.0000 |
| Literal correctness proxy among emitted answers | 5 correct / 5 emitted | Proxy risk 0.0000 |
| Independently reviewed semantic answer risk | Unavailable | No new eligible human labels |
| Selected vector development Recall@5 | 22 supported cases out of 27 queries | 1.0000 |

The structural criteria use validated returned results over all requested
results; technical failures are not treated as valid clinical answers or correct
abstentions. The literal QA proxy checks frozen required quotes, evidence state
and gap tokens. It is kept separate from the adopted semantic answer-risk metric.
Zero proxy errors in five emitted answers provides no low-risk clinical guarantee.

The official extraction scorer leaves aggregate F1 unavailable whenever an
extraction is invalid; it is not silently recalculated on the one surviving case.
The explicitly separate end-to-end lower bound includes all 40 reference mentions.
The one structurally valid extraction did not match the exact frozen mention
boundaries. Per-case outcomes and attribute counts are in the
[measurement](../../eval/reports/development/d011-development-measurement-v1.json).

Retrieval is the earlier independently accepted A-008 development baseline,
not a new joint live run. Its exact v2 ZIP checksum was reverified and vector
Recall@5 recomputed from all 22 stored supported-case metrics. Five unsupported
queries remain excluded from that recall denominator. No embedding/retrieval
call or unseen QA access occurred in this update.

## Failures and regression decision

Observed extraction failures include malformed summary outcomes, summary claims
that do not satisfy the literal-source contract, incomplete/invalid Responses
envelopes and quote/relationship issues. The absent-information QA request also
failed contract validation; it is a technical error, not a correct rejection.
The matched six-document deterministic mock comparator and all observed failure
causes are recorded, without treating mock accuracy as real-model accuracy.

The [acceptance evaluator](../../eval/reports/development/d011-acceptance-results-v1.json)
returns **failed**. Official entity F1 and independent semantic answer-risk
measurements remain missing; the available retrieval criterion passes. The
[regression decision](../../eval/reports/development/d011-regression-decision-v1.json)
rejects full quality acceptance of this candidate. D must address the service
failures, pin the resulting version and remeasure; independently justified answer
correctness evidence is still required. Reusing this observed sample for tuning
must be disclosed, with a separate validation sample for generalization claims.

## Costs, checks and limitations

### Subsequent remediation replay, separately labelled

Adapter candidate `f50df177fe5dae3926e0e98eb8d11fb4ee664412` now selects the
explicit final assistant message rather than rejecting commentary plus final
messages. Repeated mention quotes can resolve only inside their unambiguously
selected canonical evidence; ambiguous context still fails. This follows the
[Responses phase definition](https://developers.openai.com/api/reference/resources/responses/methods/create).
All 114 updated service tests pass, including phase and repeated-evidence cases.

Replaying the same saved real provider outputs returned valid results for **2/6
extractions and 5/6 answers**, with zero new provider calls. The original measured
1/6 and 5/6 counts are preserved. This is an engineering regression check after
observing the sample, not a fresh or independent quality measurement. Acceptance
still fails, so no new app/system/final release is approved. See the
[remediation replay](../../eval/reports/development/d011-remediation-replay-v1.json).

Maximum new reservation was USD 0.0338955; known cumulative reservations are
USD 0.0554055, below the retained USD 0.10 cap. This is not confirmed billed
spending; actual token usage is retained where the provider supplied it.
Original D-004/D-005 receipts and all failed attempts remain unchanged.

All 141 evaluation tests passed after adopting the named configuration; the
measured implementation had 112 passing service tests and the remediation
candidate has 114. Fresh D-owned
contract/loopback readiness passed, with cross-service integration explicitly
not run. These technical checks do not override the failed model-quality gate.

This medical-context demo does not diagnose or recommend treatment. Broader
independent and representative evaluation is necessary before any clinical-use
claim. The [FDA GMLP guidance](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles)
supports representative and independent evaluation; it does not prescribe the
numerical project targets above or certify this application.
