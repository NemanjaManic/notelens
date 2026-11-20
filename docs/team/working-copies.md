# Separate Windows working copies

Use a separate clone or worktree for each member. Keep existing drafts in their
current checkout. The initial documentation checkpoint is historical. For the
runnable foundation, B shares the full reviewed SHA when F-014 publication is
authorized and verified. Get that SHA before using these onboarding commands.

## Member mapping

| Member | Folder | New example branch | Feature | Start prompt |
| --- | --- | --- | --- | --- |
| A | notelens-member-a | member-a/foundation-work | specs/001-rag | [A](start-prompts/member-a.md) |
| B | notelens-member-b | member-b/foundation-work | specs/002-platform | [B](start-prompts/member-b.md) |
| C | notelens-member-c | member-c/foundation-work | specs/003-classification | [C](start-prompts/member-c.md) |
| D | notelens-member-d | member-d/foundation-work | specs/004-extraction-evaluation | [D](start-prompts/member-d.md) |

The public remote is https://github.com/NemanjaManic/notelens.git. The examples
use A's row. Substitute the folder, new branch and feature from your own row.

## PowerShell

Set `$env:NOTELENS_FOUNDATION_SHA` to the full SHA supplied by B in your
current PowerShell session. Start from a parent directory with the target
folder available.

```powershell
$foundationBase = $env:NOTELENS_FOUNDATION_SHA
if ($foundationBase -cnotmatch '^[0-9a-f]{40}$') { throw 'Set the full reviewed F-014 SHA.' }
git clone https://github.com/NemanjaManic/notelens.git notelens-member-a
if ($LASTEXITCODE -ne 0) { throw 'Clone failed.' }
Set-Location -LiteralPath notelens-member-a
git fetch origin refs/heads/main:refs/remotes/origin/main
if ($LASTEXITCODE -ne 0) { throw 'Could not fetch NoteLens origin.' }
git merge-base --is-ancestor $foundationBase origin/main
if ($LASTEXITCODE -ne 0) { throw 'The supplied foundation is unavailable on origin/main.' }
git switch --create member-a/foundation-work $foundationBase
if ($LASTEXITCODE -ne 0) { throw 'Could not create the owner branch.' }
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

## Git Bash on Windows

Export `NOTELENS_FOUNDATION_SHA` in the current Git Bash session before
running this example.

```bash
foundation_base="${NOTELENS_FOUNDATION_SHA:-}"
[[ "$foundation_base" =~ ^[0-9a-f]{40}$ ]] || { echo 'Set the full reviewed F-014 SHA.' >&2; exit 1; }
git clone https://github.com/NemanjaManic/notelens.git notelens-member-a || exit 1
cd notelens-member-a || exit 1
git fetch origin refs/heads/main:refs/remotes/origin/main || exit 1
git merge-base --is-ancestor "$foundation_base" origin/main || exit 1
git switch --create member-a/foundation-work "$foundation_base" || exit 1
export SPECIFY_FEATURE_DIRECTORY=specs/001-rag
export SPECIFY_FEATURE_NO_PERSIST=1
powershell.exe -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -PathsOnly -Json
```

In either shell, confirm `git rev-parse HEAD` matches the supplied SHA,
`git branch --show-current` matches your working branch, and the resolver
reports your feature. The resolver's branch field labels the selected feature.
If Windows blocks the script, review it and use an approved process-scoped
PowerShell setting.

## Optional worktree

In your existing clone, verify `git remote get-url origin`, fetch
`origin/main`, and verify the same reviewed SHA is an ancestor of it.
Create the worktree from that checked SHA. Use a folder and branch name
that are free locally. This is A's example.

```powershell
git worktree add -b member-a/foundation-work ../notelens-member-a $foundationBase
```

```bash
git worktree add -b member-a/foundation-work ../notelens-member-a "$foundation_base"
```

Open the new folder and run the feature selection from the corresponding
shell example. Keep per-checkout state and local artifacts in ignored paths.

## Reconcile prior work and run the mock

Compare overlapping paths and review the owner changes before bringing prior
commits forward. Shared PRs can contain matching content with different
history. Preserve your original branch and drafts. Resolve shared conflicts
with the responsible owner.

Run the locked setup and smoke commands from the
[mock startup runbook](../platform/f-005-mock-startup.md). Read the
[checkpoint record](foundation-checkpoint.md) for the verified source and
publication status. Continue only the approved work with its actual
prerequisites met. Use an owner-scoped PR for any separately authorized
publication.
