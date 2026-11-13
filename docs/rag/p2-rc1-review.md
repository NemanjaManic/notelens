# RAG Review of P2 RC1 Revision 2

**Reviewer:** A's coding agent for Nemanja (A).
**Review date:** 2026-11-13.
**Review type:** Technical agent assessment. Nemanja's formal owner confirmation is pending.
**Candidate:** `p2-rc1`, revision `2`, proposed wire version `1.0.0`.
**Commit reviewed:** `01e96ab6c6a676efb43073a2eca711e89e419030`.
**Candidate-manifest SHA-256:** `2c5043aa375a5aef1b0fa3806e8204284218d7b671c48bd8474ac74330c8affa`.

These reviewer/date/proposal identifiers apply to every issue below. The status
`accepted` records the agent's technical assessment of the specified behavior;
it does not assert human/team approval, canonical promotion or contract freeze.
This review does not approve D/C-owned extraction/classification details on their behalf.

## Reviewed artifacts and current A state

- [Candidate README](https://github.com/NemanjaManic/notelens/blob/01e96ab6c6a676efb43073a2eca711e89e419030/contracts/candidates/p2-rc1/README.md).
- [Candidate manifest](https://github.com/NemanjaManic/notelens/blob/01e96ab6c6a676efb43073a2eca711e89e419030/contracts/candidates/p2-rc1/candidate.json).
- [Candidate schema](https://github.com/NemanjaManic/notelens/blob/01e96ab6c6a676efb43073a2eca711e89e419030/contracts/candidates/p2-rc1/schema.json).
- [Candidate OpenAPI](https://github.com/NemanjaManic/notelens/blob/01e96ab6c6a676efb43073a2eca711e89e419030/contracts/candidates/p2-rc1/openapi.json).
- The complete historical P2 proposal, selected checker rules and fixture catalogs
  at the same commit. The concrete revision-2 artifacts take precedence over the
  older proposal's publication/status descriptions for this review.

A's published preparation commit is `b57f21555b0157f41820a9db56c848cf55b7ce60` on
`rag`. A-001/A-002 provide 401 topics and 617 attributed passages; 52 offline tests
passed during that preparation. Those historical results are not candidate-contract
tests and were not rerun for this documentation review. See [passage evidence](chunking.md).

The passage corpus version is
`2922f29e08b74bf668272c33a7f3f0599d8d16fc90d2242976e3d4476010579b`.
An index version, retriever version and generation metadata do not exist yet and
must not be fabricated from that corpus version.

## Issue responses

| Issue | Agent status | Specific behavior reviewed and response |
| --- | --- | --- |
| P2-01 | accepted | Preserve once-only canonical document preparation, exact UTF-8 hashes and half-open code-point evidence. A's literature requests remain stateless and do not receive patient documents. Optional concepts and specialty hints remain soft signals; they are not corpus-ingestion input or a hard specialty filter. |
| P2-08 | accepted | Higher returned retrieval scores mean better rank within the identified retriever/version. `score_note` explains the metric/transformation and comparison limits. `RetrievalResult` now requires `corpus_version` alongside index/retriever versions. No numerical sufficiency threshold or clinical confidence interpretation is accepted here. Weak literature support must not suppress D-supported content. |
| P2-09 | accepted | The explicit `ambiguous_reference` clarification outcome uses route `none`, insufficient evidence and no claims/sources. A receives self-contained questions; B asks the user to name the topic rather than automatically rewriting or extending A's history. This accepts the control outcome, not an unimplemented general ambiguity detector. |
| P2-10 | accepted | Business POSTs require one canonical lowercase UUID in `X-Request-ID`; services echo a valid ID on success/error and match `ErrorEnvelope.request_id`. Missing/malformed/duplicate IDs produce 400 with a fresh diagnostic UUID. B binds each call to its originating context and rejects stale/mismatched responses, including empty-source answers. IDs do not authorize access. Revision-2 health 401 diagnostic-ID rules are a separate convention from business POST validation. |
| P2-11 | change requested | Generation provenance is adequate for an executed literature-answer generator, but there is no representation for completed retrieval when generation is skipped. Preserve actual corpus/index/retriever provenance for that case without inventing provider/model/prompt metadata. See the precise scenario and proposal below. |
| P2-12 | accepted | Preserve supported claim text; prefix local component/source/claim IDs consistently with `a:`/`d:` and rewrite references together. Separate attempted routes, supported evidence routes and component mock/live origins. `notelens-compose-v1` plus null root prompt version identifies deterministic composition while executed generation versions stay in components. Keep D-supported portions and explicit literature gaps. The retrieval-only provenance issue in P2-11 remains applicable to mixed outcomes. |
| P2-13 | accepted | Completed searches use 200 with sufficient/insufficient state; operational failures use non-2xx envelopes. Remove the successful `RetrievalResult.state: error` branch after approval/promotion. Accept the stated 400/422 distinction, 500/internal_error, 502 invalid-upstream handling and 503 configuration/provider/budget cases. A must not report a configured index/version or readiness when unavailable. Actual HTTP enforcement, retry/deadline policy and live controls remain later work. |
| P2-14 | still unresolved | The request schema's non-whitespace question rule and explicit English protocol outcomes are suitable. The live common language-validation method, ambiguity-detection responsibility and question/history bounds are still unapproved implementation decisions. Fixture language records do not establish a live detector. Resolve these at their dependent activation gates; do not silently translate or reuse document limits as question limits. This is not a request to invent numerical caps during contract review. |
| P2-15 | accepted | A creates the RAG scaffold, health/readiness behavior, local tests and its dependencies/lockfile. B owns shared contracts/bindings, root configuration, startup and integration. The scaffold contribution belongs before A-010's consumer tests; it must not depend on A-010. B should record the coordinated foundation task split and provide the frozen-binding/import/startup handoff before scaffold implementation. Python compatibility must be verified explicitly. |
| P2-17 | accepted | Provider/model/account/budget/retention, numerical operational controls and deployment remain separate approval gates. Known-English synthetic/public fixtures can support the key-free foundation; they do not activate live language handling or providers. Browser requests go through B; exposed services authenticate, with the stated key-free exception limited to loopback mocks. |

The shared rendering rule was also reviewed for A's answers: substantive answer
text equals claim texts joined by two LF characters, with limitations in separate
warnings/clarification. Empty-answer notices and null unused prompt metadata are
acceptable protocol choices. Exact text/claim matching does not prove semantic support.

## Required P2-11 change: retrieval ran, generation did not

Concrete scenario:

1. A receives a self-contained literature question and performs a real retrieval
   against a configured corpus/index/retriever.
2. The completed search has insufficient evidence, so A does not call a generator.
3. A returns the fixed insufficient-answer notice, no claims/sources, null
   `prompt_version`, empty generation `components` and attempted route `literature`.

The schema currently has no corpus/index/retriever fields at the `AnswerResult`
root. Its `ComponentProvenance` represents executed generation and requires
provider/model/prompt/configuration strings; RAG components only allow operation
`literature-answer`. Adding a retrieval-only component would therefore misdescribe
execution or require a schema change. `attempted_routes` alone cannot identify
which corpus/index/retriever actually produced the evidence gap.

This is a design gap identified by artifact inspection, not a reproduced runtime
failure or a claim that B's tests failed.

Proposed resolution for B/A/D agreement:

- Represent completed retrieval provenance separately from executed generation.
  A possible field is a nullable `retrieval_provenance` record carrying actual
  mode, corpus/index/retriever versions and sufficient/insufficient outcome.
  B maintains the final field names and shared representation.
- Retain this record when retrieval completed but generation was skipped, and
  when B combines a supported D answer with insufficient literature evidence.
- Leave generation components empty/null as appropriate when no generator ran;
  do not invent a provider, model, prompt or generation invocation.
- Distinguish that case from clarification before retrieval and from an absent
  index/configuration. Those cases must not fabricate retrieval versions.

Please add positive/negative fixtures for completed retrieval without generation,
clarification before retrieval, false generator metadata, missing retrieval
versions and the mixed document-supported/literature-insufficient case. Revise
the candidate revision/manifest after changing any reviewed bytes.

## Verification performed here

- Read the supplied B reply and the published proposal/README/manifest at the
  exact commit above. The reply's local/uncommitted description is historical;
  a published review branch now exists.
- Downloaded candidate assets into inspection-process memory through read-only
  GitHub API calls. SHA-256 matched the candidate manifest for all seven generated
  assets: schema, OpenAPI, four fixture files and transport cases.
- Parsed and inspected RAG request/result, answer, claim/source, component,
  clarification and error definitions, plus both RAG OpenAPI operations and
  correlation declarations. Read relevant checker rules and fixture structure.
- Checked this authored document's review identifiers, issue coverage, local
  links, whitespace and changed-file scope.

B reports 139 expected payload outcomes, 22 simulated correlation outcomes and 51
unittests for revision 2. Those numbers remain attributed B results. This review
did not execute B's checker/test suite, run a JSON Schema validator, start HTTP
services, install dependencies or test generated bindings/model behavior.

## Next handoff

B should resolve the P2-11 request and record the deferred P2-14 activation decisions,
then provide any revised candidate's exact commit/revision/manifest for review.
Nemanja and the other affected owners retain their own confirmation responsibilities.
Technical acceptance in this file is not their formal approval.

After the actual agreement and canonical promotion/freeze, F-009 supplies generated
bindings and B coordinates the owner-created F-004/F-011 scaffolds. A can then
implement its RAG scaffold under a separately approved package and run A-010's
consumer checks. A-003 still requires A-010 and the F-014 foundation checkpoint.

This package changes only this A-owned review document. It does not edit shared
contracts, copy the candidate into the active RAG service, close A-010, authorize
canonical promotion or publish any files. No messages were sent to collaborators.
