# D-011 economical extraction comparison

Date: 2026-11-23. Status: measured improvement; quality acceptance failed.

## Selected candidate and changes

Service commit: `d41fa880177a7855bb92e57d98673b0a7a77d36b`.
The new opt-in `coverage_v2` prompt asks for clause/section coverage, explicit
procedures and interventions, repeated/negated findings, concise mention
boundaries and separate assertion, time and subject labels. It uses bounded
`low` reasoning. The baseline is `baseline_v1` with `none` reasoning, using the
same service, model `gpt-6-luna` and private quote-hint output protocol.

Python still derives trusted identity and exact offsets from literal source
quotes. Invalid candidates are visibly partial or failed and remain misses.
References never enter model requests. No contract, dependency or lockfile changed.
No semantic labels are rewritten from reference answers. The default profile
remains unchanged; the measured candidate must be selected explicitly.

The returned provider model name is also `gpt-6-luna`; no immutable dated model
snapshot was supplied or independently established. Retain returned model names
and execution dates rather than claiming stronger provider reproducibility.

## Predeclared comparison and actual results

Six documents were selected before generation by evenly spaced length ranks
among the 29 frozen development documents not used in earlier API measurements:
010, 004, 021, 037, 025 and 039. Both arms used the same six sources, the same
per-document output ceiling and alternating execution order. All 204 reference
mentions remain in the denominator, including technical failures. Four previously
observed diagnostic documents and six synthetic QA cases were measured separately.
There were 22 deliberate new calls and zero automatic retries.

| Measure on the paired six documents | Baseline | Coverage candidate |
| --- | ---: | ---: |
| Structurally valid extractions | 4/6 | 6/6 |
| Partial extractions among valid results | 3/4 | 4/6 |
| Completed summaries | 3/6 | 6/6 |
| Exact matched mentions | 47/204 | 91/204 |
| Exact precision | 0.4234 | 0.4919 |
| Exact recall | 0.2304 | 0.4461 |
| End-to-end exact F1 | 0.2984 | 0.4679 |
| Relaxed F1, diagnostic only | 0.3556 | 0.6427 |
| Exact F1 on the four documents valid in both arms | 0.3406 | 0.4721 |

The common-valid subset supports a mention-quality gain beyond recovering two
technical failures; the primary score still uses all six documents. Prompt and
reasoning changed together, so their separate effects cannot be identified.
The descriptive paired bootstrap interval for the F1 difference is approximately
[0.0063, 0.4116], from only six selected development source groups. It is not an
unseen-final estimate or evidence of clinical generalization.

There is also a context-label regression that must remain visible. Among the
31 exact reference mentions matched by both arms, temporal labels are correct
for 25/31 baseline versus 24/31 candidate. Assertion and subject are 31/31 in
both; procedure status is 9/10 in both. On each arm's own different matched set,
candidate temporality is 72/91 versus baseline 40/47. More coverage therefore
does not establish better temporal labelling. No regression acceptance is inferred.

The previous exact F1 of 0.6789 came from two different, shorter documents.
It cannot be directly compared with this broader six-document score. All earlier
results and references remain preserved; thresholds were not reduced.

## Answer review and acceptance

All six saved synthetic QA responses validate and pass the limited literal
support/state/gap proxy. There are four full answers, one partial answer and one
abstention. This proxy is not independent semantic correctness evidence. A separate
private review packet includes sources, questions, complete saved outputs, hashes
and blank current forms. Gold labels, proxy scores, agent notes and other ratings
are withheld. The historical seven-case D-008 calibration appendix stays separate.

The assistant's source-grounded supplementary review finds a redundant repeated
sentence in one response; it is explicitly AI feedback and cannot fill the
independent risk gate. Protocol adoption and eligible completed reviews remain
pending. No new human reviewer or rating has been invented.

Adopted project gates remain schema/spans 100%, exact F1 >= 0.90, unique-topic
Recall@5 >= 0.95 and semantic answer risk <= 0.05. Schema/spans pass on the twelve
candidate extraction/QA returns, including visible partials. Exact F1 fails and
semantic risk is missing. Retrieval 1.0 is carried-forward A-008 development
evidence on 22 supported queries, not a new retrieval run on these twelve returns.
These are project gates, not clinical certification. D-011 and full D-009 remain open.

## Cost and verification

For the six paired calls per arm, recorded token counts yield conservative
standard-rate estimates of USD 0.011076 baseline and USD 0.010547 candidate.
These are estimates, not billing confirmation or proof the candidate will always
be cheaper. The full 22-call run reserved at most USD 0.1054645; known cumulative
worst-case reservations are USD 0.2020124 under the announced USD 0.25 bound.
The prior USD 0.10 trial and its receipt are preserved; the expanded development
run relies on Milica's later authorization for economical additional spending.

137 service tests and 152 evaluation tests pass. Fresh local mock contract and
authenticated HTTP transport readiness pass; cross-service/app/deployment checks
are not implied. A Starlette/httpx deprecation warning remains. No medium-reasoning
experiment ran; its unmeasured configuration change was removed.

Machine-readable evidence:

- [Predeclared plan](../../eval/reports/development/d011-economic-comparison-plan-v4.json)
- [Execution record](../../eval/reports/development/d011-economic-execution-v4.json)
- [Results, attributes and provenance](../../eval/reports/development/d011-economic-comparison-results-v4.json)
- [Failed acceptance](../../eval/reports/development/d011-economic-acceptance-v4.json)
- [Semantic review preparation](../../eval/reports/development/d011-semantic-review-preparation-v1.json)
- [Proposed semantic review protocol](semantic-review-protocol-v1.md)

No additional call, final-case generation, final scoring, push or deployment is
authorized by this report. The candidate is ready for technical app inspection
and further development, not release acceptance.
