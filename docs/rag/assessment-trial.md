# Bounded Public Luna Assessment Trial: First Attempt Halted

Owner: Nemanja (A). Prepared: 2026-11-16. Updated: 2026-11-17.
Status: approved bounded trial attempted; halted after the first invalid assessment.

Nemanja approved preparing this package and its cost estimate, then separately
approved up to three generation attempts under USD 0.02 on 2026-11-17. The
[proposal](assessment-trial-proposal.json) records that approval for the exact
reviewed scope. CQ-01 returned an assessment rejected by local validation with
invalid_assessment. The batch halted; CQ-02/CQ-08 were not attempted. See the
[observed run record](assessment-trial-results.json). No retry/resume is approved.
Existing HTTP routes remain mock-only; this is an owner-local development CLI.

## Trial scope approved on 2026-11-17

| Item | Approved value for this trial |
| --- | --- |
| Model | gpt-6-luna |
| Public questions | CQ-01, CQ-02, CQ-08, at most one generation attempt each |
| Purpose | First full/partial/missing-support development probes; not final evaluation |
| Input admission limit | 20,000 provider-counted tokens per generation request |
| Maximum output | 2,048 tokens per request, including any reasoning usage |
| Reasoning effort | none |
| Request timeout | 30 seconds |
| Automatic retries | Zero, including SDK retries |
| Generation allowance | USD 0.02 total, separate from embedding allowances |
| Processing | service_tier=default, no tools, no history, store=false, truncation=disabled |

These settings apply only to this bounded trial, not general service defaults
or measured quality optima. The selected cases have one or two declared
requested parts. An incomplete response fails rather than increasing the output
limit or repeating a call automatically.

The selected saved candidate results, registry, prior agent review and prompt
are fingerprinted. Passage text is reconstructed from the verified prepared
corpus; no new search, query embedding, index build or source cleaning occurs.
Only the prior review's requested-part descriptions are model input. Expected
support labels and reference quotes are not supplied to the assessor.

The public input restriction does not authorize arbitrary submitted questions,
patient documents or their persistence. Declared requested parts remain supplied
by the caller; automatic general question decomposition is not complete.

## Actual free token-count preflight

The installed tokenizer does not register gpt-6-luna, so no approximate local
token count is presented as exact. OpenAI documents the
[Responses input-token counting endpoint as free](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens).
Three explicit counting calls were made against the official API, using the
unchanged question, instructions, schema and passage input. They generated no
model responses and used the server-side key without printing or modifying it.

The [observed preflight record](assessment-trial-preflight.json) reports:

| Question | Counted input tokens | Maximum output tokens | Estimated generation cost at maximum output |
| --- | ---: | ---: | ---: |
| CQ-01 | 3,571 | 2,048 | USD 0.0013811 |
| CQ-02 | 3,603 | 2,048 | USD 0.0013843 |
| CQ-08 | 2,334 | 2,048 | USD 0.0012574 |
| Total | 9,508 | 6,144 | USD 0.0040228 |

The estimate uses the published standard uncached text rates checked on
2026-11-16: USD 0.10/million input tokens and USD 0.50/million output tokens.
See the [official model pricing](https://developers.openai.com/api/docs/models/gpt-6-luna).
It assumes the maximum configured output, takes no cache discount and is not an
invoice or a prediction of how many output tokens a model will need.
At all three input admission ceilings and maximum outputs, the same reference
calculation is USD 0.009072. The USD 0.02 allowance was subsequently approved on
2026-11-17 for this scope; it does not authorize retry after a failed attempt.

The original counting preflight created no generation ledger or result cache.
Its record retains its historical unapproved proposal fingerprint. The scope
fingerprint is unchanged by recording the later owner approval. The existing
embedding ledgers, corpus and index were not changed.

## Implemented execution controls

[assessment_trial.py](../../services/rag/src/notelens_rag/assessment_trial.py)
requires all of the following before any potentially billable generation:

- Explicit execution of one of the three registered cases.
- A versioned approval record for the exact scope fingerprint and
  execution_approved=true in the proposal.
- The separate NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS flag set to true; its default
  is false. The embedding flag cannot activate assessment generation.
- An explicit budget argument exactly matching the proposal's allowance.
- An available server-side key and valid durable allowance state.

For each first attempt, the runner records the counting stage, obtains a fresh
input count using the same input/schema, checks the input ceiling and reserves
input cost plus the maximum output cost. The reservation is atomically persisted
before calling Responses.create. The client uses the official API origin,
verified OS TLS trust, disabled redirects and zero automatic retries.

The separate ignored services/rag/.cache/assessment-trial directory contains the
allowance ledger and only validated results for these fixed public cases. Scope,
mode, prompt and context fingerprints prevent silent reuse after a change.
Confirmed results have anchored file hashes and can be read again without a new
provider call or allowance update. Missing/corrupt caches, orphan results, changed
scope, malformed allowance state and a stale lock fail closed.

Failed or interrupted attempts keep their reservations and halt the batch.
No failed question or later question is retried automatically. Completed
validated results record reported usage; zero confirmed usage after a failure
does not establish that the provider charged nothing. Reservations are not
refunded during this trial. A mismatched input count, unexpected pricing tier,
refusal, malformed output or invalid quote also stops the trial for inspection.

This is a local runner allowance at the recorded reference rates, not an
account-wide provider spending control or authentication of human consent.
Manual deletion/editing of local state is not an approved way to obtain a retry.
Price/setting changes require renewed review rather than an allowance reset.

## Safe commands available now

From the repository root, local inspection with zero provider calls:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.assessment_trial
```

Explicitly repeat free input counting only, without paid generation:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.assessment_trial --count-inputs
```

The counting command writes only its public metadata report under the ignored
trial folder. It does not approve execution. Paid execution additionally uses
--execute and an exact --budget-usd argument. The owner approval record now exists,
but the assessment flag is disabled again and the saved failure halts all further
attempts. Do not delete/reset that state or enable a retry without a new user
decision. The approved scope is:
`d2b584c6078ff29c76a5be7c0f212de0c4dd26f6c796d1f76ead1fffc432ca5a`.

## Verification and remaining gates

All 23 runner/settings/budget checks and the full 463-test RAG suite passed again
on 2026-11-17, Windows/Python 3.13.5, before the approved execution. The test fixture
now explicitly controls its own approval state, independently of the real owner's
versioned approval. Tests use the SDK with in-memory responses; they
cover the approval/activation/budget gates, exact pre-counting, on-disk reservation
before generation, cache reuse, three-case scope, failure retention/batch halt,
stale locks, state corruption and separation from embedding activation.
The SDK adapter's existing 43 checks also passed after factoring shared request
preparation and explicit mock/live result labeling.

The preparation used three free counting calls on 2026-11-16. The approved run
on 2026-11-17 made one fresh free counting call and one generation attempt for
CQ-01. No validated assessment or full/partial/none outcome was produced. No new
embeddings, live HTTP route, clinical quality result or semantic calibration is
claimed. A/B wire interpretation for partial literature answers, A-004/A-009
completion and shared foundation gates remain open.

The scoped speckit-implement resolver selected specs/001-rag with nonpersistent
context. requirements.md had sixteen checked and zero unchecked entries; no
extension hooks were present. Task checkboxes are unchanged. No other owner's
source, shared contracts, root configuration or actual .env was edited.

## Observed first attempt, 2026-11-17

The exact approved run used --execute --budget-usd 0.02 with the separate
assessment flag enabled only for its process. It exited 1 with invalid_assessment
after CQ-01. The saved ledger has one failed attempt, halted=true and a retained
USD 0.0013811 reference-price reservation for 3,571 counted input tokens plus the
2,048-output maximum. The other two questions were not attempted. There is no
validated result cache and no active lock.

The actual invoice was not inspected. The ledger's confirmed_usd=0 means that no
fully validated result was recorded; it does not establish that generation was
free. The raw response and output-token usage were not retained after validation
failed. The fixed error identifies neither a particular field nor a quote/offset
rule, so no specific cause is inferred and no model-quality metric is reported.

A separate offline guard check used a provider factory that must never be created.
All three case IDs were blocked by the saved halted state, the factory was never
called and the ledger hash stayed unchanged. The real activation flag is false
again; the approval record and reservation remain intact. Runtime source and the
prompt were not changed for this run. No attempt was repeated or continued.

## Safe validation diagnostics, 2026-11-17

Nemanja approved this separate local diagnostics package after the halted run.
It is implemented in code checkpoint `08f5045f8f12f9373daccf93566acb167f9ab92d`.
Validation errors now carry a versioned stage, rule and field/index path. For
example, this synthetic failure describes an inexact quote:

```json
{
  "format_version": "rag-validation-diagnostic-v1",
  "stage": "assessment",
  "rule": "quote_mismatch",
  "path": "/assessment/parts/0/evidence/0/quote"
}
```

Indices are zero-based: this example locates the first evidence item in the first
requested part. Other rules distinguish malformed shapes, missing/duplicate parts,
unknown source references, invalid offset types/bounds, empty reasons, duplicate
evidence, stale context bindings, incomplete/refused upstream output and invalid
usage/JSON. A rule identifies the failed validator condition; some conditions check
a group of fields. It does not establish semantic or clinical correctness.

Only closed vocabularies of stages, rules and field names, plus bounded numeric
indices, are serialized. Unknown diagnostic metadata becomes validation_failed at
the root. Untrusted JSON keys, requirement/source IDs, question text, reasons,
quotes, provider details, raw responses and credentials are excluded. The CLI adds
this diagnostic to its existing safe error output. Newly failed trial attempts
also retain the safe metadata in their ignored ledger; old ledgers without it
remain readable. This is internal CLI metadata, not a change to shared HTTP
contracts or canonical ErrorEnvelope behavior.

All 43 added tests and the full 506-test RAG suite passed locally on
Windows/Python 3.13.5. A separate finite comparison against pre-diagnostics commit
612a50714208a57b5f53bc8f79d0a7f380a34d4e checked 3,881 synthetic inputs, including
non-BMP/repeated-text slices: 1,591 were accepted identically, 2,290 rejected
identically, and none differed. This is finite regression evidence, not a proof
over all inputs. An offline wheel build and isolated import verified packaged
diagnostics and the unchanged prompt. See [verification record](assessment-diagnostics-results.json).

The provider-forbidden guard check still blocked CQ-01/CQ-02/CQ-08 without
creating a client. The original ledger retained its exact hash, one failed attempt
and reservation; it was not backfilled with a guessed diagnostic. No provider
requests, including free input counting, were made for this package. The actual
assessment activation flag remains false. Prompt, structured-output schema,
acceptance predicates, approved scope, budgets, no-retry policy and mock HTTP
behavior remain unchanged. The original CQ-01 failure cause is still unknown.

Any later paid retry/resume needs a separate explicit decision and preserved
accounting. Diagnostics alone neither repair the old failure nor complete
A-004/A-009, semantic evaluation or the shared foundation gates.

The separate [single CQ-01 retry](assessment-retry.md) has now been prepared and
checked locally, with execution still unapproved. It preserves this original
halted ledger and carries its reservation into the cumulative allowance.
