# Bounded Public Luna Assessment Trial: Prepared, Not Activated

Owner: Nemanja (A). Prepared: 2026-11-16.
Status: implementation/preflight complete; paid generation approval pending.

Nemanja approved preparing this package and its cost estimate. The versioned
[proposal](assessment-trial-proposal.json) still has execution_approved=false and
approval=null. There has been no paid assessment/generation attempt. Existing
HTTP routes remain mock-only; this is an owner-local public-development CLI.

## Proposed scope for a separate approval

| Item | Proposed value |
| --- | --- |
| Model | gpt-6-luna |
| Public questions | CQ-01, CQ-02, CQ-08, at most one generation attempt each |
| Purpose | First full/partial/missing-support development probes; not final evaluation |
| Input admission limit | 20,000 provider-counted tokens per generation request |
| Maximum output | 2,048 tokens per request, including any reasoning usage |
| Reasoning effort | none |
| Request timeout | 30 seconds |
| Automatic retries | Zero, including SDK retries |
| Generation allowance | USD 0.02 total, separately proposed from embedding allowances |
| Processing | service_tier=default, no tools, no history, store=false, truncation=disabled |

These are reviewable proposed trial settings, not accepted general service
defaults or measured quality optima. The selected cases have one or two declared
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
calculation is USD 0.009072. The proposed USD 0.02 allowance is still unapproved.

No generation ledger or result cache was created by counting. The existing
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
--execute and an exact --budget-usd argument, but remains blocked by the current
unapproved proposal and disabled assessment flag. Do not enable it before the
separate user decision for this scope:
`d2b584c6078ff29c76a5be7c0f212de0c4dd26f6c796d1f76ead1fffc432ca5a`.

## Verification and remaining gates

All 23 new runner/settings/budget checks and the full 463-test RAG suite passed
on Windows/Python 3.13.5. Tests use the actual SDK with in-memory responses; they
cover the approval/activation/budget gates, exact pre-counting, on-disk reservation
before generation, cache reuse, three-case scope, failure retention/batch halt,
stale locks, state corruption and separation from embedding activation.
The SDK adapter's existing 43 checks also passed after factoring shared request
preparation and explicit mock/live result labeling.

Only the three free counting requests contacted OpenAI. No paid generation,
new embeddings, live HTTP route, clinical quality result or semantic calibration
is claimed. The full/partial/none judgments still need an explicitly authorized
actual model trial and independent review. A/B wire interpretation for partial
literature answers, A-004/A-009 completion and shared foundation gates remain open.

The scoped speckit-implement resolver selected specs/001-rag with nonpersistent
context. requirements.md had sixteen checked and zero unchecked entries; no
extension hooks were present. Task checkboxes are unchanged. No other owner's
source, shared contracts, root configuration or actual .env was edited.
