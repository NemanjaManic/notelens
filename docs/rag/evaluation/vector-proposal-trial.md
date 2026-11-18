# Bounded vector trial for the public QA proposals

Owner: Nemanja (A). Preflight: 2026-11-18. Execution is pending approval.

The [proposed scope](vector-proposal-scope.json) admits only the exact wording of
five public development proposals. Four other proposals already match cached
questions. Both the vector and hybrid retrievers reuse the same query vectors
against the existing verified Chroma index. The [lexical run](lexical-proposal-evaluation.md)
provides the third reference. The comparison measures ranked passages and
proposed topics. It does not generate answers or access a final question set.

| New question | Input tokens |
| --- | ---: |
| A-QA-05 | 13 |
| A-QA-06 | 12 |
| A-QA-07 | 21 |
| A-QA-08 | 20 |
| A-QA-09 | 17 |
| Total | 83 |

The five exact questions cost an estimated USD 0.00000166 at the published
standard input price of USD 0.02 per million tokens. The proposed new allowance
is USD 0.00001 for these five queries, with `text-embedding-3-small`, 1,536
dimensions, one attempt per question, a 30-second timeout and zero retries.
The run stops if one embedding fails or leaves an incomplete attempt. Prior
reservations are retained in the existing ledger, pinned by its SHA-256 digest.
Previously approved query scope is separate and already consumed. The new
allowance and cache are separate from all earlier trials. Reference pricing
does not establish actual billing. [OpenAI model price](https://developers.openai.com/api/docs/models/text-embedding-3-small).

Scope SHA-256:
`7e62e6321fc26f2a603371878d5cec8e0086b7100b74e521dfd7cec75c373647`.

## Offline checks

From the repository root, with the verified tokenizer, corpus and existing index
and cache:

```powershell
& services/rag/.venv/Scripts/python.exe -m notelens_rag.qa_vector_trial
& services/rag/.venv/Scripts/python.exe -m notelens_rag.qa_vector_trial --compare
```

The first command prints the approved-state flag, question IDs and counts,
estimated cost and scope digest. The second only ranks questions with confirmed
cached vectors, marks other rows unevaluated and compares unique-topic and exact
passage-reference coverage. In the preflight both variants ranked the four
existing questions. Each found the top-ranked target topic and the cited passages
in all three cases with supported parts. The missing-evidence probe has no
topic-recall denominator. Five questions remain unevaluated in this comparison.

The pending live path rejected execution. The two key-free commands made zero
provider calls, left the previous ledger unchanged and created no trial cache.
Six new tests verify pending or altered approval, scope and allowance separation,
replay and failure retention. The full service run passed 756 tests. Integration
and the frozen evaluation still require team confirmation and reviewed references.
