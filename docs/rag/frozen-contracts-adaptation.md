# RAG Frozen-Contract Mock Adaptation

Owner: Nemanja (A). Technical reviewer: A's coding agent. Date: 2026-11-15.
This records executed compatibility checks, not new human approval or global F-004 completion.

## Source and scope

Goran/B's [published handoff](https://github.com/NemanjaManic/notelens/blob/fd1197bd380de9ba9037ea0b73b42031dc1d4bb2/docs/team/frozen-contracts-handoff.md)
was imported through merge commit 027d7cb, preserving B's authored history. A's
adaptation changes only services/rag, docs/rag and specs/001-rag. No imported shared
schema, binding, fixture, generator, tooling source or root configuration was edited.

- Published dependency: fd1197bd380de9ba9037ea0b73b42031dc1d4bb2.
- Shared wire/package version: 1.0.0.
- Generated manifest SHA-256: a46f3cd3de95a6fcad80867560d5c1606e69822c0dfa962810e9cea5e0e9c169.
- Canonical schema SHA-256: 707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78.
- Canonical OpenAPI SHA-256: e83ddda18a03040e4092e5f1113dbb82d296471c30acc105928f6bd8114143af.

## Actual behavior

The service declares notelens-contracts as a relative editable dependency at
../../contracts/generated/python. It imports the frozen TypedDicts and applies
validate_json/validate_record at runtime. A thin service adapter pins the installed
schema and converts failures to fixed English messages without payloads/issue paths.
It does not maintain a second JSON Schema or handwritten Pydantic business model.
Old RAG-owned revision-2 assets were deleted; their history remains in Git.

Duplicate keys, malformed JSON and non-finite/overflow wire numbers use 400. Schema
and field failures use 422. Invalid response provenance, component/citation links,
versions or execution modes produce safe 500/internal_error envelopes. Request IDs
and health 401 challenge/diagnostic-ID rules retain their separate frozen behavior.

Mock AnswerResult always includes retrieval_provenance. A completed insufficient
mock search retains its synthetic corpus/index/retriever versions with no generator
component or prompt. Sufficient generation has matching search/component versions.
Pre-search clarification uses null search provenance and empty generation components.
All versions and notices remain explicitly synthetic; no real retrieval is claimed.

Default mock startup and both endpoints work with provider, corpus and Chroma access
forbidden and no API key. Live HTTP remains unavailable and cannot fall back to mock.
The separately built 617-passage public index was not rebuilt or used by these mocks.

## Executed checks

Windows, Python 3.13.5, uv 0.12.5, installed notelens-contracts 1.0.0:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
uv --system-certs --directory services/rag add --editable ../../contracts/generated/python
services/rag/.venv/Scripts/python.exe -m pytest services/rag/tests --tb=short
```

All 319 tests passed, including:

- The 153 shared wire-payload outcomes with exact expected rule/path diagnostics.
- All 22 shared simulated header/error exchanges; these are not HTTP calls.
- Actual FastAPI health 401 checks with absent/valid/malformed/duplicate incoming IDs.
- A real owned loopback Uvicorn process with health and both RAG endpoints.
- Strict JSON admission, native non-finite values, independent search history,
  malformed-output safety, cold key/corpus/index-free mock behavior and concurrency.
- Existing corpus-reader, embedding-adapter and actual local-Chroma unit checks.

Before adaptation, the new suite showed seven endpoint regressions while its 185
other cases passed. After adapting the service, those regressions and the full suite
passed. The frozen package was exercised on A's actual interpreter; B's Python
3.13.7 and TypeScript results were not substituted for these checks.

The RAG wheel was rebuilt offline and inspected: shared package dependency present,
obsolete contract_data absent, no .env. Generated-file/input hashes matched B's
manifest. The scoped speckit-implement resolver selected specs/001-rag; its checklist
had 16 checked/0 unchecked items and no extension hooks were registered.

## Handoff and limits

A's owned F-004 mock contribution is ready for B's coordinated integration review.
A-010 has local frozen-binding evidence but still depends on completed global F-004;
F-014 and A-003's formal shared dependencies are not closed by this contribution.
No other owner's service, frontend, startup orchestration or global CI was tested.
There were no paid calls, new retrieval questions, LLM generation, index rebuild,
deployment or clinical/semantic quality measurements in this adaptation.

For a fresh working copy use the committed lockfile, not another uv add operation:

```powershell
uv --system-certs sync --locked --directory services/rag --python 3.13 --dev
uv run --locked --offline --directory services/rag python -m pytest
```

The shared generated package must be present in the checkout; the dependency merge
supplies it. No manual copy or schema regeneration is needed in A's service.
