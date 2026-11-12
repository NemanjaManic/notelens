# Member B Project Checks

**Package**: F-008 only. **Recorded**: 2026-11-11. **Owner**: B.
This is executable offline contract tooling. It is not a runnable application foundation,
an implemented Python business service, a contract freeze, or human/team acceptance.

## Local setup on Windows

Run from the repository root with Python 3.13 installed. This machine has Python 3.13.7.
The following uses repository-local tooling and caches; system Python, user packages,
permanent PATH, and permanent PowerShell policy are unchanged.

```powershell
$env:PIP_CACHE_DIR = Join-Path (Get-Location).Path '.cache/pip'
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_TOOL_DIR = Join-Path (Get-Location).Path '.cache/uv-tools'
$env:UV_PYTHON_DOWNLOADS = 'never'
python -m venv .cache/tooling
& ./.cache/tooling/Scripts/python.exe -m pip install --only-binary=:all: uv==0.13.7
$contractUv = Join-Path (Get-Location).Path '.cache/tooling/Scripts/uv.exe'
& $contractUv --version
& $contractUv --system-certs sync --locked --directory scripts/project --python (Get-Command python.exe).Source
```

Stop if a setup command fails; do not run validation in an incomplete environment.
Package installation needs package-registry access, but no provider key or paid service.
The first package execution generated `uv.lock` with `sync` before subsequent locked runs.
For fresh checkouts use the locked command above. Do not regenerate the lock casually.
Python downloads are disabled, so a missing compatible local interpreter is an explicit
setup failure rather than an automatic system installation. All `.cache` and `.venv`
directories are already ignored by the existing root rules.

Pinned direct dependencies are `jsonschema[format-nongpl]` 4.26.0, `referencing` 0.37.0,
and `openapi-spec-validator` 0.9.0. This tooling has its own manifest/lock and does not
install into or edit A/C/D's service environments. It uses standard-library `unittest`.

For a fresh PowerShell session, reestablish the environment variables and `$contractUv`.
No activation script or permanent PATH edit is necessary. From another directory, use
absolute paths for `$contractUv`, `--directory`, and/or `check_contracts.py`. The checker
finds the repository from its own file path, independently of the process working directory.

## Run deterministic checks

```powershell
& $contractUv run --locked --offline --directory scripts/project python check_contracts.py
if ($LASTEXITCODE -ne 0) { throw 'Contract validation failed.' }
& $contractUv run --locked --offline --directory scripts/project python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Contract tooling tests failed.' }
```

With uv already on a session's PATH, the backlog's acceptance command is also available:

```powershell
uv run --directory scripts/project python check_contracts.py
```

The documented locked/offline form is preferred for reproducible routine checks after
installation. `--offline` prevents uv fetching packages; the checker separately denies
Python outbound TCP/UDP connections and DNS resolution while validating. Its schema
registry denies remote retrieval, and reference preflight permits only the canonical
local schema/its fragments. It never fetches fixture source URLs or document content.

`check_contracts.py` exits 0 only when schema/API validation and every expected fixture
outcome pass. Missing/malformed files, invalid catalog coverage, unexpected rejections,
unexpected passes, unresolved references, and infrastructure failures exit 1. Diagnostics
show only case IDs, rule IDs, and JSON-pointer locations, never payload bodies, validation
exception dumps, source quotes, secrets, or traces. See the [fixture guide](../../contracts/v1/fixtures/README.md).

`STRUCTURE` means the selected definition rejected the payload; `SCHEMA_INVALID` and
`OPENAPI_INVALID` identify specification errors. `OPENAPI_BINDING` rejects missing
required operations or incorrect request/200-response references, even if the API document
is otherwise structurally valid. Exact-text/relationship diagnostics
include `TEXT_UNICODE`, `TEXT_CANONICAL`, `TEXT_DIGEST`, `SPAN_BOUNDS`, `SPAN_QUOTE`,
`DOCUMENT_IDENTITY`, `CATEGORY_UNIQUE`, `DUPLICATE_ID`, `ICD_SOURCE`, `CITATION_MISSING`,
`CLAIM_PROVENANCE`, and `PARTIAL_GAP`. Curated fixture comparisons use
`REFERENCE_ATTRIBUTE` and `REFERENCE_SPAN`. These last comparisons are not general
clinical inference. English declarations are structural fields, not prose detection.

## Freeze guard for the later F-003 task

```powershell
& $contractUv run --locked --offline --directory scripts/project python check_contracts.py --require-freeze
```

**Current expected result**: fixture checks pass, then `FREEZE_PENDING` with exit code 1.
No real freeze record or team agreement exists in this package. A fixture pass must not
be interpreted as permission to freeze. This expected guarded failure does not fail F-008.

F-003 must collect actual A/B/C/D agreement, record it in `docs/decisions/contract-freeze.md`,
and create `contracts/v1/freeze.json` only after the reviewed checks pass. Its exact keys are:

| Field | Required value |
| --- | --- |
| `schema_version` | Version agreed by owners, matching the schema's PreparedDocument constant and OpenAPI info.version. |
| `schema_sha256` | Lowercase SHA256 of the exact `contracts/v1/schema.json` bytes. |
| `openapi_sha256` | Lowercase SHA256 of the exact `contracts/v1/openapi.json` bytes. |
| `fixtures_sha256` | Digest of the fixture bundle as defined below. |
| `approvals` | Exactly four objects, one per distinct member A/B/C/D, with the fields below. |

Each approval has exactly `member`, `decision` (`approved`), `date` (ISO YYYY-MM-DD), and
`evidence` (`docs/decisions/contract-freeze.md#member-a`, similarly b/c/d). The evidence
file must exist and contain the corresponding Markdown heading, such as `## Member A`.
That section should document the actual review, accepted version/changes, and remaining
exceptions. Do not fill approval values from agent inference or from fixture test data.

The fixture-bundle digest hashes a JSON object mapping each file's POSIX relative path
within `contracts/v1/fixtures` to its exact-byte SHA256. Include every file recursively,
including the catalog, payloads, documents, references, and fixture README. Encode the map
using `json.dumps(map, sort_keys=True, separators=(',', ':')).encode('utf-8')`, then SHA256
those bytes. `freeze_digests(Contracts())` exposes all three calculated digests to F-003;
it does not write approval records. To inspect the digests without creating a freeze:

```powershell
& $contractUv run --locked --offline --directory scripts/project python -c "import json; from check_contracts import Contracts, freeze_digests; print(json.dumps(freeze_digests(Contracts()), indent=2))"
```

The guard rejects absent/malformed records, version/digest drift, missing/duplicate/pending
owners, invalid dates, and unresolved evidence sections. It checks recorded consistency;
it cannot authenticate real consent or determine whether prose is a genuine approval.
Human/team review remains required. Tests create explicitly synthetic records only in
temporary ignored `.cache/contract-tests` copies; they never approve/freeze the real checkout.

## Actual workflow and verification record

Read and followed the repository [speckit-implement skill](../../.agents/skills/speckit-implement/SKILL.md)
with the user-approved scope limited to foundation T003 / F-008. No other backlog task
was executed. Pre/post extension hooks are absent (`.specify/extensions.yml` does not exist).
Verified the existing ignore rules; no repository-wide formatter or root configuration
change was needed. No templates were generated or replaced by this implementation task.

The official resolver ran with explicit context and no state persistence:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/000-foundation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

It returned `D:\Work\SITA\Capstone\specs\000-foundation` and research/data-model/contracts/
quickstart/tasks documents. All 16 built-in requirements-quality items were checked;
this is recorded agent review, not human/team acceptance. The child-only execution
policy left permanent settings unchanged. The pinned CLI was actually invoked:

```powershell
& $contractUv --system-certs tool run --python (Get-Command python.exe).Source --from 'git+https://github.com/github/spec-kit.git@v1.3.3' specify version
```

Observed: Spec Kit CLI 1.3.3 on Python 3.13.7/Windows AMD64. The Git tag resolved to
`79cb423c37bb9394bab7a66063c27dfa80b72fba`. Local uv reported 0.13.7. Tool bootstrap and
package installation were online downloads of development dependencies, not live-provider
or model checks. The caches/tools remain inside ignored repository paths.

Executed the locked/offline fixture suite: **90/90 expected outcomes, 38 positive and
52 negative**, covering all 22 definitions. Executed **29 standard-library tests**, all
passing, including wrong-reason rejection, missing coverage, duplicate cases/JSON keys,
non-finite JSON numbers, Unicode boundaries, repeated evidence, malformed embedded input,
local references, operation-reference drift, network denial, independent working directory,
and freeze-record drift.
The text boundary tests construct 100,000/100,001 emoji code points in memory; no oversized
repetitive text file is versioned. The guarded real-checkout command fails as expected
with `FREEZE_PENDING`; no actual approval record was created.

Only F-008 may be marked complete from this evidence. Full business modules, actual HTTP
payload/transport checks, generated Python/TypeScript compatibility, UI/session security,
model quality, source-relative semantic acceptance, and human/team review remain pending.
No provider activation, paid calls, dataset/corpus acquisition, deployments, commits,
merges, or pushes occurred. The earlier untracked interface-review document stays unchanged.

## Official references checked for this package

- [uv installation](https://docs.astral.sh/uv/getting-started/installation/): isolated PyPI/pip installation.
- [jsonschema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/): Draft 2020-12 and explicit format checking.
- [OpenAPI validator API](https://openapi-spec-validator.readthedocs.io/en/latest/python.html): explicit v3.1 validator and local-file base URI.
- [PowerShell execution policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1): process-only policy scope.

Package release metadata was checked on PyPI before installation. Exact transitive versions
and distribution hashes are recorded in `uv.lock`; source/schema authority still comes
from the project's [contract proposal](../../contracts/v1/README.md), not library defaults.
