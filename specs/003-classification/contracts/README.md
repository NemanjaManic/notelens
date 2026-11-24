# Python Classification: Interface References

**Owner of this reference**: C. **Canonical owner**: B.
**Status**: Canonical v1.0.0 frozen and generated bindings published through F-003/F-009 on 2026-11-13. C's local mock scaffold is checked; real business inference remains pending.

Use the [frozen shared contract](../../../contracts/v1/README.md),
[JSON Schema](../../../contracts/v1/schema.json) and
[OpenAPI](../../../contracts/v1/openapi.json).

Required records: `PreparedDocument`, `ClassificationRequest`, `ClassificationResult`, `ErrorEnvelope`.

C consumes prepared canonical text and returns a versioned specialty/uncertain/unsupported result.

The installed `notelens-contracts==1.0.0` package exports TypedDicts and explicit runtime
validators from `notelens_contracts.v1`; these are not Pydantic BaseModels. See the
[binding guide](../../../contracts/generated/README.md). The service validates incoming
JSON and native outgoing records before serialization, including non-finite scores.

Module consumers propose contract changes through B. Record agreement before shared schema,
fixture/version/binding changes; adapt through owned paths. Mock and real HTTP payloads
must pass the same contract and semantic checks. Do not mistake schema validity for
groundedness, English language or source-relative correctness.
