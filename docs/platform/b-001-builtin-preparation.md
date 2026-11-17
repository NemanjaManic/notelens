# Early B-001: built-in preparation core

Owner: B. Task: specs/002-platform/T003 / B-001, **pending**. Date: 2026-11-17.
Baseline: `c4a20ce37ba1164f34624e0867b6361419cf4deb`.

## Explicit execution-order exception

The user approved the bounded early B-001 built-in preparation core before full
B-004/F-014. This exception authorizes this server-side core and its independent
checks only. The original dependencies remain for full B-001 acceptance. It does
not extend the earlier B-004/B-002 exceptions to uploads, browser/session transport,
service integration, paid activation or deployment. B-001/B-002/B-004/F-010/F-011/
F-014 remain pending. No commit or push is authorized by this implementation.

## Scope and source of truth

`canonicalText` implements B's application preparation step, independently of the
unchanged F-012 test helper. It requires a primitive string, rejects lone UTF-16
surrogates, replaces CRLF/CR with LF, then applies NFC once. It preserves spacing,
repeated text and a leading BOM rather than trimming/reordering the content. Blank
or whitespace-only text is rejected. Both raw and canonical text must fit the
approved 100,000 Unicode code-point limit; canonical expansion beyond the limit and
oversized raw input that would shrink under NFC are rejected without truncation.
This helper establishes neither language nor permission to accept submitted text.

`prepareBuiltin` admits only eight fixed IDs from the versioned synthetic document
fixtures. It accepts no raw document, source metadata, language declaration, path,
caller document ID or digest. Prototype/path-like and unknown IDs fail before a
preparation ticket is allocated. The examples remain synthetic: their existing
`synthetic_text` source and frozen fixture language-policy declaration are preserved,
not relabeled as licensed third-party reports or a new English detection result.

For an available server-owned session capability, preparation starts a B-004 ticket
before reading/validating/preparing the selected example. The frozen example is
runtime-validated, then its text is prepared into a new record with a fresh opaque
UUID and UTF-8 SHA256 over canonical text. Metadata comes only from the validated
fixture. The fresh PreparedDocument passes the generated validator and is handed to
MemorySessions, which validates/snapshots it independently. These validations do not
normalize or alter the prepared text downstream.

The same ticket/deadline spans all preparation and validation. There is no TTL reset
at storage. Session teardown or expiry makes the operation unavailable, including
when validation crosses the deadline. After awaiting storage, the function checks
current session/document availability before returning a receipt containing only
`kind` and `docId`. The canonical document is obtained through the existing guarded
session lookup; no body, capability, hash or upstream exception is echoed in a
rejection. No input/body is logged or persisted to disk. Versioned synthetic
fixtures remain permitted repository assets, read via a static JSON import.

Each successful preparation creates a fresh document identity, even for the same
example/text in one session. The prior fixture ID and digest are not trusted as the
new submission's identity/hash. The digest is recomputed and checked against the
frozen text in tests. The B-004 memory core is unchanged. Pending tickets contain no
document content and retain B-004's existing absolute timeout cleanup if preparation
fails; no new session capacity, retry or lifetime policy is invented.

## Verification

Used the installed speckit-implement workflow for platform T003 only, with the
official PowerShell prerequisite resolver, explicit specs/002-platform and
nonpersistent selection. Quality checklist: 16/16; no extension hooks. Existing
plan/model/research, frozen definitions and approved retention/input constraints
govern this increment. No regeneration, delegation or additional dependency install.

```powershell
node apps/web/scripts/check-preparation.mjs
```

The standalone no-install coordinator runs local TypeScript NodeNext/noEmit and 47
synthetic tests using Node's existing runner. It requires the installed local
generated binding, matching protected/source hashes, fresh process output/nonce,
complete case counts/critical IDs and no skipped/cancelled/todo cases. Metadata-only
evidence is saved under ignored `.cache/review/b001-preparation/`.

Cases cover literal normalization outcomes, scalar validation, preserved BOM/spacing,
code-point versus UTF-16 boundaries, raw/NFC-expanded size rejection, all eight
allowlisted examples, fresh identities and frozen metadata, cross-session access,
absolute expiry, teardown/restart, storage rejection and late preparation completion.
Two isolated mutations are detected: delaying ticket creation until after fixture
validation, and omitting the final availability check. A copied unmodified control
runs all 47 cases successfully. Probe code explicitly reads/writes UTF-8 so non-BMP
case data survives the Windows test-copy path. Evidence is under
`.cache/review/b001-early/`; full regression/preservation results follow there after
execution. F-012 and all pre-existing test files stay unchanged.

## Deferred acceptance

This core is not wired to the public fixture viewer, cookies, routes, uploads or
browser sessions. Browser ownership must come from a separately reviewed server
transport before any submitted content is accepted. No arbitrary English/non-English
text is admitted as PreparedDocument, and no English detector, translation, OCR,
PDF parsing, HTTP service call or generated medical output is introduced. The 2 MiB
PDF gate remains B-001's later input work. Actual process restart, full frontend
lifecycle and browser integration remain separate from the simulated session tests.

No history/rate/timeout/retry/budget or operational defaults are selected here.
The new documents library, its tests/config/checker, this scope record, T003's
exception note and scaffold inventory are the only intended changes. Original
snapshots, owner/frozen pins, earlier provenance, existing UI and all drafts are
preserved. All six named gates stay pending, as does the known A chromadb finding.
