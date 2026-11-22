# D-007 final QA source planning

Use the pinned v2 staffing plan for the 26 proposed slots and the development
exclusion list supplied with it. Goran's assignment acceptance and the 54/26
split remain pending. Sara is the custodian and has confirmed restricted
authoring and review access for herself and Goran.

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

1. Sara and Goran fill the blank source-list template in the restricted folder
   before drafting. List intended sources, documented families or origins and
   identifiers. Keep each reviewed development case, reserve and exposed
   document family in development. Check both IDs and shared provenance.
2. Sara sends D the source-list version and SHA-256, number of slots checked,
   overlaps found and their dispositions. At handoff, 0 of 26 slots have been
   checked. Candidate sources still need review against known exposures.
3. Recheck any source substitutions and the completed inventory before freeze.
   Keep the actual final questions, sources selected by slot and answer keys
   in the restricted workflow. A/D evaluation access follows the manifest
   and configuration freeze.
