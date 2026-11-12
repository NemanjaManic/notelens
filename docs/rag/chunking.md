# Candidate Passage Policy and Preparation Evidence

**Owner:** Nemanja (A). **Date:** 2026-11-12.
**Status:** A-002 offline preparation complete; retrieval quality remains unmeasured.

## Approval and scope

The user approved continuing after the proposed settings and their heuristic basis
were discussed. This approves an initial corpus-preparation candidate. It does not
approve an embedding model, live calls, a quality threshold or a measured optimum.

The maximum of 2,500 Unicode code points lets all current tables remain whole:
the largest table has 2,243 code points. The summary median is 1,162 code points.
Rounding the limit to 2,500 is a practical starting choice. The up-to-300 overlap
is a heuristic cap, 12% of that maximum; it has no measured retrieval advantage yet.
Neither value is an embedding tokenizer budget.

The scoped `speckit-implement` workflow used the official PowerShell prerequisite
resolver with `SPECIFY_FEATURE_DIRECTORY=specs/001-rag` and
`SPECIFY_FEATURE_NO_PERSIST=1`. The requirements checklist had 16 checked items
and zero unchecked items. No extension pre/post hooks are configured. These are
agent workflow checks, not human/team approval of interfaces or evaluation results.

## Deterministic policy

| Setting | Behavior |
| --- | --- |
| Policy version | `source-block-passages-v1` |
| Length unit | Unicode code points in the existing `cleaned_summary` |
| Maximum passage length | 2,500 |
| Maximum actual overlap | 300; zero is allowed |
| Packing | Greedy packing of complete source blocks/groups |
| Tables | Remain whole, including headers, cells, row order and comparisons |
| Lists | Split between complete source list items, including nested items |
| Long paragraphs | Split only between whitespace-delimited words |
| Trailing NIH attribution | Group with the immediately preceding unit when both fit the same ceiling |
| Oversized table/item or unbreakable word | Explicit preparation error; no silent splitting or truncation |

Optional overlap takes complete trailing paragraphs/items only when their suffix
fits the 300-code-point cap and the next new unit can still fit under 2,500.
Tables, paragraph fragments and attribution groups are not copied as overlap.
Every successive passage advances into new content. Blocks from different topics
are never combined. No source text is reordered, rewritten or augmented with a
copied heading or invented explanation.

The existing source-HTML parser recovers block boundaries and verifies them
against the already prepared canonical text, including its recorded cleaning
counts/version. It does not replace or re-save that text. Passage bodies are
exclusively `cleaned_summary[start:end]` slices. Whitespace-only separators may
fall between passages; every non-whitespace source character is covered.

The trailing-attribution rule avoids isolating a source credit when it can stay
with preceding content. The actual artifact has zero NIH-attribution-only
passages. The rule is narrowly defined for final `NIH: ...` paragraphs; no general
semantic filter or minimum passage-quality threshold is introduced.

## Artifacts and provenance

- CLI: `python -B data/knowledge/scripts/prepare_corpus.py chunk`.
- Input: `data/knowledge/.cache/corpus/cleaned-topics.jsonl`, verified through
  the [cleaning manifest](../../data/knowledge/manifests/cleaned-corpus.json),
  extraction manifest/artifact and approved snapshot/selection.
- Output: `data/knowledge/.cache/corpus/passages.jsonl`, Git-ignored.
- Output manifest: [passages.json](../../data/knowledge/manifests/passages.json).
- Earlier source, extraction and cleaning artifacts/manifests remain unchanged.

Each passage carries topic ID/title/URL/language, creation date, synonyms,
groups, source provenance, cleaning version, topic-text digest, configuration,
actual overlap and half-open code-point offsets `[start, end)`. Original HTML
and review questions are not copied into passage records.

A stable passage ID hashes the version/configuration, carried topic metadata,
topic-text digest and offsets, with a topic-ID prefix. Repeated text at distinct
positions has different IDs. A changed policy/content/provenance changes its
identity. The corpus version hashes the cleaned-artifact identity,
passage-artifact identity and policy. This is not an embedding/index version.

These are A-owned preparation records. Their mapping to frozen shared API records
requires A-010 and its shared prerequisites; this package does not edit contracts
or create a service.

## Actual measured results

| Result | Observed value |
| --- | --- |
| Selected/prepared unique topics | 401 |
| Passages | 617 |
| Topics with one passage | 255 |
| Maximum passages for one topic | 4 |
| Passage length, min / median / max | 318 / 1432 / 2500 code points |
| Passages with nonzero overlap | 201 |
| Largest actual overlap | 300 code points |
| Whole tables | 14 |
| Complete rendered list lines checked | 4947 |
| NIH-attribution-only passages | 0 |
| Artifact size | 1,900,204 bytes |
| Artifact SHA-256 | `4915adc09d6719f84e3315f8a0ea0ac37bc363d8b1a178c6d14f449aac85c938` |
| Corpus version | `2922f29e08b74bf668272c33a7f3f0599d8d16fc90d2242976e3d4476010579b` |
| Final preparation time, UTC | 2026-11-12T18:11:47.192503Z |
| Runtime used | Python 3.14.2 |
| Synthetic/offline unit suite | 52 tests passed |

Actual commands run from the repository root:

```powershell
python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"
python -B data/knowledge/scripts/prepare_corpus.py chunk
```

The new tests were run before implementation and failed for the missing passage
functions. The final suite covers all three stages, including non-BMP/repeated
text, stable/version-sensitive identities, word/item/table boundaries, bounded
progressive overlap, trailing attribution, hash-chain/metadata tampering,
deterministic repeated output, no network, QA exclusion, owned paths and overwrite
protection. Byte-identical repeated preparation was checked on synthetic fixtures.

Independent one-off checks examined all 617 actual records without calling the
builder: exact Unicode slices, recomputed identities, carried metadata, source
coverage, limits, all 14 rendered table blocks and all 4,947 rendered list lines.
They verified unchanged input/prompt hashes and output/script digests. All 14
exact excerpts from [the earlier exploratory review](corpus-quality-review.md)
remain contained within passages; one is explicitly context-only. Containment
does not establish answerability, semantic support or retrieval success.

## Completion and next gates

A-002 closes acquisition-dependent, offline parsing/cleaning/passage preparation.
Only A-001 and A-002 are checked in [the RAG backlog](../../specs/001-rag/tasks.md).
Service/model/index integration, tokenizer compatibility, retrieval metrics,
clinical validity and Python 3.13 compatibility have not been tested here.
There were no provider calls, dependency installations, commits, pushes or
deployments in this package.

Before A-003, check A-010, F-003/F-004 and F-014 against actual shared-team evidence.
Subsequent configuration comparisons require development data and their own
approval; the source-informed ten-question review is not a held-out final test.
Default outputs already exist and the CLI refuses to overwrite them. A separately
approved repeat run requires fresh owned output paths.
