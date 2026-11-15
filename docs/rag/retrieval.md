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
