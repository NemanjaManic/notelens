# Frozen Shared Bindings: F-009

**Version:** 1.0.0. **Verified:** 2026-11-13, Windows/Python 3.13.7/Node v24.22.1.
Source: contracts/v1/schema.json, with recorded freeze and shared semantic validation.

| Consumer | Installable package path | Import |
| --- | --- | --- |
| Python | contracts/generated/python; distribution notelens-contracts 1.0.0 | notelens_contracts.v1 |
| TypeScript | contracts/generated/typescript; @notelens/contracts 1.0.0 | @notelens/contracts/v1 |

The deterministic generator derives all 29 named wire types and supporting inline types
from the single canonical schema. Python exports **TypedDicts**, not Pydantic BaseModels;
TypeScript exports interfaces/unions and typed runtime functions. As the
[Python typing documentation](https://docs.python.org/3.13/library/typing.html#typing.TypedDict)
explains, annotations alone do not enforce runtime constraints. Use the validators.

Both packages carry exact generated schema copies. Python semantic methods are generated
from the B-owned shared checker; TypeScript uses Ajv 2020-12 and contracts/runtime/typescript.mjs.
[Ajv options](https://ajv.js.org/options.html) document its number/validation controls.
Generation fingerprints source/freeze/input/output bytes and fails if the freeze is invalid.
`--check` is read-only and rejects drift. Do not hand-edit generated files or schema copies.

## Python usage

```python
from notelens_contracts.v1 import ClassificationRequest, validate_json, validate_record

request: ClassificationRequest = validate_json("ClassificationRequest", incoming_json)
result = validate_record("ClassificationResult", result_payload, document=request["document"])
```

validate_json rejects duplicate keys and nonstandard/overflow JSON numbers. validate_record
validates native Python objects before serialization, including NaN/infinity rejection.
Evidence-bearing records require canonical document context. ContractValidationError has
safe Issue(rule, path) diagnostics; never log submitted bodies. validate_exchange checks
complete synthetic header/error exchanges. Do not call model_validate/model_dump on TypedDicts.
The library declares Python >=3.11 syntax; only its installed Python 3.13.7 package was
executed here. Each owner verifies their own service interpreter and lockfile.

## TypeScript usage

```typescript
import { validateRecord, type ClassificationResult } from '@notelens/contracts/v1';
const result: ClassificationResult = await validateRecord('ClassificationResult', payload, { document });
```

validatePayload returns Issue[]; validateRecord/validateJson return a validated record or
safe error; validateExchange checks the shared correlation cases. Validation is async
for UTF-8 SHA256 through Web Crypto. No coercion, input rewriting or model/provider calls
are enabled. Node 24.22.1/TypeScript 7.0.2 were checked; Next.js/browser build remains F-004.

## Reproduce from the root on Windows

First install B's [tooling environment](../../scripts/project/README.md). Setup downloads
development dependencies, without provider keys; routine verification uses the locked cache.

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$contractUv = Join-Path (Get-Location).Path '.cache/tooling/Scripts/uv.exe'
& $contractUv run --locked --offline --directory scripts/project python check_contracts.py --require-freeze
& $contractUv run --locked --offline --directory scripts/project python generate_contracts.py --check
& $contractUv --system-certs sync --locked --directory scripts/project/consumers/python --python (Get-Command python.exe).Source
npm.cmd ci --prefix contracts/generated/typescript --ignore-scripts --no-audit --no-fund
npm.cmd ci --prefix scripts/project/consumers/typescript --ignore-scripts --no-audit --no-fund
& $contractUv run --locked --offline --directory scripts/project/consumers/python python ../../check_bindings.py
node scripts/project/check_bindings.mjs
node scripts/project/consumers/typescript/smoke.mjs
& ./scripts/project/consumers/typescript/node_modules/.bin/tsc.cmd --project scripts/project/consumers/typescript/tsconfig.json
& $contractUv run --locked --offline --directory scripts/project python -m unittest discover -s tests
```

Stop on any nonzero exit. For intentional regeneration, omit --check and rerun compatibility
checks. Locks came from actual uv/npm installs. Actual package versions: Ajv 8.20.0,
ajv-formats 3.0.1, TypeScript 7.0.2, Hatchling build backend 1.33.0, jsonschema 4.26.0.

## Executed acceptance and limitations

- Canonical checker: 155/155 outcomes (69 positive/86 negative), 22/22 simulated exchanges.
  Two schema/API-tooling cases are not wire payloads.
- Installed Python package and TypeScript runtime each passed the same **153/153 wire
  payload cases** with exact diagnostics and **22/22 exchanges**. Both rejected six native
  non-finite inputs and malformed/duplicate-key/overflow JSON; finite decision values and
  probability endpoints 0/1 remained valid.
- All 29 Python exports resolve. Installed TypeScript package import, consumer typecheck,
  and repeated/non-BMP code-point-to-UTF-16 checks passed.
- Canonical tooling suite: **57 tests passed**, including freeze drift/owner evidence,
  malformed catalogs, partial failure, provenance and native-number checks.
- Local wheel built: .cache/review/contract-wheels/notelens_contracts-1.0.0-py3-none-any.whl.
  Both npm locks passed offline ci. No registry publication was performed.

No HTTP, model, provider, web application build, real submitted-input pipeline or semantic
medical-quality checks ran. This does not complete F-004/F-014. Publication of this new
freeze/binding branch needs separate commit/push authorization.
