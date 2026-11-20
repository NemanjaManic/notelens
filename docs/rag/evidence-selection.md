# Evidence Selection V2: Local SDK and Canonical Quote Resolution

Owner: Nemanja (A). Date: 2026-11-17. Code checkpoint: 77b48f5.
Status: local implementation verified; one separately approved public v2 probe
validated on 2026-11-18. See [actual results](selection-trial-results.json).

Retrieval still finds candidate passages in the existing vector index. The new
selection step happens afterward: the model chooses which offered evidence
supports each requested part, and Python supplies its exact canonical quote and
Unicode offsets. Evidence IDs identify offered quotes; they are not specialty
labels, retrieval scores or a replacement for searching the corpus.

The preceding real CQ-01 attempt failed quote_mismatch. Its diagnostic did not
distinguish incorrect quote text from incorrect otherwise valid offsets. V2 moves
both quote reproduction and coordinate generation out of the model. This does not
retrospectively diagnose either historical failure or establish semantic quality.

## Local flow

| Stage | Responsibility |
| --- | --- |
| Retrieval | Existing query embedding/ranking produces candidate passages; unchanged here. |
| Evidence preparation | Python offers exact nonblank lines with deterministic evidence IDs. |
| Semantic assessment | The model selects evidence_ids and supplies per-requirement support judgments/reasons. |
| Resolution | Python resolves known IDs to its stored passage IDs, quotes and offsets. |
| Validation | The original support processor checks complete judgments and exact canonical evidence. |

An ID such as e1 refers to one option in this prepared context. IDs follow passage
and line order; a selection_sha256 binds their exact catalog, source occurrences,
original context and policy. Reusing a selection after an input/order change fails.

## Canonical evidence policy

The canonical-nonblank-lines-v1 policy selects complete nonblank runs separated by
CR or LF. Leading/trailing whitespace, non-BMP characters, punctuation and other
Unicode separators inside a run remain unchanged. CR/LF delimiters and blank lines
remain in the complete passage context but are not separate selectable options.
No canonical passage is rewritten, normalized or truncated. Repeated text at
different positions has different IDs and exact source spans; Python does not
choose the first text match or infer a model's intended occurrence.

Complete passages and option quotes are both sent as untrusted model input.
Numeric coordinates stay in Python's frozen catalog. The strict internal v2 schema
permits evidence_ids only, with an enum of known IDs. Model-supplied quote/start/end
fields, unknown or duplicate IDs and malformed selections are rejected. The
prepared prompt, schema, payload, catalog and fingerprints are reconstructed and
checked before resolving evidence. Safe diagnostics contain static fields and
numeric positions, never untrusted IDs or raw model text.

Resolved evidence still passes evaluate_support. It retains exact half-open
Unicode code-point spans, all declared parts, valid statuses/reasons, supported
evidence cardinality, empty evidence for not_supported and at least two distinct
spans for conflicting. The prompt retains entity/disease/location/time/units,
negation, uncertainty, subject and no-treatment constraints. Matching a source
span does not prove semantic support: those judgments remain unverified model
claims until an actual assessment and appropriate evaluation.

Each option is a whole line and may contain multiple sentences. A narrower
substring is not selectable, and a single option cannot satisfy the requirement
for two distinct conflict spans. Finer evidence granularity remains future work.

## Versioning and execution boundary

The prompt is literature-support-selection-v2, the model-output assessment format
is rag-support-selection-v2, and returned local metadata includes the selection
fingerprint and evidence policy version. The prompt SHA-256 is
`cb33ce546bab676502d43107939f78ab5d8745efb86dec783e4505ff4d4a7db9`.
This is an A-owned internal model protocol; shared v1.0.0 HTTP contracts and
canonical error envelopes are unchanged.

V1 remains available to interpret its historical attempts. Its prompt, three
prepared request payloads and stopped histories are preserved. Common SDK
envelope/usage validation and mock transport handling were factored for reuse;
the v2 SDK class still requires MockTransport and uses fixture credentials.
The adapter itself remains MockTransport-only. A separate
[one-question v2 runner](selection-trial.md) was subsequently approved and executed
once on 2026-11-18, producing a validated result. No additional generation is
approved. Neither stopped v1 runner is migrated or reopened, and both old ledger
hashes remain unchanged.

## Verification and public preparation

All 46 added tests and the full 585-test RAG suite passed on Windows/Python 3.13.5
(23.39 seconds for the full run):

```powershell
& services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

Checks cover non-BMP/CRLF/repeated text, exact occurrence selection, immutable
inputs, catalog/prompt/schema tampering, cross-version rejection, unknown/duplicate
IDs, complete support/gap/conflict rules, upstream failures and zero retries,
credential isolation, safe errors and a metadata-only preview. The offline wheel
build and an isolated prepare/resolve round trip passed with both exact packaged
prompts; credentials and caches were excluded.

The [public preparation record](evidence-selection-preflight.json) verifies all
249 offered options across three saved public cases against their canonical
passages, including coverage of every nonwhitespace source code point:

| Public question | Evidence options | V2 input JSON UTF-8 bytes |
| --- | ---: | ---: |
| CQ-01 | 89 | 33,172 |
| CQ-02 | 126 | 36,272 |
| CQ-08 | 34 | 14,130 |

These sizes exclude instructions/schema and are not provider token counts or
costs. Input is larger because full passages and options are both included. No
remote token counting was performed during that preparation. The later approved
CQ-01 probe counted 11,029 full input tokens and reported 204 output tokens.
The later approved [coverage probes](coverage-trial.md) counted 13,165 input
tokens for CQ-02 and 5,277 for CQ-08 and produced validated partial/none decisions.
These fresh counts and their retained cumulative accounting belong to that
specific scope; v1 counts and permissions were not reused as v2 approval.

For a key-free metadata preview from this checkout with its prepared public data:

```powershell
uv run --locked --offline --directory services/rag python -m notelens_rag.evidence_selection --question-id CQ-01
```

The preview cannot execute the model and prints neither the question nor passage
bodies. It supports only the existing three public case IDs. It does not require
the ignored index, assessment ledgers or a key, but the prepared corpus artifacts
must exist. Six offline probes confirmed that both stopped trial paths remain
blocked, with zero provider creation and both ledgers byte-identical.

The scoped speckit-implement workflow selected specs/001-rag using the official
PowerShell resolver, with nonpersistent context.

| Checklist | Total | Checked | Unchecked | Status |
| --- | ---: | ---: | ---: | --- |
| requirements.md | 16 | 16 | 0 | PASS |

No extension hooks were present. Task IDs,
checkboxes and actual shared dependencies are unchanged. A-004/A-009, semantic
quality evaluation, canonical partial-answer interpretation and live integration
remain incomplete. The three real v2 development responses do not establish
general semantic quality or produce a final literature answer. No clinical metric is
claimed. The actual .env and shared/root/other-owner source were not changed.
