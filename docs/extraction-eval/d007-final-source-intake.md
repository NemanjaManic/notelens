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
