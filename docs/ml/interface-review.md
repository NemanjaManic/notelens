# Classifier interface proposal for B

**Owner**: C. **Date**: 2026-11-11. **Status**: assistant inspection/proposal only.
This is not affected-owner acceptance, contract freeze or completion of C-009.
Canonical definitions remain in [contracts/v1](../../contracts/v1/README.md).

The measured five source labels map exactly to the five proposed classification display
labels after removing source-label surrounding whitespace. No enum change is needed for
this local release. C will consume B's prepared text without altering it and return the
same `doc_id` and `text_sha256` through `POST /v1/classify`.

Before C-009 can implement consumer checks, B's F-003/F-004 work needs to provide frozen
schemas, generated Python bindings and representative fixtures. Suggested acceptance
cases for B's review:

- Supported: exactly one score for each of the five categories, no duplicate category,
  selected category present, model version and honest confidence note.
- Uncertain/unsupported: null category; define whether available scores may still be
  returned. Do not imply that low confidence detects every unfamiliar language or domain.
- Probability scores: finite values in [0,1]; confirm the probability-vector sum tolerance
  if normalization is to be checked. Decision scores can be signed and are not probabilities.
- Identity: unchanged canonical text and matching document digest, including non-BMP text.
- Missing/incompatible model: safe shared configuration/unavailable error, not a fabricated
  successful prediction. Mock output must remain distinguishable from real-model output.
- Invalid/empty/oversized input: shared English validation behavior and unchanged approved
  100,000-code-point limit; no submitted-text logging or persistence.

The schema's category-count constraint alone cannot enforce unique coverage of all five
categories. The shared README already requires uniqueness; the eventual tests should check
it explicitly. Semantic language and digest checks also require runtime verification.
No schema changes or competing hand-maintained models have been introduced.

After B publishes F-014, C can complete C-002 and give D source-checksum-bound group/split
IDs. D should use those frozen manifests for assignments, not the current nonempty
inspection subset, which still contains known conflicting duplicate groups. Before model
selection, C must receive only development annotation assignments. Team/human review and
substantive quality thresholds remain pending.
