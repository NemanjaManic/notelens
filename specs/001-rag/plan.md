# Implementation Plan: Python RAG

**Branch**: rag | **Created**: 2026-11-10 | **Updated**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/001-rag/spec.md`.
**Owner**: A. **Status**: Draft local design and executable backlog proposal.
Constitution text remains a draft; confirmed source/user requirements are binding.
The plan alone does not authorize implementation, paid calls, publication or deployment.

**Approved dependency correction (2026-11-11)**: Nemanja (A) approved making local
corpus preparation independent of the shared service foundation. This package
updates documentation only. A-001 is complete, but A-002 implementation requires
its own approval. See the boundaries and dependency graph below.

**Approved extraction increment (2026-11-11)**: The user subsequently approved the
standalone script, tests and actual local extraction. That increment now exists
and extracted 401 source records with checked provenance.

**Approved cleaning increment (2026-11-12)**: The user approved plain-text summary
cleaning, tests and actual local processing, then explicitly approved preserving
table rows/cells and recording omitted image tags. All 401 topics are cleaned;
35 offline tests and the actual source-text/provenance comparisons passed on Python
3.14.2. See [cleaning evidence](../../docs/rag/sources.md#a-002-cleaning-increment).

**Approved passage increment (2026-11-12)**: After the 2500-code-point ceiling and
up-to-300 overlap were proposed and explained as an unmeasured candidate, the user
approved continuing. All 401 topics now produce 617 exact, attributable passages.
All 52 offline tests and actual coverage/offset/table checks passed; A-002 is
complete for offline preparation. See [policy and evidence](../../docs/rag/chunking.md).
This does not establish retrieval quality, a tokenizer budget or service readiness.

**Owner-local scaffold continuation (2026-11-13)**: The user explicitly requested
advancing A's work rather than waiting for another B response. This authorizes the
provisional local mock scaffold under `services/rag`, pinned to the reviewed P2 RC1
revision-2 bytes. It is a preparation exception before shared promotion, not a
contract freeze, generated-binding substitute or completion of A-010/F-004/F-014.
All 39 service tests and 52 corpus tests passed on Python 3.13.5. See
[the runnable service instructions](../../services/rag/README.md). No live provider,
real retrieval, shared file or root configuration is activated by this contribution.

**Owner-local reader continuation (2026-11-13)**: The user approved loading/checking
the real prepared corpus before indexing or provider calls. The service now has a
read-only ingestion adapter and optional server-controlled startup loading. All 75
service tests passed on Python 3.13.5, and actual loading verified 401 topics/617
passages. The adapter does not import preparation code or alter canonical content.
This extends local preparation, not the formal completion of A-003 or its shared
integration dependencies. See [reader commands](../../services/rag/README.md#verify-and-load-the-prepared-corpus).

**Owner-local embedding continuation (2026-11-14)**: The user requested continuation,
selected OpenAI `text-embedding-3-small` with 1,536 dimensions, required ignored `.env`
storage and authorized small local commits. The SDK adapter and offline preflight now
exist; all 114 service tests passed without paid calls. The user separately approved
the initial public-corpus embedding run plus one small probe, with a cumulative USD 0.10
limit for that step, batches of at most 32, 30-second request timeout and no automatic
retries. Local Chroma is approved, without Cloud/account/subscription activation.
Those approvals do not cover LLM generation, push, deployment or completion of shared
integration gates. The adapter/preflight checkpoint has not run a paid request or
built an index. See [embedding decisions and evidence](../../docs/rag/embeddings.md).

**Local index implementation and first live attempt (2026-11-14)**: Chroma 1.5.9,
versioned index/usage state, exact canonical-text checks, stored-vector integrity,
exclusive builds and explicit recovery now exist. All 126 service tests passed on
Python 3.13.5. The approved 7-token probe was rejected by the official OpenAI endpoint
for authentication/permissions. No retry or corpus embedding batch ran; zero passages
were stored and the attempted index remains interrupted. The user has a tutor-supplied
key. A read-only official OpenAI model-list request succeeded, but did not list the
approved embedding model. Embedding access therefore needs the tutor/project owner's
confirmation before further execution. See [run evidence](../../docs/rag/indexing.md).

**Successful owner-local index resume (2026-11-15)**: After the mentor's approval was
relayed and Nemanja requested continuation, model-list access included the selected
model and the explicit existing-ledger resume succeeded. All 617 passages now have
real 1,536-dimensional vectors; 20 successful corpus requests confirmed 207,790 tokens.
The reference-price estimate is USD 0.0041558; the retained USD 0.00415594 reservation
includes the old 7-token failed probe and stays below the unchanged USD 0.10 ceiling.
That probe was not repeated. Full readback, zero-call reuse and five local stored-vector
self-queries passed. No source change or extra generation was made. See the
[build record](../../data/knowledge/manifests/index-build.json). This completes the local
embedding/index increment, not A-003's formal shared prerequisites or A-004 retrieval.

## Summary

**First actual v2 public probe validated (2026-11-18)**: Nemanja explicitly
approved the prepared CQ-01 scope. All 623 offline checks passed again before
one fresh count and one generation attempt. The [actual run](../../docs/rag/selection-trial-results.json)
exited 0 with full model coverage, 11,029 input/204 output tokens and four exact
evidence references over three distinct spans. Agent inspection found alignment
with both requested definitions; this is not independent clinical/team acceptance
or general evaluation. The cumulative retained reservation is USD 0.0048891;
reported new usage gives USD 0.0012049 at reference prices, with actual billing
unverified. Key-free replay returned the validated cache with zero provider
creation and all three ledgers byte-identical. Both old histories remain halted,
activation is false, source/prompt/schema are unchanged and no further generation
is approved. Partial/missing probes, final answers, A-004/A-009 and shared gates
remain incomplete.

**Single v2 trial preparation (2026-11-17)**: Nemanja approved preparation only.
The [CQ-01 v2 runner](../../docs/rag/selection-trial.md) binds the exact new request,
prompt/catalog and both prior ledger anchors, requires fresh approval and admits
at most one count/generation attempt. It carries the latest inclusive USD 0.0027622
reservation once under a proposed USD 0.02 cumulative allowance, with a fresh
20,000-token ceiling check and 2,048-token maximum output. All 38 new checks and
the full 623-test suite passed, including deterministic halt-write failure blocking;
offline wheel/isolated inspection passed. An earlier focused old-test transient
was not reproduced and remains undiagnosed, as recorded in the trial guide.
Both old ledgers and v1 prepared requests are unchanged; new execution approval
is false, no key/provider access was made and the new trial directory is absent.
A-004/A-009, real v2 quality and shared prerequisites remain incomplete.

**V2 evidence selection, local only (2026-11-17)**: Nemanja approved replacing
model-generated quotes/offsets with offered evidence IDs and Python resolution,
without provider calls. The [v2 checkpoint](../../docs/rag/evidence-selection.md)
offers exact nonblank source lines while preserving full passage context, binds
the catalog/prompt/schema, rejects malformed or unknown selections and feeds
resolved quotes through the unchanged support processor. All 46 new checks and
the full 585-test suite passed, plus offline wheel/isolated resolution. All 249
options for the three public saved inputs matched canonical spans. V1 request
bytes and both stopped ledgers remain unchanged; no v2 live gateway, new spend
or shared HTTP behavior is introduced. Input is larger and future token counts
must be measured under a separately approved trial. Semantic quality remains
unverified; A-004/A-009 and their actual shared prerequisites remain incomplete.

**Approved CQ-01 retry halted on exact quote (2026-11-17)**: Nemanja separately
approved the prepared single-attempt scope. All 539 offline checks passed again
before one fresh count and one actual generation attempt. The response failed
with quote_mismatch at /assessment/parts/0/evidence/0/quote; no validated semantic
decision was produced. The diagnostic does not distinguish incorrect quote text
from incorrect otherwise valid offsets. The original ledger is unchanged; the
new halted ledger retains a cumulative USD 0.0027622 reference-price reservation,
not verified billing. Provider-forbidden guards confirmed both trial paths remain
blocked without changing either ledger. The actual .env, runtime source, prompt,
schema and validation predicates are unchanged; the activation flag is false.
See [actual results](../../docs/rag/assessment-retry-results.json). Further calls
and a proposed evidence-identifier selection format need separate approval.
A-004/A-009 and their shared prerequisites remain incomplete.

**Single-question retry preparation (2026-11-17)**: Nemanja approved preparation
and local checks only. The [CQ-01 retry](../../docs/rag/assessment-retry.md) requires
fresh scope approval, limits new attempts to one and carries the pinned original
reservation into the unchanged proposed USD 0.02 cumulative allowance. It reuses
the checked SDK/validation execution path with a separate anchored ledger and
shared original lock. All 33 new tests and the full 539-test RAG suite passed;
offline wheel build/import and provider-forbidden actual-history checks passed.
The original ledger is byte-identical and remains halted, new execution approval
is false, the actual .env is unchanged and no provider request was made.
Prompt/schema/input bytes, acceptance rules and mock HTTP behavior are unchanged.
A-004/A-009 and shared prerequisites remain incomplete.

**Safe assessment diagnostics (2026-11-17)**: Nemanja approved a local-only
continuation. Fixed-vocabulary diagnostics now identify failed validator rules
and field/index paths through the support processor, SDK adapter, CLI and future
failure ledger entries, without retaining untrusted output. All 43 new checks and
the full 506-test RAG suite passed. A finite 3,881-case synthetic comparison with
the preceding validator found identical decisions; offline wheel packaging and
isolated import passed. Provider-forbidden checks confirmed the original halted
ledger is byte-identical and all three case IDs remain blocked. No provider calls,
prompt/schema or acceptance changes, new retry approval or shared HTTP behavior
are introduced. The old failure cause remains unknown. See the
[diagnostics evidence](../../docs/rag/assessment-diagnostics-results.json).
A-004/A-009 and their actual shared prerequisites remain incomplete.

**Approved trial, first attempt halted (2026-11-17)**: Nemanja explicitly approved
the exact three-question GPT-6 Luna scope up to USD 0.02 with the proposed limits,
zero retries and stop-on-failure behavior. All 463 offline checks passed again;
test approval fixtures now remain independent of the owner's live approval record.
The run made one free count and one generation attempt for CQ-01, then exited 1
with invalid_assessment. No validated decision was produced; CQ-02/CQ-08 were
not attempted. The ledger is halted and retains USD 0.0013811 as a reference-price
reservation; actual billed usage is unverified. The original raw response was not
retained, so no specific quote/offset/field cause is claimed. An offline check with
provider creation forbidden confirmed that all further cases are blocked and the
ledger is unchanged. The activation flag was restored, no attempt was repeated,
and runtime source/prompt/HTTP behavior are unchanged. See the
[run record](../../docs/rag/assessment-trial-results.json) and
[limits/next proposed diagnostics](../../docs/rag/assessment-trial.md).
A-004/A-009 and all shared gates remain incomplete; retry/resume is not approved.

**Bounded assessment trial preparation (2026-11-16)**: Nemanja approved preparing
the disabled-by-default public trial and cost estimate, without paid execution.
The [package](../../docs/rag/assessment-trial.md) adds a fingerprinted three-case
proposal, separate activation/approval/budget gates, provider input counting,
durable maximum-output reservations, cache integrity and fail-stop/no-retry state.
All 23 new checks and the full 463-test suite passed. Three explicitly requested
free counting calls measured 9,508 input tokens; the maximum configured output
estimate is USD 0.0040228 at the documented standard rates. The proposed USD 0.02
allowance, 20,000-input/2,048-output limits, reasoning=none and 30-second timeout
remain pending a separate execution decision. The proposal still says
execution_approved=false. No generation, new embeddings, canonical wire activation
or A-004/A-009/shared-gate completion is claimed.

**Approved offline Luna adapter (2026-11-16)**: Nemanja explicitly approved
the model adapter and assessment prompt with local tests only. The
[checkpoint](../../docs/rag/luna-assessor.md) adds versioned strict request
preparation, actual Responses SDK wiring through mandatory MockTransport,
native JSON/usage/completion/refusal validation and the existing support processor.
All 43 new checks and the full 440-test suite passed. The wheel contains the prompt
and loads it by resource path. There is no real-key loading, live switch, provider
call, new spending allowance or automatic semantic-quality claim. Caller-supplied
question parts, actual model calibration, A/B partial wire interpretation and all
shared completion gates remain open; A-004/A-009 remain incomplete.

**Owner-local support processor (2026-11-16)**: Nemanja requested continuation
at evidence assessment. A's pure local processor now validates supplied requested-
part judgments, exact passage quotes and request/candidate/part fingerprints,
deriving internal full/partial/none coverage without providing semantic judgments
or canonical wire-state mapping. All 39 new checks and the full 397-test suite
passed. Replaying ten prior agent review records preserved their 8/1/1 outcomes
without new embedding/generation calls; this is not independent semantic evaluation.
Nemanja selected GPT-6 Luna; the official identifier gpt-6-luna was confirmed by
documentation and one read-only account lookup. No generation, budget, assessor
parameters, partial wire interpretation or shared completion gates were activated.
See [processor behavior and limits](../../docs/rag/support-assessment.md).

**Answer support policy proposal (2026-11-15)**: Nemanja approved preparing the
next behavior proposal without paid calls. The [proposal](../../docs/rag/answer-support-policy.md)
defines per-requested-part support, explicit partial gaps, abstention, preserved
meaning/provenance and operational-error boundaries. Six synthetic shared-validator
probes produced expected outcomes. AS-01 through AS-10 acceptance, semantic-assessor
selection and A/B confirmation of the binary retrieval gate for partial literature
generation remain open. No implementation, schema change, threshold or paid
activation is included; A-004/A-009 and dependency gates remain unchanged.

**Agent passage-content review (2026-11-15)**: The user approved reviewing the
actual retrieved text before further implementation. All fifty passages from
the existing ten public questions were inspected without new API calls. Agent
judgments found eight full, one partial and one missing-evidence case; thirteen
supporting quotes have exact canonical topic/passage offsets. A related disease's
duration cannot fill CQ-02's gap, and CQ-08 lacks its requested location/year rate.
Scores overlap support categories, so no rejection threshold or runtime policy
was chosen. See [review and limitations](../../docs/rag/retrieval-content-review.md).
This exploratory A-004 preparation leaves formal task/dependency gates unchanged.

**Completed public retrieval trial (2026-11-15)**: All ten separately approved public
development queries completed, returning five candidates each. Ten requests confirmed
143 query tokens (USD 0.00000286 reference-price cost) under the separate USD 0.01 cap.
All ten were repeated with provider creation forbidden, reusing cached vectors with
zero API calls and an unchanged ledger. All fifty returned source texts matched the
prepared corpus; the original 617-passage index still verified. The unchanged source
had passed 358 offline tests before this data-only run. See [observed results](../../docs/rag/retrieval-smoke-results.json).
This is not a semantic benchmark, a support/rejection threshold or full A-004 closure.

**Bounded public-query runner (2026-11-15)**: The local CLI now admits only the ten
versioned public English questions from A's prior corpus review. A separate persistent
USD 0.01/ten-attempt allowance and verified question-vector cache prevent repeated
charging; failures do not retry. Preflight counted 143 tokens total, estimated
USD 0.00000286. All 358 service tests passed before the first live trial, including
15 new cache/admission/budget checks. The existing index and HTTP mock are unchanged.
This remains internal candidate ranking with answerability not assessed, not a new
shared API state or full A-004 acceptance. See [runner behavior](../../docs/rag/retrieval.md#public-development-cli-and-separate-query-allowance).

**Owner-local candidate retrieval (2026-11-15)**: The user approved local question-to-
passage ranking with up to five sources and no automatic answerability decision,
plus at most ten public English development queries under a separate USD 0.01 cap,
30-second timeout and zero retries. The candidate-ranking primitive now validates
requests, verifies index/embedding compatibility, preserves source text and returns
versioned cosine-similarity candidates. All 24 new offline checks passed. This is an
A-004 preparation increment, not a shared live HTTP activation or a substitute for
the pending support policy/global dependency gates. See [retrieval behavior](../../docs/rag/retrieval.md).

**Frozen-binding mock adaptation (2026-11-15)**: The user requested continued work
after Goran's handoff and more frequent commit/push checkpoints. B's published
fd1197bd380de9ba9037ea0b73b42031dc1d4bb2 dependency was merged without conflicts.
A's service now uses installed notelens-contracts 1.0.0 TypedDicts/runtime validators,
strict shared JSON parsing, truthful mock retrieval provenance and safe error mapping.
All 319 service tests passed on Python 3.13.5, including 153 shared wire fixtures and
22 simulated exchanges plus actual HTTP/health checks. Old owned candidate assets
were removed; B's imported sources were not manually edited. This is A's local
F-004 contribution and A-010 consumer evidence, not completion of global F-004/F-014,
real question retrieval, generation or deployment. See [handoff](../../docs/rag/frozen-contracts-adaptation.md).

Inspect permitted Health Topics, parse/chunk with stable identifiers, establish embedding-only retrieval, compare lexical/hybrid on fixed development questions, and generate literature answers in Python with claim-linked evidence. Keep ranking, semantic support and abstention measurements separate.

## Technical Context

**Language/Version**: Python 3.13.5 verified for the provisional independent services/rag
project and uv.lock. Python 3.14.2 was used for earlier corpus preparation.
The standalone corpus-preparation script uses only Python's standard library and
does not require the service project, its lockfile or third-party installations.
**Primary Dependencies**: FastAPI/Uvicorn; OpenAI SDK, tiktoken and python-dotenv;
narrow embedding and approved local Chroma adapters; lexical/hybrid candidate; pytest.
The initial embedding model/dimensions are approved. Generative models and further live
budgets remain activation decisions; Google Gen AI was an earlier candidate, not activated.
**Storage**: Versioned permitted English MedlinePlus metadata/manifests; ignored public corpus/index caches. No submitted documents enter this corpus or disk cache.
**Testing**: Contract/schema/semantic tests, deterministic fixtures and owner-local tests;
live and frozen final evaluation run only under separate approved gates.
**Target Platform**: Local Windows/PowerShell verified for workflow tooling; Node/Python
application execution and Bash/macOS/Linux runbooks must be verified during F-004/F-005.
**Project Type**: Monorepo workstream with explicit independent service/UI ownership.
**Performance Goals**: No latency/throughput SLO invented. Measure actual performance on
development data; bounded live policies require approval before activation.
**Constraints**: English only, key-free mocks, no submitted-document persistence,
approved 2 MiB PDFs/100,000 code points/60-minute maximum, delivery 2026-11-24.
**Scale/Scope**: Four members, five specialties, small inspectable literature corpus;
40-document annotation and approximately 80-QA targets, not measured datasets.

## Constitution Check

Gate evaluated before research and re-evaluated after this design:
| Principle | Pre-research / post-design assessment |
| --- | --- |
| English and educational MVP | PASS in design; source exclusions and notices preserved. |
| Ownership and independent work | PASS in design; one owner per path, member annotation exceptions, no business overlap. |
| Contract-first Python/TypeScript boundaries | PASS in design; schema/OAS are proposals, freeze required before real consumers. |
| Canonical text and evidence | PASS in design; one preparation step, code-point spans, semantic validation distinct. |
| Honest uncertainty | PASS in design; no clinical probabilities, partial mixed support, no hard specialty filtering. |
| Reproducibility and final-test protection | PASS in design; audit-driven manifests and development-only selection. |
| Measured acceptance | PASS in design; structural/span target 100%, substantive thresholds remain explicit team gates. |
| Security/privacy | PASS in design; memory-only policy and approved caps, isolation and redacted logs. |
| Key-free/cost controls | PASS for local design; paid activation and cloud freeze remain BLOCKED pending approval. |
| Real workflow/review | PASS for artifact preparation; no ratification, business implementation or deployment claimed. |

No unjustified constitutional exception is proposed. Pending external activation/contract
review gates are explicit; the cloud/provider portion is not frozen. Local planning can
proceed without selecting a paid service or fabricating runtime defaults.

## Project Structure

### Documentation (this feature)

```text
specs/001-rag/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/README.md
  quickstart.md
  tasks.md
  checklists/requirements.md
```

### Source Code (repository root)

Owned workstream paths. Offline extraction code now exists under data/knowledge;
service implementation remains a future deliverable:

```text
services/rag/**
data/knowledge/**
docs/rag/**
specs/001-rag/**
eval/annotations/member-a/**
```

**Structure Decision**: Keep the confirmed monorepo and one owner per path.
The shared [allowed-path matrix](../../docs/team/allowed-paths.md) controls exceptions.
Initial coordinator scaffolding across service paths is allowed only before the checkpoint.
Root configs/global Spec Kit files and canonical bindings remain B-owned.

### Offline corpus preparation and service integration

Keep A-002 as an owner-local data pipeline under `data/knowledge/**`:

- Implemented extraction/cleaning increments: `data/knowledge/scripts/prepare_corpus.py` and standard-library
  tests in `data/knowledge/tests/test_prepare_corpus.py`.
- Input: the acquired local MedlinePlus ZIP and approved 401-ID selection recorded
  in `data/knowledge/manifests/snapshot.json`.
- First separately approved increment, now executed: extract the selected English topic records,
  including summaries and attributable metadata, without cleaning/chunking or calls
  to the web, another service or a provider.
- Second separately approved increment, now executed: preserve original records and add
  plain-text summaries, with headings/paragraphs/lists and table rows/cells preserved.
  Decode HTML character references once; normalize whitespace; retain visible link text
  without URLs/attributes or fetching. Omit image tags/comments and record counts/affected
  topic IDs. Unknown, unbalanced or unsupported table markup fails before output.
- Third approved increment, now executed: pack exact canonical slices with a
  2500-code-point ceiling and optional whole-unit overlap up to 300. Keep tables
  and individual list items whole; split oversized paragraphs between words.
  Group a trailing NIH attribution with the previous unit when both fit, so
  attribution need not become a standalone passage. See [the full policy](../../docs/rag/chunking.md).
- Extraction output now exists: Git-ignored artifacts under `data/knowledge/.cache/corpus/**` and
  a small version/count/checksum manifest at `data/knowledge/manifests/prepared-corpus.json`.
  These are A-owned internal artifacts, not a competing shared API schema.
- Separate cleaned output: `data/knowledge/.cache/corpus/cleaned-topics.jsonl`, with
  `data/knowledge/manifests/cleaned-corpus.json` linking input identities and output checksum.
  Existing extraction inputs/manifests remain unchanged; original HTML is retained per record.
- Separate passage output: `data/knowledge/.cache/corpus/passages.jsonl`, with
  `data/knowledge/manifests/passages.json` recording stable IDs, configuration,
  corpus version, measured counts and checksums. Earlier artifacts remain unchanged.
- Available preparation checks: `python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"`.
  All 52 checks passed on Python 3.14.2; these do not establish clinical validity,
  retrieval quality, token budgets or service/Python 3.13 compatibility.

A-002 depends only on completed A-001 and the applicable user approval. Its
extraction CLI is `python -B data/knowledge/scripts/prepare_corpus.py extract`.
Its cleaning CLI is `python -B data/knowledge/scripts/prepare_corpus.py clean`.
Its passage CLI is `python -B data/knowledge/scripts/prepare_corpus.py chunk`.
The script refuses to overwrite existing outputs and makes no network calls. It does not
create HTTP routes, install the service scaffold, modify shared contracts or touch
root configuration. A-002 is complete after all three increments and actual checks;
the passage settings remain a candidate for later development measurements.

A-003 subsequently consumes the prepared artifacts through the service adapter
`services/rag/src/notelens_rag/ingestion.py`; parsing/cleaning is not independently
reimplemented there. A-003 requires A-002, A-010 and F-014. A-010 still requires
F-003/F-004, preserving contract, generated-binding and scaffold checks before
service integration. The shared runnable-foundation checkpoint remains pending.

## Research and Design Phases

### Phase 0: Research

[research.md](research.md) records choices, rationale and alternatives from the primary
[feasibility review](../../docs/decisions/technical-feasibility.md). No research agents were
spawned. Unknown data counts/configuration outcomes are assigned measured/approval tasks,
not substituted with claimed results or silent defaults.

### Phase 1: Data and interfaces

Use [data-model.md](data-model.md), [contract references](contracts/README.md) and the
single draft [canonical proposal](../../contracts/v1/README.md).
Canonicalization, enum and field proposals need owner review before freeze.
Generate bindings rather than diverging copies. Schema validation alone cannot verify
English, source support, span slices, SHA256 or citation foreign keys.

### Phase 2: Implementation handoff (future approval)

Generate an owner-specific [backlog](tasks.md) using the installed tasks workflow.
Follow its dependencies and distinct mock/module/live definitions of done.
Mock fixtures do not complete business tasks. Use [quickstart.md](quickstart.md) for
current safe checks versus planned commands after their named prerequisite creates files.

## Delivery Priorities and Dependencies

MUST: independent mocked interfaces, correct evidence/provenance, required baseline/evaluation,
English states, privacy/isolation and reproducible checks. SHOULD: measured improvements
within the deadline. COULD: reranking, extra datasets, embedding classifier variants,
ONNX/ICD extensions; these do not block the core.

Critical path: contract review/freeze -> shared mock scaffold -> independent baseline modules
and C's split manifests -> D's reviewed references/QA -> real integration -> human review ->
configuration freeze and locked final checks on 2026-11-22/23 -> delivery 2026-11-24.
A may inspect corpus sources, C audit data, D draft guidelines/evaluator and B prepare mocks
without waiting for complete real modules. First development measurement/threshold review
remains targeted for 2026-11-14. No available hours or velocity are assumed.

The offline branch of this dependency graph is now `A-001 -> A-002`; it can run
independently of B's shared service preparation after separate implementation
approval. Both branches meet at `A-003 <- A-002, A-010, F-014`, followed by A-004
retrieval and later generation/evaluation. All other task dependencies are preserved.

## Complexity Tracking

No constitutional violation requiring an exception. Three small Python services preserve
the confirmed ownership; they are not an invitation to add a distributed platform.
Any new paid service, scope/privacy change or cross-owner edit needs the applicable review.
