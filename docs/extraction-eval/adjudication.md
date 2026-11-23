# D-013 canonical reference adjudication

The coordinator is Milica (D). The current inventory contains all 40 primary
submissions and 12 eligible declared independent reviews, exceeding the required
ten reviews. Review declarations and disclosed AI assistance remain part of the
provenance. This is human-reviewed benchmark material, without a claim of clinical
validation.

## One complete coordinator packet

The restricted `D013-complete-adjudication-v1` packet accounts for every currently
known pending decision and all 40 development assignments. It supersedes the
six-item delivery workflow for remaining work. Earlier completed decisions remain
recorded and are not requested again.

The packet groups 217 pending items by document:

| Items | Scope |
| --- | --- |
| 152 | Earlier paired-record proposals awaiting coordinator signoff |
| 14 | Remaining questions on canonical texts 004 and 007 |
| 49 | B primary questions on texts awaiting canonical-source delivery |
| 2 | Complete new comparison dispositions for 004 and 007 |

The full comparison for 001 is retained. Its five question decisions already
resolve its semantic differences; matching-label evidence can be combined without
changing the approved labels. The preparation audit accounts for 250 IDs: the 217
pending items and 33 previously resolved proposal/question IDs. Earlier topic and
question decisions retain their own artifact pins and are also shown in the packet.

The [preparation receipt](../../eval/reports/development/d013-complete-adjudication-preparation-v1.json)
contains counts and hashes without source text. Source bodies, submitted labels,
candidate references and the browser worksheet remain in the restricted local
handoff folder. Do not commit or publish the packet.

## Coordinator procedure

1. Open `review.html` from the private packet in Chrome or Edge.
2. Work through the document sections. Read the relevant canonical source, working
   reference, recommendations and submitted alternatives. Earlier recorded decisions
   are available for context. The working references remain proposals.
3. Accept a recommendation, replace it with an explicit correction, or defer it with
   a reason. Corrections can use exact source wording and attributes; the coordinator
   does not need to calculate offsets manually.
4. After reviewing a document, its **Accept remaining recommendations and approve
   document** button records explicit acceptance of undecided recommendations.
   Existing revisions are preserved. Deferred decisions and unfinished corrections
   block approval. **Approve using my recorded decisions** requires every item to
   have an explicit disposition already.
5. Record any additional reference correction in the document's correction field.
   Document approval covers the working reference with the recorded item decisions
   and corrections applied. It does not attest a new independent secondary review.
6. Use **Save progress JSON** when interrupted. Browser autosave is attempted and
   portable progress can be restored. Imported source files must be selected again
   after reopening the page; saved decisions are retained.
7. After all sources, decisions and 40 document approvals are complete, confirm the
   personal-review declaration and export `d013-complete-human-decisions-v1.json`.
   D then verifies the returned source pins, applies the exact decisions, validates
   the resulting references and records the reference freeze.

## Outstanding external source delivery

Goran or Sara must provide the ten exact canonical UTF-8 files for assignments
020–029, with a filename-to-assignment manifest and SHA-256 checksums. The reviewed
B annotation archives contain labels and digests but no full canonical texts.
Preserve 022 and 029 as supplied: 62 and 112 code points. Do not normalize,
reconstruct or expand those sources.

The worksheet accepts all ten files in one selection, matches them by the frozen
SHA-256 and checks every mention and evidence span using Unicode code-point
offsets. It unlocks a document only after its checks pass. Source-dependent
decisions cannot be approved from annotation quotes alone. File verification and
review stay local; the worksheet makes no network requests.

The source request is included as `Request-Goran-canonical-texts.txt` in the private
packet. No additional primary submissions or independent reviews are currently
required. New source mismatches must be corrected without substituting a different
canonical version.

## Closure gate

D-013 remains open until all of the following hold:

- All 40 original primary records and required independent reviews remain immutable
  and their identities and provenance are preserved.
- All 40 canonical hashes, mention spans and evidence spans match the frozen
  allocation. Evidence supports assertion, time, subject and procedure state.
- Every retained question and paired difference has a recorded disposition.
  An explicitly adjudicated source gap may remain an unknown label or an exclusion
  with rationale; it must not remain an unanswered adjudication request.
- Returned human decisions and corrections are applied to distinct reference files,
  with an application audit and original submission hashes.
- Reference integrity checks pass, group-separated development provenance is
  confirmed, and the reviewed reference version and freeze manifest are recorded.

All 40 annotation assignments belong to development. This task does not require
provider-backed D-004/D-005 runs, unseen-final QA measurement or new B-005/B-009
acceptance. Those have their own task gates. Preparing a worksheet or exporting
decisions alone does not close D-013.

## Reproducible checks

The public renderer accepts a permitted private `packet.json`; it does not obtain
or reconstruct missing sources:

```powershell
python -B eval/tools/build_adjudication_review.py <private-packet.json> <private-output-folder> --receipt <source-free-receipt.json>
python -B -m pytest eval/tests/test_adjudication_review.py -q
node eval/tools/test_adjudication_review.cjs
```

The renderer rejects incomplete coverage, repeated IDs, mismatched sources and
invalid anchors. Synthetic browser-state checks cover missing-source gating,
explicit review, preserved corrections, progress recovery and Unicode offsets.
They add no human-review credit.

The [2026-11-23 verification](../../eval/reports/development/d013-complete-adjudication-verification-2026-11-23.json)
records 141 passing evaluation tests, passing synthetic browser-state checks and
an actual local Chrome check of all 40 sections and 217 items. The Chrome check
also verified source-file import, unmatched-file rejection and missing-source
approval gating, with no exported human decisions.
