# Local Support Assessment Processor

Owner: Nemanja (A). Updated: 2026-11-16.
Scope: owner-local A-004 preparation; no live HTTP or generation activation.

## Implemented behavior

The user requested continuation at evidence assessment. The new
[support.py](../../services/rag/src/notelens_rag/support.py) implements the local
validation and decision step independently of a model/provider. It consumes:

- A frozen-contract RetrievalRequest and the existing internal candidate record.
- An explicit list of requested parts, each with requirement_id and description.
- A completed supplied assessment for every part, with a status, nonempty reason
  and exact evidence where applicable.

support_context_sha256 binds a review to the exact request, candidates, scores,
versions, declared requested parts and processor version. A changed input cannot
silently reuse the assessment. The snapshot is taken in memory, without modifying
or saving the inputs.

evaluate_support checks that all declared parts are reviewed exactly once:

| Supplied part status | Evidence requirement | Coverage contribution |
| --- | --- | --- |
| supported | At least one exact quote from a returned passage | Counts as a supported requested part |
| not_supported | No purported supporting quote | Remains an explicit missing part |
| conflicting | At least two distinct exact evidence spans | Remains missing, with an explicit conflict flag |

Quotes use half-open Unicode code-point offsets in the unchanged retrieved
passage text. Unknown passages, duplicate spans, boolean/out-of-range offsets,
changed quotes and stale review bindings fail closed. The processor does not
search for a matching occurrence and silently move an offset. A repeated quote
remains bound to the caller's explicit position.

The immutable internal SupportDecision reports coverage=full when all declared
parts have supported judgments, partial when some do, and none when none do.
It retains supported/missing/conflicting part IDs, reasons and checked quotes.
An incomplete or malformed assessment raises a fixed SupportError; it is not
converted into a no-evidence verdict. Bodies and reasons are omitted from result
representations; the processor does not log, persist content or contact a provider.

## Boundaries that remain explicit

This processor validates supplied semantic judgments. It does not determine their
meaning from natural-language text. It cannot prove that the declared requested
parts cover the whole question or that a matched quote supports the fact.
Both semantic_support_independently_verified and wire_mapping_applied remain false.
The tests include a mechanically valid quote with unverified meaning to preserve
this distinction.

Its local formats, statuses and error codes are not new shared API records.
There is no conversion into RetrievalResult.sufficient/insufficient, no answer
generation, no source promotion into AnswerResult and no HTTP/readiness change.
The [binary retrieval gate interpretation](answer-support-policy.md#frozen-interface-interpretation-requiring-confirmation)
for partial literature answers remains unresolved. No clinical threshold or
shared dependency is declared complete by this increment.

## Calling the local processor

Given an admitted request, candidates and independently reviewed requested parts:

```python
from notelens_rag.support import evaluate_support, support_context_sha256

context_sha256 = support_context_sha256(request, candidates, requirements)
# The caller supplies every part judgment and its exact passage evidence.
assessment = {
    "format_version": "rag-support-assessment-v1",
    "context_sha256": context_sha256,
    "parts": supplied_part_reviews,
}
decision = evaluate_support(request, candidates, requirements, assessment)
```

Each supplied part record has requirement_id, status, reason and evidence.
Each evidence record has passage_id, start, end and quote. This is a Python-level
interface, not a new command for arbitrary user questions or private documents.
There is no provider configuration to enable in this package.

## Model selection and read-only access check

On 2026-11-16, Nemanja named OpenAI GPT-6 Luna as the generative model supplied by
the tutor. Its official API identifier is gpt-6-luna; the
[official model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
documents structured outputs. A single read-only models.retrieve request against
the official API confirmed that gpt-6-luna is visible to the configured local key.
The key was loaded from the existing ignored .env and was not printed or changed.

That lookup made zero generation calls and does not demonstrate successful
generation or sufficient account quota. No new paid allowance, assessor prompt,
reasoning setting, output-token limit, timeout/retry policy or general deployment
policy is inferred from the model selection. The earlier embedding allowances
do not authorize generative calls.

The next provider package needs an approved bounded configuration, a structured
assessment adapter and development measurement against independent reviews.
Provider refusals, incomplete responses and invalid judgments must remain
operational failures rather than fabricated missing-evidence decisions.

## Executed checks

Windows / Python 3.13.5, from the repository root:

```powershell
services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests/test_support.py --tb=short
services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

All 39 new processor checks passed, and the full service suite passed 397 tests.
They cover coverage decisions, conflicts, complete part accounting, changed
question/hints/source/score/version bindings, exact Unicode/repeated-text spans,
invalid evidence, immutable output, unchanged inputs and fixed safe diagnostics.
They use supplied synthetic judgments, not a live semantic model.

A separate local replay loaded the ten existing agent content-review records,
their declared requested parts and their exact canonical evidence. The processor
reproduced eight full, one partial and one none outcome. This was reuse of the
prior agent labels, not an independent assessment, model evaluation or accuracy
measurement. Saved source reports and the public-query usage ledger were unchanged;
the replay made zero embedding or generation calls.

The scoped speckit-implement workflow used the official prerequisite resolver for
specs/001-rag with nonpersistent feature selection. requirements.md had sixteen
checked and zero unchecked entries. No extension hooks existed. The scope was
only this independent local preparation, preserving A-004/A-009 and F-004/F-014
completion gates. No other owner's implementation or shared schema was edited.

## Subsequent approved adapter checkpoint, 2026-11-16

The user approved preparing the GPT-6 Luna connection and assessment prompt
with local tests only. The [offline SDK adapter](luna-assessor.md) now supplies
versioned structured request preparation and strict response handling through
mandatory MockTransport. All 43 new checks and the full 440-test suite passed;
the packaged prompt loaded directly from an offline-built wheel. No real key,
provider call, live switch, semantic quality result or canonical state mapping
was introduced. The caller still supplies the declared requested parts.
