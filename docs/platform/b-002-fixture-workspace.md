# Early B-002 fixture-only report workspace

Owner: B. Platform task: T004 / B-002, **pending**. Date: 2026-11-17.
Implementation baseline: `e6d070c5c0771dadd135ae6135fd472070d6af22`.

## Explicit execution-order exception

The user approved this bounded B-owned fixture UI before full B-004 and F-014.
This is a separate exception from early B-004. It permits presentation against
versioned synthetic fixtures and independent checks only. The existing B-004/F-014
dependencies remain requirements for full B-002 acceptance. B-002/B-004/F-010/F-011/
F-014 remain pending. No owner-service edit, frozen-contract change, paid activation,
deployment, commit or push is authorized. Existing design/state drafts are read-only
inputs and stay unmodified; no copy of a draft is staged as part of this package.

## Implemented UI and data boundary

The dynamic home page displays thirteen labeled fixture previews: overview, uncertain
or unsupported specialty, partial findings, independent summary/findings failures,
empty findings, a planned procedure, invalid result, failed call, loading illustration,
empty workspace and unavailable document. Native navigation links select allowlisted
states. Loading/failure/expiry previews are illustrations, not measurements or actual
service requests. Unknown/repeated query parameters do not inject a result or text.

The selected PreparedDocument is validated first; C and D result records then pass
through the B-010 mock consumer independently. Invalid extraction withholds its entire
findings/summary result; a valid classification remains usable. Independent extraction
and summary outcomes are displayed without filling failed sections. Uncertain and
unsupported classification never hides document support. Empty findings do not claim
the absence of conditions. All scores keep their supplied kind and limitation note.

Findings retain assertion, temporality and subject separately; procedure status is
shown explicitly. Summary claims retain their document source IDs and link to their
exact validated passage. Selected evidence is matched only against currently accepted
result passages. Unicode code-point slicing is explicitly converted into strings for
React rendering, preserving non-BMP characters, line breaks and repeated occurrences.
Invalid selection is ignored; scenario navigation clears the selection. Source text
and labels are escaped by React; no raw HTML is rendered. Upstream error messages
are not displayed. A hash link focuses the canonical document and highlights one
supplied passage; a clear-highlight action resets the selection.

The UI has visible mock/demo/not-a-doctor/no-real-personal-report notices. Desktop
panels use two columns; narrow screens use document-first reading order. Keyboard
skip/navigation links, focus outlines, named regions, headings, native score details
and textual state messages are provided. This is not a comprehensive accessibility
audit. The privacy copy distinguishes future submitted-document retention from these
versioned public fixtures, which may remain in the repository.

## Runtime and verification decisions

The negative frozen payload catalog contains intentionally invalid Unicode inputs.
Importing it as a Turbopack JSON module fails. It is preserved byte-for-byte and read
only on the Node server through fixed repository-relative catalog paths. Supported
local command working directories are the repository root and apps/web. No user
input controls that path, and submitted content is never written/read there.
Only reviewed mock fixture selections are exposed; the full catalog is not a client
input channel. The existing document fixtures are imported read-only.

No dependency, package, lock or global tool change is needed. The report test config
uses the installed TypeScript compiler to typecheck/emit JSX and rewrite .ts/.tsx
imports into a fresh ignored directory. Node and React's server renderer then run
37 synthetic model/render/evidence/security cases. The compiler may copy frozen
synthetic JSON fixtures into that ignored run directory; no submitted content is used.

```powershell
node apps/web/scripts/check-report.mjs
```

The coordinator checks the installed binding origin, current source/protected hashes,
fresh nonce/process output, exact counts/required case IDs and nonzero child exits.
Metadata-only evidence is under `.cache/review/b002-report/`. These checks do not
claim a hosted CI run or clinical correctness. The shared scaffold runner is run
separately, alongside B-010, early B-004 and F-012 regressions.

The installed speckit-implement workflow was scoped to T004 with the official
PowerShell prerequisite resolver, explicit specs/002-platform and nonpersistent
selection. Quality checklist: 16/16; no extension hooks. No regeneration or delegation.
The IDE-provided chrome-devtools CLI is used with its throwaway browser profile for
local browser verification; synthetic screenshots/evidence stay under ignored
`.cache/review/b002-early/`. No existing user browser/profile is used.

## Deferred acceptance

This package supplies no uploads/PDF/text input, browser-session authentication,
submission lifecycle/real expiry, service clients, routing/composition, question
controls, literature generation or live providers. The memory session core is not
wired to this public fixture preview. No operational timeout/history/rate/retry/
spending defaults are introduced. B-001/B-003 and full B-004/B-002 acceptance remain
their own work; the exception does not authorize them. No user-facing clinical-quality
claim is made. F-010/F-011/F-014 and the known A chromadb advisory remain open.

Only the existing home page/styles, the B-owned presentation/model/highlight modules,
their tests/checker/config, this scope record, T004's exception note and the scaffold
inventory are changed. Original snapshots, owner/frozen pins and prior provenance
entries are retained; the two shell paths gain narrow approved editable entries.
Final verification/preservation results are recorded in ignored
`.cache/review/b002-early/result.json` after the checks finish.
