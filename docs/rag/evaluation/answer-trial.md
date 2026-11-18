# First public cited-answer trial

Owner: Nemanja (A). Prepared and executed: 2026-11-18. Scope closed.

The [prepared scope](answer-trial-proposal.json) covered one completion
for CQ-01, the public question about the difference between systolic and diastolic
blood pressure. It uses the previous verified full-support decision and the
versioned `literature-answer-v1` prompt. Input contains the exact question and
only previously selected public evidence. The count and completion requests use
the same question, instructions and strict output schema. Expected review checks
cover both definitions, the distinction between heartbeats and the interval
between them, the exact source links, and absence of extraneous claims or advice.

## Local review results

The review reconstructed all three earlier public support decisions from their
verified caches and compared their context and evidence. It used authored mock
completions for full and partial and local abstention for absent evidence.

| Case | Result | Claims | Quote references | Missing part |
| --- | --- | ---: | ---: | --- |
| CQ-01 | sufficient | 2 | 2 | None |
| CQ-02 | partial | 1 | 1 | Duration of infectiousness for COVID-19 |
| CQ-08 | insufficient | 0 | 0 | The requested Serbia 2025 incidence rate |

The CQ-02 mock tests the proposed partial-wire interpretation. Actual use of that
interpretation still requires A/B agreement. The CQ-08 response uses the existing
canonical abstention and runs no model. The mock checks establish response shape,
claim-to-source linkage and explicit gaps. They do not measure the model's prose
quality or provide independent semantic review. Real generation is limited to
the full-support CQ-01 case in this proposal.

## Limits and preflight

- GPT-6 Luna, one completion attempt, no automatic retries, 30-second timeout,
  maximum 4,096 input tokens and 512 output tokens, reasoning `none`.
- Fresh provider input count before reservation. The program records the
  reservation before sending the completion. A changed request, input-limit
  breach or invalid answer stops the trial. `store=false` and tools disabled.
- The existing cumulative USD 0.02 assessment allowance is the proposed ceiling.
  USD 0.0087813 remains reserved from earlier trials. This new completion can
  add up to USD 0.0006656 at standard reference prices, for a combined reservation
  of at most USD 0.0094469. These calculations use USD 0.10 input and USD 0.50
  output per million tokens. Actual invoicing can differ. [OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-6-luna).
- The previous histories stay available for replay. The answer uses its own
  locked ledger and cache, and inherits the earlier cumulative reservation once.

Review scope SHA-256:
`d24a62b9767c0acc60c3da6a79c795b27017b7a466d9da3b2a43d1f23ba63748`.

Run from this checkout with its retained public assessment history:

```powershell
& services/rag/.venv/Scripts/python.exe -m notelens_rag.answer_trial
& services/rag/.venv/Scripts/python.exe -m notelens_rag.answer_trial --review
```

Both modes use local data and no provider. The pending execution path rejected
the live attempt before creating an answer ledger. All 760 RAG tests passed,
including four new checks using the actual SDK with MockTransport. These cover
the unchanged count/completion request fields, reservation, cache replay and
halting after an invalid count or citation. The shared UI and HTTP runtime are
outside this trial.

## Actual answer and review

The approved run made one provider input count and one GPT-6 Luna completion.
The count matched the reported input usage of 736 tokens. The output used 98
tokens, for 834 total. There were zero retries and no new embedding or search.
The result passed the frozen `AnswerResult` validator and returned two English
claims with four exact references over three distinct spans in two sources.

The coding agent reviewed each claim against the exact selected text. The two
sentences distinguish pressure in the arteries during a heartbeat from pressure
between beats. Both facts are explicitly supported. The response contains no
unrelated advice or patient-specific facts. The [result record](answer-trial-results.json)
contains the generated claims and matched reference coordinates without source
bodies or the raw provider envelope. The review covers this one known development
question and awaits independent acceptance.

The new standard-price usage is USD 0.0001226. The reserved amount is USD
0.0003296, including the configured maximum output. Across all retained assessment
and answer trials, confirmed reference usage is USD 0.0033647 and cumulative
reservations are USD 0.0091109 within the USD 0.02 ceiling. Reservations were
retained and the actual invoice was not inspected.

The temporary paid activation flag was restored and the scope closed for new
calls. Cache replay with key loading, client creation and network forbidden
returned the exact validated answer. Five ledgers and four caches stayed
byte-identical; no lock remained. The closed scope also rejected an attempt
without an existing ledger. No live partial answer, final QA or application
integration was run.
