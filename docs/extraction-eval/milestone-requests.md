# Member D requests for the local milestone

**Date:** 2026-11-11. Local handoff only; no messages or remote issues were sent.

## B — contract and integration

The checkout still has draft P1, not a freeze or generated bindings. D uses its
schema directly read-only. Please provide the reviewed schema revision/freeze and
bindings, plus decisions on the outstanding interface review. Until then this is a
locally integratable mock **provisional adapter**, not approved shared integration.

- Confirm the existing extract-with-summary and document-answer operations. The
  local `/health` route is not yet listed in shared OpenAPI. Requests use the existing
  PreparedDocument; no conflicting body fields were added.
- Confirm correlation header `X-Request-ID` and B's document/session/expiry binding.
  Example: a source-free insufficient AnswerResult still echoes the originating
  request ID, so B can reject it after a document switch. Affected consumers: A/B/D.
- Confirm unsupported/partial extraction representation, planned/cancelled procedure
  and unknown assertion rules. These remain open; mock catalog does not invent
  enum values. Annotations can flag unresolved cases separately.
- Confirm whether exact mention spans should become a shared field. Evaluation
  currently derives a unique name span from item evidence and rejects ambiguous
  occurrences. Example: repeated `chest pain` requires occurrence-specific evidence,
  never the first substring by default. Affected consumers: B/D and all annotators.
- Clarify the duplicate-leading-BOM edge case in nfc-lf-v1. The README says to
  remove at most one initial U+FEFF; with two in the source the prepared output could
  still start with one. The current strict local validator rejects any leading U+FEFF.
  Agree the intended canonical invariant/fixture before declaring full compatibility;
  D has not changed the shared preparation rule.
- Confirm the HTTP/error mapping in integration.md, including 500 and the 502 code,
  request/history/language controls, live policy and service auth. The local literal
  summary/answer policy intentionally rejects unsupported paraphrases until support
  validation is agreed. Keep document-bound bodies out of logs/caches.
- Record the owner-created D scaffold contribution to the foundation; do not mark
  shared F-003/F-004/F-014 complete from D's local service tests.

## C — exact missing annotation input

No `data/mtsamples/manifests` files or permitted canonical source documents exist here.
Please provide your frozen C-002 source/split/group versions, checksums, actual label
mapping/counts, conflict/near-duplicate exclusions, stable document/group IDs and
validation/test membership. Agree access/redistribution and exact canonical text/hash
mapping with B/D. C's local C-001 report is not enough to select actual assignments.

D's provisional selector needs the adapter fields in annotation-tooling.md; it can
then propose the real 40-document set, ten primary records per member and at least
ten independent reviews. C must only receive development primary/review content before
selection freeze. Agree the final-set access policy for D too. No production split
replacement, real assignment or human label has been invented in this milestone.

## A — later retrieval/QA evaluation

Provide the reviewed corpus snapshot/preparation/index/retriever versions and stable
topic/passage IDs with permitted content and actual passage-level evidence. Agree
answerability/relevance case formats with D and source-preserving composition with B.
The current smoke is document-only; it does not measure A's retrieval or the complete
80-QA cross-module benchmark. Reference answers must remain outside the index.

## User/team — live generation decision

Gemini is only a candidate in repository planning; no approved provider/model,
account authorization, enforceable amount/call/token cap, deadline/retry policy or
provider retention terms are recorded. Supply decisions/configuration through the
agreed server-side workflow, never secret values in chat. Then D can add the approved
SDK adapter behind the existing boundary and run an authorized development-only live
smoke. Until then live mode fails with 503 `configuration_required`; no live call ran.
