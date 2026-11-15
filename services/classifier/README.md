# Classifier F-004 Mock Scaffold

**Owner:** C / Sara. **Verified locally:** 2026-11-14.

**Educational demo only. This is not a doctor or medical advice. Do not submit real
personal medical reports. Use known English public/synthetic fixtures only.**

This package implements C's local F-004 contribution: `POST /v1/classify`, four
deterministic synthetic scenarios, explicit input/output validation, request correlation
and safe error envelopes. It has no trained classifier, language detector, scope/OOD
detector, dataset processing, provider call or document store.

Shared prerequisite package: `aabbfc7844a8092194b4ab1cae561563e83ae13d`, with the
publication documentation at `fd1197bd380de9ba9037ea0b73b42031dc1d4bb2` on
`member-b/task-contract-freeze-bindings`. See the [frozen handoff](../../docs/team/frozen-contracts-handoff.md)
and [classifier brief](../../docs/team/classifier-scaffold-p2.md).

## Dependency boundaries

The service installs `notelens-contracts==1.0.0` from
`../../contracts/generated/python`. Its TypedDicts describe dictionaries; the service
explicitly calls `validate_json` and `validate_record`. No local wire schema or Pydantic
model competes with the canonical contract. `mock_results.json` contains four copied
synthetic canonical examples; tests compare them to the frozen source fixtures after
binding the actual incoming document ID and digest.

Python 3.11.9 is verified here. The package allows >=3.11,<3.14, but this run makes no
claim about other interpreters. Exact installed versions include FastAPI 0.162.7,
Uvicorn 0.54.0, Starlette 1.10.0, pytest 9.2.0, HTTPX 0.28.1, jsonschema 4.26.0 and
referencing 0.37.0. The independent `uv.lock` records transitive dependencies. No ML
training dependencies are installed yet.

## Windows setup and checks

From the repository root, using the installed Python 3.11 interpreter:

```powershell
python -m venv .cache/classifier-tooling
& ./.cache/classifier-tooling/Scripts/python.exe -m pip install --only-binary=:all: uv==0.13.7
$classifierUv = Join-Path (Get-Location).Path '.cache/classifier-tooling/Scripts/uv.exe'
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
& $classifierUv --system-certs sync --locked --directory services/classifier --python (Get-Command python.exe).Source
```

Initial installation downloads development dependencies. Routine checks after setup
are offline and key-free:

```powershell
& $classifierUv sync --locked --offline --directory services/classifier
& $classifierUv run --locked --offline --directory services/classifier python -B -m pytest -q
& ./services/classifier/.venv/Scripts/python.exe -B scripts/project/check_bindings.py
```

Stop after any failed command. The first editable installation required an online sync
to cache `editables`; a premature offline sync failed, then succeeded after that setup.
No system Python installation, global package installation or shared lockfile change
was made.

## Local start and scenarios

```powershell
$env:NOTELENS_CLASSIFIER_MODE = 'mock'
$env:NOTELENS_CLASSIFIER_MOCK_SCENARIO = 'supported'
& $classifierUv run --locked --offline --directory services/classifier python -m notelens_classifier
```

The launcher binds `127.0.0.1:8002`, disables proxy-header trust and access logging, and
supports `--port` for local integration. Stop a manually started process with Ctrl+C.
Use this local-only launcher; no public listener or deployment is approved.

| Server-side scenario | Result |
| --- | --- |
| `supported` | One category, five ordered synthetic decision scores. |
| `uncertain` | Null category, five ordered synthetic decision scores. |
| `unsupported_skipped` | Null category, empty scores and null model/score kind. |
| `unsupported_performed` | Null category, five synthetic scores and explicit fixture scope/pipeline metadata. |

`classification_execution: performed` in a mock simulates execution only; every result
keeps `mode: mock` and the frozen fixture's honest confidence note. Document text cannot
choose the scenario or activate another mode. Unset/invalid mode, invalid scenario, or
`live` mode without a real pipeline fails with 503/configuration_required. There is no
automatic fallback and no real-mode inference implementation.

All business calls require one canonical UUID `X-Request-ID`. Valid IDs are echoed;
missing/malformed/duplicate IDs receive a safe 400 envelope with a new diagnostic UUID.
The output always binds the actual incoming `doc_id` and `text_sha256`. Malformed,
duplicate-key and non-finite JSON receives 400; invalid document structure/hash/language
policy receives 422; text exceeding 100,000 code points receives 413 without truncation.
Unexpected failures, including invalid outgoing scores, become safe 500 envelopes.

Optional `NOTELENS_CLASSIFIER_SERVICE_TOKEN` configures server-side bearer authentication.
When set, missing/invalid/duplicate authorization is rejected with 401. Never paste token
values into chat or commit them. With no token, only loopback peers in explicit mock mode
are admitted. Remote peers receive a configuration error; forwarded headers cannot make
them local. This is not authorization to expose this scaffold publicly.

## Evidence and remaining gates

- **51 tests passed:** frozen mock shapes and identities, Unicode/text limits, strict JSON,
  invalid headers, authentication/configuration failures, native non-finite output,
  request isolation, safe failures, no file writes during mock requests, and a real
  loopback Uvicorn HTTP smoke with process cleanup.
- Installed Python bindings passed **153/153 payload outcomes and 22/22 simulated
  exchanges**, all 29 type exports, native-number and strict JSON negatives.
- One test-library warning remains: Starlette deprecates its HTTPX TestClient backend
  in favor of HTTPX2. Current pinned tests pass; no warning was suppressed.
- The socket smoke checks process startup, real POST responses and test-process
  termination. It does not establish B's coordinated graceful startup/shutdown.

**F-004 is not complete across the project.** C's local contribution does not mark
B's shared task done. As required by the handoff, `/health/live` and `/health/ready`
are deferred to F-011 after F-004; they currently return 404. Their future 200/503/401
semantics remain those of the frozen contract. C-009 remains unchecked even though
scaffold checks use `tests/test_contract.py`; it requires the completed shared F-004.
C-002 still also requires F-014. No model metrics, final splits or annotation results
are produced here.

The service processes request content transiently, with no body logging, application
cache, file writes, background jobs or session store. A disconnected body never reaches
classification. Runtime bounds, cancellation of real synchronous inference, stalled
request handling and the end-to-end 60-minute maximum are unverified integration gates,
not guarantees inferred from these mocks. No numeric operational limits were invented.
B's evaluated language method is still required before real user input is enabled;
an accepted fixture policy record is not a language detector.

Implementation references: [FastAPI direct Request handling](https://fastapi.tiangolo.com/advanced/using-request-directly/)
requires explicit validation when bypassing its body models; [uv path dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)
support the independent local generated-package dependency used here.
