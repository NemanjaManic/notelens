# D-009 A runtime and missing corpus artifact: v3 reconciliation

Prepared: 2026-11-24. Owner: Nemanja (A). Recipient: Goran (B).
Authority: the user relayed Goran's request to reconcile the A pin with the tested
whole-stack watchdog at `d846dcfee5a066dc180a59dbf0c1ed8888809f38` and privately
transfer the exact missing cleaned corpus file.

The new app pin supersedes `9fc7c333ca74971768e1df13ed6238798c48e90e` in the
existing launcher and policy template. No model, prompt, retrieval, dependency,
budget, token, timeout, retry or retention setting is changed. The existing
approval remains in force; no additional scope approval is requested.

## Exact private artifact

Extract the supplied artifact into the **A service checkout** at:

`data/knowledge/.cache/corpus/cleaned-topics.jsonl`

- Exact size: **2,631,848 bytes**.
- SHA-256: `2d12d44f9be4f09db3ebaeb969a0335beb621ded7cdb793ccbafdbbfc0658639`.
- Content: the existing 401-topic prepared public MedlinePlus corpus, unchanged.
- No evaluation questions, scoring references, credentials or new embeddings are
  included in that JSONL file. Do not reformat, normalize or regenerate it.

The file is inside the private v3 transfer ZIP with its repository-relative path.
It remains ignored locally and is not published to Git. The original artifact
and the historical ledgers remain unchanged. This package is prepared for the
approved private route; preparing it does not claim an external upload occurred.

## Reconciled pins

- App/watchdog commit: `d846dcfee5a066dc180a59dbf0c1ed8888809f38`.
- New A launcher SHA-256:
  `3a60beed0aceca76ebe9b425167dd412557c8ea4ec1c79f08f8cff4723a0a785`.
- Historical A selection-manifest SHA-256 remains:
  `d0502196edabc1301b06b55f2d1ddb1f888ac678b51502227d0f9a0fd5a67685`.
- B managed runner `scripts/project/run_bounded_evaluation.py` SHA-256:
  `bda439b7bb431031b897b26a7ff1b5e2fb33f158a878af5c23fc20f9b9804866`.
- B Windows job controller `scripts/project/scaffold_process.py` SHA-256:
  `112183e58bdaaa6256bbb38b17f65584b8b430a338035965f0289342f538849c`.

- Updated policy-template SHA-256:
  `ea2154c0d87e74245a6e14b8b14ae649496a4ad1e6772f9f918f5a7ea7d305de`.
Both historical v1/v2 archives remain unchanged.

The exact Git-object comparison found no `contracts/**` or `services/rag/**`
change between the two app commits. Source inspection confirms the new managed
runner uses a monotonic deadline, passes the corresponding deadline into the web
profile, owns the web and service descendants through a Windows Job Object, and
terminates/drains that job on the watchdog or exit. It preserves output and failure
receipts. Goran supplied the claim that this watchdog was tested; A's reconciliation
is source/pin inspection plus A's own key-free checks, not a repeated B browser or
whole-stack rehearsal.

## Operator actions for the existing approved attempt

Keep the B app checkout clean at the exact watchdog SHA. Place A's new module,
template and corpus artifact in its separate service checkout. The managed B
runner requires a clean app checkout; A's supplementary source overlay belongs
to the A checkout referenced by B's `service_launch.rag` configuration.

Update only these two pins in the existing private A operator policy:

```json
{
  "app_sha": "d846dcfee5a066dc180a59dbf0c1ed8888809f38",
  "launcher_sha256": "3a60beed0aceca76ebe9b425167dd412557c8ea4ec1c79f08f8cff4723a0a785"
}
```

Preserve its actual `run_id`, 16 question hashes, receipt path, pricing confirmation
and approval information. The distributed template is not a replacement for that
completed private policy. Do not overwrite or reset an existing attempt receipt.

Verify and run the existing key-free A preflight from the A checkout root:

```powershell
(Get-FileHash -LiteralPath './data/knowledge/.cache/corpus/cleaned-topics.jsonl' -Algorithm SHA256).Hash
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/.cache/final/approved-policy.json
```

The subsequent approved A service command remains:

```powershell
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/.cache/final/approved-policy.json --serve --port 8001
```

B's final operator entry point is the managed runner at the pinned commit:

```powershell
& ./scripts/project/.venv/Scripts/python.exe -B ./scripts/project/run_bounded_evaluation.py --approved-config $approvedConfig --approval-sha256 $approvalSha256 --manifest $runtimeManifest --runtime-zip $runtimeZip --output $finalOutput
```

Retain B's **3600-second** whole-stack deadline and **240000-ms** web timeout.
A still enforces 30 seconds per provider operation, USD 0.08, 16 embeddings,
48 generations and up to 48 input counts; the whole-system approved cap remains
USD 0.58 and 144 provider HTTP requests. No corpus re-embedding is authorized.
The scope is one pass, zero retries/repairs, first unexpected error or global
deadline stops dispatch, partial outputs and reservations preserved.

Final extraction F1 and independent semantic risk remain explicitly unmeasured.
No paid provider request or final-case access is needed for this reconciliation.

## Executed checks

The focused final-runtime, contract, answer and failure suite passed **100 tests**
after the pin update. Key-free CLI preflight verified all 56 unchanged historical
file pins and the 617-passage corpus with the new app SHA, approved scope,
30-second operations and zero provider calls. The distributed template still
reports `preflight_blocked` until Goran's private pricing confirmation and exact
16 question hashes are supplied; A does not replace his populated operator file.
The ZIP checksums and extracted corpus bytes are verified during packaging.
