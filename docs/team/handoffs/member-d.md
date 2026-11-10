# Member D: Extraction and Evaluation

**Feature**: specs/004-extraction-evaluation. **Branch**: member-d/extraction-evaluation.
**Current base**: initial documentation handoff, not the runnable foundation.
Read the [scope decision](../../decisions/initial-documentation-handoff.md) and
[working-copy guide](../working-copies.md) before starting.

## Responsibility and paths

Owned paths: services/extraction/**, eval/** except the explicit member-a/b/c annotation paths, docs/extraction-eval/**, specs/004-extraction-evaluation/**.
See the [complete matrix](../allowed-paths.md). Member annotation paths override D's parent
ownership. Read shared context freely; do not edit another owner or canonical contracts
independently. Submit shared proposals to B and wait for agreement.

## Read in order

1. [Root instructions](../../../AGENTS.md) and [constitution draft](../../../.specify/memory/constitution.md).
2. [Original prompt](../../../prompts/NoteLens_Codex_SpecKit_prompt_00.md) as requirements context,
   not as authorization to rerun setup or implement all workstreams.
3. Your [spec](../../../specs/004-extraction-evaluation/spec.md),
   [plan](../../../specs/004-extraction-evaluation/plan.md) and
   [tasks](../../../specs/004-extraction-evaluation/tasks.md).
4. [Draft contracts](../../../contracts/v1/README.md), [open decisions](../open-decisions.md)
   and [your start prompt](../start-prompts/member-d.md).

## Select the feature in your own clone/worktree

PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/004-extraction-evaluation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Git Bash on Windows:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/004-extraction-evaluation
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Expected: FEATURE_DIR selects specs/004-extraction-evaluation, regardless of branch name.
No package install, provider key or other complete module is needed for this path check.

## Inputs and outputs

- **Inputs**: ExtractionRequest / DocumentQuestionRequest containing unchanged canonical text; versioned module outputs for evaluation.
- **Outputs**: ExtractionResult, English evidence-linked summaries/document answers, proposed annotation/reference/QA records and shared measured reports.
- **Canonical source**: contracts/v1/schema.json and its referenced OpenAPI proposal.
  These remain draft; B coordinates freeze and generated bindings.
- **Failures**: English safe shared errors for invalid/unsupported input, timeout,
  rate/provider/configuration problems and insufficient evidence. Partial document support
  must remain usable when literature is weak. Follow code-point evidence and hash rules.

## Illustrative payload

**Example type**: ExtractionResult.
This is a documentation example, not a running mock, real measurement or completed module.
Mode mock identifies its illustrative nature. No provider/service was called.

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "doc_id": "illustrative-document",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "items": [
    {
      "entity_id": "illustrative-entity",
      "type": "symptom",
      "name": "chest pain",
      "assertion": "suspected",
      "temporality": "unknown",
      "subject": "unknown",
      "evidence": [
        {
          "start": 22,
          "end": 46,
          "quote": "Chest pain is suspected."
        }
      ]
    }
  ],
  "summary": {
    "language": "en",
    "text": "The text includes a suspected mention of chest pain.",
    "claims": [
      {
        "claim_id": "illustrative-claim",
        "text": "The text includes a suspected mention of chest pain.",
        "scope": "document_fact",
        "source_ids": [
          "illustrative-document-source"
        ]
      }
    ],
    "sources": [
      {
        "source_id": "illustrative-document-source",
        "kind": "document",
        "doc_id": "illustrative-document",
        "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
        "evidence": {
          "start": 22,
          "end": 46,
          "quote": "Chest pain is suspected."
        }
      }
    ],
    "evidence_state": "sufficient",
    "warnings": [
      "Synthetic illustration only; no extraction service was called."
    ]
  },
  "extractor_version": "illustrative-only",
  "prompt_version": "illustrative-only"
}
```

The shared text used for document-bound examples is synthetic. Its exact digest and evidence
interval were computed for the illustration; no clinical validation or real patient is implied.

## First ready action

D-001: draft entity/status/subject, exact-span, annotation and evidence-support instructions from the agreed requirements.
Begin with read-only inspection; ask for approval before the first concrete owned change
package. Do not automatically implement the entire backlog.

## First five-task sequence

| Alias | Local ID | Deliverable | Availability |
| --- | --- | --- | --- |
| D-001 | T001 | Draft annotation ontology, evidence rules and extraction interface proposals | May start as an approved inspection/proposal package. |
| D-010 | T002 | Create D's independent offline evaluation packages, fixtures and mock adapters | Wait for listed prerequisites; see tasks.md. |
| D-004 | T003 | Implement structured Python extraction and bounded semantic/span validation | Wait for listed prerequisites; see tasks.md. |
| D-005 | T004 | Generate English summaries and document answers with supported claims | Wait for listed prerequisites; see tasks.md. |
| D-002 | T005 | Select and freeze representative annotation assignment candidates | Wait for listed prerequisites; see tasks.md. |

The first audit/rule-drafting task can start without other complete modules. Later tasks remain blocked by their actual contract/scaffold/published-foundation prerequisites.
This is a five-task sequence, not a claim that five business tasks are immediately ready.

## Checks and honest status

The feature path check above exists now. Test/CLI commands in tasks.md are future acceptance
targets created by the named tasks and prerequisites. There is no service-start/npm script
available today. Mock checks, actual-module checks and separately authorized live checks
must be reported distinctly; do not close real tasks based on an illustrative payload.
English artifacts, the user's approved 60-minute/2-MiB/100,000-code-point policies, held-out
data protection and no paid calls without approval remain binding.
