# Local F-004 Candidate Runbook

This candidate combines unchanged service files from A `24c2b6d`, C `df842f9` and
D `36ea2a1` with B's 22-file web input snapshot. Full commit hashes, source bytes,
support-file inventory and B input/output distinctions are in
[scaffold_inputs.json](../../scripts/project/scaffold_inputs.json).

No Git merge, commit or push was used to assemble it. This is a local F-004 verification
candidate, not the F-014 published foundation or F-005 shared report/startup flow.
The original main checkout and its drafts are preserved.

The approved B input snapshot remains unchanged in the manifest. Next's type generation
and production build replace development declaration imports with production imports in
the candidate's `apps/web/next-env.d.ts`; that exact generated output is recorded separately
as `b_generated_outputs`. Other B input changes are limited to the approved checker/tests.
Unexpected edits to the generated declaration still invalidate verification.

The inventory requires every listed input, including both editable B verifier files.
Additional Markdown files beneath `docs/` are preserved and excluded from this package's
fingerprint. Listed documentation remains pinned; unexpected code/configuration or
non-Markdown files are still rejected. This permits the existing B design/handoff drafts
to coexist without importing, deleting or changing them.

Use separate service environments, unchanged uv locks, the unchanged root npm lock and
the frozen generated packages. Known toolchain: Windows, Python 3.13.7, Node v24.22.1,
npm 11.19.1, uv 0.13.7. Setup may download development packages; no provider/model
activation, real corpus/index or personal report is needed. A's full tests build only
temporary synthetic fixtures/vectors, using the imported A test helper. D's service
tests use its imported synthetic training checker/examples. The eval workspace is excluded.

After explicit setup with `uv sync --locked` for each of `services/rag`,
`services/classifier`, `services/extraction` and `scripts/project`, and clean root
`npm.cmd ci`, run from this candidate's repository root:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_scaffold_checks.py
if ($LASTEXITCODE -ne 0) { throw 'Candidate verification failed; inspect .cache/scaffold logs.' }
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scaffold.py
```

The runner installs nothing. It checks canonical freeze/generation, B tests, all three
owner service suites, installed bindings in each service, web typecheck/build/render and
30 real Node-to-Python module HTTP cases. It scrubs inherited credentials/configuration,
uses mock modes and a Python loopback-only network guard, and stops only its own temporary
module processes. No submitted input is accepted; only public/synthetic fixtures are used.
Test harness deadlines are not application timeout/retry/rate/history policy.

Each verification command starts behind an assignment gate in its own Windows job.
The coordinator stops the job on completion, failure, timeout or interruption and checks
that it is empty; loss of the coordinator closes the non-inherited job handle and stops
its descendants. Assignment failure stops verification before the command can start.
This uses [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
only for finite checks, with no shared development supervisor or global process cleanup.
The HTTP receipt must contain all 12 expected service/scenario cleanup records, including
positive process IDs, stopped processes and closed ports; partial/duplicate coverage fails.

Full verification requires a current-source, current-runtime receipt with complete case
coverage, exact owner test counts (319/51/59), unchanged imported/frozen bytes and hashed
logs/artifacts. The default checker does not install or start services. `--web-only`
keeps its separate B-only meaning. Missing/stale/partial evidence fails rather than
being inferred from file presence. Local receipts do not authenticate human acceptance.

Actual command logs, machine-readable receipt, service XML results, HTTP cases and process
cleanup records are under ignored `.cache/scaffold/`. Read them for observed outcomes;
this source guide does not fabricate a checked integration commit or deployment URL.

Owner READMEs are preserved verbatim. Some refer to omitted owner documentation; use
their pinned upstream context rather than interpreting missing local owner docs as
permission to import unrelated data/evaluation/business work:

- [A source and owner documentation](https://github.com/NemanjaManic/notelens/tree/24c2b6d96fc00c7e2ffe5dcd63be57d72dc406ac/docs/rag).
- [C source and owner documentation](https://github.com/NemanjaManic/notelens/tree/df842f928d8b856aa404afa00893415511ab1cd1/docs/ml).
- [D source and owner documentation](https://github.com/NemanjaManic/notelens/tree/36ea2a1b59e382930daee7d088c883b0d103c619/docs/extraction-eval).

C's health endpoints are intentionally absent until F-011. Existing A/D health tests
do not complete global F-011. No Unicode preparation/highlighting implementation,
web-client routing/composition, upload/session controls, live model, semantic/clinical
benchmark, browser acceptance, shared startup or deployment is provided by this package.
F-005/F-011/F-012/F-014 and business tasks keep their existing dependencies.

Final delivery remains 2026-11-24. Publication, promotion to the main working copy and
colleague messages require their applicable authorization; no such action occurred here.
