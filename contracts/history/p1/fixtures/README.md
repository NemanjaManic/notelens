# Draft v1 Contract Acceptance Fixtures

**Owner**: B. **Status**: synthetic, key-free fixtures against the current draft proposal.
No service, model, retriever, embedding, paid call, or actual clinical record is involved.
These fixtures are not evaluation QA and must not be ingested into a literature index.
The canonical [schema](../schema.json) and [OpenAPI](../openapi.json) remain unchanged.

## Files and catalog format

- `manifest.json` contains `catalog_version: 1` and a nonempty `cases` list.
- `payloads.json` maps each case ID to its actual payload or deliberately invalid schema/API.
- `documents.json` supplies valid prepared-document contexts keyed by document alias.
- `references.json` contains separate, curated synthetic expectations, not model outputs.

Each case has `id`, `kind` (`payload`, `schema`, or `openapi`), `expected`, and `scenarios`.
Payload cases also name a canonical `$defs` `definition`, and may name `document` and
`reference` context keys. IDs are unique lowercase ASCII slugs. Missing/orphaned payloads,
contexts, references, unknown definitions, duplicate expectations, and missing mandatory
coverage make the catalog fail. At least one positive case covers each of the 22 definitions.

`expected: []` means valid. Invalid cases list exact diagnostics, such as
`[{"rule": "SPAN_QUOTE", "path": ""}]`. Paths are JSON pointers; the empty pointer means
the root payload. Actual and expected rule/path sets must match exactly. Rejecting an
invalid case for an unrelated reason does not pass it. Changing an expectation requires
review of why the case should pass/fail, not editing it merely to obtain a green result.

There are **90 cases: 38 positive and 52 negative**. They cover required fields, additional
properties, schema/API validity, all classification states, score kinds, retrieval states,
answer routes, document identity, hashes, Unicode, exact/repeated spans, citations,
entity/source/claim uniqueness, provenance, historical/family attributes, and copied ICD.

The offset example matches B's illustrative handoff: 61 code points, an emoji, and a
repeated denial. Its last denial uses code-point interval [47,61), corresponding to UTF-16
[48,62). A valid quote at the first occurrence cannot be rejected from quote equality alone:
the separate reference identifies the intended second occurrence.

Historical/family reference attributes are explicit facts in synthetic sentences. Comparing
against those curated attributes is a fixture-specific check, not an assertion that this
tool interprets arbitrary medical text. The code checks that an ICD string appears as a
complete source token in its exact evidence, not whether that code is clinically appropriate.

Literature fixtures use `example.invalid` URLs, invented topic/passage IDs, and a preparation
date of 2026-11-11. They are not downloaded MedlinePlus content, measured retrieval output,
real corpus metadata, or medical references. Scores are arbitrary fixture numbers, not
performance results, thresholds, calibration evidence, or clinical certainty.

## Scope and limitations

The validator checks Draft 2020-12 structure with format validation, OpenAPI 3.1.1 and
local references, exact hashes/quotes, documented cross-record invariants, and the
curated reference expectations. Network retrieval is prohibited. Normal validation does
not repair/normalize input, infer patient conditions, inspect real PDF uploads, choose
thresholds, detect English prose, or prove semantic support from arbitrary passages.

Prepared canonical text must be NFC/LF and nonempty, with the correct UTF-8 digest.
Original BOM removal cannot be inferred from the prepared text: removing at most one
leading BOM from a raw input that starts with two can leave one. The payload checker
therefore does not reject a leading BOM solely by guessing the original input. Actual
raw-input preparation and PDF checks belong to B-001, with their own input/output tests.

Bounds and quote checks need a prepared-document context. Aggregate results establish
citation relationships; an isolated `Claim` cannot establish citation resolution without
its parent sources. Empty entity results remain valid and do not establish medical absence.
The acceptance suite is finite: passing it does not establish general model quality,
clinical validation, runtime session security, or human/team agreement.

See [tooling setup, checks, and freeze-record format](../../../scripts/project/README.md).
