# Embedding-Only Candidate Retrieval

Owner: Nemanja (A). Updated: 2026-11-15.

The user approved a first local ranking increment: up to five relevant passages
with sources, without an automatic answerability verdict or LLM generation. A
separate public-development query run is approved for up to ten short English
questions, USD 0.01 total, 30-second timeout and no automatic retry. This is not
an increase of the earlier corpus-indexing allowance or a general live-service policy.

## Ranking primitive

CandidateRetriever in services/rag/src/notelens_rag/retrieval.py consumes the
verified, versioned Chroma index and an embedder in the same execution mode/model
and dimensional space. It validates the frozen RetrievalRequest, verifies the
index before any embedding call and embeds the unchanged self-contained question.

It queries Chroma by vector without a specialty filter and returns up to five
passages. Each source is reconstructed from the unchanged prepared corpus and
validated with the shared RetrievalPassage validator. Concept/specialty fields
are admitted but deliberately unused in this question-only baseline; A-006 adds
their measured soft use later. An incorrect hint cannot exclude another specialty.

Score = 1 - cosine distance. Higher is better only within the identified
retriever/index version. Scores are not clinical confidence or proof of semantic
support. Equal scores use passage-ID order within the returned candidate pool;
ties at the approximate-search boundary are not claimed to be globally stable.
Top-k, query/score/tie policies, embedding-space and index versions identify the
retriever. Repeated passages from one topic remain distinct; later topic-level
metrics must deduplicate topic IDs rather than inflate recall.

## Internal output and unchanged HTTP contract

The output is an A-owned internal candidate-ranking record with explicit
answerability=not_assessed. It is not a frozen RetrievalResult, not a new shared
state/schema, and not an assertion of sufficient or insufficient semantic support.
The per-passage shape is shared. A future canonical success result requires the
development-selected support/rejection policy; it is not inferred from high scores.

The existing frozen-contract HTTP mock remains available without keys/corpus/index.
No real question route, language detector, generation, clinical validation, deployment,
global F-004/F-014 completion or full A-004 completion is claimed by this increment.
The library primitive's caller must admit reviewed English input. Public live trials
will use the versioned development-question registry, not arbitrary submitted text
or D's held-out final questions. Evaluation QA never enters the retrieval index.

## Deterministic checks

```powershell
uv run --locked --offline --directory services/rag python -m pytest tests/test_retrieval.py
```

All 24 new offline tests passed on Python 3.13.5. They cover unchanged Unicode text,
source identity/versions, score direction, stable returned-pool ties, unused hints,
invalid requests/index/model/dimensions, malformed ranking data and safe failures.
They use synthetic records/embeddings and do not measure semantic retrieval quality.

The scoped speckit-implement prerequisite resolver selected specs/001-rag with
SPECIFY_FEATURE_NO_PERSIST=1; the checklist was 16/16 and no extension hooks existed.
This user-approved local preparation preserves the formal shared dependency gates.

## Public development CLI and separate query allowance

The local runner admits only question IDs from
[retrieval-smoke-questions.json](retrieval-smoke-questions.json), derived verbatim
from A's earlier [corpus review](corpus-quality-review.md). Those ten English public
questions include supported, partial and data-gap probes. Their prior coding-agent
assessments are not D's frozen final benchmark or human-approved gold labels.
Question/reference records are never inserted into Chroma.

The default CLI uses only cached query vectors. New embeddings need --execute,
an explicit initial budget no greater than USD 0.01 and paid execution enabled for
the process. The local .env supplies the key; command arguments never contain it.
The current default HTTP mock is unchanged. This runner is not arbitrary user-input
admission or a general language detector, and does not accept a patient document.

Run the separately approved trial from the repository root:

```powershell
$env:NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS = 'true'
try {
    uv run --locked --offline --directory services/rag python -m notelens_rag.query_smoke --all --summary --execute --budget-usd 0.01
    if ($LASTEXITCODE -ne 0) { throw 'The public query trial stopped; inspect before any retry.' }
} finally {
    Remove-Item Env:NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS
}
```

After success, repeat without paid execution or a key. Omit --summary to inspect
the exact public passage text along with its source:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.query_smoke --question-id CQ-01
uv run --locked --offline --directory services/rag python -m notelens_rag.query_smoke --all --summary
```

The ignored services/rag/.cache/retrieval-smoke directory holds one persistent usage
ledger and public question-vector files. Registry identity, embedding space and
mock/live origin bind the allowance/cache. A changed registry/space cannot silently
reset it. Each registered question is attempted at most once, with a total ceiling
of ten attempts, a 30-second request timeout and SDK retries disabled. Failed or
uncertain attempts and token reservations remain; no automatic retry or cache reset
is supported. A completed vector file is fingerprinted in the ledger. Missing or
tampered cache/state fails closed rather than issuing another paid request.

Cached embeddings are reranked against the currently verified index, not used as
a stale result cache. Only the explicitly public questions/vectors may persist;
this policy does not authorize caching submitted private questions/documents.
The ledger cannot limit unrelated account usage. No LLM generation occurs.

Before live execution, all 358 service tests passed on Python 3.13.5, including
15 new public-runner checks. Exact local preflight counted 143 total question tokens
(largest 27), estimated USD 0.00000286 at USD 0.02 per million input tokens. That
estimate is not an invoice. No API call was made by these offline checks.

## Executed public trial and cache verification, 2026-11-15

The approved trial completed all ten registered questions against the existing
617-passage live index, using implementation checkpoint 55471c8. Each returned
five candidate passages. Ten embedding requests confirmed 143 input tokens, with
zero retries or generation requests. The reference-price cost is USD 0.00000286,
below the separate USD 0.01 allowance; the provider invoice was not inspected.
The corpus/index was not rebuilt and its original embedding allowance was unchanged.

All ten queries were then repeated with a provider factory that raises if created.
All used the verified vector cache with zero provider calls, an unchanged usage
ledger, and all fifty returned passage texts matching the prepared canonical corpus.
The complete index still passed readback. No source-code change was made after the
358-test offline suite; the live run/cache checks are separate new evidence.

See [compact observed results](retrieval-smoke-results.json). The report includes
public question text, source identities/URLs/titles and scores, without copying
passage bodies, vectors or credentials. The full source text remains inspectable
through the local CLI. Cached vectors and the run ledger remain Git-ignored.

Surface inspection found expected subject-related titles, such as High Blood
Pressure for CQ-01 and Carpal Tunnel Syndrome for CQ-03. Multiple top-ranked CQ-03
passages belong to the same topic; no unique-topic recall metric is inferred.
The prior partial/data-gap probes CQ-02/CQ-08 also return related candidates. A
topic match or high score therefore remains separate from evidence that answers
the question. No semantic benchmark, calibrated rejection policy, clinical validity
or automatic answerability result is claimed here.

## Agent content review, 2026-11-15

All fifty actual passage bodies have subsequently been read against their ten
questions. The agent found evidence covering eight complete questions, one
partial question and one missing requested statistic. Thirteen exact supporting
quotes have checked topic/passage offsets. CQ-02 must not borrow RSV transmission
timing; CQ-08's related topic does not supply Serbia-specific 2025 incidence.
The observed scores overlap these support categories, so no automatic sufficiency
cutoff was selected. See the [review and limits](retrieval-content-review.md) and
[structured evidence](retrieval-content-review.json). This offline review made
no API calls, changed no runtime policy and does not complete A-004 or human
evaluation. The original trial's not_assessed output remains historical evidence.

## Proposed next behavior

The [answer support policy proposal](answer-support-policy.md) defines full,
partial and unsupported outcomes for review. Six local synthetic compatibility
probes produced their expected validator outcomes. Rule acceptance, automatic
semantic assessment and the binary retrieval gate's meaning for partial literature
generation remain explicit decisions. This documentation activates no policy,
model or live route and does not change the existing ranking output.

## Local assessment processor, 2026-11-16

The [support processor](support-assessment.md) now validates externally supplied
per-part judgments and exact evidence against a fingerprint of the request,
candidates and declared requested parts. It derives internal full/partial/none
coverage without treating scores or quote existence as semantic proof. All 39
new checks and the 397-test full service suite passed. A replay of prior agent
records is labeled as replay, not automatic semantic evaluation. GPT-6 Luna was
selected and found visible in a read-only model lookup; no generation occurred.
The original candidate output, HTTP mock and shared retrieval gate are unchanged.
