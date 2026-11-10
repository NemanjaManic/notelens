# Member C: Python Classification

**Feature**: specs/003-classification. **Branch**: member-c/classification.
**Current base**: initial documentation handoff, not the runnable foundation.
Read the [scope decision](../../decisions/initial-documentation-handoff.md) and
[working-copy guide](../working-copies.md) before starting.

## Responsibility and paths

Owned paths: services/classifier/**, data/mtsamples/**, docs/ml/**, specs/003-classification/**, eval/annotations/member-c/**.
See the [complete matrix](../allowed-paths.md). Member annotation paths override D's parent
ownership. Read shared context freely; do not edit another owner or canonical contracts
independently. Submit shared proposals to B and wait for agreement.

## Read in order

1. [Root instructions](../../../AGENTS.md) and [constitution draft](../../../.specify/memory/constitution.md).
2. [Original prompt](../../../prompts/NoteLens_Codex_SpecKit_prompt_00.md) as requirements context,
   not as authorization to rerun setup or implement all workstreams.
3. Your [spec](../../../specs/003-classification/spec.md),
   [plan](../../../specs/003-classification/plan.md) and
   [tasks](../../../specs/003-classification/tasks.md).
4. [Draft contracts](../../../contracts/v1/README.md), [open decisions](../open-decisions.md)
   and [your start prompt](../start-prompts/member-c.md).

## Select the feature in your own clone/worktree

PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/003-classification'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Git Bash on Windows:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/003-classification
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Expected: FEATURE_DIR selects specs/003-classification, regardless of branch name.
No package install, provider key or other complete module is needed for this path check.

## Inputs and outputs

- **Inputs**: ClassificationRequest containing B's unchanged PreparedDocument.
- **Outputs**: ClassificationResult with one of the five specialties or uncertain/unsupported state, score meaning and model version.
- **Canonical source**: contracts/v1/schema.json and its referenced OpenAPI proposal.
  These remain draft; B coordinates freeze and generated bindings.
- **Failures**: English safe shared errors for invalid/unsupported input, timeout,
  rate/provider/configuration problems and insufficient evidence. Partial document support
  must remain usable when literature is weak. Follow code-point evidence and hash rules.

## Illustrative payload

**Example type**: ClassificationResult.
This is a documentation example, not a running mock, real measurement or completed module.
Mode mock identifies its illustrative nature. No provider/service was called.

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "doc_id": "illustrative-document",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "status": "uncertain",
  "category": null,
  "scores": [],
  "score_kind": "probability",
  "confidence_note": "Illustrative uncertainty output; no model was run and no calibration is claimed.",
  "model_version": "illustrative-only"
}
```

The shared text used for document-bound examples is synthetic. Its exact digest and evidence
interval were computed for the illustration; no clinical validation or real patient is implied.

## First ready action

C-001: inspect provenance/reuse conditions and the authorized local CSV acquisition path; measure counts only when actual data is supplied.
Begin with read-only inspection; ask for approval before the first concrete owned change
package. Do not automatically implement the entire backlog.

## First five-task sequence

| Alias | Local ID | Deliverable | Availability |
| --- | --- | --- | --- |
| C-001 | T001 | Audit authorized MTSamples input, provenance and measured class mapping | May start as an approved inspection/proposal package. |
| C-009 | T002 | Review classifier contracts and build standalone mock consumer checks | Wait for listed prerequisites; see tasks.md. |
| C-002 | T003 | Group duplicates/conflicting labels and freeze seeded split manifests | Wait for listed prerequisites; see tasks.md. |
| C-010 | T004 | Complete C's development-only primary annotations and independent reviews | Wait for listed prerequisites; see tasks.md. |
| C-003 | T005 | Train majority and TF-IDF plus Logistic Regression baselines | Wait for listed prerequisites; see tasks.md. |

The first audit/rule-drafting task can start without other complete modules. Later tasks remain blocked by their actual contract/scaffold/published-foundation prerequisites.
This is a five-task sequence, not a claim that five business tasks are immediately ready.

## Checks and honest status

The feature path check above exists now. Test/CLI commands in tasks.md are future acceptance
targets created by the named tasks and prerequisites. There is no service-start/npm script
available today. Mock checks, actual-module checks and separately authorized live checks
must be reported distinctly; do not close real tasks based on an illustrative payload.
English artifacts, the user's approved 60-minute/2-MiB/100,000-code-point policies, held-out
data protection and no paid calls without approval remain binding.
