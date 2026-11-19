# F-010 First-main CI Bootstrap

**Owner** B. **F-010, F-011 and F-014 remain pending.**

## Ownership and declarations

The [allowed-path matrix](allowed-paths.md) remains authoritative. Its exact rules and
source digest are mirrored in [.github/scope-policy.json](../../.github/scope-policy.json).
The most-specific annotation path overrides D's parent `eval/**` ownership. Unknown
root/shared files require B review; there is no default root-owner wildcard.

The [PR template](../../.github/pull_request_template.md) requires exactly one fenced
`notelens-scope` JSON block with format `notelens-scope-v1`, `member` A/B/C/D, a stable
task alias and exact paths. Rename/copy declarations include source and destination.
The CLI checks path scope; it does not authenticate the person or prove approval.
Cross-owner work and changes to the ownership policy require separately recorded
B/affected-owner review. There is no PR-body approval flag or blanket B override.
Frozen contract/generated files and the supplied prompt retain their separate process.

## Stage-one scope

The first PR installs the guard on the documentation base
`e7bc839c0632c3db4fd3bcf7c38838c6da16070d` using B's published source
`98a0b1f799c444137e9297e3f99150ea211e558f`. Use a B-owned F-010 declaration
listing these exact additions:

| Path | Treatment |
| --- | --- |
| `.github/scope-policy.json` | Exact copy |
| `.github/pull_request_template.md` | Exact copy |
| `scripts/project/check_scope.py` | Exact copy |
| `scripts/project/scaffold_process.py` | Exact copy |
| `scripts/project/tests/test_scope.py` | Exact copy |
| `.github/workflows/key-free-ci.yml` | Guard-only workflow |
| `scripts/project/check_ci.py` | Guard-only workflow policy |
| `scripts/project/tests/test_ci.py` | Bootstrap policy regressions |
| `docs/team/f-010-review-routing.md` | Bootstrap procedure |

Keep the target's ownership matrix and frozen paths at their current bytes. Service
and web files, manifests and locks, CODEOWNERS, and checkpoint records are outside
this scope.

## Workflow and initial installation

The [workflow](../../.github/workflows/key-free-ci.yml) uses the JSON subset of YAML.
It runs on ordinary pull requests with read-only contents permission, a Windows
2022 runner and a 45-minute timeout. It uses pinned checkout and Python setup
actions and Python 3.13.7. The exact PR base and head go into separate `trusted/`
and `candidate/` directories with full history and disabled credential persistence.

The bootstrap gate requires both guard entry points in the target checkout. The
trusted step reads the PR event as data and runs target-base scope, secret history
and workflow-policy checks in that order. A failing check stops the job. An original
documentation base missing the guards stops with `BOOTSTRAP_REVIEW_REQUIRED`.
Record that result as non-passing. PR workflows and guard changes still require
review, including when repository rules provide no automatic enforcement.

## Local checks on Windows

Use Python 3.13.7 and Git in an isolated checkout. The guard and focused tests use
the Python standard library. Keep reports under ignored `.cache/review/f010/`.

```powershell
python -B scripts/project/check_scope.py --self-test
python -B scripts/project/check_ci.py --self-test
python -B scripts/project/check_ci.py --workflow
python -B scripts/project/check_scope.py --member B --staged --local-policy --declaration .cache/review/f010/declaration.json
python -B scripts/project/check_ci.py --secrets --staged
```

The last two commands use the prepared isolated index. Save the exact nine-path
declaration and verify the staged additions, the five source blob matches, the four
adapted blobs, and the existing matrix digest. The scope result carries
`local-policy-not-approval`. Normal PR checks use `--event` and target-base policy.

Once an exact reviewed head commit exists, scan the complete proposed range with
`python -B scripts/project/check_ci.py --secrets --base <full-base> --head <full-head>`.
The staged scan covers the proposed tree. The range scan also checks each intermediate
commit, including secrets removed later. Diagnostics include finding locations and
rule IDs. Keep the reports separate from configuration, credentials and local drafts.

Record the old-target stop and a successful trusted-base exercise on a synthetic,
declared B-owned change. Local tests and exercises provide technical evidence.

## Maintainer review and hosted proof

On the first PR, record exact base and head SHAs, the nine changed paths, guard and
workflow blob identities, local evidence and the workflow result if available. B
records technical review. Nemanja records separate human maintainer acceptance of
that exact candidate. Re-review a changed head or base. Recheck applicable repository
rules before separate publication authorization. If approved under the applicable
rules, use a PR merge commit to keep the reviewed head in the resulting ancestry.

After publication, record the resulting trusted main SHA, PR and merge references,
the reviewed head and the published guard, policy and workflow blobs. On a separately
authorized narrow PR with an exact B declaration, record the hosted run URL, target
and head SHAs and results of all three trusted checks. Hosted proof and reviewer
routing remain acceptance items for F-010.

PR #2 established trusted main at
`9cc4e8dbad60973984eaa1981e2073e087a26996`. The initial hosted run stopped at
`BOOTSTRAP_REVIEW_REQUIRED`. For the next narrow PR, verify the base and head
in the checkout logs, then record the scope, secrets and workflow outcomes in
order from the Trusted guard step.
[Merged PR #2](https://github.com/NemanjaManic/notelens/pull/2)

## Deferred lanes and policy transition

The bootstrap defers dependency advisories, service and web regressions and F-011
health checks. The existing dependency-audit command remains available in the
checker for the later full profile with its locked tooling and inventory.

Review the full workflow, trusted validator, tests and runbook as a separate
trust-policy transition. Record the expected result from the stage-one guard and
the agreed maintainer procedure before raising that PR. Review first-time frozen
and other-owner paths against their exact source pins with the affected owners.
The later runnable checkpoint still requires its own full dependency, scaffold,
web, service and acceptance evidence. F-011 and F-014 remain pending.
