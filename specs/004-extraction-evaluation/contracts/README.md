# Python Extraction and Shared Evaluation: Interface References

**Owner of this reference**: D. **Canonical owner**: B.
**Status**: D-owned interface reference to the frozen shared wire contract v1.0.0. This file does not define or change the shared API.

Use the [frozen shared contract](../../../contracts/v1/README.md),
[JSON Schema](../../../contracts/v1/schema.json) and
[OpenAPI](../../../contracts/v1/openapi.json).

Required records: `PreparedDocument`, `ExtractionRequest`, `ExtractionResult`, `DocumentQuestionRequest`, `AnswerResult`, `ErrorEnvelope`.

D consumes prepared text and produces extraction, summaries and document answers; D also calls the agreed APIs from evaluation adapters.

Module consumers propose contract changes through B. Record agreement before shared schema,
fixture/version/binding changes; adapt through owned paths. D's mock HTTP payloads
must pass the same contract and semantic checks. Do not mistake schema validity for
groundedness, English language or source-relative correctness.
