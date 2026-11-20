# Python RAG: Interface References

**Owner of this reference**: A. **Canonical owner**: B.
**Status**: frozen shared wire contract v1.0.0; A's mock consumer adapted on 2026-11-15.

Use the [shared canonical contract](../../../contracts/v1/README.md),
[JSON Schema](../../../contracts/v1/schema.json) and
[OpenAPI](../../../contracts/v1/openapi.json).

B's published fd1197bd380de9ba9037ea0b73b42031dc1d4bb2 package was merged as a
dependency into rag. Python services consume notelens-contracts 1.0.0 from
contracts/generated/python and import notelens_contracts.v1. TypedDict annotations
require explicit runtime validation through validate_json/validate_record; they
are not Pydantic BaseModels. The obsolete RAG-owned P2 revision-2 copies are removed.
See [A's compatibility evidence](../../../docs/rag/frozen-contracts-adaptation.md).

Required records: `RetrievalRequest`, `RetrievalResult`, `LiteratureAnswerRequest`, `AnswerResult`, `ErrorEnvelope`.

A produces retrieval and literature answers in Python. B supplies question/concept hints and never implements RAG.

Module consumers propose contract changes through B. Record agreement before shared schema,
fixture/version/binding changes; adapt through owned paths. Mock and real HTTP payloads
must pass the same contract and semantic checks. Do not mistake schema validity for
groundedness, English language or source-relative correctness.
