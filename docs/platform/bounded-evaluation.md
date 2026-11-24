# Bounded whole-web evaluation

## Key-free dry run

From the repository root, use the locked Windows setup from the
[Windows readiness runbook](deployment.md) and build the production app.

```powershell
npm.cmd run build
if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_bounded_evaluation.py
if ($LASTEXITCODE -ne 0) { throw 'Bounded evaluation dry run failed.' }
```

The checker uses versioned synthetic fixtures and three authenticated local HTTP
doubles. It exercises the app's document submission, fitted-classifier response,
report, question and citation paths with live-shaped D and RAG responses. The
normal scenario exercises two unique sources, concurrent report requests,
reopens, a duplicate source in another session and a cited answer. Fresh
scenarios exhaust each HTTP ceiling and verify no excess request reaches a
service. An injected retryable HTTP 503 verifies that the queued literature
branch and subsequent answer attempts stay unsent. The dry run also checks the
single-use startup receipt and shuts down its owned listeners.

## Standalone bounded profile

For the frozen run, use the [operator runner](#operator-runner-and-output-capture)
so one watchdog owns all four processes. The standalone launcher owns the web
process for separately approved checks with services already running.

Use the approved config only after the team approves the system and
reference freeze and the complete provider execution scope. Keep it in the
approved restricted run directory. The local JSON has these required fields:

- `approved` set to true and a stable `run_id`.
- `services.rag`, `services.extraction` and `services.classifier`, each with the
  approved loopback `port` and expected `model_version`.
- `http_limits` with explicit nonnegative integer ceilings for `extract`,
  `document-answer` and `literature-answer`.
- `http_timeout_ms` with the approved time limit for a single web-to-service
  request, bounded by the one-hour document lifetime.

Start the pinned, independently bounded service instances. Set the three
service authentication tokens server-side using `NOTELENS_RAG_SERVICE_TOKEN`,
`NOTELENS_SERVICE_TOKEN` and `NOTELENS_CLASSIFIER_SERVICE_TOKEN`. Run the launcher
against the approved config:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/start_bounded_evaluation.py $approvedConfig
```

The launcher checks authenticated live readiness and the three expected model
versions, then starts one web process on loopback with its own labelled profile.
It claims the run once in the restricted config directory and preserves the
startup receipt even when startup fails. Preserve that receipt and the upstream
provider receipts when recording the outcome.

The app serializes D and RAG exchanges. It reserves an attempt before dispatch,
uses separate operation ceilings, and stops further dispatch after a failed
exchange or an attempt to exceed a ceiling. Partial and insufficient evidence
records can still be valid exchanges. Local classifier requests do not consume
the provider ceilings.

Extraction is attempted at most once per canonical text SHA-256 in the run.
The owning session's active document entry stores the in-flight and completed
result, so reopens, question turns and citation links reuse it. Use the original
document ID and owning session for other questions on that source. Resubmitting
the same source under a new ID cannot launch another extraction or access the
original session's result. Session expiry or deletion removes the report result.

These are app-to-service HTTP ceilings. D and RAG must independently enforce the
approved provider-call, token, cost and retry limits inside their services. A RAG
HTTP request can make several completion or embedding calls. The dry run verifies
the web dispatch controls and supplies no provider-spend or final-case evidence.

## Operator runner and output capture

Run the operator dry run after the production build. It creates its own synthetic
runtime ZIP and metadata manifest in a temporary directory and starts local HTTP
doubles. It verifies hash rejection, case and source capture, duplicate-source
reuse, stop-on-error behavior, deadline enforcement and checksum coverage.
The full-size exercise runs 26 synthetic cases across sessions and checks the
16-source extraction count and both answer ceilings.
The watchdog exercise uses three separately started loopback doubles and the
production web process. It stalls a RAG request across an eight-second deadline
and verifies four closed listeners, an empty Windows job, and a checksummed
timeout receipt with the completed output still present.

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_bounded_operator.py
if ($LASTEXITCODE -ne 0) { throw 'Bounded operator dry run failed.' }
```

For a separately approved run, build the production app at the exact clean app
revision. The operator runner starts all four components. Leave the configured
loopback service ports free. The approved config also supplies `operator`, `approved_by`,
`app_sha`, `runtime_manifest_sha256`, `service_pins` for `classifier`, `extraction`
and `rag`, `deadline_seconds` (1 through 3600), and the approved `document_scope`
(`synthetic` or `public`). Its HTTP ceilings must match the verified runtime
inventory. Obtain the approval file's SHA-256 from the freeze record. Choose a
new output directory under an existing restricted parent outside the checkout.

Add a `service_launch` entry for `rag`, `extraction`, and `classifier`. Each
entry provides `argv` (an absolute Windows executable followed by the exact
arguments), `cwd` (the absolute working directory), and `inherit_env` (the
names of any additional environment variables that component needs). Use the
approved service launch commands and loopback ports from the freeze. The
runner injects each service's bearer from its existing server-side environment
variable. Keep credentials out of the approval file and command arguments.

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/run_bounded_evaluation.py `
  --approved-config $approvedConfig --approval-sha256 $approvedConfigSha256 `
  --manifest $runtimeManifest --runtime-zip $runtimeZip --output $restrictedOutput
```

The manifest pins the runtime ZIP, each exact case version and runtime-entry
hash, and each canonical source hash. The ZIP carries `runtime-cases.json`,
its declared source files, and optional README and checksum files. Runtime
entries carry `case_id`, `case_version`, `question`, and `document_file`.
Case hashes are SHA-256 of the entry serialized as UTF-8 JSON, with the bundle's
key order, two-space indentation, literal Unicode and one trailing LF. Keep
scoring references in the separate custodian packet.

The runner submits each distinct source once and holds the app document IDs and
session cookies in memory. It records the app's classification, extraction and
structured answers. It follows the manifest route for each question, submits the
same frozen question to both branches for a mixed case, and exercises the app's
unsupported response for a case declared out of scope. For the operator's
bounded literature and shared mixed requests, the launcher supplies exact
UTF-8 SHA-256 values by route from the verified runtime packet. The app checks
canonical bytes and the usual size limits before accepting an exact reviewed
question. The public English admission rules and default demo remain the same.
The same monotonic deadline starts before service startup
and runs for at most 60 minutes. A Windows Job Object owns the web, RAG,
extraction and classifier process trees. At the deadline the watchdog
terminates that job, including descendants, while the operator writes the
final failure and checksum files. The receipt records whether the watchdog
triggered, whether the job drained, and which listeners closed. Service-side
provider limits and usage receipts still apply to work already dispatched.

Preserve the private `source-*.json`, `case-*.json`, `run-receipt.json`, and
`SHA256SUMS.txt`. They bind the saved results to the app and service pins, bundle
hashes, case versions and app-issued identities. A stopped run also retains
`failures.json` when a preflight, startup or case step fails. Completed outputs and any
returned partial result are retained when a service exchange fails. Case answer
records can contain cited excerpts. Keep them in the approved output directory
and preserve upstream raw provider receipts separately.

## Reviewed literature dispatch check

With authorization to use the restricted runtime-only packet offline, run this
check after the production build. The app submits questions in runtime order
against local doubles, with built-in synthetic documents anchoring the mixed
route. The receipt lists hashes and case identities. Keep the packet and
receipt in restricted storage.

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_reviewed_literature.py `
  --manifest $runtimeManifest --runtime-zip $runtimeZip `
  --hash-inventory $reviewedHashes --inventory-sha256 $reviewedHashesSha256 `
  --receipt $restrictedReplayReceipt
```
