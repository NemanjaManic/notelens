# Quickstart Validation: Python RAG

**Status**: A-001 completed; the approved A-002 extraction and cleaning increments are
implemented and verified. Passages and service commands remain future
work. Run from the repository root. No command here authorizes paid calls or
implementation beyond the user's approved package.

## Available now: correct feature selection

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-rag'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
& ./.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly
```

Expected: FEATURE_DIR selects this feature regardless of Git branch. This checks paths,
not whether an application, plan/task tests or services execute successfully.
The installed script exists and has been verified; no feature-state file is overwritten.

## Available now: approved local corpus extraction

A-002 now depends only on completed A-001. It does not wait for A-010, F-003,
F-004 or F-014 because it prepares A-owned local data without exposing an API.
The user separately approved implementation and execution of extraction after
the documentation correction.

The standard-library script `data/knowledge/scripts/prepare_corpus.py` reads the
local source ZIP and `data/knowledge/manifests/snapshot.json`. Its first increment extracts the 401
approved English topic records with summaries and source metadata. The separately
approved cleaning increment is also implemented, as described below. Passage
construction remains a later increment; A-002 is not complete. Chunk settings
are not chosen by this guide.

The extracted artifact is `data/knowledge/.cache/corpus/selected-topics.jsonl`,
which is Git-ignored. The small provenance/count/checksum record is
`data/knowledge/manifests/prepared-corpus.json`. No root package or shared schema
is required or changed by the offline pipeline.

The actual extraction command, executed on 2026-11-11, is:

```powershell
python -B data/knowledge/scripts/prepare_corpus.py extract
```

The script verifies approved selection status, selected-ID uniqueness, archive/XML
checksums and nonempty English summaries before writing. Existing output files
are never overwritten; the default outputs now exist in this working copy. For
a separately approved repeat run, select fresh owned paths with `--output` and
`--output-manifest`. The input manifest can be selected with `--snapshot-manifest`.
Paths are resolved against the script's repository root and constrained to the
owned input/output directories.

Run the available extraction/cleaning checks:

```powershell
python -B -m unittest discover -s data/knowledge/tests -p "test_prepare_corpus.py"
```

All 35 current checks passed on Python 3.14.2. They use synthetic XML/ZIP fixtures and
cover faithful Unicode/repeated-text preservation, IDs/language, source integrity,
excluded content, no network access, output path constraints and overwrite refusal.
An additional actual-source check compared all 401 extracted summaries and metadata
to the acquired XML. This does not establish retrieval quality, clinical validity,
or future service/Python 3.13 compatibility. A-002 remains unchecked until the
passage increment is implemented and checked.

## Available now: approved local summary cleaning

The user approved cleaning on 2026-11-12, including table preservation and recording
omitted images. The actual command was:

```powershell
python -B data/knowledge/scripts/prepare_corpus.py clean
```

This verifies the extraction artifact and snapshot-manifest checksums, approved
topic ID set and source provenance. It creates
`data/knowledge/.cache/corpus/cleaned-topics.jsonl` and
`data/knowledge/manifests/cleaned-corpus.json`. Original extraction inputs and
manifests remain unchanged. Every cleaned record retains the original HTML/metadata
and adds plain text plus its digest and cleaning version/counts.

All 401 topics were cleaned. Four image tags in topic 6681 were omitted and
recorded; 14 tables in 11 topics retain their text with row/cell boundaries.
Two HTML comments were omitted. No image/link body is downloaded or inferred.
See [rules, evidence and limits](../../docs/rag/sources.md#a-002-cleaning-increment).

The default outputs now exist and cannot be overwritten. A separately approved
repeat run must select fresh owned `--output` and `--output-manifest` paths.
Use `--extraction-manifest` to select another verified extraction record.
This command does not create passages or approve chunk settings. Render its
plain-text field as text, not trusted HTML.

## Future: service integration after foundation prerequisites

The later F-003/F-004/F-005 tasks must create frozen contracts/fixtures, dependency locks,
stubs and runnable commands. A command that names a missing file is not an executed pass.
These are service/integration prerequisites, not prerequisites of local A-002 data
preparation. A-003 joins the prepared corpus to the service only after A-002,
A-010 and F-014; A-010 itself requires F-003/F-004.
After those prerequisites and the relevant implementation tasks create the listed checks:

```text
uv run --directory services/rag python -m pytest tests/test_contract.py tests/test_retrieval.py tests/test_answers.py
```

These are planned acceptance commands using real tool CLIs, not claims that package scripts
or test files exist today. The backlog names the task that creates each target.
No npm run script is assumed; B must document and verify actual package scripts later.

## Independent scenarios

1. Start this workstream in key-free mock mode with other business modules absent.
2. Submit a valid synthetic/public example and verify shared structure plus evidence semantics.
3. Exercise empty/unsupported/insufficient, malformed upstream and provider-failure fixtures.
4. Include non-BMP/repeated-span cases, approved input caps and cross-session/expiry behavior
   where relevant. Use a controlled clock for expiry.
5. Report actual mock/module/live checks separately; business metrics and live checks remain
   unexecuted until their data, approvals and implementations exist.

## Exit and review

[Tasks](tasks.md) provide owner/path/dependency/acceptance details. Only A-001 is
checked in this backlog; A-002 and all service tasks remain unchecked. Do not
declare the shared foundation ready until the runnable mock flow,
handoffs, separate-working-copy commands and checkpoint evidence have passed.
