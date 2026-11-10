# Separate Working Copies on Windows

**Scope**: the initial documentation handoff. All four members confirmed Windows.
PowerShell is primary; Git Bash commands below also target Windows.
Use one clone per person (recommended). Worktrees are an alternative for separate local
folders on one machine. Never run four active Codex sessions in the same checkout.

## Member mapping

| Member | Clone/folder | Branch | Feature | Prompt |
| --- | --- | --- | --- | --- |
| A | notelens-member-a | member-a/rag | specs/001-rag | [Start](start-prompts/member-a.md) |
| B | notelens-member-b | member-b/platform | specs/002-platform | [Start](start-prompts/member-b.md) |
| C | notelens-member-c | member-c/classification | specs/003-classification | [Start](start-prompts/member-c.md) |
| D | notelens-member-d | member-d/extraction-evaluation | specs/004-extraction-evaluation | [Start](start-prompts/member-d.md) |

The public remote is https://github.com/NemanjaManic/notelens.git.
Use your own Git identity and account; repository creation by A does not transfer B's scope.

## PowerShell: clone and branch (example for A)

Run from a parent directory where the target folder does not already exist:

```powershell
git clone https://github.com/NemanjaManic/notelens.git notelens-member-a
Set-Location -LiteralPath notelens-member-a
$handoffBase = @(git rev-list --max-parents=0 origin/main)
if ($handoffBase.Count -ne 1) { throw 'Expected one initial documentation commit; ask B for the correct base.' }
git switch --create member-a/rag $handoffBase[0]
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

The single root commit identifies this initial documentation base without embedding a
self-referential hash inside its own files. This is not the later runnable-foundation base.
B/C/D use their own folder, branch and feature from the table, not A's values.
Each member handoff contains its exact feature-selection commands.

Expected output: FEATURE_DIR points at the chosen feature. BRANCH in resolver output is a
feature-context label; confirm the real branch with git branch --show-current.
The local feature state file must stay ignored; setting NO_PERSIST avoids rewriting it.

## Git Bash on Windows: clone and branch (example for A)

```bash
git clone https://github.com/NemanjaManic/notelens.git notelens-member-a
cd notelens-member-a
handoff_base="$(git rev-list --max-parents=0 origin/main)"
git switch --create member-a/rag "$handoff_base"
export SPECIFY_FEATURE_DIRECTORY=specs/001-rag
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

PowerShell scripts are what this integration installs. Exporting Bash variables alone does
not install Bash variants of Spec Kit. Git Bash can call the Windows powershell.exe shown
above. Linux/macOS workflows were not selected or verified for this team.
If a local execution policy blocks scripts, review the scripts and ask for an approved
process-scoped solution; do not change machine-wide policy as an onboarding shortcut.

## Optional worktrees

From a normal user-owned clone, after fetching origin/main, use distinct local folders.
Do not reuse a branch already checked out in another worktree.

PowerShell:

```powershell
git fetch origin
$handoffBase = @(git rev-list --max-parents=0 origin/main)
if ($handoffBase.Count -ne 1) { throw 'Ask B for the correct documentation base.' }
git worktree add -b member-a/rag ../notelens-member-a $handoffBase[0]
git worktree add -b member-b/platform ../notelens-member-b $handoffBase[0]
git worktree add -b member-c/classification ../notelens-member-c $handoffBase[0]
git worktree add -b member-d/extraction-evaluation ../notelens-member-d $handoffBase[0]
```

Git Bash:

```bash
git fetch origin
handoff_base="$(git rev-list --max-parents=0 origin/main)"
git worktree add -b member-a/rag ../notelens-member-a "$handoff_base"
git worktree add -b member-b/platform ../notelens-member-b "$handoff_base"
git worktree add -b member-c/classification ../notelens-member-c "$handoff_base"
git worktree add -b member-d/extraction-evaluation ../notelens-member-d "$handoff_base"
```

Each worktree has separate ignored feature state but shares Git object storage. Open Codex
in the specific worktree folder, set that member's feature variables and use that member's
prompt. Choose the clone path or the worktree path; do not run both examples on the same
already-used branch/folder.

## Staying coordinated

Read-only inspection and source/interface proposals can begin on this documentation base.
Before business integration, B must coordinate the agreed contracts and later runnable
foundation. Record that later immutable base separately. On an existing member branch,
fetch and merge the reviewed main update before work that depends on it:

```powershell
git fetch origin
git merge origin/main
```

Resolve any conflict only with the responsible owner. Do not reset or force-push to hide it.
The global F-014 task in the current backlogs refers to the later runnable foundation and
stays open after this documentation release.

When a member has approved owned work to publish, use a separate PR from their branch;
do not directly push module changes to main. This guide does not grant future commit/push
or paid/deployment approval; each session follows its explicit package authorization.
