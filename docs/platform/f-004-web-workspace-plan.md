# F-004: Member B Web Workspace Contribution

**Prepared:** 2026-11-13. **Owner:** B. **Story:** foundation US1.
**Task:** `specs/000-foundation/tasks.md` T006 / F-004.
**Status:** B-owned implementation approved and checked on 2026-11-14.
The user approved this concrete package and explicitly prohibited commit/push.
See [execution evidence](../../apps/web/README.md) for delivered files, commands and limits.
The proposal and inspection below record the original pre-implementation state.

This supplements the existing [foundation plan](../../specs/000-foundation/plan.md)
and [backlog](../../specs/000-foundation/tasks.md); it does not replace them, regenerate
feature artifacts, or create new task IDs. B's contribution can be checked independently.
Shared F-004 stays open until the required A/C/D contributions are also checked.

## Verified starting state

- Working branch: `member-b/task-contract-freeze-bindings`.
- HEAD: `fd1197bd380de9ba9037ea0b73b42031dc1d4bb2`; checked contract package:
  `aabbfc7844a8092194b4ab1cae561563e83ae13d`.
- `git ls-remote --heads origin` confirmed the freeze branch at HEAD and `main` at
  `e7bc839c0632c3db4fd3bcf7c38838c6da16070d`. The freeze package is not merged into main.
- Tracked files were clean. These six untracked files predate this proposal and must
  remain byte-for-byte intact and outside any later package staging:
  `docs/team/member-b-next-chat-handoff.md`, `member-b-reply-to-a.md`,
  `member-b-reply-to-c-p2.md`, `p2-revision-2-review-request.md`,
  `p2-revision-3-checkout-for-d.md`, and `p2-revision-3-reply-to-d.md`
  (all in `docs/team/`).
- The checked-out `apps/web` and three service directories contain only their AGENTS.md
  guides. Root `package.json`, root `package-lock.json`, `.env.example`,
  `apps/web/package.json` and `scripts/project/check_scaffold.py` are absent.
  `.gitignore` and `.gitattributes` already exist.
- F-001/F-002/F-008/F-003/F-009 are checked in the foundation backlog.
  F-004 and F-014 remain unchecked.

Read-only remote inspection fetched the three member branches without checkout or merge:

| Remote branch / inspected commit | Observed contribution | Limit of this inspection |
| --- | --- | --- |
| `rag` / `3ef5497b8b7d35204071751d231754d6f3d06629` | A has a Python scaffold, lock and tests. Its validator explicitly pins P2 RC1 revision 2, candidate commit `01e96ab6c6a676efb43073a2eca711e89e419030`. | Requires A's adaptation to frozen v1; no service tests/install were run here. |
| `member-c/classification` / `093e5478f3e938a7e909199fcac445d7666cef34` | Published service path contains AGENTS.md only; commit describes dataset audit/proposals. | No classifier scaffold was found in that committed service path; unpushed work is unknown. |
| `member-d/extraction-evaluation` / `cd8fc5ff15605abda17318f4b5f1e6f313d70702` | D has a Python scaffold, lock and tests. Its validator reads the checkout's schema directly; its manifest does not depend on the generated Python package. | Frozen-binding adaptation and runtime compatibility are unverified here. |

These observations do not assign colleagues new tasks or approve their implementations.
Do not merge entire member branches to obtain scaffolds: their shared-file changes need
separate review against the frozen base.

## Governing boundaries

Use the [allowed-path matrix](../team/allowed-paths.md),
[freeze decision](../decisions/contract-freeze.md), and
[binding guide](../../contracts/generated/README.md).
Later confirmed decisions override historical draft wording in the feature plans,
including their old coordinator exception for editing Python service scaffolds.

Canonical v1.0.0 remains unchanged. Schema SHA256:
`707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78`.
Preserve schema/API/fixture/freeze bytes, generated sources, existing package manifests
and locks, historical candidates, and the supplied prompt. Do not run the old candidate
builder on canonical v1. Import `@notelens/contracts/v1`; use its async runtime validators
rather than casting unchecked data or maintaining parallel record definitions.

A owns `services/rag/**`, C owns `services/classifier/**`, D owns
`services/extraction/**`, including their dependencies and locks. This package does not
edit, install into, replace, or implement those services.

## Proposed implementation package

After approval, create `member-b/task-f-004-web-workspace` from the verified HEAD,
preserving the drafts. Recheck HEAD/status first; investigate any change to the base
before proceeding. Apply the installed `speckit-implement` workflow only to B's part of
T006, with explicit foundation context and no persistent feature selection.

| B-owned path | Proposed deliverable and acceptance |
| --- | --- |
| Root `package.json`, `package-lock.json` | Private npm root with explicit workspaces `apps/web` and `contracts/generated/typescript`; reproducible root install/lock and web command forwarding. Exclude service projects and existing tooling consumers from workspace globs. |
| `apps/web/package.json`, `tsconfig.json`, `next-env.d.ts`, `next.config.ts` | Minimal Next.js App Router/TypeScript application; strict typecheck, dev/build/start scripts and explicit monorepo root configuration as required by the verified framework. No nested web lock. |
| `apps/web/src/app/layout.tsx`, `page.tsx`, `globals.css` | English scaffold shell, `lang="en"`, visible mock status and notices: educational demonstration, does not replace a doctor, and do not upload real personal medical reports. No submission controls or generated report/chat flow yet. Use local styles/system fonts without build-time remote asset fetching. |
| `apps/web/src/lib/scaffold/**` | Small, lazily loaded mock/configuration boundary using generated types. Exercise a runtime validator import in the actual Next build with an existing public/synthetic fixture. Keep this separate from later production clients/routing. No Python algorithms in TypeScript. |
| `.env.example` | Key-free scaffold settings, explicit mock mode, no secrets or live credentials. Live mode is unavailable and must fail explicitly rather than fall back to mocks. No invented provider, timeout/retry/history/rate/spend values. |
| `scripts/project/check_scaffold.py` and focused checker tests | Read-only scaffold checker with an explicit `--web-only` mode, path resolution from its own file, safe diagnostics and honest incomplete-service reporting. Reuse the existing B tooling environment; change its manifest/lock only if a demonstrated need arises. |
| `.gitignore`, `.gitattributes` | Inspect existing rules first; make only a demonstrated minimal addition for new local/build artifacts. Existing LF policy and supplied-prompt exception remain intact. No mass renormalization or repository-wide formatting. |
| `apps/web/README.md`, this proposal | Record exact dependency choices, setup/check commands, observed results and remaining shared gates after implementation. No task checkbox changes for partial delivery. |

The generated TypeScript package becomes a root workspace member without editing its
manifest, standalone lock or generated files. The web declares the local package at
version `1.0.0`; verify npm resolves it to this checkout, without registry substitution.
Existing standalone Python/TypeScript consumer environments and their locks stay intact.
The new root lock governs the web workspace install; it does not replace those locks.

Do not implement B-010's full malformed-result consumer suite, B-004 sessions,
B-001 uploads/canonical preparation, B-002 report panels/highlighting, or B-003 real
clients/routing in this package. A small build/import probe is F-004 compatibility
evidence, not completion of any of those tasks.

## Dependency evidence and installation gate

Observed locally: Node `v24.22.1`, npm `11.19.1`, Python `3.13.7`, local uv `0.13.7`.
Read-only npm registry queries on 2026-11-13 returned these candidates:

| Package | Candidate | Registry metadata / evidence limit |
| --- | --- | --- |
| Next.js | `16.4.6` | Node `>=20.9.0`; React/React DOM peers accept `^19.0.0`. |
| React / React DOM | `19.3.1` / `19.3.1` | React DOM requires React `^19.3.1`. |
| TypeScript | `7.0.2` | Node `>=16.20.0`; matches existing binding tooling, but Next integration is untested. |

[Next.js installation](https://nextjs.org/docs/app/getting-started/installation)
documents App Router setup and a minimum TypeScript 5.1.
[npm workspaces](https://docs.npmjs.com/cli/v11/using-npm/workspaces/)
documents local workspace linking.
The installed Node satisfies the declared minimums; this does not prove the candidate
combination builds. Registry metadata came from `npm.cmd view ... --json --cache .cache/npm`
for `next@latest`, `react@latest`, `react-dom@latest`, and `typescript@latest`.

Before installing, recheck exact candidate metadata and relevant official release/security
guidance. Pin explicit versions and compatible type packages; do not put `latest` in
manifests. Inspect installed Next documentation for the selected release during
implementation. Prove a clean locked install, generated ESM/JSON-import/Ajv resolution,
TypeScript checking, and a real Next production build on this Windows environment.
Do not bypass peer/type/build failures with force, legacy peer resolution, or disabled
typechecking. If a compatible web TypeScript version is needed, isolate that change to
the web package and root lock; preserve frozen binding files and report the evidence.

No application dependency installation, Next build or browser check was performed while
preparing this proposal. Registry/documentation access is not a provider/model call.

## Execution order and verification after approval

1. Read the implementation skill, check hooks/checklists, and resolve the existing
   foundation feature using the official script. Do not regenerate plans/templates.
2. Create the task branch from the checked base; add only the listed B-owned scaffold
   files. Install/pin the verified application dependencies locally and generate the root
   lock through npm. Preserve all pre-existing files outside the approved package.
3. Link the frozen workspace package and implement the small build/import probe and
   mock-only shell. Add only the configuration needed by this scaffold.
4. Implement the checker. `--web-only` must identify its scope in output and exit zero
   only for a passing B contribution. Default mode must check all required scaffold
   contributions and return nonzero for missing or incompatible contributions, never
   infer readiness from AGENTS.md or mere file presence. It must not install dependencies,
   launch services, call providers, or alter another owner's environment. Record actual
   owner-local installation/runtime checks separately before closing shared F-004.
5. Run a clean root `npm ci`, workspace typecheck/build, generated-package resolution
   and runtime import checks, plus a local shell render check with the Python services
   absent. Check notices and mock labeling; terminate only the web process started for
   that check. This does not create F-005's multi-process startup/smoke deliverable.
6. Re-run the freeze and generation drift guards. Review the diff for scope, unchanged
   draft hashes and unchanged frozen files; report B-only results and shared gaps.

The following are **proposed commands for files/scripts to be delivered**, not commands
available in the current checkout. Record exact successful invocations after creation:

```powershell
npm.cmd ci --cache .cache/npm --no-audit --no-fund
npm.cmd ls --workspace apps/web @notelens/contracts next react react-dom typescript
npm.cmd run typecheck --workspace apps/web
npm.cmd run build --workspace apps/web
& $contractUv run --locked --offline --directory scripts/project python check_scaffold.py --web-only
& $contractUv run --locked --offline --directory scripts/project python check_scaffold.py
```

Full scaffold verification is expected to report incomplete until owner contributions
are integrated and checked. Do not treat that expected shared failure as a B-only pass
or mark T006 complete. Add negative checker coverage for absent service files and invalid
workspace/package resolution so partial readiness cannot produce a shared pass.

## Checks actually executed for this proposal

The official prerequisite resolver was run successfully:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/000-foundation'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
```

It selected `D:\Work\SITA\Capstone\specs\000-foundation` and found research,
data-model, contracts, quickstart and tasks artifacts. This was existing-feature
resolution, not a new `speckit-plan` or `speckit-implement` execution. The project is
pinned to Spec Kit 1.3.3; the CLI version command was not rerun in this inspection.

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$contractUv = Join-Path (Get-Location).Path '.cache/tooling/Scripts/uv.exe'
& $contractUv run --locked --offline --directory scripts/project python check_contracts.py --require-freeze
& $contractUv run --locked --offline --directory scripts/project python generate_contracts.py --check
```

Both exited zero: 155/155 canonical fixture outcomes (69 positive/86 negative),
22 simulated correlation outcomes, recorded freeze consistency and reproducible
generated-binding match. No HTTP server was called. Human approvals remain the recorded
user-confirmed decisions, not approvals inferred by this inspection. The historical full
binding/unittest suites were not repeated for a documentation-only proposal.

## Remaining gates and definition of this contribution

F-003/F-009 satisfy the prerequisites for this owned F-004 contribution. A/C/D may
complete their owned scaffolds independently; real models/corpus/generation are not
required. Their existing backlog and ownership remain authoritative.

B-only completion requires reproducible installation, typecheck, Next build, local shell
render/import checks and an honestly scoped checker. It supplies no live/module-quality
evidence. Whole F-004 additionally needs all three owner-built independent services,
their manifests/locks and actual compatibility checks. F-011 health, F-012 Unicode
integration and F-010 follow completed F-004; F-005 follows F-004/F-011/F-012.
B-010 requires completed F-004. B-004 requires B-010/F-014; B-001/B-002 require
B-010/B-004/F-014; B-003 follows B-001/B-002. F-014 remains incomplete.

No new functionality/privacy/cost decision is needed for a shell with no submitted-input
path. Preserve the later approved limits: 2,097,152 PDF bytes, 100,000 Unicode code points,
server-memory-only submitted content for at most 60 minutes, no body logging, and no
silent truncation or translation. Real language/ambiguity validation, session controls,
provider/model/budget and operational limits stay behind their recorded later gates.
Final delivery remains **2026-11-24**; this proposal makes no schedule/capacity promise.

The user supplied the explicit new-package approval required by root AGENTS.md.
Commit/push/merge, deployment, paid activation and collaborator messages are separate
actions outside this proposal's authorization. No delegation is authorized.
