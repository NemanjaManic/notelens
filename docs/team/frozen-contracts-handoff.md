# Frozen Contract and Binding Handoff

**Prepared:** 2026-11-13. **Coordinator:** B.
**Local result:** F-003/F-009 completed and checked. **Publication:** pending separate
commit/push authorization on member-b/task-contract-freeze-bindings; no published hash is invented.

All human approvals are recorded in [the decision](../decisions/contract-freeze.md).
Wire/schema version is 1.0.0; canonical sources are contracts/v1/schema.json and openapi.json,
bound by freeze.json. [Generated bindings and actual Windows checks](../../contracts/generated/README.md)
provide reproducible package/fixture evidence.

Python distribution **notelens-contracts** at **contracts/generated/python** exports
**notelens_contracts.v1**. A service path dependency is `../../contracts/generated/python`.
TypeScript imports **@notelens/contracts/v1** from contracts/generated/typescript. Both
package versions are 1.0.0. B owns root/workspace configuration; each Python service owner
declares the local package and generates its own lockfile. No service files were edited.

## Exact next owner contributions after publication

| Owner | F-004 contribution |
| --- | --- |
| A / Nemanja | Create/adapt services/rag only: retrieve and literature-answer mock endpoints using frozen types/validators, independent retrieval provenance and safe error mapping. No keys, corpus/index or actual generation may be required. Existing A-reported scaffold checks need actual adaptation checks; B has not rerun them. |
| C / Sara | Implement services/classifier only under the [classifier brief](classifier-scaffold-p2.md): deterministic supported/uncertain/unsupported mock scenarios, actual incoming identity, five ordered finite scores, correct skipped metadata and language-policy record. No training/OOD detector is introduced. |
| D / Milica | Create/adapt services/extraction only: extraction/summary and document-answer mocks, exact mentions/evidence, independent section outcomes and partial supported answers. Validate against the actual canonical document; no real business model is required. |
| B | Web workspace, thin mock clients, root configuration and coordinated startup/integration. A/C/D keep independent manifests/dependencies/locks. |

Python exports are TypedDict dictionaries with validate_json/validate_record helpers,
not BaseModels. Services explicitly apply runtime validation and map safe errors into the
approved HTTP channels. Their owners verify FastAPI/Uvicorn/interpreter compatibility.
B checked the installed package on Python 3.13.7; other service environments need owner checks.

F-011 health/readiness follows F-004: agreed 200/503 shapes and authenticated 401 envelope,
challenge and fresh diagnostic ID. Business POST IDs retain their distinct admission rules.
Keep loopback key-free mock exceptions local, bind results to actual incoming doc_id/hash,
retain data transiently without body logging, and never silently fall back from live mode.

## Remaining gates

- A-010/C-009 still require **completed F-004** as well as F-003. Owned F-004 contributions
  create that prerequisite; they do not require finished RAG/classifier/extraction models.
- A-003 retains A-002/A-010/F-014; C-002 retains C-001/C-009 and reviewed published F-014.
- B-010 follows F-004; B's sessions/input/report work retains B-004/F-014 and other backlog gates.
- Health, Unicode checks, startup/shutdown, smoke flow, CI/scope checks, handoffs, reviewed
  acceptance and foundation publication still need completion. This is not F-014.
- Live language/ambiguity evaluation, provider/model/budget activation, numeric operational
  controls and deployment remain separate gates. No new defaults are added here.

## Executed workflow

Used the repository speckit-implement skill scoped to foundation T004/F-003 and T005/F-009.
Selected specs/000-foundation with SPECIFY_FEATURE_NO_PERSIST=1 and ran:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

The official resolver returned the foundation documents. The requirements checklist had
16 checked items and zero unchecked; no pre/post extension hooks existed. Existing ignore
rules cover environments, generated caches and dependency directories. No templates were
generated, no global configuration changed, and no repository-wide formatter was run.
The local scope is recorded/checkable; publication remains a separate authorized action.
