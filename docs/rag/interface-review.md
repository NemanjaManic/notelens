# RAG interface review

The [initial RAG feedback](../team/contract-reviews/p1/member-a-response-to-b.md)
records A's technical review of the original proposal. The [shared contract
freeze](../decisions/contract-freeze.md) records the accepted v1.0.0 interface.

## Frozen contract consumer closeout

On 2026-11-19, A's agent verified the published interim checkpoint
`7aa6c321e7c40c364d234467adbecbab0d06a497` on `origin/main`. Its tree is
`74ab9bdb1f064b9e049decd0cfbf7a4ebd6f7129` and its foundation backlog records
F-003 and F-004 as complete. The canonical `contracts/v1` and `contracts/generated`
trees match RAG revision `24f77211da1395a9da99d7b0f1ca17621c6e64d0`.

With Spec Kit 1.3.3, the PowerShell `check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks`
resolver on `rag` selected `specs/001-rag`, with all 16 requirements checklist items checked.
The owner checkout passed 241 targeted checks with the following commands.

```powershell
git diff --exit-code 7aa6c321 24f7721 -- contracts/v1 contracts/generated
uv run --locked --offline --directory services/rag python -B -m pytest -o addopts= -q tests/test_contract.py tests/test_frozen_bindings.py tests/test_http_smoke.py tests/test_failures.py
```

The isolated PR #4 checkout also ran the locked RAG suite with Python 3.13.5
and cached dependencies. The default install passed 307 tests and skipped one
Chroma test module. With the optional indexing extra, all 319 tests passed.

```powershell
uv run --locked --offline --directory services/rag --python 3.13 python -B -m pytest -o addopts= -q
uv run --locked --offline --directory services/rag --python 3.13 --extra indexing python -B -m pytest -o addopts= -q
```

The checks exercised the generated v1.0.0 bindings, both RAG routes over loopback,
mock provenance, insufficient-evidence responses, and safe operational errors.
Unconfigured live mode returned `503 configuration_required` without mock fallback.
A-010 is complete for the RAG consumer. F-014 remains open on the published foundation
backlog and is still required for A-003. Application routing, independent semantic
review and provider activation are outside this closeout.
