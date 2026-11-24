# C-001: MTSamples acquisition and audit

**Owner**: C. **Measured/reviewed**: 2026-11-11.
**Scope**: User-authorized local acquisition and audit; no training, inference or final evaluation.
**Branch**: `member-c/classification`, based on local documentation commit `e7bc839`.
The existing checkout is used for C's session; no additional worktree was created.

## Source identity and reuse review

The user supplied `mtsamples.csv` from the local Downloads archive. The original remains
unchanged. Its byte-identical copy is `data/mtsamples/raw/mtsamples.csv` (17,007,236 bytes).
SHA-256:

```text
a92cb78569f460606661ee7da50c92305b60d0fac2be4b06c8d2de0f234612d4
```

Attribution: Tara Boyle, *Medical Transcriptions*, Kaggle; source reports from MTSamples.com.
The [Kaggle data card](https://www.kaggle.com/tboyle10/medicaltranscriptions/data)
identifies scraped MTSamples reports and displays CC0: Public Domain.
The [metadata page](https://www.kaggle.com/tboyle10/medicaltranscriptions/metadata)
displays Version 1. The canonical `/datasets/` page returned no readable text; the alternate
Kaggle pages were readable through search. No remote checksum or authenticated download
was obtained, so this local file is versioned by checksum, not asserted to match Version 1.

The [upstream MTSamples site](https://www.mtsamples.com/) describes educational reference
use, permits educational printing/sharing/linking and requests credit to the site. It also
describes user-contributed reports without a guarantee of completeness or correctness.
These observations are a source review, not a legal opinion or certification of each
report's rights, privacy or clinical accuracy. The Kaggle license label does not by itself
verify rights in every upstream contribution. Local educational inspection follows the
user's request. Raw or cleaned text is not being redistributed; any later redistribution
needs the project's separate publication authorization and review of the actual material.
Keep the attribution above when sharing permitted material. No project-wide license is assigned.

## Measured schema and cleaning

Strict UTF-8 decoding succeeded. The six columns are an unnamed source-row ID column,
`description`, `medical_specialty`, `sample_name`, `transcription`, and `keywords`.
The audit checks field counts and unique nonempty source IDs. All 4,999 IDs passed.
The local file has 40 raw specialty labels, 33 empty/whitespace-only transcriptions,
and 4,966 nonempty transcriptions across all specialties.

Every target source label has one leading ASCII space. The JSON manifest preserves the
exact strings; the mapping removes surrounding label whitespace only. It performs no
case folding, synonym mapping or broad-category merging. In particular, Surgery and
Neurosurgery are not mapped to an organ-system target.

| Exact source label (JSON string) | Target | Before | Empty removed | After empty removal |
| --- | --- | ---: | ---: | ---: |
| `" Cardiovascular / Pulmonary"` | Cardiovascular / Pulmonary | 372 | 1 | 371 |
| `" Orthopedic"` | Orthopedic | 355 | 0 | 355 |
| `" Gastroenterology"` | Gastroenterology | 230 | 6 | 224 |
| `" Neurology"` | Neurology | 223 | 0 | 223 |
| `" Urology"` | Urology | 158 | 2 | 156 |
| Total | Five targets | 1,338 | 9 | 1,329 |

The other 3,661 source rows are outside the target label set. These counts partition all
4,999 rows as 3,661 non-target + 9 target-empty + 1,329 target-nonempty. Non-target rows
include their own empty rows, so do not subtract all 33 empties again.

The local generated subset contains document ID, source row ID, mapped category and
unchanged transcription. Empty detection uses `str.strip()` only as a predicate; retained
text is neither stripped nor normalized. It is not B's application canonicalization.
Descriptions, titles and keywords are excluded from the subset; labels and IDs must also
be excluded from future predictors. No language classifier, English review, semantic label
review or privacy certification has been performed.

## Preliminary duplicate warning

SHA-256 of unchanged UTF-8 transcription within nonempty targets finds 46 exact duplicate
groups covering 92 rows. All 46 have conflicting target labels. They remain in the
inspection subset so this audit does not silently make C-002 decisions. They must be
excluded from the initial single-label benchmark when C-002 runs. This is not a final
conflict count: normalization and near-duplicate analysis may reveal more groups.

No train/validation/test manifest, proportions, seed, fitted transformation or model has
been created. C-002 must document grouping criteria, inspect feasibility after conflict
exclusions, then freeze group-disjoint splits. Do not assume row-level stratification is safe.

## Reproducibility and executed verification

Implementation: [audit.py](../../data/mtsamples/audit.py), standard library only.
Aggregate evidence: [source.json](../../data/mtsamples/manifests/source.json).
Commands are run from the repository root with Python 3.11.9:

```powershell
python -B -m unittest discover -s data/mtsamples/tests -v
python -B data/mtsamples/audit.py
python -B data/mtsamples/audit.py --check
python -B -m json.tool data/mtsamples/manifests/source.json
git check-ignore data/mtsamples/raw/mtsamples.csv data/mtsamples/raw/targets-nonempty.csv
```

Eight synthetic tests passed: exact target/empty filtering and Unicode/CSV round trip,
conflicting duplicates, duplicate IDs, missing columns, malformed rows, invalid UTF-8,
repeatable CLI/stale-output detection, and protection from overwriting the source.
The real CSV audit and exact-byte regeneration check passed; the JSON parsed; both local
CSVs are ignored. Original and copied source SHA-256 hashes match. No document contents
are included in the manifest or command output. Synthetic checks do not measure model quality.

Spec Kit workflow: the installed `speckit-implement` skill was used only for T001/C-001,
respecting all later task dependencies. No template generation was needed. The repository
integration is pinned to 1.3.3; its upstream CLI version was not reinstalled or rechecked.
The official `check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` resolver selected
`specs/003-classification` with `SPECIFY_FEATURE_NO_PERSIST=1`. Direct execution was blocked
by PowerShell execution policy; the resolver succeeded in a child PowerShell process with
`-NoProfile -ExecutionPolicy Bypass`. No machine/user policy was changed. The 16/16 checked
requirements items are prior assistant specification review, not human acceptance.
No `.specify/extensions.yml` exists, so there were no before/after implementation hooks.

## First five tasks and remaining dependencies

| Task | Actual status | Required next input |
| --- | --- | --- |
| T001 / C-001 | Complete: local source, review, mapping, measured empty filtering and checks | No live-provider check applies |
| T002 / C-009 | Blocked; read-only interface proposal is available | B: F-003 frozen contracts and F-004 scaffold, including generated bindings |
| T003 / C-002 | Blocked | C-009 and B's F-014 reviewed runnable-foundation publication |
| T004 / C-010 | Blocked | D-003 development-only annotation assignments and independent-review instructions |
| T005 / C-003 | Blocked | C-002 frozen grouped splits |

XGBoost comparison, uncertainty policy, FastAPI packaging, B/D integration and the final
model card follow those tasks. C's annotation output cannot substitute for independent
human review. Final evaluation requires selection freeze and must not be run now.
See [interface proposal](interface-review.md) for concrete feedback to B. No external
messages, commits, pushes, deployments or paid calls were performed. Deadline remains
2026-11-24; completion of C-001 is not completion of Member C's workstream.
