# Implementation Plan: Python Extraction and Shared Evaluation

**Branch**: member-d/extraction-evaluation | **Original plan date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/004-extraction-evaluation/spec.md`.
**Owner**: D. **Status**: The frozen v1.0.0 contracts and generated bindings are available.
The shared mock scaffold is [technically complete under F-004](../../docs/team/f-004-technical-completion.md).
F-014 foundation publication remains pending.
Constitution text remains a draft; confirmed source/user requirements are binding.
The 2026-11-11 continuation authorized a D-owned local mock implementation. The
2026-11-13 handoff records F-003/F-009 complete and the generated package published;
this checkout consumes that package. Paid calls, publication and deployment remain
outside this package.

## Authorized local continuation (2026-11-11)

The D-004/D-005 mock service and first D-010/D-006 evaluation slice now consume the
published frozen bindings through D-owned adapters. Map completed local subtasks to the
existing backlog. Track F-014 publication, real-data work and human review separately
from F-004 scaffold completion. Reuse the training checker and dependency-free evidence logic;
do not copy or modify B-owned schemas/bindings.

Actual local setup is Python 3.11.7 with extraction/eval uv locks and independent
environments; 3.13 was proposed but is not present. Node 24.20.0 and eval-local
Promptfoo 0.125.1 support a key-free HTTP smoke. The provider is a deterministic
catalog fake behind a replaceable interface; no live provider/model is selected.

See [state and evidence](../../docs/extraction-eval/milestone-state.md),
[integration commands](../../docs/extraction-eval/integration.md) and
[remaining requests](../../docs/extraction-eval/milestone-requests.md). Annotation
selection/blank templates/adjudication run on synthetic fixtures; actual C-002
manifests, human submissions and team review remain required. No global setup,
shared schema, another service or another member's annotation paths are edited.

## Summary

The owner-local key-free mock now provides evidence-linked extraction, summary and document answers against frozen v1.0.0 records, alongside an offline-first evaluator. Remaining work includes F-014 foundation publication, real-data inputs, independent human review and separately approved live behavior. Freeze group-separated development/final references and calibrate judges only on development material.

## Technical Context

**Language/Version**: D service/evaluation environments verified locally on Python 3.11.7; Promptfoo via a D-owned local eval package; shared root JavaScript lockfile stays B-owned. The generated contract package supports Python >=3.11; each service owner verifies its own environment.
**Primary Dependencies**: FastAPI/Uvicorn, narrow structured-generation adapter, schema validators, deterministic scorers, Promptfoo Python API adapters, pytest; optional judge is approval-gated.
**Storage**: Human-reviewed permitted reference/QA/manifests and redacted aggregate reports; no submitted app document enters eval logs/caches. Service request bodies are transient.
**Testing**: Contract/schema/semantic tests, deterministic fixtures and owner-local tests;
live and frozen final evaluation run only under separate approved gates.
**Target Platform**: F-004 verified the shared Node/Python mock scaffold on Windows.
Startup and runbook verification follow the F-005 scope.
**Project Type**: Monorepo workstream with explicit independent service/UI ownership.
**Performance Goals**: No latency/throughput SLO invented. Measure actual performance on
development data; bounded live policies require approval before activation.
**Constraints**: English only, key-free mocks, no submitted-document persistence,
approved 2 MiB PDFs/100,000 code points/60-minute maximum, delivery 2026-11-24.
**Scale/Scope**: Four members, five specialties, small inspectable literature corpus;
40-document annotation and approximately 80-QA targets, not measured datasets.

## Constitution Check

Gate evaluated before research and re-evaluated after this design:
| Principle | Pre-research / post-design assessment |
| --- | --- |
| English and educational MVP | PASS in design; source exclusions and notices preserved. |
| Ownership and independent work | PASS in design; one owner per path, member annotation exceptions, no business overlap. |
| Contract-first Python/TypeScript boundaries | PASS for the frozen v1.0.0 boundary, generated bindings and F-004 technical mock scaffold checks. F-014 remains pending. |
| Canonical text and evidence | PASS in design; one preparation step, code-point spans, semantic validation distinct. |
| Honest uncertainty | PASS in design; no clinical probabilities, partial mixed support, no hard specialty filtering. |
| Reproducibility and final-test protection | PASS in design; audit-driven manifests and development-only selection. |
| Measured acceptance | PASS in design; structural/span target 100%, substantive thresholds remain explicit team gates. |
| Security/privacy | PASS in design; memory-only policy and approved caps, isolation and redacted logs. |
| Key-free/cost controls | PASS for local design; paid activation and cloud freeze remain BLOCKED pending approval. |
| Real workflow/review | PASS for artifact preparation; no ratification, business implementation or deployment claimed. |

No unjustified constitutional exception is proposed. Pending external activation/contract
review gates are explicit; the cloud/provider portion is not frozen. Local planning can
proceed without selecting a paid service or fabricating runtime defaults.

## Project Structure

### Documentation (this feature)

```text
specs/004-extraction-evaluation/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/README.md
  quickstart.md
  tasks.md
  checklists/requirements.md
```

### Source Code (repository root)

Owned implementation and documentation paths:

```text
services/extraction/**
eval/** (except member-a/b/c annotation overrides)
docs/extraction-eval/**
specs/004-extraction-evaluation/**
```

**Structure Decision**: Keep the confirmed monorepo and one owner per path.
The shared [allowed-path matrix](../../docs/team/allowed-paths.md) controls exceptions.
Initial coordinator scaffolding across service paths is allowed only before the checkpoint.
Root configs/global Spec Kit files and canonical bindings remain B-owned.

## Research and Design Phases

### Phase 0: Research

[research.md](research.md) records choices, rationale and alternatives from the primary
[feasibility review](../../docs/decisions/technical-feasibility.md). No research agents were
spawned. Unknown data counts/configuration outcomes are assigned measured/approval tasks,
not substituted with claimed results or silent defaults.

### Phase 1: Data and interfaces

Use [data-model.md](data-model.md), [contract references](contracts/README.md) and the
single B-owned frozen [canonical contract](../../contracts/v1/README.md).
Do not edit canonicalization, enums, fields or generated bindings in D's branch; submit
any proposed shared change to B for owner review. Schema validation alone cannot verify
English, source support, span slices, SHA256 or citation foreign keys.

### Phase 2: D-owned mock implementation and coordinated handoff

Follow the owner-specific [backlog](tasks.md) and its dependencies and distinct
mock/module/live definitions of done. Local mock fixtures do not complete cross-service,
real-data, live-model or human-review gates. Use [quickstart.md](quickstart.md) for
current owner-local checks and remaining coordinated gates.

## Delivery Priorities and Dependencies

MUST: independent mocked interfaces, correct evidence/provenance, required baseline/evaluation,
English states, privacy/isolation and reproducible checks. SHOULD: measured improvements
within the deadline. COULD: reranking, extra datasets, embedding classifier variants,
ONNX/ICD extensions; these do not block the core.

Critical path: completed contract review/freeze and bindings -> coordinated shared mock scaffold -> independent baseline modules
and C's split manifests -> D's reviewed references/QA -> real integration -> human review ->
configuration freeze and locked final checks on 2026-11-22/23 -> delivery 2026-11-24.
A may inspect corpus sources, C audit data, D draft guidelines/evaluator and B prepare mocks
without waiting for complete real modules. First development measurement/threshold review
remains targeted for 2026-11-14. No available hours or velocity are assumed.

## Complexity Tracking

No constitutional violation requiring an exception. Three small Python services preserve
the confirmed ownership; they are not an invitation to add a distributed platform.
Any new paid service, scope/privacy change or cross-owner edit needs the applicable review.
