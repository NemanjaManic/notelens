# F-010: Declared Scope, Review Routing and Key-Free CI

**Owner:** B. **Baseline:** `60b2b27986649e230f90723693c4e05b88e8891a`.
The local F-010 tooling is implemented. Full F-010 remains pending verified GitHub
identities/access, accepted routing and an actual authorized hosted run/settings review.
F-011 and F-014 remain pending. No branch rules or collaborators were changed.

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

## Local checks on Windows

Use the B tooling environment with the committed lock. The user-approved F-010 update
adds pip-audit 2.10.1 and its dependencies only to that environment; service locks and
root/web packages are unchanged. From the repository root after locked setup:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scope.py --self-test
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --self-test
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --workflow
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --secrets
```

`--secrets` scans committed HEAD. For a prepared index use `--secrets --staged`;
for a complete PR range use `--secrets --base <full-sha> --head <full-sha>`. Intermediate
commits are scanned so a credential removed in a later commit remains detectable.
Unrelated untracked/ignored drafts are not scanned or staged. Diagnostics never include
the matched secret. This finite pattern/file guard is not universal secret detection.

Prepare a declaration under ignored `.cache/review/f010/declaration.json`, with only
the actual intended files. These commands read an existing index; they do not stage:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scope.py --member B --staged --local-policy --declaration .cache/review/f010/declaration.json
```

`--local-policy` explicitly uses the checked-out policy for local review. The report
labels it `local-policy-not-approval`; this is not a trusted CI review. The current
implementation must be reviewed without staging the user's real index: use an isolated
review clone/index for candidate checks. Empty indices and stale declarations fail.
Reports go to `.cache/review/f010/scope-report.json`, separate from declaration inputs.

For normal committed ranges omit `--local-policy` and pass `--base`/`--head`; policy and
checker authority must come from the trusted target base. The workflow passes the PR
event file as data using `--event`; it never executes PR text as shell source.
Exit codes: 0 = evaluated scope passes, 1 = violation/incomplete, 2 = CLI usage error.

## Workflow and initial installation

The [workflow](../../.github/workflows/key-free-ci.yml) uses JSON-formatted YAML, parsed
strictly with Python's standard library for the supported policy checks. JSON is a
[subset of YAML](https://yaml.org/spec/1.2.2/#12-yaml-history). This avoids another parser
dependency; local policy validation does not prove GitHub accepted or executed it.

Only read-only contents permission, pinned first-party actions and standard Windows
2022 hosted runners are configured. Upstream v6 action targets were verified on
2026-11-16 using `git ls-remote` from their official repositories:

| Action | Full pin |
| --- | --- |
| [checkout](https://github.com/actions/checkout) | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| [setup-python](https://github.com/actions/setup-python) | `ece7cb06caefa5fff74198d8649806c4678c61a1` |
| [setup-node](https://github.com/actions/setup-node) | `249970729cb0ef3589644e2896645e5dc5ba9c38` |

The workflow checks out trusted base and candidate separately, disables credential
persistence/caches, and runs the base guard before candidate setup/code. If the target
base lacks the tooling, `BOOTSTRAP_REVIEW_REQUIRED` stops the run. This first package
needs real maintainer review before establishing the trusted base; it must not silently
substitute head policy. A proposed policy change similarly reports review required.
PR workflows themselves are reviewable code; this is not tamper-proof enforcement
without protected repository settings and review of guard/workflow changes.

The regression lane runs scope/CI self-tests, existing scaffold checks and F-012.
The existing 30-case HTTP suite is module smoke, not F-005's future UI flow. Dependency
audits are online queries of public package/version metadata; deterministic checker
tests are offline. No model, corpus, index or provider key is used.

`workflow_dispatch` offers one boolean, `run_health`, default false. The optional
health job runs `check_health.py --mode mock`; a nonzero result fails that job. It is
not masked by continue-on-error or converted to a passing foundation status. When not
run, F-011 is pending/unexecuted. Manual dispatch requires the workflow on the default
branch; this uncommitted feature work is not evidence of hosted readiness.

## Online dependency checks and evidence

After locked setup and inventory updates, run explicitly:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_ci.py --dependencies
```

The wrapper runs npm's non-fixing audit and pip-audit against exact installed external
versions from B's environment and each service's own interpreter. It does not install
audit tools in owner environments or regenerate their locks. The local generated
contract package and the three local owner service packages are source/origin checked
and reported separately. Service module bytes must match their pinned owner source;
an arbitrary local name or URL is not an audit exemption. Missing/skipped
external packages, malformed results and advisory failures cannot be reported green.
Any advisory fails the audit; no severity override, vulnerability exception or automatic
repair is applied. Findings require an appropriate owner-maintained follow-up.

Each command invalidates its prior success report before work and writes only safe
metadata to `.cache/review/f010/`. Dependency reports include query time and inventories;
results vary with advisory data. Raw audit command output is temporary and removed.
Do not upload arbitrary cache/log trees, credentials or document bodies to CI artifacts.
The implementation's snapshot/results are under `.cache/review/f010-implementation/`.

## Routing and completion limits

[CODEOWNERS](../../.github/CODEOWNERS) is intentionally comments only until actual
A/B/C/D handles and repository write access are verified. It neither invents accounts
nor creates automatic reviewers. After agreement, place broad patterns before the
annotation exceptions and protect `.github/` itself. GitHub uses the target branch's
CODEOWNERS; rules requiring reviews/status checks must be separately authorized and
observed. See [GitHub's rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).

Local agent checks, hosted CI execution and human/team acceptance are distinct.
Publication, repository settings, reviewer invitations and paid/live activation require
their applicable explicit authorization. No such action is performed by these tools.
F-010 is partial while those proofs are missing; F-011/F-014 stay open, and delivery
remains 2026-11-24.
