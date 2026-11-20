# Public partial-answer trial

Owner: Nemanja (A). Prepared and executed on 2026-11-19. Execution scope closed.

The [proposal](partial-answer-trial-proposal.json) binds one completion for the existing public development question CQ-02, “What causes COVID-19, and how long can an infected person transmit it to others?” The retained actual support assessment covers the cause and records a gap for the duration of infectiousness. The trial reuses that verified decision and the `literature-answer-v1` prompt. The generator receives the exact question and only the previously selected supported evidence. Python constructs the explicit gap warning from the missing requested part.

The [runner](../../../services/rag/src/notelens_rag/partial_answer_trial.py) uses the existing single-attempt token-count, reservation, completion and validated-cache path. Its separate ledger carries the completed CQ-01 answer ledger's inclusive reservation once. The proposal binds that ledger, its result and scope, plus the partial request, prompt, parameters and local partial-policy selection. Nemanja approved this exact scope on 2026-11-19. The completed proposal retains that approval and has `execution_approved=false`.

The approved limits were one token-count request and one completion, with a 30-second timeout, zero automatic retries, 4,096 input tokens, 512 output tokens, reasoning `none`, tools disabled and `store=false`. The token count must fit before the reservation is written and completion is sent. An invalid response, count, citation or unsupported-part claim halts the attempt. Replaying a confirmed cache needs no key or new allowance.

At the published rates of USD 0.10 per million input tokens and USD 0.50 per million output tokens, the maximum new standard-price reservation was USD 0.0006656. The previous inclusive reservation was USD 0.0091109, making the approved combined maximum USD 0.0097765 within the USD 0.02 cumulative reference ceiling. Actual billing has not been inspected. [Model rates checked on 2026-11-19](https://developers.openai.com/api/docs/models/gpt-6-luna)

Run the local preflight from the repository root with the retained public corpus and trial history present.

```powershell
uv run --locked --offline --directory services/rag python -B -m notelens_rag.partial_answer_trial
```

The review checks that the generated claim covers the supported cause, every citation resolves to its exact canonical span, and the warning identifies the unsupported duration. Semantic claim review remains necessary even after structural validation. The owner-local partial-policy selection still awaits B's confirmation before application integration. This trial covers public development evidence and final answer composition.

Twelve new offline checks and the full 772-test service suite passed. The checks cover pending approval, a successful partial completion through the SDK mock transport, exact citations, the carried reservation, cache replay, rejection of an unsupported-part claim, changed scope/history, and stopping after one failed attempt. An initial test-fixture revision omitted one historical question ID and used an incorrect expected reservation. Both fixture issues were corrected before the passing runs.

The actual retained-history preflight ran with credentials, provider creation and network access forbidden. It preserved all ten history JSON files, rejected execution with `execution_not_approved`, created no new trial directory and left no locks. The prepared scope SHA-256 is `d61f31bb1b29d20bec70302dbe78969a7acdeb4dfaadcb46c4a462010597f201`. The source, tests and proposal are local changes awaiting review.

## Actual result

The approved run counted 555 input tokens and produced 56 output tokens in one completion, with zero retries and zero new searches or embeddings. The English answer contains one claim, "COVID-19 is caused by SARS-CoV-2, a coronavirus." The coding agent checked it against the exact selected MedlinePlus span. The source explicitly names both the virus and its coronavirus type. The answer carries a warning identifying the missing duration of infectiousness. One citation matches the canonical passage at Unicode offsets `[0, 373)`.

The [result record](partial-answer-trial-results.json) contains the claim, warning, reference hash, request and source versions, and accounting. The new standard-price usage is USD 0.0000835, with USD 0.0003115 reserved. Across the retained assessment and answer histories, confirmed reference usage is USD 0.0034482 and reservations are USD 0.0094224 within the USD 0.02 ceiling. The actual invoice remains unverified.

The activation flag was temporary and restored after execution. Cache replay with key loading, provider creation and network access forbidden returned the same validated result. All twelve history JSON files stayed byte-identical during replay, and no lock remained. A fresh-directory attempt under the closed scope was rejected before creating state. The result has agent content review. Independent acceptance and B's partial-wire confirmation remain pending.
