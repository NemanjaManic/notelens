# Interim Main Checkpoint — Proposal for Owner Review

**Prepared by:** D (Milica)\
**Date:** 2026-11-18\
**Status:** Review proposal only. No owner acceptance, merge authorization, F-011 closure, or F-014 closure is implied.

## 1. Purpose and boundary

This proposal asks A, B, and C to review whether a narrowly scoped, key-free mock integration snapshot can be promoted to `main` before the full runnable-foundation checkpoint is complete.

An interim main checkpoint would be a **reviewed integration snapshot** for shared development and reproducible mock checks. It would not mean:

- F-011 health/readiness acceptance is complete;
- F-014 runnable foundation is complete or that remote working copies are ready for business implementation;
- any owner’s business task is complete;
- real-data, human, clinical, production, deployment, or live-provider acceptance;
- permission to change another owner’s files or to merge, commit, or push.

The project records F-014 as requiring its own reviewed checkpoint and separate commit/push authorization. This proposal does not replace those gates. Until the team resolves the questions below and the user separately authorizes publication, this remains a review document.

## 2. Candidate source inventory

The hashes below are the supplied audit prompt’s 2026-11-18 observations, except D’s current checkout values, which were read locally. The live remote lookup failed during the audit, so A/B/C/main hashes below are **reported, not independently verified**.

| Component | Reported candidate | Reported relationship / review requirement |
|---|---|---|
| Initial main | `e7bc839c0632c3db4fd3bcf7c38838c6da16070d` | Local main and origin/main tracking ref still point here. |
| A / RAG | `24f77211da1395a9da99d7b0f1ca17621c6e64d0` | B reports importing snapshot `24c2b6d96fc00c7e2ffe5dcd63be57d72dc406ac`. A must confirm exact source and any newer owner delta. |
| B / integration candidate | `98a0b1f799c444137e9297e3f99150ea211e558f` | Reported candidate on `member-b/task-f-004-web-workspace`; B owns the candidate manifest, source inventory, checks, and explanation of import/ancestry. It is not verified from this checkout. |
| C / classification | `50ee841177494a0b4eb30c1f994cb455d8b5e` | B reports importing snapshot `df842f928d8b856aa404afa00893415511ab1cd1`. C must confirm exact source and any newer owner delta. |
| D / extraction and eval | `36ea2a1b59e382930daee7d088c883b0d103c619` | Confirmed local HEAD and local origin/D tracking ref. B reports importing this exact D snapshot. |

**Candidate composition rule:** B should identify the exact reviewed source snapshot for each included owner in the candidate’s `scaffold_inputs.json` (or its agreed equivalent), list imported paths, and show ancestry/merge-base facts from B’s clone. Review and import only named, owner-approved snapshots. Do not merge whole historical owner branches or infer ancestry from matching file contents.

D's audited commit changes only D-owned paths: docs/extraction-eval/**, eval/**, services/extraction/**, and specs/004-extraction-evaluation/**. It contains the canonical planned-procedure answer/evidence/document-identity correction, readiness URL correction in the D smoke wrapper, request-ID admission ordering, duplicate Authorization rejection, and regressions. There is no D contract-v1 change after the published freeze in that commit.

Two later D documents are present only as untracked local drafts: `docs/extraction-eval/d-standalone-work-2026-11-15.md` and `docs/extraction-eval/selection.md`. They are not part of the reported B candidate and are excluded from this proposal’s candidate inventory. They do not contain real assignment IDs or runtime changes.

## 3. Recommended promotion policy

**Recommendation: review the candidate now, but do not call it main-ready until its included services have exact-source evidence and there are no unexplained failures for the included scope.**

The audit prompt reports a shared health matrix of **154 passed / 50 failed / 6 blocked**, with the 50 failures attributed to C’s missing health routes. An earlier B follow-up in this conversation reports **148 passed / 50 failed / 12 blocked**. Those reported totals differ. B should identify the exact source hash and run that produced the authoritative matrix before the owners assess promotion.

Use these gates:

1. **Source and ownership gate**
   - B supplies the exact candidate hash and import manifest.
   - A, B, C, and D each confirm their own included snapshot and path inventory.
   - Any path outside an owner’s agreed scope is removed or referred to its owner.
   - No credentials, raw corpora, local indexes, ignored test receipts, or another member’s annotation records are copied into the candidate.

2. **Contract and deterministic-check gate**
   - Confirm the frozen contract and generated binding version remain v1.0.0; run the candidate’s contract/binding integrity checks.
   - Run the actual locked, key-free service and web checks against the exact candidate.
   - Record command, working directory, source hash, environment versions, result counts, warnings/failures, and cleanup evidence.
   - Do not run training, paid/live providers, deployment, or locked final evaluation as part of this checkpoint.

3. **Included-service health gate**
   - Run B’s actual `check_health.py --mode mock` against the exact candidate, not a simulated response.
   - Resolve C’s reported missing-health-route failures or explicitly remove C’s runnable service from the proposed interim scope with C’s agreement. Do not include it and silently waive its failures.
   - Retain the D six business failure checks: timeout 504, rate-limit 429, and provider outage 503 on both business routes, with safe errors and request-ID correlation.
   - Add D’s mock-not-ready case only after D implements and tests a real owner-factory seam: mock mode, readiness 503 with valid HealthResult and safe nonempty reason; liveness 200/alive.
   - List any intentionally blocked scenarios separately. A blocked case is not a pass.

4. **Explicit status gate**
   - Keep F-011 and F-014 checkboxes open and say “pending” in any checkpoint note.
   - Mark the candidate as an **interim mock integration snapshot**, not a complete foundation or an approved base for downstream business work.
   - Do not claim clinical, live-model, deployment, or real-data validation.

If the team wants a main update before all service health checks pass, the safer alternative is a clearly narrower documentation/review snapshot that excludes any unverified runnable service. It must not be described as an integrated runnable baseline. Whether such a limited snapshot is useful is a team decision.

## 4. Owner review checklist

| Owner | Review requested | Evidence needed before a promotion decision |
|---|---|---|
| **A** | Confirm the RAG snapshot and paths; review retrieval/readiness behavior, provenance and data/license boundaries. State whether the included A service is runnable in mock mode. | Exact source hash; owner-local test commands/results; health/error endpoints; confirmation no raw corpus/index or unapproved data is in the candidate. |
| **B** | Confirm the candidate tree, imported snapshots, ancestry and shared-file ownership. Explain the two reported health-matrix totals and supply the exact F-011 run. | Candidate full hash; import manifest; contract/scaffold/web/health commands and results; process cleanup; list of blocked/failing cases. |
| **C** | Review the included classifier snapshot. Address the reported health-route failures or recommend excluding the runnable C service from a limited interim scope. Keep data selection separate. | Exact source hash; health/readiness and safe mock-failure behavior; owner-local tests; no raw data or unapproved MTSamples material. C-002 manifests are not required for a mock-only checkpoint and must not be invented. |
| **D** | Confirm D snapshot 36ea2a1b59e382930daee7d088c883b0d103c619 and current owner test results, six failure mappings and the outstanding mock-not-ready gap. | Reproduced service/eval tests and HTTP checks against the candidate; proposed readiness seam and owner tests before it can count as passed. |
| **Team / user** | Decide whether an interim snapshot is useful before F-014; define its intended use and whether the limited-scope alternative is acceptable. | Explicitly approve any later publication action separately. This proposal itself is not publication authorization. |

## 5. D evidence and known limits

The D audit reproduced the following against local HEAD `36ea2a1b59e382930daee7d088c883b0d103c619`:

- Extraction suite: **59 passed**, with one Starlette/HTTPX deprecation warning.
- Eval suite: **36 passed**.
- Training-example structural check: **16 documents, 18 mentions, 37 spans passed**.
- Direct factory/handler probes: **6/6** timeout, rate-limit, and provider-outage cases across `/v1/extract` and `/v1/document-answer`; retryable flags, request-ID correlation, and error sanitization passed.
- Health probes: healthy mock readiness 200; live-mode readiness 503; both liveness routes 200/alive. These do **not** test mock-mode not-ready.
- D’s current code derives readiness solely from `provider.mode == "mock"`; the required mock-not-ready seam is not present in the published D snapshot.

These D-local checks do not verify B’s health checker, the candidate source tree, C’s service, or a main integration. The D HTTP probes use the actual D `create_app` factory but are not a substitute for the exact B checker run.

The audit could not fetch B’s candidate or remote tips. The Spec Kit paths-only resolver was blocked by local PowerShell execution policy. Promptfoo’s CLI version attempt failed during SQLite startup; no Promptfoo evaluation was run in the audit. These are limitations of this evidence package, not passes.

## 6. Relationship to foundation tasks

| Gate | Interim proposal treatment | F-014 treatment |
|---|---|---|
| F-003/F-009 frozen contracts and bindings | Include only the approved v1.0.0 package and integrity evidence. | Their completion does not complete F-014. |
| F-004 scaffold | May be represented as an interim owner snapshot after exact-source review; do not mark its parent task complete from local module tests. | Coordinated F-004 acceptance remains required. |
| F-011 health/readiness/failure matrix | Keep pending. Report D’s six passing cases and the mock-not-ready gap; resolve or explicitly scope C’s reported failures before including its runnable service. | Must be accepted through B’s coordinated exact-source checks. |
| F-012 canonicalization | D’s Python tests are supporting evidence only; cross-language acceptance still needs B’s candidate checks. | Remains a prerequisite to the shared mock smoke path. |
| F-005 input-to-answer smoke | Include only as a required candidate check if the actual web workspace and all included services are available. | Its completion is not implied by D’s loopback test. |
| F-010/F-006/F-013/F-007 | Record as open unless B supplies exact-source evidence and owner review. | These lead to the F-014 checkpoint. |
| F-014 | Label the interim result “not F-014”; do not alter its task marker. | Remains pending until its own acceptance and separately authorized publication. |

## 7. Decisions requested for the A/B/C review

1. Does the team want a limited interim main snapshot before F-014, and what work may safely depend on it?
2. Is the intended candidate B’s reported `98a0b1f…` tree? B should confirm the exact hash and imports before owners review source.
3. Which F-011 matrix is authoritative: 154/50/6 or 148/50/12? Please provide the exact-source run behind it.
4. Should C resolve its health failures before any runnable service snapshot is considered, or should a limited proposal exclude C’s runnable service?
5. Does the team agree the interim checkpoint must remain explicitly non-final, non-live, non-clinical, and not a substitute for F-014?

No team decision is assumed. Unknown owner capacity and effort remain unknown.

## Handoff

**Proposed D source:** `member-d/extraction-evaluation` at `36ea2a1b59e382930daee7d088c883b0d103c619`. **Required before promotion review:** B’s exact candidate/import manifest and current checker run; A/C owner confirmation; D mock-not-ready implementation and tests if that case remains required; no unexplained health failures for included services. **Still pending:** F-011, F-014, team decision on interim scope, and separate user authorization for any publication. This document is an uncommitted D-owned proposal for review only.
