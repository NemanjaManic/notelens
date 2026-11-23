# D-007 final QA source planning

Use the pinned v2 staffing plan for the 26 slots and the development exclusion
list supplied with it. Goran accepted his assignments and the 54/26 split.
Sara is the custodian and has confirmed restricted authoring and review access
for herself and Goran. Keep current named permissions until any additional
account is separately confirmed by its owner.

## Where to find source candidates

- **Document-only and the document side of mixed cases.** Write fresh English
  synthetic documents for the planned cases, or use public material with
  documented project permission. Record the document ID, canonical UTF-8
  SHA-256 and source-family provenance. Screen reworded variants, duplicate
  groups and examples exposed in earlier project reviews or demos.
- **Literature-only and the literature side of mixed cases.** Start with the
  approved English MedlinePlus Health Topic summaries in the project passage
  snapshot. The manifest is `data/knowledge/manifests/passages.json`. The
  pinned `passages.jsonl` SHA-256 is
  `4915adc09d6719f84e3315f8a0ea0ac37bc363d8b1a178c6d14f449aac85c938`.
  Use topic and passage IDs to find candidate evidence and confirm that the
  selected corpus and index will be included in the evaluation configuration.
  Obtain the pinned file through Nemanja's approved handoff if needed.
  Credit **Source: MedlinePlus, National Library of Medicine.**
- **Coverage.** All eight mixed slots require independently supported document
  and literature evidence. `F-LIT-08` needs at least two distinct literature
  topics. Record the evidence search or planned gap for `F-DOC-07`,
  `F-DOC-08` and `F-LIT-07`. Mark genuinely source-free out-of-scope slots
  explicitly.

## Check and handoff

Also apply the additive [D-008 replacement family exclusions](../../eval/reports/development/d008-replacement-development-source-exclusions-v1.json)
when checking final-source candidates. These seven fresh synthetic calibration
documents and their reworded family variants are development-only. They add
exclusions without changing the frozen 54-case QA selection or the original
74-candidate inventory. Keep the new examples outside the unseen final set.

Apply the [early-exposed planned-document exclusions](../../eval/reports/development/d007-exposed-planned-document-exclusions-v1.json)
as well. The document families originally assigned to F-MIX-05 through
F-MIX-08 were viewed by D's assistant before the freeze. Replace those source
families in the restricted workflow. Send D metadata and check dispositions,
not further unseen canonical texts or final questions/answers before release.

1. Sara and Goran fill the blank source-list template in the restricted folder
   before drafting. List intended sources, documented families or origins and
   identifiers. Keep each reviewed development case, reserve and exposed
   document family in development. Check both IDs and shared provenance.
2. Sara sends D the source-list version and SHA-256, number of slots checked,
   overlaps found and their dispositions. Sara and Goran completed this step
   for all 26 planned slots. See the [joint provenance result](qa-development-inventory.md#joint-final-source-provenance-and-a-008-intake-2026-11-22).
3. Recheck any source substitutions and the completed inventory before freeze.
   Keep the actual final questions, sources selected by slot and answer keys
   in the restricted workflow. A/D evaluation access follows the manifest
   and configuration freeze.

## Author confirmation clarification (2026-11-23)

Goran's message relayed by Milica confirms four fresh synthetic replacement
documents from new families for F-MIX-05 through F-MIX-08. The four previously
exposed families remain retired from unseen final use. Sara's technical check
reportedly covered all 26 slots, found zero matches against known development
exclusions and matched all four replacement checksums. The reconciled source-list
SHA-256 is `6198b4085b45e702d065535e9705c5b6bf7d841230d35a247bcee327fb26ebf0`,
matching the previously recorded D intake.

Sara's confirmation of pre-handoff provenance relies on Goran's account as the
author. She is aware of no exposure outside the restricted workflow. Record this
as author-attested history and a reported technical check; it does not establish
independent observation of pre-handoff history or universal absence of exposure.
D did not open final source texts or answer keys or rerun these checks in this
update. The source-list bytes were not newly rehashed. See the
[confirmation receipt](../../eval/reports/development/d007-goran-replacement-provenance-confirmation-v1.json).
Completed case/review inventory and the approved final source/system freeze
remain pending; this message does not close D-007 or authorize final measurement.

Sara's subsequent message reconfirms her access to the pinned literature snapshot
and the source check covering all 26 planned slots. She explicitly reports
authoring and cross-review still open. She will agree a handoff date with Goran
and provide the versioned metadata inventory and reviewer receipts after those
steps. No delivery date or completed authoring/review is inferred. Her access
confirmation does not confirm Goran's access. See the
[combined follow-up receipt](../../eval/reports/development/d008-sara-non-independent-feedback-intake-v1.json).

## Goran draft authoring-status update (2026-11-23)

The forwarded section is explicitly labelled a draft reply. It reports Goran's
access to the pinned MedlinePlus snapshot, 617 passages across 401 topics, and
SHA-256 `4915adc09d6719f84e3315f8a0ea0ac37bc363d8b1a178c6d14f449aac85c938`.
The stated digest matches the existing pin; D did not rerun the corpus check.
It also identifies the existing 26-slot v2 source-planning inventory at SHA-256
`6198b4085b45e702d065535e9705c5b6bf7d841230d35a247bcee327fb26ebf0`.
This is a source plan, not a delivered completed case/review inventory.

Goran reports eight local drafts, F-LIT-01 through F-LIT-08. His five remaining
drafts are F-MIX-05 through F-MIX-08 and F-OOS-02. Together these match his thirteen
author slots in the staffing plan. Sara is the assigned reviewer of Goran's
cases. Cross-review completion, reviewer receipts, the authored-case metadata
inventory and an agreed handoff date are not supplied. Sara's own completion
count is not established by Goran's draft. Preserve restricted custody and the
retirement of exposed families; D-007 remains open. See the
[authoring-progress intake](../../eval/reports/development/d007-goran-authoring-progress-intake-v1.json).

## Interim metadata intake (2026-11-23)

Sara supplied `d007-final-qa-metadata-status-v1.json`; its SHA-256 verifies as
`8d5904245990624943cce2fd64604e88779d3f29dec904dfa6d5d956376b6fd3`.
D checked 26 unique case IDs, routes and author/reviewer assignments against the
local staffing plan. All assignments match. The source-intake bytes match the
reported `6198b4085b45e702d065535e9705c5b6bf7d841230d35a247bcee327fb26ebf0` pin.
Sixteen document-hash entries and seventeen passage-hash entries have valid
formats; underlying final texts/passages were not opened or rehashed.

The staffing-plan pin needs reconciliation: Sara's metadata reports
`39f05b80107ef8d04e0a070eec172ef9ea08dcd5d82619c25ff39a4979335d3e`,
whereas both local copies of `d007-final-author-review-plan-v2.json` hash to
`87e635b802ed648c5c8d62352d46524acfc592213bf3011e3ed031ca6117fed3`.
Sara/Goran should supply the exact pinned plan or correct the metadata reference.
Matching assignments do not resolve a byte-identity mismatch.

The inventory confirms zero case versions and zero reviewer receipts in the
restricted folder. All 26 await completion confirmation and the handoff date is
unset. This does not negate Goran's separately reported eight local drafts.
Sara/Goran still own authoring, reciprocal review and delivery of versioned
metadata/receipts. D-007 and final freeze remain pending. Original metadata and
checksum are privately archived; see the source-free
[intake receipt](../../eval/reports/development/d007-final-qa-metadata-status-intake-v1.json).

## V2 metadata update (2026-11-23; current)

Sara's `d007-final-qa-metadata-status-v2.json` checksum verifies as
`50139e072f46c70a02e9c03d03e41cefc5abe172109a41b7f3e42f4003f14261`.
All 26 unique case IDs, routes and staffing assignments match the local plan.
Case fields other than authoring status are unchanged from v1; source-intake
bytes still match the recorded pin. The staffing-plan SHA mismatch above persists.
The original attachment/checksum are archived privately without changing v1.

V2 now records Goran's reported snapshot access/checksum and eight local drafts
F-LIT-01 through F-LIT-08. His five not-yet-drafted cases are F-MIX-05 through
F-MIX-08 and F-OOS-02. Sara's thirteen authoring statuses await confirmation.
These reported statuses do not establish delivered or reviewed case versions.
The restricted-folder inventory remains zero confirmed case versions, zero
reviewer receipts and no agreed handoff date. D did not access final case text.

Goran should place the eight drafts in the restricted folder with case IDs,
versions and SHA-256 checksums so Sara can begin version-specific cross-review
while he drafts the remaining five. Sara should confirm her own thirteen-case
status. Both owners still reconcile the plan pin, complete reciprocal reviews,
agree a handoff date and send D metadata and version-specific receipts through
the approved private route. D validates these before any final freeze. See the
[v2 intake receipt](../../eval/reports/development/d007-final-qa-metadata-status-intake-v2.json).

## V3 and Goran cross-review intake (2026-11-23; current)

The exact attached staffing plan hashes to the metadata pin
`39f05b80107ef8d04e0a070eec172ef9ea08dcd5d82619c25ff39a4979335d3e`.
The earlier identity mismatch is resolved by retaining these exact bytes privately.
The local confirmed plan is preserved: only its status and team-confirmation fields
differ, while all slots and other fields match. All 26 v3 assignments verify.
The v3 digest computed by D is
`c4b2d62d5595595b9e747766037cee3dea6b74935cd88fa43b776e3462b0ee0c`;
no sender-supplied v3 checksum was provided for independent comparison.

V3 reports all thirteen Goran drafts at v1 as author-reviewed, superseding the
earlier eight-draft/five-unwritten report. The private draft archive was not
supplied to D or opened. V3 still contains no review receipt hashes and reports
zero restricted-folder verified versions/receipts; this is an older snapshot
than the separately delivered Goran review receipts. Do not use it to negate
that later delivery or infer completion for the other review direction.

Goran's receipt file digest verifies against his supplied checksum:
`3e6dc9da88a0ff3eff62f46fe04342adc772011b8a8a825509cf412dbfb14796`.
It covers exactly his thirteen assigned Sara-authored cases: twelve v1 cases
and F-DOC-06 v2, all personally approved with no unresolved issues reported.
Receipt fields include case hashes, dates, human confirmation and exposure,
preparation and AI-assistance disclosures. The F-DOC-06 receipt hash matches
his personal revision confirmation. D checked metadata consistency, not the
underlying source spans or case bytes. Full receipts stay private; the
[source-free review intake](../../eval/reports/development/d007-goran-cross-review-intake-v1.json)
contains only identities, dispositions and limitations.

Final reconciliation remains blocked on Sara's thirteen version-specific reviews
of Goran's cases and a final 26-case version/hash inventory tied to all receipts.
The Goran receipts reference metadata v4 (hash
`4858c31730d4232c4d432e484480712b5d87b39cb4815d0481d0df1f76b22def`)
and a case inventory that were not supplied. Their author-release statement covers
v1; obtain Sara's approval of the final F-DOC-06 v2 identity explicitly.
No final freeze, final measurement or parent closure is recorded.

Exposure accounting: the initial receipt preview rendered reviewer technical
observations for F-DOC-01, F-DOC-02 and F-DOC-03 to D's assistant before freeze.
No full case, canonical source or answer-key files were opened. Preserve this
limited exposure for the freeze owners' assessment; do not assert universal
absence of exposure. Subsequent receipt processing selects identity/status fields
without rendering semantic reviewer notes. See the
[v3 metadata intake](../../eval/reports/development/d007-final-qa-metadata-status-intake-v3.json).
