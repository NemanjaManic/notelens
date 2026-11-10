# Planning Package Status

**Date**: 2026-11-10. **Owner**: B, with approved initial-coordinator preparation.
**Status**: Planning/design package complete for review; runnable foundation still pending.

**Later user decision**: publish documentation/tasks now and defer runnable mocks/UI.
The current [handoff decision](../decisions/initial-documentation-handoff.md) and
[documentation checkpoint](documentation-checkpoint.md) govern onboarding.
The remaining-gates list below describes the planning-stage state; member handoffs and
working-copy instructions have since been prepared, without completing runtime gates.

## Artifacts

| Scope | Owner | Plan | Backlog | Tasks |
| --- | --- | --- | --- | --- |
| Shared Foundation | B | [plan](../../specs/000-foundation/plan.md) | [tasks](../../specs/000-foundation/tasks.md) | 14 |
| Python RAG | A | [plan](../../specs/001-rag/plan.md) | [tasks](../../specs/001-rag/tasks.md) | 11 |
| Complete Frontend and Integration | B | [plan](../../specs/002-platform/plan.md) | [tasks](../../specs/002-platform/tasks.md) | 11 |
| Python Classification | C | [plan](../../specs/003-classification/plan.md) | [tasks](../../specs/003-classification/tasks.md) | 10 |
| Python Extraction and Shared Evaluation | D | [plan](../../specs/004-extraction-evaluation/plan.md) | [tasks](../../specs/004-extraction-evaluation/tasks.md) | 13 |

Each feature also has research.md, data-model.md, contracts/README.md and quickstart.md.
[Shared schema/OpenAPI proposal](../../contracts/v1/README.md) is draft, not frozen.
[Technical feasibility](../decisions/technical-feasibility.md) records primary sources,
choices, alternatives and documentation/account limitations.
[Recorded analysis output](planning-analysis-record.md) copies the completed read-only
analysis result for review; the analysis workflow did not edit specifications/plans/tasks.

## Clarification workflow

Ran the installed clarify prerequisite path resolver once per feature and assessed scope,
data, interaction, nonfunctional, integration, failure, constraints, terminology and completion.
Asked two questions, answered both, and immediately integrated them into platform spec
Clarifications/FR-002/FR-011/FR-023 and governing guidance/open-decision notes:

1. Application-side submitted-document retention: server memory only, absolute maximum
   60 minutes, deletion on expiry/restart; built-in public examples may remain versioned.
2. Input limits: 2 MiB (2,097,152 bytes) per PDF and 100,000 Unicode code points per
   document; reject rather than truncate.

Platform built-in checklist remained 16/16 after revalidation: no toggles/regressions.
No human/team acceptance or ratification is implied.

| Coverage category | Outcome |
| --- | --- |
| Functional scope, roles, English/out-of-scope behavior | Clear from confirmed source. |
| Domain identity/provenance and terminology | Clear for design; shared field proposals await owner review. |
| Interaction and document lifecycle | Resolved for retention/input caps; explicit English expiry/error states. |
| Security/privacy/reliability | Local boundary clear; remaining live controls are approval tasks. |
| Integration/failures/constraints | Clear for mocks; cloud/account/model activation explicitly deferred. |
| Completion signals | Clear; checks, backlogs and real/mock/live status distinguished. |
| Miscellaneous unknown empirical values | Deferred to measured acquisition/development tasks, not guessed. |

No remaining question blocks key-free local design. This does not authorize unresolved
hosting, provider retention, spending, timeout/retry/history/rate choices.

## Actual plan/tasks workflows

Read and followed installed speckit-plan and speckit-tasks skills with each feature's spec,
constitution and design documents. No subagents were used. Set the exact
SPECIFY_FEATURE_DIRECTORY and SPECIFY_FEATURE_NO_PERSIST=1, then ran:

```powershell
& ./.specify/scripts/powershell/setup-plan.ps1 -Json
& ./.specify/scripts/powershell/setup-tasks.ps1 -Json
```

The setup-plan script resolved/copied each plan template; completed its required technical
context, constitution gates, structures and research/design outputs. The task setup script
returned its active 9,135-character template and all four design-document categories for
each feature. Task generation used that structure and retained standard checkbox/local IDs,
stable source aliases, owners, story references, paths, acceptance, dependencies, real
tool-CLI verification commands and separate mock/module/live done conditions.

Commands that refer to future tests/scripts are explicitly labeled planned deliverables;
they are not claimed available or passing today. Independent Python commands use
uv run --directory so relative test paths resolve inside the correct service/eval project.
No fictional npm run script is documented.

Only F-001 and F-002 are checked, reflecting actual previously executed integration/
constitution-draft/specification documentation. The other 57 tasks remain unchecked.
Business implementation tasks are all incomplete. Optional work must not block MVP delivery.

## Executed validation

- Five specs/plans/backlogs, 59 unique tasks, 112 functional requirements and 30 success
  criteria all have explicit work mappings.
- All cross-feature aliases/local IDs resolve; no dependency cycle was found.
- Each task has one owner/story, paths, dependencies, acceptance, verification and done states.
- Markdown links and whitespace checks passed; source prompt and all 21 official
  managed-asset checksums stayed unchanged.
- No non-Markdown application/service/data/eval/infra/project-script files were created
  by the planning package. Schema/OpenAPI are design JSON, not API implementations.
- JSON Schema Draft 2020-12 metaschema validation passed for the proposal with 22 definitions.
- OpenAPI 3.1.1 validation with local schema references passed for five proposed operations.
  Validator versions came from official PyPI metadata: jsonschema 4.26.0 and
  openapi-spec-validator 0.9.0, used only in transient uv tooling.
- Installed speckit-analyze prerequisite checks ran once per feature using:

```powershell
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks
```

The analysis itself was strictly read-only. It reported no blocking artifact inconsistencies.
Reference coverage is not proof of semantic correctness, implemented behavior or universal
security. Source-support/span fixtures and HTTP transport/runtime checks remain future work.

## Gates that remain

- Constitution/user review and actual A/B/C/D contract agreement/freeze.
- Positive/negative semantic fixtures and generated bindings.
- Real dependency installation/locks, three mock services, minimal mock web flow/startup,
  health/error/isolation checks and actual run commands.
- Four full handoffs/start prompts and verified independent-working-copy instructions.
- Actual foundation checkpoint and separately authorized commit/push.
- All real RAG, classification, extraction/generation/evaluation work.
- Actual accounts/model/prices/provider-retention review, budget and operational limits
  before any live activation; approved hosting before deployment.

No paid model call, data acquisition, model training, runtime mock smoke, benchmark,
deployment, commit or push was executed in this package.
The final delivery date remains **2026-11-24**.
