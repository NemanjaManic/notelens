# Implementation Plan: Python Extraction and Shared Evaluation

**Branch**: main (no feature branch created) | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification at `specs/004-extraction-evaluation/spec.md`.
**Owner**: D. **Status**: Draft local design and executable backlog proposal.
Constitution text remains a draft; confirmed source/user requirements are binding.
This stage does not authorize business implementation, paid calls, publication or deployment.

## Summary

Draft annotation/matching rules early, implement evidence-linked extraction/summary/document answers in Python after contracts, and build an offline-first evaluator before complete real modules. Freeze group-separated development/final references and calibrate judges only on development material.

## Technical Context

**Language/Version**: Python 3.13 proposed for extraction/scoring; Promptfoo via a D-owned local eval package; shared root JavaScript lockfile stays B-owned.
**Primary Dependencies**: FastAPI/Uvicorn, narrow structured-generation adapter, schema validators, deterministic scorers, Promptfoo Python API adapters, pytest; optional judge is approval-gated.
**Storage**: Human-reviewed permitted reference/QA/manifests and redacted aggregate reports; no submitted app document enters eval logs/caches. Service request bodies are transient.
**Testing**: Contract/schema/semantic tests, deterministic fixtures and owner-local tests;
live and frozen final evaluation run only under separate approved gates.
**Target Platform**: Local Windows/PowerShell verified for workflow tooling; Node/Python
application execution and Bash/macOS/Linux runbooks must be verified during F-004/F-005.
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
| Contract-first Python/TypeScript boundaries | PASS in design; schema/OAS are proposals, freeze required before real consumers. |
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

Proposed owned paths; currently only contributor documentation exists:

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
single draft [canonical proposal](../../contracts/v1/README.md).
Canonicalization, enum and field proposals need owner review before freeze.
Generate bindings rather than diverging copies. Schema validation alone cannot verify
English, source support, span slices, SHA256 or citation foreign keys.

### Phase 2: Implementation handoff (future approval)

Generate an owner-specific [backlog](tasks.md) using the installed tasks workflow.
Follow its dependencies and distinct mock/module/live definitions of done.
Mock fixtures do not complete business tasks. Use [quickstart.md](quickstart.md) for
current safe checks versus planned commands after their named prerequisite creates files.

## Delivery Priorities and Dependencies

MUST: independent mocked interfaces, correct evidence/provenance, required baseline/evaluation,
English states, privacy/isolation and reproducible checks. SHOULD: measured improvements
within the deadline. COULD: reranking, extra datasets, embedding classifier variants,
ONNX/ICD extensions; these do not block the core.

Critical path: contract review/freeze -> shared mock scaffold -> independent baseline modules
and C's split manifests -> D's reviewed references/QA -> real integration -> human review ->
configuration freeze and locked final checks on 2026-11-22/23 -> delivery 2026-11-24.
A may inspect corpus sources, C audit data, D draft guidelines/evaluator and B prepare mocks
without waiting for complete real modules. First development measurement/threshold review
remains targeted for 2026-11-14. No available hours or velocity are assumed.

## Complexity Tracking

No constitutional violation requiring an exception. Three small Python services preserve
the confirmed ownership; they are not an invitation to add a distributed platform.
Any new paid service, scope/privacy change or cross-owner edit needs the applicable review.
