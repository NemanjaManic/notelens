# Member B: Frontend and Integration

**Feature**: specs/002-platform. **Branch**: member-b/platform.
**Current base**: initial documentation handoff, not the runnable foundation.
Read the [scope decision](../../decisions/initial-documentation-handoff.md) and
[working-copy guide](../working-copies.md) before starting.

## Responsibility and paths

Owned paths: apps/web/**, contracts/**, infra/**, .github/**, scripts/project/**, docs/platform/**, docs/team/**, docs/decisions/**, specs/000-foundation/**, specs/002-platform/**, root/shared configuration, eval/annotations/member-b/**.
See the [complete matrix](../allowed-paths.md). Member annotation paths override D's parent
ownership. Read shared context freely; do not edit another owner or canonical contracts
independently. Submit shared proposals to B and wait for agreement.

## Read in order

1. [Root instructions](../../../AGENTS.md) and [constitution draft](../../../.specify/memory/constitution.md).
2. [Original prompt](../../../prompts/NoteLens_Codex_SpecKit_prompt_00.md) as requirements context,
   not as authorization to rerun setup or implement all workstreams.
3. Your [spec](../../../specs/002-platform/spec.md),
   [plan](../../../specs/002-platform/plan.md) and
   [tasks](../../../specs/002-platform/tasks.md).
4. [Draft contracts](../../../contracts/v1/README.md), [open decisions](../open-decisions.md)
   and [your start prompt](../start-prompts/member-b.md).

## Select the feature in your own clone/worktree

PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/002-platform'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Git Bash on Windows:

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/002-platform
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

Expected: FEATURE_DIR selects specs/002-platform, regardless of branch name.
No package install, provider key or other complete module is needed for this path check.

## Inputs and outputs

- **Inputs**: Prepared documents and the agreed classifier/extraction/retrieval/answer records.
- **Outputs**: Canonical PreparedDocument and the complete English document/report/chat experience with preserved claim/source links. Real UI work is a later approved package.
- **Canonical source**: contracts/v1/schema.json and its referenced OpenAPI proposal.
  These remain draft; B coordinates freeze and generated bindings.
- **Failures**: English safe shared errors for invalid/unsupported input, timeout,
  rate/provider/configuration problems and insufficient evidence. Partial document support
  must remain usable when literature is weak. Follow code-point evidence and hash rules.

## Illustrative payload

**Example type**: PreparedDocument.
This is a documentation example, not a running mock, real measurement or completed module.
Mode mock identifies its illustrative nature. No provider/service was called.

```json
{
  "schema_version": "1.0.0",
  "doc_id": "illustrative-document",
  "text_sha256": "329f8b7de91dbd8671fda013973ca76abb355254624d2fd746e5cf4d66e41f3e",
  "text": "Demo 🩺\nNo chest pain.\nChest pain is suspected.\nNo chest pain.",
  "canonicalization_version": "nfc-lf-v1",
  "source": {
    "kind": "synthetic_text",
    "name": "Illustrative handoff text"
  },
  "language": "en"
}
```

The shared text used for document-bound examples is synthetic. Its exact digest and evidence
interval were computed for the illustration; no clinical validation or real patient is implied.

## First ready action

Review the draft contracts and collect A/C/D feedback for F-003; record proposals without pretending that freeze/fixtures are complete.
Begin with read-only inspection; ask for approval before the first concrete owned change
package. Do not automatically implement the entire backlog.

## First five-task sequence

| Alias | Local ID | Deliverable | Availability |
| --- | --- | --- | --- |
| B-010 | T001 | Review shared-record proposals and establish the web mock consumer suite | Wait for listed prerequisites; see tasks.md. |
| B-004 | T002 | Implement approved memory lifetime, session ownership and guarded configuration | Wait for listed prerequisites; see tasks.md. |
| B-001 | T003 | Implement built-in/text/PDF input and canonical preparation | Wait for listed prerequisites; see tasks.md. |
| B-002 | T004 | Build complete English report panels and exact evidence highlighting | Wait for listed prerequisites; see tasks.md. |
| B-003 | T005 | Implement thin service clients, source-preserving routing and bounded state | Wait for listed prerequisites; see tasks.md. |

B's immediate ready contribution is shared proposal review/coordination. The first platform implementation tasks remain gated; the user deferred UI/mock implementation during this initial handoff.
This is a five-task sequence, not a claim that five business tasks are immediately ready.

## Checks and honest status

The feature path check above exists now. Test/CLI commands in tasks.md are future acceptance
targets created by the named tasks and prerequisites. There is no service-start/npm script
available today. Mock checks, actual-module checks and separately authorized live checks
must be reported distinctly; do not close real tasks based on an illustrative payload.
English artifacts, the user's approved 60-minute/2-MiB/100,000-code-point policies, held-out
data protection and no paid calls without approval remain binding.
