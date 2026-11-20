# C-002: Provisional duplicate analysis and split proposal

**Owner:** C / Sara. **Date:** 2026-11-16. **Status:** draft; not frozen or
approved for annotation or final evaluation. Sara subsequently authorized one
exploratory training run, reported in [the development experiment](experiments/draft-baseline-v1.md).

Sara authorized C to begin this bounded preparation before F-014. C-001 and C-009
are complete; this is not a claim that F-014, C-002 or a team-approved dependency
change is complete. Final manifests and downstream publication remain pending review.

## Source and limitations

The local source is `data/mtsamples/raw/mtsamples.csv`, SHA-256
`a92cb78569f460606661ee7da50c92305b60d0fac2be4b06c8d2de0f234612d4`.
The source audit verifies schema, IDs, exact five-target mapping and empty filtering.
Source and derived content are ignored by Git. See [data audit](data-audit.md) for
provenance and redistribution limitations. No source text appears in this report.
The draft local artifact contains source IDs, document/group IDs, labels, source text
hashes and draft assignments, so keep it local pending access/redistribution review.
Dataset IDs are not interchangeable with per-submission API document IDs.

This analysis does not establish English language, source rights, absence of personal
information, clinical validity or a complete patient-identity separation. There is
no reviewed canonical document/text-hash mapping for annotators. The temporary NFC/LF
length check is only a draft feasibility check, not a replacement for B's canonicalizer.
Review any source/excerpt/ID access and record the actual preparation version before use.

## Draft method

`data/mtsamples/draft_splits.py` verifies the source checksum, groups all nonempty
five-target rows by temporary comparison text (NFC, line-ending normalization,
case-folding and whitespace collapse), and preserves the original text for hashing.
Comparison equality is not proof of clinical equivalence. The tokenizer preserves
Unicode word runs and punctuation; the code records Python and Unicode versions.

For each distinct comparison group, exhaustive five-token shingle intersections are
computed across groups, including across specialties. The draft screening rule flags
Jaccard >= 0.80 or containment of the smaller shingle set >= 0.95. These are **provisional
screening parameters**, not calibrated or agreed duplicate thresholds. Every flagged
pair is unresolved and both groups are quarantined. No candidate is represented as a
human-confirmed duplicate. Groups with conflicting labels, fewer than five tokens or
over 100,000 provisionally normalized code points are also excluded or quarantined.
Flags may overlap; the excluded row total is counted once per group.

The illustration allocates remaining whole comparison groups by class using fixed
seed `c002-draft-v1`, weights 70/15/15, descending group size and seeded hash tie
breaks; it repeatedly chooses the largest current per-class target deficit. The weights
and seed are **proposals**, not a frozen decision. No model or performance metric was
used. Rows from each comparison group stay together. Candidates and conflicts remain
out of all three draft partitions. Short texts are not treated as duplicates merely
because they lack shingles.

## Measured provisional results

The run considered 1,329 nonempty target rows and 1,283 comparison groups. It found
46 conflicting-label groups covering 92 rows; three unresolved near-candidate pairs
involving six groups; four short groups; and zero over-limit groups under the draft
normalization check. With overlapping flags counted once, 101 rows are excluded or
quarantined and 1,228 appear in the illustration below. These are not final counts.

| Specialty | Draft train | Draft validation | Draft test |
| --- | ---: | ---: | ---: |
| Cardiovascular / Pulmonary | 255 | 55 | 55 |
| Orthopedic | 221 | 47 | 47 |
| Gastroenterology | 151 | 32 | 32 |
| Neurology | 129 | 28 | 27 |
| Urology | 104 | 23 | 22 |
| Total | 860 | 185 | 183 |

Every provisionally included row is in exactly one comparison group and one draft
partition; no group crosses partitions. The counts above do **not** establish feasibility
after language, source-access, candidate adjudication or team review. They are not
performance feedback and are not a final-test result.

## Commands and checks

From the repository root with the authorized local source:

```powershell
python -B data/mtsamples/draft_splits.py
python -B data/mtsamples/draft_splits.py --check
$env:UV_CACHE_DIR = Join-Path (Get-Location).Path '.cache/uv'
$env:UV_PYTHON_DOWNLOADS = 'never'
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location).Path '.cache/classifier-httpx2-py313'
& ./.cache/classifier-tooling/Scripts/uv.exe run --locked --offline --directory services/classifier python -B -m pytest tests/test_splits.py -q
python -B -m unittest discover -s data/mtsamples/tests -q
```

The generated `data/mtsamples/raw/c002-provisional.json` is ignored and contains no
document bodies. `--check` recomputes and compares exact bytes. After the first draft
writer was changed from platform text mode to explicit UTF-8 bytes, `--check` correctly
rejected the old line-ending representation; regenerating produced a passing check.
Identical input produced identical output in repeated runs. Five synthetic grouping
tests and eight prior audit tests passed. Actual-output checks verified unique document
IDs, reconciliation, no assignment for flagged groups and assignment of each other
group to one partition. Existing ignore rules cover the local draft and raw data.

The `speckit-implement` workflow selected `specs/003-classification` via the official
PowerShell resolver with `SPECIFY_FEATURE_NO_PERSIST=1`; the requirements checklist
had 16 checked and zero unchecked. No extension hooks were configured.

## Before any freeze or downstream use

1. Agree and document duplicate-screening thresholds and review the three pairs, short
   groups, candidate-selection limitations and a documented sample below the screening
   band. Keep unresolved relationships quarantined; do not invent reviewer decisions.
2. Establish the actual review-exposure ledger. Any case C sees substantively for rule
   design, including its final duplicate component, must be reserved for development.
   Design and record final-set access before exposing final-reference material.
3. Reconcile language/content review, canonicalization and exact source/prepared hashes,
   source/license restrictions, conflict/exclusion reasons and all group memberships.
   Check near-duplicates against non-target data before any unsupported-set evaluation.
4. Agree feasible split proportions/seed and support after exclusions. Recompute and
   verify one split per group, all class supports, transitive relationships and review
   reservations; report feasibility limits rather than quietly changing the rules.
5. Coordinate the reviewable ID mapping, authorized document access and development-only
   C primary **and review** allocation with D. Freeze and publish versioned manifests
   only after actual review and the agreed shared-foundation/publication conditions.

No final benchmark, human adjudication or final measurement is claimed. A later,
user-authorized exploratory baseline used the draft training and validation portions;
that run does not complete C-002 or constitute final benchmark training. The project
deadline remains 2026-11-24.

On 2026-11-19 the audit and draft byte checks both passed on Python 3.11.9.
The local comparison also rejected repeated source IDs across partitions.
For the split review, record document ID, duplicate group ID, review purpose,
reviewer and date before opening substantive text. Assign exposed duplicate
components to development before freezing the groups and splits. Keep
the exposure record in authorized local storage. See
[the development comparison](validation-report.md) and [D's handoff](integration.md#b-and-d-handoff).

## Prepared local review queue, 2026-11-19

`data/mtsamples/prepare_split_review.py` read the provisional metadata and
matched it to the source checksum, split checksum and row and group counts
recorded in the executed development comparison. It prepared these
ignored artifacts under `.cache/c002-split-review-2026-11-19`:

- `duplicate-review-queue.json` contains the three candidate pairs from
  six quarantined groups, their local document and group IDs, overlap
  counts, scores and empty reviewer, decision, reason and date fields.
- `development-exposure.json` records 860 training groups and 185
  validation groups, including member document IDs for future group
  reconciliation. These 1,045 groups were used in development. The
  ledger excludes all 183 draft-test groups and the pending candidate
  groups. The ledger records model use only. In-person or other review
  exposure can be added after the access decision.

| Queue row | Shared / side A / side B shingles | Jaccard | Smaller-side containment |
| --- | ---: | ---: | ---: |
| 1 | 1 / 784 / 1 | 0.0013 | 1.0000 |
| 2 | 374 / 593 / 388 | 0.6161 | 0.9639 |
| 3 | 151 / 163 / 160 | 0.8779 | 0.94375 |

The first pair was flagged because the smaller group has only one
five-token shingle and that shingle is shared. Treat it as a potential
short-fragment match for review. The second pair was flagged by
containment and the third by Jaccard. All three decisions are pending.
Queue generation used metadata. The review files contain no transcripts
or excerpts and stay in authorized local storage.

After access and reviewer approval, record the groups and documents to
be examined, reviewer, date and purpose before opening text. Record
whether the pair is a duplicate, a non-duplicate or unresolved, with a
reason. Record any newly exposed identities separately from the model
training and validation entries in the development ledger.
When grouping changes, propagate exposure from any member document
to its entire resulting duplicate component. Keep unresolved pairs
quarantined. The final split, canonical-text access and D's assignments
still depend on their reviews and F-014.

```powershell
python -B data/mtsamples/prepare_split_review.py `
  --development-receipt .cache/c-development-comparison-v1-verified/metrics.json `
  --output .cache/c002-split-review-reproduction
python -B -m unittest discover -s data/mtsamples/tests -q
```

All 11 data tests passed. A metadata reconciliation also confirmed that
the three pairs remain quarantined and that the development ledger is
disjoint from the 183 draft-test groups.

## Review decision preview, 2026-11-19

`data/mtsamples/preview_reviewed_split.py` compares the review inputs
against the original provisional metadata and executed development
receipt. It combines confirmed duplicate links transitively. Exposure
to any member places the whole resulting component in development.
Pending or unresolved links keep affected components unassigned.
Conflicting labels remain excluded. A component spanning two previous
partitions or an exposed component in the draft test partition is
flagged for review and its old assignment is withheld.

The verified [local preview](#reproduce-the-preview) has three pending
pair decisions across six quarantined groups. With the existing
review queue and model exposure ledger, it retains the following
provisional allocation. All five classes are represented in each split.

| Partition | Documents |
| --- | ---: |
| Train | 860 |
| Validation | 185 |
| Draft test | 183 |
| Unassigned | 101 |

The 101 unassigned documents form 55 provisional components. The
component flags include 46 label conflicts, six pending review groups
and four short-text flags. Flags can overlap. The preview contains
metadata and counts. It reads no source CSV or document bodies and
does not change the current split, assign newly eligible groups or
write a frozen manifest.

### Prepare review records after access is approved

Work on local copies of the queue and ledger. Keep the generated
group membership, input checksums and overlap measurements as issued.

1. Before substantively opening a document, reserve both groups for
   development with the reviewer, document and group IDs, review
   purpose, split version and reservation timestamp.
2. Record actual access with the reviewer, exact opened document IDs,
   their groups, split version, timestamp with timezone and review
   scope. Keep the scope brief and omit excerpts or personal details.
3. After reviewing a pair, record the decision as `duplicate`,
   `non_duplicate` or `unresolved`, together with the reviewer, date
   and reason. The new versioned workflow keeps a decision pending
   until both groups have recorded actual access by the decision date.
4. Run the preview against the reviewed copies. Resolve flagged
   components and agree the allocation of any newly eligible
   groups with the affected owners before preparing the freeze.
   A newly exposed component is eligible for development only.

Use `data/mtsamples/record_split_review.py` with the original pair numbers.
The `reserve`, `access` and `decide` actions each write a new local copy
after validation. An access record must follow the reviewer's reservation.
The tool uses the draft identifier `c002-draft-v1` bound to the verified
draft checksum. The operator supplies actual access details after the
team approves access.

```powershell
$reviewDir = '.cache/c002-split-review-2026-11-19'
$reviewer = '<approved reviewer>'
$reviewDate = '<actual date in YYYY-MM-DD>'
$reservedAt = '<actual reservation timestamp with timezone>'
$accessedAt = '<actual access timestamp with timezone>'
$receipt = '.cache/c-development-comparison-v1-verified/metrics.json'
$queue = "$reviewDir/duplicate-review-queue.json"
$ledger = "$reviewDir/development-exposure.json"
$reserved = "$reviewDir/development-exposure-pair-1.json"
$accessed = "$reviewDir/development-exposure-pair-1-accessed.json"
$reviewedQueue = "$reviewDir/duplicate-review-queue-pair-1.json"
python -B data/mtsamples/record_split_review.py --development-receipt $receipt --queue $queue --exposure $ledger `
  reserve --pair 1 --reviewer $reviewer --date $reviewDate --at $reservedAt --purpose 'Duplicate review' --output $reserved
# Open the reserved pair only after the reservation succeeds and access has been approved.
$documentArgs = foreach ($documentId in $openedDocumentIds) { '--document-id'; $documentId }
python -B data/mtsamples/record_split_review.py --development-receipt $receipt --queue $queue --exposure $reserved `
  access --pair 1 --reviewer $reviewer --at $accessedAt @documentArgs --reviewed $reviewedScope --output $accessed
python -B data/mtsamples/record_split_review.py --development-receipt $receipt --queue $queue --exposure $accessed `
  decide --pair 1 --reviewer $reviewer --date $reviewDate --decision $actualDecision --reason $briefReason --output $reviewedQueue
```

Set `$openedDocumentIds`, `$reviewedScope`, `$actualDecision` and
`$briefReason` from the real review. Record separate access events for
separate times or scopes, each based on the latest ledger. Preview the
updated queue with that ledger. For confirmed merges, `group_changes`
records previous group IDs with their documents and splits, the proposed
new group ID, proposed split, development-only status and reason. Share
changes with D through the approved access path before assignment freeze.
See [the B review request](c002-handoff-to-b.md) and
[D's confirmation](c002-handoff-to-d.md#ds-confirmation-2026-11-19).

The preview verifies recorded decisions and metadata consistency.
Reviewer acceptance, secure access to canonical text and F-014 still
govern final split freeze and D's downstream handoff.

### Reproduce the preview

```powershell
$reviewDir = '.cache/c002-split-review-2026-11-19'
python -B data/mtsamples/preview_reviewed_split.py `
  --development-receipt .cache/c-development-comparison-v1-verified/metrics.json `
  --queue "$reviewDir/duplicate-review-queue.json" `
  --exposure "$reviewDir/development-exposure.json" `
  --output "$reviewDir/split-preview-reproduction.json"
python -B -m unittest discover -s data/mtsamples/tests -q
```

The executed preview is `.cache/c002-split-review-2026-11-19/split-preview.json`.
The metadata rerun matched the saved preview and all input checksums.
All 22 data tests passed, including synthetic transitive merges, conflicting
labels, erroneous decisions, exclusion of exposed test groups and the
reservation, access and decision workflow.

### B confirmation and remaining prerequisites

On 2026-11-19 B confirmed C's ownership of provenance and reuse review,
and the canonical preparation rules for `nfc-lf-v1`. The published web
helper normalizes line endings to LF, applies NFC, and the built-in
synthetic preparation hashes the resulting UTF-8 bytes. Review access,
the dataset preparation entry point and the restricted C-to-D mapping
location still need agreement. [B's confirmation](c002-handoff-to-b.md#bs-confirmation-2026-11-19)

The local metadata check found three pending pairs across six
quarantined groups and zero recorded review access events. Git ignore
checks cover the queue, ledger and preview. Keep identifier-bearing
artifacts outside Git and chat. At verified `main` commit `1ac8bfe`,
F-011 was complete and F-014 was open. The allocation remains a preview
until review and the freeze prerequisites are complete.

D confirmed the stable dataset `doc_id`, shared assignment and digest,
unique submission IDs and restricted mapping access on 2026-11-20.
See the [assignment identity and access convention](c002-handoff-to-d.md#assignment-identifiers-and-access-2026-11-20).

### Authorized review and canonical preparation

On 2026-11-20 B approved Sara as sole reviewer of the three
quarantined pairs in the C-001 local copy. The checksum and length
were verified against the audit. Keep the source reports and
source-row mapping under Git-ignored `data/mtsamples/raw/`. The
mapping is to be deleted after review sign-off. Use the existing
[reservation and access workflow](#prepare-review-records-after-access-is-approved)
before and during review. The automated checks exercised synthetic
examples and did not read report bodies for review.

Use `data/mtsamples/prepare_transcription.py::prepare_transcription`
once per decoded transcription when preparing reviewed records.
The function returns `text`, `text_sha256` and
`canonicalization_version`. Use the same prepared text for evidence
offsets and keep the source hash separate from the canonical text
hash. The existing draft duplicate-comparison transform remains a
heuristic for grouping. It is not the canonical preparation path.

The function passed all seven preparation vectors from F-012 at
`1ac8bfe`. The C data suite ran 27 tests, and a separate comparison
against B's actual TypeScript implementation matched all 19 synthetic
inputs. Python and Node used different Unicode table versions. The
comparison covers the exercised inputs. The approved review can
proceed with Sara. F-014 is complete at tag `f-014-foundation`
(`7eb12e56f33240a428f916ba583b9e00077712df`).

## Signed-off local split freeze, 2026-11-20

Sara confirmed the three assisted review decisions. Pair 1 remains
unresolved and in quarantine. Pairs 2 and 3 each form one new duplicate
component. The local access ledger attributes document access to Codex
and the separate sign-off record attributes the decisions to Sara.

Local version `c002-split-v1` preserves all existing memberships from
`c002-draft-v1`. For the two newly eligible groups, the original
per-specialty target deficit uses the draft seed and 70/15/15 target
weights with assignment restricted to development. Both groups went
to training. The resulting counts are 864 training, 185 validation,
183 test and 97 excluded documents. All five specialties are represented
in each partition. Verification found disjoint document and group
memberships and confirmed that the test document and group membership
matches the draft exactly.

`data/mtsamples/freeze_splits.py` builds separate train, validation and
test manifests and a checksum summary from signed-off metadata. Run it
with the local development receipt and the ignored review directory.
Repeat with `--check` to verify the generated bytes. Actual transcriptions
are outside this freeze step. The local manifests and identifier-bearing
review files stay in the ignored raw directory.

`data/mtsamples/prepare_annotation_handoff.py` creates the approved
development metadata from the frozen validation partition. It records
local preparation access before accessing the source and applies
`nfc-lf-v1` to the selected transcriptions in memory. The output
version `c002-d002-development-v1` contains a checked manifest and
checksum sidecar. [D delivery status](c002-handoff-to-d.md#development-metadata-package-2026-11-20).
