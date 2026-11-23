# NoteLens D-009 delivery evidence — final measurement pending

Date: 2026-11-23. Delivery target: 2026-11-24.

**Status: blocked; full joint final evaluation has not been executed.**
Milica explicitly retained the full D-009 scope and asked to wait for Goran's
configured app verification. No reduced development-only closure, acceptance
waiver or release approval is recorded. This document consolidates measured
development evidence and C's separately verified owner-final aggregate; it does
not present them as a joint unseen-final result.

## Available evidence

| Component | Observed evidence | Profile and limits |
| --- | --- | --- |
| D extraction and document QA | Earlier synthetic smoke: five supported extraction items, five summary claims and a supported cough answer; raw final results passed unchanged. | One synthetic document/question; 112 service tests and two saved-live-response HTTP replays passed. |
| D-011 broader development pilot | Valid returned extractions 1/6; answers 5/6; 6/12 valid records. Forty reference mentions included. | **Acceptance failed.** Complete-case entity F1 and independent semantic risk unavailable. Conservative end-to-end exact F1 0.0000; five emitted literal answers had zero proxy errors. |
| D service remediation replay | Same saved outputs: 2/6 valid extractions, 5/6 valid answers; 114 service tests pass. | Candidate f50df177; zero new generation, observed-sample regression check only. Acceptance still fails; original measurements preserved. |
| Latest quote-hint candidate | Source-grounded outputs validate for 11/11 development documents (nine complete, two partial) and 3/3 QA; 130 service tests pass. | Candidate 8ef63edd. Same-six exact F1 0.6500; two further post-fix fresh documents 0.6789 exact / 0.8440 relaxed. Exact target 0.90 and semantic-risk gate remain uncleared. |
| A selected vector retrieval | Development Recall@5 1.0000; MRR@5 0.909091; 22/22 all-topic supported cases. | Previously accepted A-008 development evidence, 27 total queries and 22 recall-eligible cases; no new retrieval run. |
| C-008 classifier | Forced-choice accuracy 176/183 (0.96175), macro-F1 0.9582; selective coverage 174/183 and accuracy 169/174. | C-owned locked final aggregate, independently checked against the pinned confusion matrix; not joint system performance. |
| D-008 calibration | Fourteen original ratings over seven paired cases, five entity-evidence reviews, initial agreement 43/49 (87.76%), six approved adjudications. | Explicitly accepted reduced mock development pilot; no new independent provider-output review credit. |
| Security/platform | Previously verified B evidence and six successful hosted runs; recorded locked build and 160 key-free cases. | Exact revisions/profiles retained in platform intake. New Windows default/indexed reruns and rendered provider app acceptance are not claimed. |
| Fresh D local readiness | Contract inspection and authenticated loopback transport passed; 141 eval tests passed. | Cross-service, deployment and Chrome acceptance not executed in this update. |

See [D-011 methods/results](d011-development-measurement-v1.md), the
[D-004/D-005 reviewed smoke handoff](d005-reviewed-handoff-v3.md) and the
[machine-readable final readiness record](../../eval/reports/final/d009-final-readiness-v1.json).
The adopted thresholds are recorded in `eval/config/acceptance.json`: schema and
spans 100%, exact entity F1 at least 0.90, Recall@5 at least 0.95 and semantic
answer risk at most 0.05. They are project release gates, not clinical certification.

## Reference identity freeze and custody

D-013 freezes 40 development references with 1,189 mentions and 1,320 evidence
spans. These remain development data and cannot be relabelled unseen final.
D-007 freezes the identities of 26 QA cases: eight document-only, eight
literature-only, eight mixed and two out-of-scope. Twenty-five are v1 and
F-DOC-06 is v2. Both sets of thirteen case-version-specific approvals match their
recorded hashes. Full final source texts, questions and answer keys remain in
Sara/Goran's restricted workflow and were not opened for this report.

Technical reviewer notes for F-DOC-01/02/03 were previously exposed to D's
assistant. Their eligibility needs an explicit disposition before a fully unseen
claim. Metadata/reference identity freeze is distinct from approved joint system
freeze, actual generation and independently reviewed output scoring.

## Candidate system and executable scoring preparation

Measured D service: c7d0797a86061c643b0f23e6d56f8caa9e7a6813.
Latest remediation candidate: 8ef63edd4ab1cb39de73b0f31b97bb12359f7731
with explicit input_format messages / output_format quote_hints,
selected RAG manifest d0502196edabc1301b06b55f2d1ddb1f888ac678b51502227d0f9a0fd5a67685,
and C-008 classifier manifest fd87686bddfe7d3f86103b562161c64c241f6e4759ca69467d1360d35283ac70.
The new D pin still needs further remediation, fresh development acceptance and
the matching app receipt; no earlier app/smoke approval transfers automatically.

`eval/config/d009-final-freeze-candidate-v1.json` pins known identities, the
adopted acceptance configuration, reference identity manifest, C aggregate and
196 known development/source identifiers. It remains **approved: false**.
Missing restricted reference/prediction hashes stay null. Screening identifiers
alone does not establish source-family independence; final custodians must
confirm provenance and group declarations.

The saved-output final scorer is implemented and covered by key-free regression
tests. It verifies an approved freeze, exact artifact hashes, declared final
partition, separate development groups, selected versions and real-mode outputs.
No final receipt was claimed and no final artifact was scored by this update.

## Required closure gates and owners

1. **D:** remediate failed extraction/summary/contract behavior, remeasure the
   pinned service against development references and provide independently
   justified answer-risk evidence. Retain thresholds and failure history.
2. **Goran:** provide the configured app receipt with exact app/service SHAs,
   profile and identity/highlight/partial/insufficient/out-of-scope findings.
3. **Sara/Goran with Milica:** resolve eligibility of the three exposed-note
   cases and retain exact final case versions, source provenance and approvals.
4. **A/B/C/D with Milica:** approve the exact joint system/configuration/reference
   freeze and a bounded final execution scope after the preceding gates clear.
5. **Restricted operators/custodians:** execute the frozen 26 cases with only
   runtime inputs, keep gold references separate and supply saved outputs,
   usage/receipts, source-group declarations and independent correctness evidence.
   Full final extraction scoring also needs distinct final extraction references;
   D-013 development labels cannot be reused as unseen final references.
6. **D:** verify the resulting artifacts, score once using the exact approved
   freeze, then publish measured final results and the actual acceptance decision.

An apparent pass in one component cannot fill missing results for another.
Deployment acceptance and B-005/B-007/B-009 remain with B and are not inferred.

## Costs, publication and limitations

Known cumulative worst-case provider reservations are USD 0.0965479. They are
not confirmed billed spending; token usage and exclusive receipts are retained
privately. No additional final-provider spending is authorized by the unapproved
candidate. No unseen final generation, scoring, deployment, push or external
message was performed for this report.

The single-document smoke, length-biased six-document pilot, synthetic QA and
non-independent agent support checks are explicitly bounded evidence. They
cannot establish clinical safety, representative medical performance or a
joint final release pass. The failed quality gate is preserved without hidden
threshold reduction, selective sample omission or fabricated reviewer approval.
