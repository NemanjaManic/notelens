# F-010 review routing and key-free CI rollout

## Review routing

The proposed CODEOWNERS file maps the existing allowed paths to verified GitHub
collaborators with write access. The first account is the path owner. The
second can review the owner's own PR. The allowed-path matrix still controls
write scope. For a PR from a different author, request the affected primary
owner's review. No catch-all owner is assigned. Annotation-specific entries
follow the broad evaluation entry because GitHub applies the last match.

GitHub reads CODEOWNERS from the target branch. On a pattern with multiple
accounts, approval from either listed account satisfies GitHub's code-owner rule.
Keep affected-owner agreement for coordinated changes in the review record.

## Checks

The proposed **NoteLens key-free CI** workflow runs **NoteLens key-free checks**
on PRs targeting `main`. The trusted target checkout runs the declared-scope
and secret-history checks before the candidate executes. The Windows job uses
a read-only token, pinned actions, no checkout credential persistence and no
provider credentials. It installs the default locked Python and npm
environments, verifies frozen contracts and generated files, checks public
dependency advisories, builds the web workspace, and runs the F-005 smoke.

The PR dependency profile accepts changes to owner source while validating
installed package origins and checking for source drift during the audit.
The separate checkpoint profile still checks its pinned source inventory.
The hosted job uses the default RAG dependencies. Its evidence excludes the
optional indexing extra, which remains subject to A's dependency review.

For local checks with dependencies already installed, run from the root:

```powershell
uv run --locked --offline --directory scripts/project python -B check_scope.py --self-test
uv run --locked --offline --directory scripts/project python -B check_ci.py --self-test
uv run --locked --offline --directory scripts/project python -B check_ci.py --workflow
uv run --locked --offline --directory scripts/project python -B check_ci.py --pr-dependencies
uv run --locked --offline --directory scripts/project python -B check_contracts.py --require-freeze
uv run --locked --offline --directory scripts/project python -B generate_contracts.py --check
npm.cmd run build
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

The dependency audit queries public registries. uv's offline option applies
to startup of the installed checker. Use the exact changed paths in the
PR's `notelens-scope` block. The trusted guard rejects cross-owner, frozen
contract and ownership-policy changes under its normal profile. Agree the
maintainer procedure for authorized coordinated changes before requiring the
status check. The workflow and its validator changes require independent review.

## Activation and evidence

1. Review and merge F-005 so the smoke entry point exists on `main`. Review the
   exact F-010 change and merge it by an independently approved PR.
2. Check automatic CODEOWNERS requests and a successful **NoteLens key-free
   checks** run from GitHub Actions on an ordinary review PR targeting
   `main`. Record the exact check context, base/head and run URL.
3. Ask the repository admin to configure branch protection for `main`.
   Require a PR and at least one approval, code-owner review, dismissal of
   stale approvals, resolved conversations, and the verified GitHub Actions
   check with an up-to-date branch. Apply the rules to administrators and
   disable force pushes and deletion. Keep merge commits available for
   reviewed checkpoint publication.
4. Verify the effective settings and review enforcement. Record F-010
   completion only after the hosted and routing evidence is available.

[GitHub CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
and [GitHub protected branch settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
describe the hosting behavior.
