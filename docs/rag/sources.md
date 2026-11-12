# RAG Corpus Sources and Approved Initial Selection

**Owner**: Nemanja (A). **Updated**: 2026-11-12. Source reuse review: 2026-11-11.
**Task**: [A-001 / T001](../../specs/001-rag/tasks.md).
**Status**: Source review, source-archive acquisition, metadata inspection and initial
topic selection are approved and recorded. The initial selection has 401 topics.
A-001 acquisition/provenance acceptance passed and its task is checked complete.
The A-002 extraction and summary-cleaning increments are implemented and verified.
Passage construction and RAG service implementation are not complete.

## Reviewed official sources

| Source | Purpose |
| --- | --- |
| [MedlinePlus XML files](https://medlineplus.gov/xml.html) | Official Health Topic downloads and dated releases. |
| [Health Topic XML description](https://medlineplus.gov/xmldescription.html) | Topic fields, summaries, language, synonyms and group membership. |
| [Linking to and Using Content from MedlinePlus](https://medlineplus.gov/about/using/usingcontent/) | Reuse boundaries and source acknowledgement. |

These documentation pages were inspected before acquisition. After explicit user
approval, the dated source ZIP described below was downloaded. No linked medical
article or additional external dataset was downloaded.

## Permitted content boundary

MedlinePlus identifies Health Topic summaries as public-domain content under its
published reuse guidance. It requests source acknowledgement. Use the following
credit with retained summaries and source displays:

> Source: MedlinePlus, National Library of Medicine.

The same guidance distinguishes copyrighted material, including A.D.A.M.
encyclopedia content, drug monographs and many images. Their availability through
links on MedlinePlus does not authorize copying them into this corpus. This review
does not assign a license to the NoteLens repository.

For NoteLens, retain only selected English Health Topic summaries and relevant
topic metadata. Exclude encyclopedia articles, drug monographs, images and linked
third-party page bodies. Do not follow outbound links or fetch linked pages while
preparing the corpus. Preserve the original topic URL for attribution and citations.

## Relevant XML fields

The official XML includes both English and Spanish topics. Select records with
`language="English"`; do not translate Spanish records into the supported corpus.

Preserve the topic ID, title, URL, language, creation date when present,
`full-summary`, available `also-called` synonyms and group identities/names.
Synonyms are optional, and a topic may belong to multiple groups. The topic creation
date is distinct from the downloaded release date. Record release and retrieval
dates separately for reproducibility.

## Acquisition and initial selection record

1. **Completed**: With explicit user approval, select the Health Topic ZIP release
   dated 2026-11-10 from the official download page and record its exact URL.
2. **Completed**: Download the ZIP into Git-ignored `data/knowledge/raw/**` and
   record its measured size, SHA-256 and UTC retrieval timestamp before any
   transformation. Check ZIP integrity without extracting files to disk.
3. **Completed**: With explicit user approval, inspect English topic metadata,
   count the base candidates and review the proposed scope adjustments below.
4. **Completed for the initial selection**: Record the user-approved rule,
   selected source topic IDs, exclusions/additions and measured selected-topic
   counts in the A-owned manifest. Disclose overlaps rather than treating the
   specialty-count sum as the unique total. This does not create a cleaned corpus.
5. Preserve the source acknowledgement and provenance for every retained topic.
   Check the retained content boundary before proposing any redistribution.
   Corpus cleaning, passage construction and index creation belong to later tasks
   with their existing prerequisites.

The [snapshot manifest](../../data/knowledge/manifests/snapshot.json) records the
source/download URLs, release date, retrieval timestamp, archive and member
checksums/sizes, attribution and actual archive checks. It now also records the
metadata inspection, measured source/candidate counts and the base group mapping.
The approved initial rule version, all selected IDs and selected-topic counts are
now populated. Processed/retained corpus and passage counts remain null.
These are A-owned corpus provenance records, not changes to B's shared API contracts.

## Acquired source archive

| Item | Observed value |
| --- | --- |
| Release date | 2026-11-10 |
| Download | [Official dated ZIP](https://medlineplus.gov/xml/mplus_topics_compressed_2026-11-10.zip) |
| Retrieved at (UTC) | 2026-11-11T07:36:15.2979036Z |
| Local archive | `data/knowledge/raw/2026-11-10/mplus_topics_compressed_2026-11-10.zip` |
| Archive size | 4,789,269 bytes |
| Archive SHA-256 | `d9ad993d2d277060c31ab2bb17144b1a85bdfadf47bf9aba197c58a849e9a501` |
| ZIP member | `mplus_topics_2026-11-10.xml` |
| XML member size | 30,150,738 bytes uncompressed |
| XML member SHA-256 | `53ac4b07603a8a23c90d7ec338296d9398a2d2d371bf038906df1e2796730e32` |
| Integrity check | ZIP CRC verification passed; no files extracted to disk |

These digests were computed locally. An upstream expected checksum was not
verified. The archive remains an unfiltered source snapshot containing both
languages; selected IDs are recorded separately. After the integrity check,
topic metadata was inspected locally in memory with separate user approval. This was a
one-off read-only inspection, not implementation of the A-002 ingestion module.

## Measured metadata inspection and candidate proposal

The local inspection on 2026-11-11 read the acquired XML without extracting files
to disk or following links. The measured 2,033 topic records match the XML root's
declared total: 1,017 English and 1,016 Spanish. All 1,017 English topic IDs are
unique. No English record was missing an ID, title, URL or group membership.

One English record has no nonempty summary: `Phobias` (topic ID `360`, group `5`).
It is outside the candidate groups below. Here, nonempty means that the summary
element exists and its text is not blank; it does not establish semantic support
for a question or demonstrate clinical review.

The proposed candidate rule takes English topics belonging to any listed group
and deduplicates them by topic ID. It applies no final exclusions or additions.

| Project specialty | Proposed MedlinePlus groups (IDs) | Unique candidate topics |
| --- | --- | ---: |
| Cardiovascular / Pulmonary | Blood, Heart and Circulation (`7`); Lungs and Breathing (`15`) | 140 |
| Orthopedic | Bones, Joints and Muscles (`10`) | 78 |
| Gastroenterology | Digestive System (`2`) | 79 |
| Neurology | Brain and Nerves (`14`) | 102 |
| Urology | Kidneys and Urinary System (`11`) | 25 |

The union contains **396 unique candidate topics**, all with nonempty summaries.
The specialty counts sum to 424 because some topics belong to multiple specialty
candidate sets; 424 is not the unique corpus count. The first row is already the
union of its two groups (93 and 51 topics, with four shared topics). Pairwise
cross-specialty overlaps are recorded in the snapshot manifest.

These are broad source groups, not an exact clinical-specialty mapping. The
candidate inspection found leukemia topics in the cardiovascular/pulmonary set. The
separate Male Reproductive System group (`43`) includes `Enlarged Prostate (BPH)`,
`Prostate Cancer`, `Prostate Cancer Screening` and `Prostate Diseases`, none of
which belongs to the urinary group in this snapshot. Group `43` has not been
added as an entire group to the base candidate rule. The approved adjustments
are recorded below; no arbitrary corpus-size limit has been chosen.

The first approval covered recording these findings as candidates. A subsequent
explicit user approval accepted the initial selection below.

## Approved initial topic selection

Nemanja (A) explicitly approved the initial selection on 2026-11-11. The rule
version is `medlineplus-en-topics-v1`, applied to the recorded 2026-11-10 XML
member and its SHA-256 digest.

Start with the 396 English candidates from the base groups. Remove the seven
explicit IDs below from every specialty set, then add the twelve explicit IDs
below to Urology. Deduplicate the result by topic ID. This retains 389 base
candidates and adds twelve previously absent topics: **401 unique selected topics**.

The complete numerically sorted ID list, IDs by specialty, source-member digest
and reasons are recorded in the snapshot manifest. These IDs identify topics
inside the acquired archive; no cleaned corpus file has been produced.

### Approved exclusions

| Topic ID | Title | Initial selection reason |
| --- | --- | --- |
| 138 | Anatomy | Very short summary primarily directing readers to links/images; linked bodies are not acquired. |
| 1437 | Acute Lymphocytic Leukemia | Defer leukemia-focused hematologic oncology from this initial corpus. |
| 1438 | Childhood Leukemia | Same scope decision. |
| 5620 | Leukemia | Same scope decision. |
| 5622 | Acute Myeloid Leukemia | Same scope decision. |
| 5624 | Chronic Myeloid Leukemia | Same scope decision. |
| 87 | Chronic Lymphocytic Leukemia | Same scope decision. |

This scope choice does not establish that the excluded sources are invalid.
Other blood-related candidates remain in the initial selection. Questions whose
needed evidence is absent must receive an explicit evidence-gap outcome.

### Approved Urology additions

All twelve additions are English topics from Male Reproductive System (group
`43`) and were absent from the original 396-topic union. The whole group is not
automatically included.

| Topic ID | Title | Coverage added |
| --- | --- | --- |
| 6196 | Enlarged Prostate (BPH) | Prostate explanations |
| 7 | Prostate Diseases | Prostate explanations |
| 112 | Prostate Cancer | Prostate explanations |
| 6208 | Prostate Cancer Screening | Screening explanations |
| 4280 | Testicular Disorders | Testicular explanations |
| 434 | Testicular Cancer | Testicular explanations |
| 1360 | Penis Disorders | Male genital explanations |
| 118 | Erectile Dysfunction | Sexual-function explanations |
| 5571 | Sexual Problems in Men | Sexual-function explanations |
| 5656 | Male Infertility | Male fertility explanations |
| 189 | Circumcision | Named-procedure explanation |
| 5821 | Vasectomy | Named-procedure explanation |

The twelve remaining supplemental topics are deferred: Assisted Reproductive
Technology, Birth Control, Chlamydia Infections, Genital Herpes, Genital Warts,
Gonorrhea, Herpes Simplex, Infertility, Reproductive Hazards, Sexual Health,
Sexually Transmitted Infections and Syphilis. Their IDs are recorded in the
manifest. This is an initial coverage choice, not a clinical classification claim.

### Selected-topic counts and review limits

| Project specialty | Selected topics |
| --- | ---: |
| Cardiovascular / Pulmonary | 133 |
| Orthopedic | 77 |
| Gastroenterology | 78 |
| Neurology | 101 |
| Urology | 36 |

These counts sum to 425 because specialty sets overlap. Their union is 401;
specialty memberships are metadata and must not become mandatory retrieval filters.

The review covered titles of all 396 base candidates and all 25 supplemental-group
topics, plus the full summaries of the nineteen explicit exclusions/additions.
The remaining 389 base summaries have not received individual semantic review.
This is agent scope review followed by user approval of the initial selection;
clinical validation, question-level evidence support and measured retrieval quality
are not established. The approval does not freeze prompts, models or final tests.

## A-001 acceptance review

**Reviewed**: 2026-11-11. **Result**: A-001 completed for source acquisition,
provenance and initial topic selection, after the user's explicit conditional
approval and successful checks. This does not complete the RAG module.

| A-001 criterion | Evidence and result |
| --- | --- |
| Review English Health Topic fields, reuse and attribution | Official documentation reviewed; field boundary, reuse URLs and source acknowledgement recorded above and in the manifest. |
| Acquire authorized content | Explicitly approved dated Health Topic ZIP acquired from the official URL; no linked page bodies or additional datasets acquired. |
| Record the actual snapshot and checksums | Release/retrieval dates, ZIP/member sizes and SHA-256 digests recorded and matched against the local archive. |
| Record measured topic counts | 2,033 source records, 1,017 English records, 396 base candidates and 401 approved selected IDs; specialty overlap is explicit. |
| No outbound crawling | Only the approved source ZIP and official documentation were accessed; linked content was not fetched. |

The required command, `python -B -m json.tool data/knowledge/manifests/snapshot.json`,
passed. Additional one-off local Python standard-library checks verified ZIP CRC,
sizes/digests, all selected IDs, the approved selection rule, nonempty summaries
and the raw archive's Git exclusion. All 401 selected topics have a title, source
URL and creation date; 224 have optional `also-called` synonym fields preserved
in the source XML. Empty synonym lists are permitted by the source format.

The recorded checks examined the actual acquired archive. They are not mock
service tests, clinical validation or retrieval measurements. No upstream
expected checksum was verified. The source download was an actual authorized
network operation; paid-provider and deployment checks were not applicable and
were not run.

The manifest preserves the source archive identity and selected IDs. Canonical
topic records, text cleaning, stable passages and passage counts are A-002
deliverables, and embeddings/indexing are A-003 deliverables. Their prerequisites
and unchecked task status remain unchanged. No full Spec Kit implementation
workflow was invoked to close the entire backlog; this was an A-001 acceptance
review only.

## A-002 extraction increment

**Executed**: 2026-11-11. **Owner**: Nemanja (A). **Status**: extraction-only;
A-002 remains unchecked. The user explicitly approved the script, tests, local
extraction and source/count record after the dependency correction.

Implemented [the standalone extractor](../../data/knowledge/scripts/prepare_corpus.py)
and [its tests](../../data/knowledge/tests/test_prepare_corpus.py) using Python's
standard library. No service scaffold, shared schema or root dependency files
were changed. The script reads only the local approved snapshot and ZIP, verifies
their source identity, and extracts the exact approved topic-ID set.

The local output is `data/knowledge/.cache/corpus/selected-topics.jsonl` and is
excluded from Git. It preserves the original logical XML summary value, including
HTML markup, whitespace, Unicode characters and repeated text. Topic records
include title, URL, language, creation date, synonyms, groups, snapshot date,
attribution and source digests. Site records, linked page bodies and evaluation
references are not extracted. No HTML cleaning or rendering is performed.

| Observed result | Value |
| --- | --- |
| Extracted unique English topics | 401 |
| Topics with available synonyms | 224 |
| Artifact format | UTF-8 JSONL, one topic per line |
| Artifact size | 1,602,715 bytes |
| Artifact SHA-256 | `e29f7943cec01d428db10dcee8287b799d116edc64b7b713ef75a4fe68ab17ed` |
| Actual extraction time (UTC) | 2026-11-11T17:42:56.454443Z |
| Runtime used for checks | Python 3.14.2 |
| Synthetic/offline unit checks | 19 passed |
| Actual source comparison | All 401 summaries and extracted metadata matched the source XML |
| Cleaned topics / passages | Not produced; null counts |

The [prepared-corpus manifest](../../data/knowledge/manifests/prepared-corpus.json)
records input manifest/archive/member identities, selection/extractor version,
script digest, output size/checksum and measured counts. The original snapshot
manifest and ZIP are unchanged. Output files are created exclusively; an existing
artifact or report is never overwritten.

Actual commands run from the repository root:

```powershell
python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py" -v
python -B data/knowledge/scripts/prepare_corpus.py extract
```

The unit suite uses synthetic MedlinePlus-shaped XML/ZIP fixtures and covers
Unicode/repeated text, exact selection, invalid IDs/language/metadata, source
integrity, forbidden entity declarations, excluded linked/evaluation content,
no network access, constrained owned paths and overwrite refusal. A separate
read-only comparison checked every actual output record against the acquired XML
and independently recomputed the output checksum. This is finite offline
extraction evidence, not clinical validation or a running RAG/retrieval check.

The `speckit-implement` agent workflow was scoped to this user-approved partial
A-002 increment. Its official PowerShell prerequisite check selected
`specs/001-rag`, and the built-in requirements checklist had 16 checked items and
zero unchecked items. That is agent-maintained specification-quality evidence,
not human acceptance or completion of the remaining backlog. The script and
tests are actual new implementations; future service tests were not run.

At the end of extraction, summary cleaning and stable passage construction remained
separately approved increments; the subsequent cleaning is recorded below.
Original summary HTML must not be treated as sanitized UI
content. Embeddings, indexing, retrieval, provider calls and deployment were not
performed in this package.

## A-002 cleaning increment

On 2026-11-12, Nemanja approved plain-text cleaning, tests and processing of the
local corpus. After the HTML structure audit found tables/images, he explicitly
approved preserving table text/structure and recording omitted image tags. This
package uses the `speckit-implement` agent workflow scoped to cleaning only.
The official PowerShell prerequisite resolver selected `specs/001-rag` using
`SPECIFY_FEATURE_DIRECTORY` and `SPECIFY_FEATURE_NO_PERSIST=1`; all 16 specification
checklist items were checked. No extension pre/post hooks are configured. These
are agent workflow/check results, not human/team acceptance of interfaces.

Cleaning uses Python's standard-library `HTMLParser`. It preserves visible text
order, heading/paragraph boundaries, list markers and visible link text; HTML
character references are decoded once and whitespace is normalized. Inline
formatting does not split words. Table rows stay in order on separate lines;
cells use ` | ` separators, including empty cells, and retain header/value order.
Lists within cells retain `- ` item markers with cell whitespace collapsed.
Image tags and comments are omitted and counted; attributes, image content and
linked page bodies are not imported. Unsupported/unbalanced markup, merged table
cells and empty summaries fail rather than silently dropping topic text. There
is no case-folding, stemming, deduplication, translation or medical rewriting.

The new artifact is `data/knowledge/.cache/corpus/cleaned-topics.jsonl`, Git-ignored.
Every record retains all original fields, including `full_summary`, and adds
`cleaned_summary` plus `cleaning` version/format/text digest and omission/table
counts. The new [cleaning manifest](../../data/knowledge/manifests/cleaned-corpus.json)
links extraction manifest/artifact and source identities, script/cleaner version,
output size/checksum, measured counts and affected topic IDs. Existing snapshot,
ZIP, extraction artifact and extraction manifest remain unchanged. Output files
are created exclusively and are not overwritten.

| Observed result | Value |
| --- | --- |
| Cleaned unique English topics | 401 |
| Tables / affected topics | 14 / 11 |
| Omitted image tags / affected topics | 4 / 1: topic 6681, Guide to Good Posture |
| Omitted comments / affected topics | 2 / 1: topic 1095 |
| Artifact size | 2,631,848 bytes, including retained original HTML |
| Artifact SHA-256 | `2d12d44f9be4f09db3ebaeb969a0335beb621ded7cdb793ccbafdbbfc0658639` |
| Actual final cleaning time (UTC) | 2026-11-12T10:31:27.444837Z |
| Runtime / synthetic offline tests | Python 3.14.2 / 35 passed |
| Passages | Not produced; null count |

All four image tags had empty alternative text. Their content was neither
downloaded nor inferred; inspect the source topic for visual information.
All affected table/image/comment topic IDs are recorded in the manifest.

Actual commands run:

```powershell
python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"
python -B data/knowledge/scripts/prepare_corpus.py clean
```

The expanded suite covers paragraph/list/table structure, lists inside cells,
negations/numbers, non-BMP/repeated text, single entity decoding, link/image/comment
handling, unsupported markup, input checksums/IDs/provenance, deterministic artifact
bytes, omission reports, unchanged inputs, path/overwrite protection and no network.
Initial tests failed for missing cleaning functions before implementation. A
read-only actual-corpus preview then exposed lists inside two tables; support
and a regression check were added before producing the final output.

An independent read-only comparison checked every original field and the order of
visible non-formatting characters against source HTML for all 401 topics. It
ignores whitespace and the formatting characters `-`/`|`; it is not a semantic
equivalence test. Per-topic text/artifact/script digests, image/table/comment
counts and all four unchanged input digests were verified. This is finite offline
evidence, not clinical validation, retrieval measurement, service compatibility
or a Python 3.13 test. Original HTML is not sanitized; cleaned text must be
rendered as text rather than inserted as trusted HTML.

No passages, embeddings, index, HTTP service, provider call, installation,
commit/push or deployment is part of this increment. A-002 remains unchecked.
Next propose and approve chunk settings before the passage-building increment.

## Current evidence and remaining work

- The source ZIP is acquired and locally integrity-checked; it remains outside Git.
- Source, base-candidate, approved selected-topic and actual extraction counts are
  measured as reported above. All 401 selected topics are cleaned; passage count
  remains unmeasured/null. Snapshot and prepared-corpus manifests remain acquisition
  and extraction records; cleaned-corpus records the separate cleaning stage.
- The initial topic selection is approved. Further scope changes require another
  applicable approval. No corpus size target has been invented.
- XML parsing was used for the earlier local inspection and the approved standalone
  extraction script. No service ingestion adapter, embeddings, vector index,
  provider calls or retrieval evaluation ran.
  Evaluation questions/reference answers must remain outside the retrieval index.
- A-001 is complete for source review, source-archive acquisition, provenance and
  the approved initial selection. A-002 has verified extraction/cleaning progress;
  no other task was marked complete. The user-approved 2026-11-11 dependency
  correction makes standalone local A-002 preparation dependent only on A-001.
  Extraction and cleaning are separately approved and executed; passages are pending.
  See the [revised plan](../../specs/001-rag/plan.md) and
  [task boundaries](../../specs/001-rag/tasks.md). Service integration retains
  A-010/F-014 prerequisites at A-003; separate implementation approvals still apply.

Follow the [RAG specification](../../specs/001-rag/spec.md),
[task dependencies](../../specs/001-rag/tasks.md) and
[allowed paths](../team/allowed-paths.md) for subsequent work. Publication, paid
activation and later implementation require their own applicable approvals.
