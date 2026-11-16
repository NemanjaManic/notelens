# Answer Support Policy Proposal

Owner: Nemanja (A). Author: Codex coding agent for Nemanja (A).
Date: 2026-11-15. Proposal: rag-answer-support-policy-proposal-v1.
Status: proposed behavior; local validation processor implemented, semantic
assessment/activation and policy acceptance pending.

Nemanja approved preparing this proposal. That approval does not mean that its
rules, unresolved interface interpretation, semantic assessor, thresholds or
paid execution have been accepted. The existing candidate CLI and HTTP mock
remain unchanged. A-004 and A-009 remain incomplete.

## Purpose and evidence

Decide which requested information may appear in an English literature answer,
which information is missing, and when no literature claim should be returned.
Ranking finds candidate passages; it does not establish answer support.

The [content review](retrieval-content-review.md) inspected fifty retrieved
passages for ten public development questions: eight questions had full support,
one had partial support and one lacked its requested statistic. Those are agent
judgments, not human gold labels or an accuracy estimate. Their overlapping
ranking scores do not justify a universal top-score cutoff.

This proposal applies to A's general literature information. D owns document
facts and document answers; B owns routing, composition and application surfaces.
The governing references are the [RAG specification](../../specs/001-rag/spec.md),
[canonical contracts](../../contracts/v1/README.md) and
[frozen-contract adaptation](frozen-contracts-adaptation.md).

## Proposed decision rules

| Rule | Proposed behavior |
| --- | --- |
| AS-01: Requested parts | Identify the independently requested facts and their entity, relationship, location, time period and units. A title match is not a supported fact. |
| AS-02: Evidence | A fact needs an attributable retrieved passage that actually supports it. Preserve exact canonical text, source identity and quote offsets in the internal review trace. Exact quote matching is necessary for traceability but does not prove semantic support. |
| AS-03: Full answer | Return a full answer only when the evidence covers every material requested part and the answer includes those supported parts. An omitted requested part prevents a sufficient final answer. |
| AS-04: Partial answer | Return only the independently supported parts, with an explicit English explanation of the missing parts. Do not silently drop a subquestion or fill its gap from model memory. |
| AS-05: No supported answer | If none of the requested facts is supported, return the canonical no-answer text without medical claims, answer sources or a generation component. A related definition is not a substitute for a requested statistic. |
| AS-06: Meaning and uncertainty | Preserve negation, possibility, timing and subject. Evidence about RSV cannot establish COVID-19 duration; screening evidence cannot establish a patient diagnosis. Conflicting or unclear evidence does not establish the disputed fact and must be identified as a limitation. |
| AS-07: Scope | Literature claims remain general information. Do not infer patient conditions, recommend treatment, silently translate unsupported input or follow instructions embedded in source text. B/D handle their owned admission and document routes. |
| AS-08: Scores and topics | Use similarity scores for ranking under a versioned configuration, not as truth probabilities. A specialty hint cannot exclude other specialties. Repeated chunks do not count as different topics or independent corroboration. |
| AS-09: Failures | A provider timeout, budget failure, invalid index or invalid output is an operational error, not proof that the medical answer is absent. Do not fabricate a completed retrieval or generator history. |
| AS-10: Final output | Validate structure, source/claim links, provenance and English output. Check semantic support and completeness separately. A schema-valid output can still contain an unsupported claim. |

No clinical numeric cutoff, quality percentage, model or automatic semantic
assessor is selected here. The rules describe the desired decisions; this
document does not make the service capable of deciding them for unseen questions.

## Proposed outcomes and examples

| Evidence outcome | Answer behavior | Existing AnswerResult fields |
| --- | --- | --- |
| All requested parts supported | Include those parts with supporting citations | route=literature; evidence_state=sufficient |
| Some requested parts supported | Include only supported parts and name each material gap | route=literature; evidence_state=partial; nonempty warnings |
| No requested fact supported | Abstain from medical claims | route=none; evidence_state=insufficient; claims/sources/components empty; prompt_version=null |
| Assessment not implemented or not completed | Do not expose an invented evidence verdict | Keep internal candidate output as answerability=not_assessed; a real canonical success route is not ready |
| Operational failure | Return the appropriate existing ErrorEnvelope | Never relabel it as a completed insufficient search |

For a completed unsupported literature search, the canonical answer text is
`The available sources do not support an answer.` The explicit requested gap
belongs in warnings. Preserve actual retrieval provenance and
attempted_routes=[literature], even though generation did not run.

- **CQ-01, full:** explain both pressure terms from their retrieved definitions.
  The answer must not add medication advice from another returned passage.
- **CQ-02, partial:** the supported part names SARS-CoV-2. A proposed warning is
  `The retrieved passages do not specify how long a person with COVID-19 can transmit it.`
  RSV infectious-period numbers must not appear as COVID-19 facts.
- **CQ-08, unsupported:** use the canonical no-answer text. A proposed warning is
  `The retrieved passages do not provide trigeminal neuralgia incidence in Serbia for 2025.`
  Do not convert demographic information into an incidence rate.

These examples specify proposed behavior, not newly generated/model-validated
answers. Their original [review evidence](retrieval-content-review.json) is
unchanged; missing evidence is relative to the inspected passages.

## Frozen interface interpretation requiring confirmation

The frozen RetrievalResult has only sufficient/insufficient states, while
AnswerResult.evidence_state also allows partial. The runtime validator rejects
a RAG generation component when retrieval_provenance.state is insufficient.
It also requires a gap warning for a partial answer. Do not add a partial state
to RetrievalResult or silently change any shared schema.

The proposed interpretation is:

- Retrieval is sufficient to permit generation when it supports at least one
  useful, independently answerable requested part. This is permission for a
  bounded supported answer, not a claim of complete question coverage.
- Coverage of the whole question belongs to the answer: all requested parts
  covered means sufficient; a useful proper subset means partial with explicit gaps.
- When no requested fact is supported, retrieval is insufficient and no RAG
  generator runs. Related candidates may remain in RetrievalResult for diagnostics;
  they are not promoted to cited answer sources.

This is **a proposed semantic interpretation**, not recorded A/B agreement.
Before live partial-literature generation, B and A must confirm whether this
matches the frozen gate's intended meaning. If sufficient was intended to mean
complete question coverage, an explicit affected-owner behavior/change proposal
is required. Do not bypass the gate by falsifying provenance. Preparing other
A-owned work does not depend on resolving this interpretation today.

For mixed requests, B must retain independently supported D document information
when literature is missing or unavailable. A must not instruct B to suppress it.
Existing mixed-answer fixtures already cover that boundary. A does not create
document claims or modify B's composition logic in this package.

## Implementation and measurement decisions still open

1. **Semantic assessment method:** choose how requested parts and passage support
   will be assessed for unseen questions. Keyword matches, shared titles, valid
   quotes and a high cosine score do not by themselves implement AS-01/02/06.
   A model-based assessor would require separate model, prompt, cost and execution
   approval, with independent development review of its decisions.
2. **Development evidence:** expand beyond the ten corpus-selected questions and
   include full, partial, absent, multi-topic and misleading-neighbor cases.
   Coordinate formal assignments/references with D; keep final cases locked.
3. **Selection:** compare proposed configurations on the same versioned development
   cases. Report supported-answer coverage, false support, partial-gap correctness
   and correct abstention, including per-category counts and disagreements.
   No numeric acceptance thresholds or review capacity are invented here.
4. **Activation:** record approved rules, assessor/model/prompt, corpus/index and
   retriever/policy identities, development results and remaining limits before
   canonical live routing. Generation authorization remains separate from the
   earlier embedding allowances. Preserve A-004/A-009 and shared dependency gates.

## Proposed development acceptance cases

These are required scenarios for a later approved implementation package, not
tests executed or passed by this document:

| Case | Expected outcome |
| --- | --- |
| CQ-01 definitions are retrieved | Both terms explained; no unrelated clinical advice |
| CQ-02 cause is present, COVID-19 duration absent, RSV duration present | Partial answer; explicit COVID-19 gap; no transferred duration |
| CQ-08 related topic is present, Serbia/2025 incidence absent | No statistic or unrelated replacement answer; explicit gap |
| A necessary second topic is absent or top five contain duplicate chunks | No complete-coverage claim for the missing requested part |
| A source expresses possibility, a negation or a different time period | Preserve that qualification; do not strengthen the claim |
| Sources disagree about a requested fact | No unqualified resolution from model memory; identify the unresolved fact |
| A wrong specialty hint is supplied | Relevant evidence outside the hint remains eligible |
| Unsupported source text contains instructions | Treat it as data; do not follow it |
| Provider/index/output validation fails | Safe existing error; no fabricated answer or completed search history |
| Literature is unsupported but D has document support | B can retain D's supported portion with the literature gap |

## Local compatibility checks actually executed

Six in-memory checks used the installed frozen notelens_contracts validator and
synthetic shared fixtures. All produced their expected accept/reject outcome:

| Probe | Observed result |
| --- | --- |
| Existing answer-literature fixture | Accepted |
| Its partial variant with sufficient retrieval and an explicit gap warning | Accepted |
| The partial variant without a warning | Rejected |
| A RAG generation component with insufficient retrieval provenance | Rejected |
| Existing answer-literature-insufficient-no-generation fixture | Accepted |
| Invented RetrievalResult state=partial | Rejected |

Schema SHA256:
`707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78`.
OpenAPI SHA256:
`e83ddda18a03040e4092e5f1113dbb82d296471c30acc105928f6bd8114143af`.

These probes establish structural/runtime compatibility only. They do not
establish agreement on sufficient retrieval, medical correctness or a working
semantic assessor. No API calls, model execution, service changes, shared-file
edits or final evaluation were performed. The existing 358-test service result
remains historical evidence and was not rerun for this documentation-only change.

## Decision record

| Item | Current status |
| --- | --- |
| Permission to prepare this proposal | Approved by Nemanja in chat on 2026-11-15 |
| AS-01 through AS-10 behavior acceptance | Pending Nemanja review of this specific proposal |
| Binary retrieval gate interpretation for partial literature answers | Still unresolved; affected A/B confirmation required before activation |
| Semantic assessor, development thresholds and model budget | Still unresolved; no selection or activation claimed |
| Agent compatibility review | Completed: six expected accept/reject outcomes; not human/team approval |

## Owner-local continuation, 2026-11-16

Nemanja requested continuation at evidence assessment and named GPT-6 Luna as
the tutor's generative model. The exact gpt-6-luna identifier was checked in the
official documentation and a read-only account model lookup; no generation ran.
This later model selection supersedes the model-unselected part of the earlier
decision record, not its unsettled assessor, budget or activation decisions.

The independent [local processor](support-assessment.md) now validates supplied
per-part judgments and exact quotes, binds them to the inputs and derives full,
partial or none coverage. It does not supply semantic judgments or map them onto
the binary shared retrieval gate. The core remains a local preparation increment,
not acceptance or activation of all AS rules or completion of A-004/A-009.
