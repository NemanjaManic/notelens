# Annotation selection, pending templates and explicit adjudication

**Status:** runnable provisional tooling, synthetic demonstration only (2026-11-11).
C's production manifests and permitted canonical documents are absent in this checkout.
Actual D-002/D-003 selection/assignments and human reference work remain blocked.

## Synthetic selection demonstration

From the repository root after eval setup:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.annotations select eval/fixtures/annotation-source-synthetic.json --count 20 --reviews 10 --seed 20261111 --output eval/reports/local/annotation-demo
```

This command was executed. It writes an assignment **proposal** and reusable blank
templates under D-owned eval paths, never into A/B/C annotation directories. The
20 invented candidates exercise selection; they are not the promised real set.
Each primary quota is count/4; ten independent secondary reviews are planned here.
Every template has `entities: null`, `review_state: pending`, no human review and
`complete_document_review: false`. The output is not an instruction to begin final
annotation: `access_state: pending_team_policy` requires a team access decision first.

The algorithm is also tested with 40 distinct synthetic groups: ten primary items
per member, eight per specialty and at least ten separate reviewers. C's primary and
secondary work is development-only. This is algorithm verification, not 40 real
assignments. No generated reference labels are substituted for human annotations.

## Provisional input adapter for C review

C should provide a permitted source manifest with `kind: permitted_benchmark`, a
`source_version` and a `documents` array. Each document needs `doc_id`, `group_id`,
`specialty` (one of the five agreed display labels), `split` (validation/test), exact
canonical `text_sha256`, and `permitted_for_annotation: true`. These are **adapter
requirements**, not an unofficial replacement for C's split format. Agree the field
mapping with C, including dataset IDs versus B's per-submission IDs and canonical text
access. The tool does not download or regenerate source splits or verify licenses.

Selection is seeded and deterministic. It takes one representative per group,
allocates C from development first and prefers underrepresented specialties. It
rejects duplicate document IDs, cross-split duplicate groups or identical hashes,
conflicting group specialties, missing permission flags and infeasible counts.
Portion and specialty counts are reported; no dev/final proportion is silently
declared team-approved. Review feasibility/balance and final-set access before freeze.

## Submission and adjudication path

Each annotator fills only their own primary/review record in their own annotation
path after assignments and permissions are agreed. The blank template needs a unique
`submission_id` when filled. Primary and secondary records remain separate; a second
reviewer first creates an independent record before seeing the primary labels.

The `merge` command reads a permitted bundle containing `kind`, `assignment`,
`document`, `submissions` and an optional explicit `decision`, and writes a separate
reference file:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.annotations merge path/to/permitted-bundle.json --output path/to/reference.json
```

No real bundle is available yet. A pending-only workflow can be exercised with
the supplied synthetic fixture, without generating any labels:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.annotations merge eval/fixtures/pending-merge-bundle.json --output eval/reports/local/pending-reference.json
```

The merge function was also exercised with in-memory synthetic submissions. It checks
assignment/document identity and hashes, roles, independent annotators, exact mention
and evidence spans, required completed records and an explicit selected submission,
adjudicator and rationale. It retains normalized input-record SHA-256 provenance.
Without a decision it outputs pending adjudication with no canonical labels. A
synthetic decision can only produce `synthetic_adjudication`, never human review.
For real records, explicit human attestations are required; the tool does not prove
they are truthful and does not clinically validate them. D must review the evidence.

Partial label-by-label reconciliation can be recorded as a separately reviewed new
submission before an explicit adjudication decision. The merger does not manufacture
new labels or automatically resolve disagreements. No real or mock completed
submissions were written to other members' directories.
