# Proposed root README amendment for B

Status: concrete D-owned handoff for B integration, not an edit to the shared root README.
Inspected platform checkout: 710706af0dfff60d00708e051a1c3b45fb39cc3d.
The latest remote main was not fetched or assumed identical.

Replace obsolete documentation-only status with the actual selected demo state.
Distinguish default mock, indexed key-free RAG, configured live and saved replay.
Link docs/platform/f-005-mock-startup.md and docs/platform/b-005-rag-app-check.md.
For the default mock finite web smoke, after locked setup/build in that platform checkout:

```powershell
uv run --locked --offline --directory scripts/project python -B smoke_mock.py
```

Expected behavior from the existing checker: built-in/pasted synthetic document,
owner isolation, saved answer/history, citation pages, explicit gaps, fallback and shutdown.
These are expected checks, not a fresh pass: the local locked Python launch was blocked
by Windows Application Control before the app started.

For D's selected candidate use docs/extraction-eval/d005-coverage-candidate-handoff-v5.md:
service d41fa880177a7855bb92e57d98673b0a7a77d36b, quote_hints / coverage_v2 / low.
That guide supplies exact Windows commands and prompt hashes. Keep B's separate
pinned e61140d mock check distinct from the new candidate. Neither mock command
establishes a configured-live whole-web result.

Before publishing a live-demo command, B must confirm the actual joint launcher,
server policy, service URLs and pinned app commit. Do not publish keys or invent
an unsupported live launcher. Show one actually rendered model answer with exact
citation and an explicit evidence gap. Link its real receipt and execution trace.

Link the CAP evidence map and EV web plan/results. Say which outcomes remain pending.
Clean-checkout installation and one common demo commit for all members still require
verification on the selected joint configuration.
