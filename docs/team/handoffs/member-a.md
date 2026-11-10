# Member A: Python RAG

**Feature**: specs/001-rag. **Branch**: member-a/rag.
**Current base**: initial documentation handoff, not the runnable foundation.
Read the [scope decision](../../decisions/initial-documentation-handoff.md) and
[working-copy guide](../working-copies.md) before starting.

## Responsibility and paths

Owned paths: services/rag/**, data/knowledge/**, docs/rag/**, specs/001-rag/**, eval/annotations/member-a/**.
See the [complete matrix](../allowed-paths.md). Member annotation paths override D's parent
ownership. Read shared context freely; do not edit another owner or canonical contracts
independently. Submit shared proposals to B and wait for agreement.

## Read in order

1. [Root instructions](../../../AGENTS.md) and [constitution draft](../../../.specify/memory/constitution.md).
2. [Original prompt](../../../prompts/NoteLens_Codex_SpecKit_prompt_00.md) as requirements context,
   not as authorization to rerun setup or implement all workstreams.
3. Your [spec](../../../specs/001-rag/spec.md),
   [plan](../../../specs/001-rag/plan.md) and
   [tasks](../../../specs/001-rag/tasks.md).
4. [Draft contracts](../../../contracts/v1/README.md), [open decisions](../open-decisions.md)
   and [your start prompt](../start-prompts/member-a.md).

## Select the feature in your own clone/worktree

PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Git Bash on Windows:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/001-rag
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Expected: FEATURE_DIR selects specs/001-rag, regardless of branch name.
No package install, provider key or other complete module is needed for this path check.

## Inputs and outputs

- **Inputs**: RetrievalRequest / LiteratureAnswerRequest with an English question, optional concept names and soft specialty hint.
- **Outputs**: RetrievalResult / AnswerResult with attributable literature passages, versions, English claims and explicit evidence limits.
- **Canonical source**: contracts/v1/schema.json and its referenced OpenAPI proposal.
  These remain draft; B coordinates freeze and generated bindings.
- **Failures**: English safe shared errors for invalid/unsupported input, timeout,
  rate/provider/configuration problems and insufficient evidence. Partial document support
  must remain usable when literature is weak. Follow code-point evidence and hash rules.

## Illustrative payload

**Example type**: RetrievalResult.
This is a documentation example, not a running mock, real measurement or completed module.
Mode mock identifies its illustrative nature. No provider/service was called.

```json
{
  "schema_version": "1.0.0",
  "mode": "mock",
  "state": "insufficient",
  "passages": [],
  "retriever_version": "illustrative-only",
  "index_version": "not-built",
  "score_note": "Illustrative payload only; no retrieval or measurement was performed."
}
```

The shared text used for document-bound examples is synthetic. Its exact digest and evidence
interval were computed for the illustration; no clinical validation or real patient is implied.

## First ready action

A-001: inspect permitted MedlinePlus sources and write an acquisition/provenance proposal.
Begin with read-only inspection; ask for approval before the first concrete owned change
package. Do not automatically implement the entire backlog.

## First five-task sequence

| Alias | Local ID | Deliverable | Availability |
| --- | --- | --- | --- |
| A-001 | T001 | Audit permitted corpus sources and prepare snapshot acquisition/provenance | May start as an approved inspection/proposal package. |
| A-010 | T002 | Review RAG boundary proposals and local mock consumer checks | Wait for listed prerequisites; see tasks.md. |
| A-002 | T003 | Implement English XML parsing, cleaning and stable attributed passages | Wait for listed prerequisites; see tasks.md. |
| A-003 | T004 | Implement embedding/store adapters, versioned index ingestion and cache boundaries | Wait for listed prerequisites; see tasks.md. |
| A-004 | T005 | Expose an embedding-only retrieval baseline with valid source records | Wait for listed prerequisites; see tasks.md. |

The first audit/rule-drafting task can start without other complete modules. Later tasks remain blocked by their actual contract/scaffold/published-foundation prerequisites.
This is a five-task sequence, not a claim that five business tasks are immediately ready.

## Checks and honest status

The feature path check above exists now. Test/CLI commands in tasks.md are future acceptance
targets created by the named tasks and prerequisites. There is no service-start/npm script
available today. Mock checks, actual-module checks and separately authorized live checks
must be reported distinctly; do not close real tasks based on an illustrative payload.
English artifacts, the user's approved 60-minute/2-MiB/100,000-code-point policies, held-out
data protection and no paid calls without approval remain binding.
