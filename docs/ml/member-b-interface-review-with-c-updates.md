# Member C update to B's interface review

**Date** 2026-11-11. This historical note records C's findings and proposals before the contract freeze. See [B's interface review](../platform/interface-review.md) for the original guide and [C's complete response](../team/contract-reviews/p1/member-c-response-to-b.md) for the review discussion.

## Data and proposed classifier behavior

**Measured C-001 status:** the supplied local CSV contains 4,999 rows; 1,338 belong to the
five target specialties and 1,329 remain after removing nine empty target transcriptions.
Counts are Cardiovascular / Pulmonary 371, Orthopedic 355, Gastroenterology 224, Neurology
223 and Urology 156. The exact source labels each have a leading space; no enum changes
or broad-label merges are needed. See [C's data audit](data-audit.md).

There are 46 preliminary exact duplicate groups with conflicting target labels, covering
92 rows. The current subset is not a frozen benchmark. C-002 must handle near duplicates,
exclude conflicting groups and establish reproducible group-disjoint splits. Eight
synthetic audit tests and source-regeneration checks passed; no model/API checks ran.

**C proposals for B's agreement:**

- Preserve canonical input text and return its original ID/hash. Derive model features
  internally; do not alter or repair the document. Fit learned preprocessing on train only.
- `supported`: selected category and exactly five finite scores, one per target category.
  `uncertain`: null category and all five computed scores. `unsupported`: null category,
  with empty scores if inference was skipped or five scores if it ran; explain the reason.
- Low confidence alone means uncertainty, not proof of unsupported input. Select thresholds
  on development data. Probability scores are not clinical certainty or proven calibration.
- Use an error envelope for malformed requests, model/configuration failures and runtime
  failures. Missing model artifacts must not trigger mock fallback or a successful
  uncertain result. C proposes 400 for malformed JSON, 422 for invalid fields/hash/empty
  text, 413 for oversized text, and 503 for unavailable model configuration.
- C proposes 500 / `internal_error` for unexpected classifier failures. B must review the
  missing 500 entry in the canonical API. The local API already includes 502; B should use
  it when rejecting an invalid upstream classifier result. Full mappings are in C's response.
- C proposes common language validation at B's preparation boundary, with rejected
  non-English input using `unsupported_language` and proposed HTTP 422. The detection
  method is unresolved; `language: en` and classifier confidence are not language checks.
- C proposes creating the classifier scaffold, health/readiness, tests and local dependency
  lockfile in its own service paths. B coordinates F-004/F-011, shared contracts and startup.
  Record this ownership before execution. The foundation scaffold contribution precedes
  C-009, which depends on the scaffold; do not introduce a circular dependency.
- Exposed classifier services use the agreed server-to-server authentication; local key-free
  mocks stay on loopback. No submitted text is retained in service logs or files. Hosting,
  operational limits and deployment remain separate unresolved gates.

No A/D interface choices are adopted by this C update. C's category remains a soft retrieval
hint; uncertain or failed classification must not suppress independent supported outputs.

C has completed the exact source-label audit: the five labels map to the proposed enum
after removing surrounding source-label whitespace. The measured uncertainty policy is
still pending development experiments. This legacy empty-score mock is illustrative;
C proposes retaining all five computed scores for real uncertain outcomes.

## Handoffs proposed at the time

B must resolve C's proposals and complete the F-003 freeze, F-009 bindings and coordinated
F-004 scaffold before C-009's actual consumer checks can run. C-002 additionally depends
on C-009 and F-014's reviewed publication, not merely the original documentation commit.
C-003 training then follows C-002. These gates remain unchanged by this copy.

D can prepare annotation guidance now. D-002 selection requires C-002 splits; D-003 then
assigns C's development-only primary annotations and separate reviews. C's initial training
does not depend on C-010 annotations; the C-008 final-task gate does. A's completed RAG model
is not a direct prerequisite for C's training, although A participates in the shared foundation.

See [C's status and dependency report](member-c-status-and-dependencies.md) for exact
requested artifacts and the next task each handoff unlocks.
