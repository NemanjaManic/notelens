# F-010: B-Owned Ownership Checks and Key-Free CI Plan

**Prepared:** 2026-11-16. **Owner/story:** B / US3. **Task:** foundation T010 / F-010.
**Status:** scoped local implementation delivered after separate user approval.
Full F-010 remains pending routing identities/access and authorized hosted/settings evidence.
**Baseline:** `60b2b27986649e230f90723693c4e05b88e8891a` on
`member-b/task-f-004-web-workspace`.
**Dependency:** technically completed F-004/T006. F-010 does not depend on F-011.
**Pending:** T010/F-010 itself, T007/F-011 and T014/F-014 remain unchecked.

This supplements the existing [foundation plan](../../specs/000-foundation/plan.md)
and [F-010 task](../../specs/000-foundation/tasks.md). The initial planning change
added this document only. The later approved implementation is recorded below.
Existing drafts, owner files and frozen/generated contracts remain preserved; only
the scoped T010 progress note changes a feature artifact, with every checkbox
unchanged. No repository setting, collaborator message, commit, push or hosted
workflow execution is activated by this local delivery.

## Summary and current evidence

Implement a small local declared-scope checker, honest review-routing preparation
and Windows key-free CI around checks that already exist. Match the
[allowed-path matrix](../team/allowed-paths.md), including the member annotation
exceptions. Keep declared ownership distinct from authenticated identity or approval.

At the committed baseline `.github/` contained its ownership guide, with no CODEOWNERS
or CI workflow, and `check_scope.py` did not exist. Prior regression evidence covered 111 B
tests, A/C/D 319/51/59 service tests, web checks, 30 shared module HTTP exchanges and
54 F-012 cross-runtime cases. These are local key-free results, not hosted CI results.

F-011 currently reports 148 passed, 50 C missing-health-route outcomes and 12 blocked
cases; all 10 owned processes stopped. Its default exit is 1/incomplete. Do not weaken
that result or substitute the passing 30-case F-004 module smoke for F-011 or F-005.
F-005 still requires completed F-011/F-012; F-006/F-013/F-007/F-014 retain their graph.

## Technical context and proposed paths

- Python 3.13 tooling, standard-library Git/path/JSON handling and existing unittest.
  Existing web checks use Node 24/npm 11 and the unchanged root npm lock.
- Windows/PowerShell only for initial CI, matching the existing process-containment
  implementation. Propose `windows-2022` and the locally verified Python 3.13.7,
  Node 24.22.1, npm 11.19.1 and uv 0.13.7; hosted compatibility must be measured.
  An explicit Windows label is supported by GitHub's
  [runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- Propose `pip-audit==2.10.1` in B's tooling environment for Python advisory queries,
  with a reviewed B-only lock update. No owner environment receives this tool and no
  owner lock is regenerated. No other new Python framework is proposed.
- Store local scope/security metadata under ignored `.cache/review/f010/`; never
  accept submitted documents, persist credentials or scan arbitrary external paths.
- Finite test/job deadlines are verification controls, not application SLOs, provider
  budgets, session/history limits or runtime retry/rate policies.

Candidate implementation paths, all B-owned:

| Path | Deliverable |
| --- | --- |
| `scripts/project/check_scope.py` | Read-only declared-scope CLI and `--self-test` entry point. |
| `scripts/project/tests/test_scope.py` | Meaningful ownership, Git-diff and malformed-input regressions. |
| `.github/scope-policy.json` | Explicit machine-readable rules with provenance to the allowed-path matrix. |
| `.github/pull_request_template.md` | One structured scope declaration, affected owners and actual checks/review evidence. |
| `.github/CODEOWNERS` | Routing preparation with no fabricated identities or misleading active entries. |
| `.github/workflows/key-free-ci.yml` | Key-free regression/security checks and a separately labeled optional health diagnostic. |
| `scripts/project/check_ci.py` | Secret/dependency checks, safe summaries and CI policy checks. |
| `scripts/project/tests/test_ci.py` | Negative security/report/CI-policy cases without live advisory calls. |
| `scripts/project/pyproject.toml`, `scripts/project/uv.lock` | B-only pinned audit dependency and reviewed resolution changes. |
| `scripts/project/scaffold_inputs.json` | Add approved B sources/configuration; retain original B snapshot and owner/frozen pins. |
| `docs/team/f-010-review-routing.md` | Local/PR usage, identity gaps, bootstrap and branch-protection instructions. |
| This plan; `specs/000-foundation/tasks.md` | Actual evidence and scoped status only after implementation. |

The exact future file count is subject to diff review; this is not permission to add
unlisted shared root files. No owner service/test/lock, data/eval, root/web dependency
or contract change is proposed. Reuse existing process helpers without editing them.

## Constitution check, before and after design

| Gate | Design assessment |
| --- | --- |
| Ownership / most-specific exceptions | Pass: exact rules, owner-local changes, unlisted paths rejected for review. |
| English artifacts / 2026-11-24 delivery | Pass; no language, scope or deadline change. |
| Frozen records / provenance | Pass: validators and pins retained; no new wire schema or service algorithm. |
| Privacy / key-free work | Pass for design: synthetic tests, no provider secrets, metadata-only reports. |
| Costs / external actions | Pass for planning: no CI execution, paid runner, deployment or account activation. |
| Honest evidence / real acceptance | Pass: declared scope, local tests, hosted runs and human approval stay distinct. |
| Workflow / preservation | Pass: official setup/resolver used without replacing foundation artifacts or feature state. |

No constitutional exception is proposed. Missing GitHub identities/access, hosted
verification and settings activation remain explicit later gates, not invented facts.

## Phase 0: research decisions

**Ownership source.** Use the committed allowed-path matrix as authority. A small
explicit JSON policy records its source Git-blob digest and equivalent path rules;
tests detect missing rows, mismatched owners and annotation precedence drift. Do not
use Git author names or branch prefixes as identity. A blanket B-owned root wildcard
and a self-asserted `approved=true` declaration are rejected alternatives.

**Review routing.** Prepare CODEOWNERS with comments describing the complete A/B/C/D
mapping until actual handles and repository write access are verified. Do not emit
`@A`, guessed handles, or empty-owner override lines. After verification, broader
patterns precede annotation exceptions. GitHub uses the last matching pattern and
the target branch's CODEOWNERS; eligible owners need write access. Enforcement
requires repository rules, not merely the file. See
[GitHub's CODEOWNERS rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

**CI trust boundary.** Use `pull_request` plus optional `workflow_dispatch`, minimum
read permissions, ephemeral hosted runners and no persisted checkout credentials.
No `pull_request_target`, privileged artifact follow-up, OIDC, secret inheritance,
deployment or self-hosted runner is needed. Pin actions to verified full commit SHAs
at implementation, recording upstream references rather than inventing hashes.
This follows GitHub's
[workflow security guidance](https://docs.github.com/en/actions/reference/security/secure-use)
and [untrusted PR guidance](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target).

**Dependency coverage.** Use `npm audit` and PyPA pip-audit rather than assuming an
ecosystem-independent GitHub dependency graph covers every locked Python environment.
Query public advisories only for package names/versions; report network failures or
unrecognized coverage as incomplete. Audit tools do not repair locks. The proposed
Python pin and no-resolution mode are documented by
[PyPA](https://github.com/pypa/pip-audit/tree/v2.10.1); npm documents JSON reports and
nonzero vulnerability outcomes in its
[audit reference](https://docs.npmjs.com/cli/commands/npm-audit/).

**Cost/activation.** Propose only standard public-repository hosted runners. GitHub
documents their compute as free, but actual repository visibility/settings and any
artifact/storage implications must be verified before activation. No larger runner,
paid add-on or assumed spending allowance is included. See
[GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage).

## Phase 1: scope model and CLI design

These are internal tooling interfaces, not additions to frozen `contracts/v1`.

| Record | Minimal fields and invariant |
| --- | --- |
| Scope policy | Format version, source path/blob digest, explicit path-to-member rules; exactly A/B/C/D. |
| Declaration | Format version, one declared member, task alias and exact repository-relative changed paths; no glob approval. |
| Change | Git status, old/new paths and modes, owner(s); deletion uses old path and rename checks both sides. |
| Scope report | Base/head or staged fingerprint, policy digest, case/rule IDs, path/owner findings, result; no whole PR body. |
| CI report | Source/run identity, executed checks, exit/coverage/cleanup metadata and pending gates; no raw bodies or tokens. |

Designed commands, now implemented for local verification:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scope.py --self-test
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scope.py --member B --staged --declaration .cache/review/f010/scope.json
```

CI supplies full base/head object IDs and a declaration parsed from the event file,
not shell-expanded PR text. Proposed range mode is `--member B --base <sha>
--head <sha> --declaration <file>`; the actual member comes from the declaration.
Verify object existence and use merge-base-to-head coverage with NUL-delimited Git
records. Missing history, invalid objects or malformed declarations fail explicitly.
Decode Git paths as UTF-8 and write UTF-8/LF metadata; reject invalid encodings rather
than interpreting path bytes through a Windows legacy code page.
Local staged mode reads the index without staging, resetting or touching draft files.

Enforce these rules:

1. Require a nonempty valid declaration, unique exact paths and a recognized member.
   Every actual changed path must be declared; stale extra declared paths also fail.
2. Resolve most-specific ownership. D's `eval/**` must not absorb A/B/C annotation
   files. Include services, owner docs/data/specs, shared configuration and global
   Spec Kit paths. Expand root-file categories explicitly, with no catch-all owner.
3. Reject absolute/traversal/ambiguous paths, case collisions, unexpected diff status,
   unapproved symlink/submodule modes and unmapped new root files. Never follow a
   changed symlink to scan or write an external location.
4. Check both ends of renames and copies, deletions and mode-only changes. A rename
   across owners does not become authorized by its destination. An ordinary member
   declaration grants no cross-owner implementation rights.
5. Report cross-owner coordinated packages as requiring B/affected-owner review;
   do not add a blanket override. Document how a separately approved, exact-scope
   coordinated import is reviewed before its trusted policy/authorization is updated.
   A declaration cannot create the required approval evidence.
6. Protect the frozen canonical/generated contract bundle. B ownership alone is not
   approval to alter it. Preserve the supplied prompt and current protected/owner
   hashes throughout this implementation; future contract changes use their existing
   separate review/version process.

Return 0 only for a valid evaluated scope, 1 for violations/incomplete evidence and
2 for invalid CLI usage. A self-test pass proves checker behavior, not a real PR's
identity, authorization or reviewer acceptance.

Use trusted target-base policy/checker code for the scope guard, before executing
head scripts or installing head dependencies. Validate any proposed policy changes
against that base. If the target base predates this tooling, report
`BOOTSTRAP_REVIEW_REQUIRED`; do not silently trust head policy. The first installation
requires maintainer review. Once established, changes to the guard/workflow/policy
remain B review items. Without protected repository rules and verified identities,
this remains a declared-scope aid, not proof against a malicious contributor.

## Secret and dependency checks

`check_ci.py` should expose explicit `--secrets`, `--dependencies` and `--self-test`
modes. Keep deterministic self-tests offline; label advisory queries as online.

The secret guard reads tracked/candidate Git blobs, including new commits in the
reviewed range, so deleting a credential before the final head does not conceal an
earlier addition. Inspect private-key blocks, recognized credential patterns and
forbidden secret-file names; `.env.example` is a specific permitted example file,
not a bypass for credential contents. Do not scan unrelated ignored/untracked drafts.
Print only path, rule ID and safe location metadata; never matching text. Build
synthetic negative fixtures in ignored temporary storage. Any false-positive exception
must be exact, reviewed and content-bound; do not add broad test/doc exclusions.
This finite guard is not a claim of universal secret detection or history cleansing.

For dependencies, preserve all existing owner/root locks and install only with their
locked commands. Audit npm's locked package tree without `audit fix`. Read installed
distribution metadata through each service's own interpreter and B's tooling
interpreter; export exact external package name/version pairs to ignored files for
`pip-audit --no-deps --disable-pip`. Do not import the service apps for this inventory.
The local `notelens-contracts==1.0.0`, owner service packages and private npm workspace
code are separately source/schema validated, explicitly listed as local coverage,
not queried as public packages. Reject unexpected skipped external packages or
incomplete result sets.

Propose failing on any reported advisory; do not add severity exemptions or suppress
findings to get green. Report advisory service failures separately from vulnerability
findings. No automatic dependency fix, owner lock refresh or paid security integration
is part of this package. Record tool versions, dependency inventories and advisory
query time; changing advisory data is not a deterministic regression result.

## CI lanes and result semantics

Propose one Windows regression workflow with clear check names, per-PR concurrency
and bounded execution. Read the PR event as data; checkout without persisted
credentials and do not interpolate titles, bodies or branch names into shell code.
Verify source/policy before setup, use locked setup, then run existing checks:

| Lane | Planned checks | Meaning |
| --- | --- | --- |
| Declared scope / secret guard | Scope self-tests, actual PR scope and candidate/range secret checks. | Path/declaration validation and finite secret checks, not human approval. |
| Key-free regressions | Full scaffold runner/verifier plus F-012 checker; new checker regressions join B discovery. | Existing scaffold/module and cross-runtime behavior only. |
| Dependency audit | Locked setup plus npm/Python external-package advisory checks. | Online dependency findings, separately labeled from offline tests. |
| F-011 health diagnostic | Explicit opt-in mock-only dispatch; run the unchanged all-service health command. | Nonzero remains failed/incomplete; never a successful foundation check. |

PR regressions do not require running the known-incomplete health diagnostic.
An unexecuted health lane is labeled pending/not run, never passed. When explicitly
run, preserve the health command's exit code, `passed`/`complete` flags and coverage;
no `continue-on-error`, unconditional success or snapshot count allowance may turn
it green. The current 148/50/12 counts explain the baseline, not a new acceptance
threshold. There is no CI input that selects live mode or supplies a provider key.

The initial automatic smoke coverage is the existing 30-case module HTTP suite.
F-005's UI input-to-answer startup/smoke is still unavailable; add it only after that
task is separately delivered. Current owner guards stay 319/51/59 until a separately
reviewed import changes them. Preserve job containment and port-cleanup checks; do
not bypass them if hosted Windows behaves differently from the local machine.

Package setup and advisory queries need network access; mock execution remains
key-free with scrubbed provider/corpus/index settings and existing loopback guards.
Those Python guards are not an OS firewall. Bootstrap no models, datasets or indexes.
Do not restore dependency caches from untrusted PRs or publish arbitrary cache/log
trees. Publish only allowlisted, schema-checked metadata summaries; free-form service
output, environments, PR bodies and submitted content are excluded.

Hosted execution and branch settings are later authorized actions. A manual workflow
must be available on the default branch to be dispatchable; a feature-branch file
alone does not prove it can run. See GitHub's
[workflow event rules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).
No hosted pass or enforced branch protection is claimed from local YAML checks.

## Implementation order and verification guide

All steps below are proposed B / US3 work after separate implementation approval:

1. Freeze an exact working-file/draft/protected/owner snapshot. Implement the explicit
   ownership policy, scope CLI and self-tests; read actual base/index Git records.
2. Prepare PR declaration/routing documents and comment-only CODEOWNERS while handles
   remain unverified. Record missing bindings/access as routing pending.
3. Implement secret checks, dependency inventory/audit handling and their offline
   negative tests. Review the B-only pip-audit lock change before use.
4. Add the pinned-action Windows workflow and static policy checks. Validate minimum
   permissions, event types, no live/secret input, action pins, safe data handling and
   non-masked health failure. Review actual YAML acceptance when hosted testing is
   authorized; a limited static guard is not a full GitHub workflow interpreter.
5. Add only the approved B files to the scaffold inventory. Preserve frozen/owner pins,
   the original B input snapshot and earlier verification provenance. Record this
   package separately; do not generalize the inventory to permit arbitrary edits.
6. Run scoped negatives, full relevant regressions and a normalized proposed-tree
   inventory check; record actual commands, failures and limits. Keep task markers
   pending wherever routing/hosted proof is absent. Review before any commit/push.

Required scope cases include all A/B/C/D boundaries, each annotation exception,
unknown root paths, missing/stale/duplicate declarations, staged versus committed
differences, cross-owner rename/copy, deletion/mode changes, Unicode/spaced paths,
missing history, forbidden symlinks/submodules and head-policy tampering. Use isolated
Git repositories under `.cache/review`; never stage/reset the user's index for tests.

Required CI/security negatives include forbidden credential names/content with safe
diagnostics, secrets removed in a later commit, untracked draft preservation, missing
audit packages, malformed/offline advisory results, unexpected skips, writable token
permissions, mutable action references, privileged PR events, shell-expanded PR input,
stale evidence and attempts to label incomplete F-011 coverage as passing. Test real
finite process cleanup through the existing helpers; do not invent a passing count.

After the new commands exist, from the repository root:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scope.py --self-test
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --self-test
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --secrets
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --dependencies
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_scaffold_checks.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scaffold.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_unicode.py
```

The actual declaration check also needs explicit staged or base/head input as above.
The original planning step ran none of these implementation checks; the separately
approved execution and actual outcomes are recorded below. No hosted job was run.

## Completion limits and pending decisions

Local delivery requires passing meaningful checker tests, actual candidate scope
evaluation, unchanged protected/owner files, reviewed dependency results and passing
existing regressions. Hosted CI requires an actual authorized run and retained
metadata for the exact published commit. Human review is separate from either.

Automatic review routing additionally needs verified A/B/C/D GitHub bindings with
write access and an accepted CODEOWNERS on the target branch. Enforcement needs
separately authorized repository rules and observed required checks. Until then,
the routing guide is preparation and F-010 must not be reported fully complete.
No collaborators, handles, approvals, licensing policy or administrative access are
inferred. These gaps do not prevent local implementation of the B-owned checkers.

F-011 owner updates are separate packages, reviewed and imported only with their
applicable authorization. F-014 remains pending through the remaining foundation
acceptance/checkpoint/publication gates. Nothing here accelerates business tasks past
their dependencies, changes retention/upload limits or moves delivery from 2026-11-24.

## Actual planning workflow and preservation

Applied the installed [speckit-plan skill](../../.agents/skills/speckit-plan/SKILL.md)
as a scoped F-010 supplement. The repository integration remains pinned to Spec Kit
1.3.3. Research/design/validation details are consolidated here instead of replacing
the existing foundation research, data model, plan, contracts or quickstart. No
feature creation, task regeneration, global CLI reinstall or subagent was used.

Executed the committed official Windows scripts with explicit foundation context:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/000-foundation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
$env:SPECIFY_INIT_DIR = 'D:/Work/SITA/Capstone'
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/setup-plan.ps1 -Json
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks -Template plan-template
```

`setup-plan.ps1` detected the existing foundation plan and skipped the copy. The
resolver selected `specs/000-foundation` and returned the composed plan template;
its logical feature label does not change the actual Git branch. The existing
requirements checklist is 16/16 checked. Pre/post extension hooks are absent.
No persistent `.specify/feature.json` was created. This is scoped planning evidence,
not execution of the full foundation implementation or human acceptance.

Official-source research is linked beside the decisions it supports, checked on
2026-11-16. Local resolver/template and preservation evidence is saved under ignored
`.cache/review/f010-plan/`. The preservation audit passed: all 308 baseline files,
16 existing drafts (including the three F-011 messages), 72 protected files and 57
imported owner files are unchanged, with only this new plan added. Local links,
source inventory, the existing scaffold receipt and feature-state preservation were
checked. Existing implementation suites were not rerun for this documentation change.
Git HEAD/upstream remain at `60b2b27`, the actual index remains unchanged, and
F-010/F-011/F-014 remain unchecked. No implementation, message sending, commit or
push is part of this package.

## Approved local implementation and observed checks

Checks executed on 2026-11-16; execution record finalized on 2026-11-17.

Implemented the 14-file B-owned package against parent `60b2b27`: scope/CI checkers and
regressions; explicit policy, PR template, comment-only CODEOWNERS and pinned workflow;
B tooling dependency/lock and inventory updates; this execution record, routing guide
and unchecked T010 progress note. The 16 pre-existing drafts remain outside the package.
No owner service, owner lock, root/web dependency, frozen record or original B input
snapshot changed. The B lock adds 27 audit packages and preserves all 32 existing
external package entries byte-for-byte at the parsed record level.

The workflow uses the JSON subset of YAML for strict standard-library parsing. Its
bounded policy validates full action pins, read-only permissions, exact trusted guard
scripts, checkout history/credential controls, guard ordering, locked setup and health
exit propagation. Mutating the scope call into a self-test cannot pass that guard.
This is not a general GitHub workflow interpreter or proof of hosted acceptance.
No additional parser dependency, cache upload or live-provider input was introduced.

| Executed check | Observed result |
| --- | --- |
| Scope regressions | 25 tests; A/B/C/D areas, annotation exceptions, real isolated Git ranges/indexes, rename/copy/deletion/modes, non-BMP paths, malformed declarations, policy tampering and bootstrap behavior. |
| CI/security regressions | 29 tests; secret diagnostics/history, advisory coverage/failures, local package origins/module bytes, workflow privileges/action pins/order and unmasked health failures. |
| Full scaffold runner | All 15 steps passed; 165 B tests; A/C/D 319/51/59 with no failures/errors/skips; web typecheck/build/bindings/config/render and 30 module HTTP cases. All 12 module processes stopped and ports closed. |
| Default scaffold verifier | Exit 0 with a current-source/current-runtime receipt. |
| F-012 dedicated suite | 54/54 Python/TypeScript cases and test typecheck passed; its source/artifact hashes remain current. |
| Workflow static guard | Exit 0; hosted verification remains false. |
| Secret guard | Committed HEAD passed; the exact new candidate is additionally checked through an isolated index without staging the real branch. |
| Online dependency audit | Exit 1: npm, B tooling, C and D clear; A's `chromadb==1.5.9` has reported vulnerabilities. No finding was suppressed or repaired. |

The first advisory attempt exposed a B inventory gap: installed local service packages
were being queried as public dependencies. The correction accepts only each exact
owner pyproject name/version with its own environment, metadata and direct source URL;
every installed Python source module must match the owner source. The generated
contract package retains its separate source/schema checks. Four regression tests
cover editable/wheel provenance and source drift. No arbitrary name-prefix exception
or external-package skip was added. The final audit covers five environments: 59 B
tooling, 105 RAG, 41 C and 41 D external distributions, plus npm's package tree.

The RAG finding was confirmed by the 2026-11-16 query of
[PyPI's metadata for chromadb 1.5.9](https://pypi.org/pypi/chromadb/1.5.9/json): aliases
include CVE-2026-45829, CVE-2026-45830, CVE-2026-45831 and CVE-2026-45833. Multiple
GHSA/PYSEC records refer to these same issues; they are not eight distinct findings.
The returned metadata declared no fixed versions. This requires A-owned assessment
and a separately reviewed dependency decision. B did not change A's lock, activate
a real index/model/provider or make a claim about exploitability in the mock path.
The dependency lane remains failing until an appropriate owner-maintained resolution;
that outcome is not a checker failure or a full F-010 pass.

Actual final commands were the documented checker modes, full scaffold runner/default
verifier and F-012 checker. Advisory results are online package-metadata measurements;
the 54 new checker regressions are deterministic offline cases. Earlier receipts are
archived under `.cache/review/f010-implementation/`; current source-bound dependency
results are in `.cache/review/f010/dependencies.json`, with official advisory IDs in
`chromadb-advisories.json` under the implementation directory. No broad cache/log
artifact was published. Another checkout must execute its own checks.

The execution used the scoped
[speckit-implement skill](../../.agents/skills/speckit-implement/SKILL.md), the official
foundation prerequisite resolver with no persistent feature state, the existing 16/16
requirements gate and no extension hooks. No other feature task was executed or
checkbox closed. F-010 remains partial for the dependency finding, identities/access,
routing and hosted/settings evidence. F-011/F-014 remain pending. The final scope and
preservation audit is saved in `.cache/review/f010-implementation/result.json`.
No actual-branch staging, commit, push, merge, colleague message or repository-setting
change is part of this execution.
