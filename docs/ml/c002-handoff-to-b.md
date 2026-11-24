# C-002 review request for B

**From:** Sara / C

**Date:** 2026-11-19

Hi B,

C's local duplicate-review tools and split preview are ready. The
preview has 860 training, 185 validation and 183 draft test documents.
Another 101 documents remain unassigned. Three potential duplicate
pairs span six quarantined groups and await review. The development
ledger records all 1,045 groups already used in training or validation.

Could you confirm these items before I proceed?

1. **Review access.** Which authorized local copy may the designated
   reviewers open, and who may access the documents and their local
   identifier mapping? If reuse or access approval belongs to someone
   else, please identify the appropriate decision owner. D also needs
   the applicable annotation permissions and access, retention and
   redistribution limits for the reviewed handoff.
2. **Canonical preparation.** Which B-owned entry point and version
   should C use to verify the exact canonical text and its SHA-256
   for the C-to-D handoff? Please confirm where the mapping from
   dataset document IDs to prepared document IDs and text digests
   belongs and how reviewers may access it.
3. **Foundation publication.** Please share the reviewed F-014
   commit when it is available. The last verified `main` was
   `82ce4d5`, where F-014 was still pending.

After access is confirmed, I will record which groups are reserved
for review before opening the documents. I will record the pair
decisions, rerun the split preview and flag the impact on assignments.
Exposed duplicate components will stay in development. I will keep
unresolved components quarantined and coordinate the freeze after
review and F-014.

This note contains aggregate counts only. The local queue and exposure
ledger contain identifiers and require the agreed access path.

Thanks,

Sara / C

## B's confirmation, 2026-11-19

B confirmed C's ownership of MTSamples provenance and reuse review.
The [C-001 audit](data-audit.md#source-identity-and-reuse-review) records
the local source provenance and reuse findings. The authorized local
copy, named reviewers, visibility of the identifier mapping and
applicable annotation and reuse permissions remain open. The queue,
ledger and any future mapping stay outside Git and chat. All three
pairs remain quarantined while access is pending.

B confirmed the `nfc-lf-v1` preparation rules. On the verified
published source, `canonicalText()` normalizes CRLF and CR to LF and
applies NFC. `prepareBuiltin()` then computes SHA-256 over the exact
canonical UTF-8 bytes for the versioned synthetic catalog. The team
still needs to agree a dataset preparation entry point and a
restricted location for the C-to-D mapping before exchanging records.

Published `main` was verified at `1ac8bfe`. Its foundation task list
marks F-011 complete and leaves F-014 open. C-002 stays in preview
pending approved review access, pair decisions and the freeze
prerequisites. [Published foundation status](https://github.com/NemanjaManic/notelens/blob/1ac8bfe9cf3ea9853c417ffe3f86ed7a1a15b6f8/specs/000-foundation/tasks.md)

## Review authorization and preparation entry point, 2026-11-20

B approved Sara as sole reviewer for the three quarantined pairs in
the checksum-verified C-001 copy. The local file matched the audit
checksum and byte count. Reports and the source-row mapping stay in
the Git-ignored `data/mtsamples/raw/` directory in Sara's checkout.
The mapping is to be deleted after review sign-off. D receives only
permitted metadata through the agreed access path. Final-test access
remains restricted. No pair decision or review access was recorded
by this preparation work.

The C-002 Python entry point is
`data/mtsamples/prepare_transcription.py::prepare_transcription`.
It accepts an already decoded transcription, applies `nfc-lf-v1`,
and returns the canonical text and its SHA-256. It checks Unicode
and the code-point limit, converts CRLF and CR to LF and applies NFC.
Spacing and U+FEFF are preserved in accepted text. The digest is
over exactly the canonical UTF-8 bytes. The function prepares text
and does not grant access or annotation permission.

The published base for this preparation is `1ac8bfe`. All seven
F-012 preparation vectors from that base passed in the 27-test C data
suite. A separate comparison against the actual B `canonicalText()`
at the same commit matched all 19 synthetic inputs, including
rejection codes and SHA-256 values. The comparison used Python 3.11.9
with Unicode tables 14.0.0 and Node 24.20.0 with Unicode tables 17.0.
The results cover the exercised inputs.

## Published foundation baseline, 2026-11-20

B confirmed F-014 is complete. The published `f-014-foundation` tag
resolves to `7eb12e56f33240a428f916ba583b9e00077712df`. The
[publication record on main](https://github.com/NemanjaManic/notelens/blob/cde4dd6ab2da6be5937521c97b4875e97fdc496c/specs/000-foundation/tasks.md)
confirms the tagged baseline.

## Local split freeze, 2026-11-20

Sara signed off on the assisted review. Pair 1 remains quarantined.
Pairs 2 and 3 were each grouped as duplicates and assigned to training
as development-only components. The local `c002-split-v1` split has
864 training, 185 validation and 183 test documents. All existing test
memberships were preserved. Sara confirmed development annotation
permission and reported that Milica received the validation-only
metadata and checksum through the restricted handoff folder.
