# C Review of the F-004 Candidate

**Date:** 2026-11-16
**Owner:** Sara / C
**Reviewer:** Coding agent assisting C; human owner approval is not asserted here.
**Shared candidate:** `8282a739727f3c696be8b63d5c1c13ea13ae81fc`
**Imported classifier source:** `df842f928d8b856aa404afa00893415511ab1cd1`

The shared F-004 candidate passed the complete coordinated mock checks and the
current-checkout evidence checker on my machine. The classifier source and lock
in that candidate match my published classifier commit.

The review used Windows, Python **3.13.7**, Node **v24.20.0**, npm **11.19.0**
and uv **0.13.7** in a detached worktree at the exact candidate commit. After the
locked setup described in the candidate runbook, the following commands both
returned exit code 0:

```powershell
$env:UV_PYTHON_DOWNLOADS = 'never'
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_scaffold_checks.py
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_scaffold.py
```

Results from the successful run:

- Frozen contracts: **155/155** fixture outcomes and **22/22** simulated correlation outcomes; generated bindings matched.
- Shared project tests: **80 passed**. RAG, classifier and extraction: **319, 51 and 59 passed**, respectively, with no failures, errors or skips.
- Installed service binding checks, web typecheck, build, configuration and local render passed.
- **30/30** real loopback Node-to-Python HTTP cases passed, including the eight classifier scenario/document cases and invalid-ID case. All **12** test processes stopped and their ports closed.
- The runner recorded a current-source receipt and all **15** steps passed. The source fingerprint was `31b04fb8cfd695ca652967f969d3110ee0217b0e9484cc36e1463673384e52ac`.

Earlier attempts encountered a classifier startup timeout and a shared unit-test
timeout. The unchanged runner subsequently completed: its 80 shared tests took
142.048 seconds in the successful run. I retained the earlier diagnostics locally;
no test deadlines were changed. The classifier and extraction suites emitted the
known Starlette TestClient deprecation warning during the candidate run.

## Follow-up in C's working copy

After reviewing the shared candidate, I updated my classifier's **development**
dependencies to add `httpx2==2.16.0`, which Starlette uses for TestClient. The
existing `httpx==0.28.1` remains for the separate asynchronous privacy test.
The classifier `pyproject.toml`, `uv.lock` and README changes are available on
`member-c/classification`; they are not part of the shared candidate or the receipt above.

With the updated lock, all **51 classifier tests passed** on both Python **3.11.9**
and **3.13.7**, with Starlette deprecation warnings treated as errors. The installed
Python bindings also passed **153/153** payload outcomes and **22/22** simulated
correlation outcomes on Python 3.13.7. No classifier runtime source or shared
contract was changed by this follow-up. D owns any corresponding extraction change.

Please record the shared F-004 completion decision and provide the exact shared
base and any integration instructions when available. C-009 is not automatically
complete from this review, and C-002 still requires completed C-009 and the reviewed,
published F-014 base. The checks above cover key-free mocks; they do not establish
trained model behavior or F-014 completion.
