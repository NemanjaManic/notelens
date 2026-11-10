# Python RAG: Interface References

**Owner of this reference**: A. **Canonical owner**: B.
**Status**: draft; no contract freeze or business API is implied.

Use the [shared contract proposal](../../../contracts/v1/README.md),
[JSON Schema](../../../contracts/v1/schema.json) and
[OpenAPI](../../../contracts/v1/openapi.json).

Required records: `RetrievalRequest`, `RetrievalResult`, `LiteratureAnswerRequest`, `AnswerResult`, `ErrorEnvelope`.

A produces retrieval and literature answers in Python. B supplies question/concept hints and never implements RAG.

Module consumers propose contract changes through B. Record agreement before shared schema,
fixture/version/binding changes; adapt through owned paths. Mock and real HTTP payloads
must pass the same contract and semantic checks. Do not mistake schema validity for
groundedness, English language or source-relative correctness.
