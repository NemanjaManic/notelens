# Cleaning and duplicate-grouping proposal

**Owner:** C

**Date:** 2026-11-11

**Status:** Documentation proposal for C-002; not an executed grouping or frozen split.

**Related plan:** [Classification experiments](classification-experiment-plan.md)

## 1. Purpose, scope and execution gate

Prepare reproducible five-specialty data while preventing related copies of a report from
crossing train, validation and test boundaries. This proposal defines cleaning decisions,
duplicate evidence, conflict handling and the later split procedure. It does not select
a numeric similarity threshold, split proportions or seed, and does not run any data changes.

The existing C-002 gate remains C-001 + C-009 + F-014. C-009 requires F-003/F-004.
Writing this proposal does not complete any of those tasks or authorize shared-contract edits.
See [C's backlog](../../specs/003-classification/tasks.md) and
[team dependencies](member-c-status-and-dependencies.md).

## 2. Known input and measured starting point

Use the user-supplied local `data/mtsamples/raw/mtsamples.csv`, identified by SHA-256:

```text
a92cb78569f460606661ee7da50c92305b60d0fac2be4b06c8d2de0f234612d4
```

The existing audit measured 4,999 rows, 40 labels, 1,338 target rows and 1,329 nonempty
target rows. Within those targets, unchanged-text hashing found 46 duplicate groups,
all with conflicting target labels, covering 92 rows. These are preliminary observations,
not final group counts. Do not derive a claimed final usable total by subtracting only
those 92 rows: near duplicates and other exclusions remain unknown.

The [source manifest](../../data/mtsamples/manifests/source.json) and
[audit report](data-audit.md) preserve source identity, exact label strings and measured
counts. No remote release equivalence, full language review or privacy certification is implied.

## 3. Cleaning rules

| Input or condition | Proposed action | Recorded evidence |
| --- | --- | --- |
| Wrong checksum or changed source | Stop the frozen-release workflow; audit as a new source version. | Actual checksum and source version; no silent replacement. |
| Invalid UTF-8, malformed CSV or missing/duplicate source IDs | Fail validation; do not repair or guess fields. | Safe error and row reference where possible, without document bodies. |
| Label with surrounding whitespace | Strip label whitespace and match the exact five approved names. | Original label and mapped label. |
| Other category, including Surgery or Neurosurgery | Exclude from the five-class benchmark; retain an inventory entry. | `non_target_label`. |
| Empty/whitespace-only transcription | Exclude; do not replace with description, title or keywords. | `empty_transcription`. |
| Nonempty target transcription | Preserve the source text unchanged. | Source row ID, document ID and text digest. |
| Suspected non-English, corrupted or unusable content | Flag for documented review; unresolved cases do not enter the frozen benchmark. | Review status, reason and reviewer; no invented detector. |
| Text exceeding the supported application limit | Flag and exclude from the initial service-aligned benchmark unless reviewed requirements change. Never truncate. | `over_text_limit`, measured length and preparation version. |

Target labels are Cardiovascular / Pulmonary, Orthopedic, Gastroenterology, Neurology
and Urology. Only transcription text may become a predictor. Labels, IDs, descriptions,
titles and keywords are metadata or targets, not hidden model features.

B's eventual frozen canonicalization must be used consistently for service-aligned
training and inference inputs. Preserve a mapping from source digest to prepared digest.
C must not introduce a competing application canonicalizer. Count the 100,000-code-point
limit against that agreed prepared representation; C-001's current subset is not yet such
a service-aligned dataset. The 2 MiB limit applies to PDFs, not this benchmark CSV.

Use one primary exclusion reason in a documented precedence order for totals, and allow
additional flags. Reconcile source rows into non-target, empty target, other excluded
target and eligible target counts without double-counting overlapping reasons.

## 4. Three text representations

1. **Source text:** unchanged CSV transcription, with its original digest.
2. **Prepared text:** B's agreed canonical representation when available; preserved
   unchanged downstream and used for evidence/inference consistency.
3. **Comparison text:** temporary derived representation used only for duplicate detection.
   It must never replace source/prepared text or be used as evidence offsets.

Proposed comparison transformation: normalize Unicode to NFC, convert CRLF/CR to LF,
case-fold, and collapse runs of whitespace to one space, trimming outer comparison whitespace.
Keep digits, punctuation, negation, units and all other words. Do not remove boilerplate,
stop words, names, dates or numbers, and do not stem or translate. Version the transformation.
Comparison equality indicates a grouping relationship, not clinical equivalence.

## 5. Detect exact and near-duplicate relationships

### Exact relationships

Compare all nonempty target documents across all five labels. Never restrict candidate
pairs to a shared specialty. Confirm string equality when hashes match.

- `exact_source`: unchanged source text is equal.
- `exact_prepared`: the agreed prepared text is equal, if that representation is available.
- `exact_comparison`: comparison text is equal under the recorded transformation.

Keep these relationship types separate. The existing 46 groups come only from the first
type. Do not replace their recorded evidence with a stronger unmeasured claim.

### Near-duplicate candidate method

Propose a transparent lexical method, with no embeddings or corpus-fitted vectorizer:

1. Tokenize comparison text into Unicode word runs and individual non-whitespace
   punctuation tokens, preserving order. Record the tokenizer and Unicode/runtime version.
2. Form sets of contiguous five-token sequences (shingles). Five is a proposed method
   parameter, not a measured similarity threshold or an approved final configuration.
3. Compare every pair of distinct exact-group representatives. Retain member mappings.
   This target dataset is small enough to start with an inspectable exhaustive design;
   runtime must still be measured. Do not silently switch to approximate candidate search.
4. Record Jaccard overlap `|A intersection B| / |A union B|`, plus directional containment
   `|A intersection B| / |A|` and `|A intersection B| / |B|`, and both token lengths.
   Containment helps flag a copied report with an added section; it is not proof of duplication.
5. For fewer than five tokens, do not divide empty shingle sets or declare two short texts
   duplicates because both sets are empty. Exact matching still applies; flag nonexact short
   texts separately for review. Any additional short-text similarity method needs documentation.

No numeric Jaccard/containment cutoff is selected here. During C-002, inspect synthetic
duplicate/nonduplicate cases and a recorded development-reserved review set, including
scores near prospective boundaries. Select and record candidate thresholds before final
split freeze and before any model-performance results are available. Never tune duplicate
rules to make a classifier score improve.

Initially, near-match thresholds nominate pairs for review rather than automatically
proving duplicates. Review whether shared text represents a copied/edited report or only
a common template. Changed negation, dosage, anatomy or subject warrants explicit attention.
Lexical overlap is not semantic or clinical validation.

Each nominated pair receives `related_copy`, `shared_template_only`, or `unresolved`,
with a reason and actual reviewer. Accepted related copies become edges. Unresolved
candidate components are quarantined from the initial benchmark instead of being split
apart. Below-cutoff pairs are not proven unrelated; report candidate-selection limitations
and inspect a documented sample outside the nominated band.

## 6. Form groups and resolve conflicting labels

Create an undirected graph of eligible target documents, with exact and accepted
near-duplicate relationships as edges. A group is a connected component. If A is linked
to B and B to C, keep A/B/C together even when A/C have lower similarity. Inspect component
sizes and bridges for unintended template chains before freezing the graph.

Define a deterministic group digest from a versioned, unambiguous serialization of sorted
member document IDs. Preserve edge evidence and method/configuration version separately.
Changing memberships or grouping rules creates a new manifest version; do not silently
reuse an old split as though its groups were unchanged.

| Group outcome | Initial benchmark policy |
| --- | --- |
| Exactly one target label and no unresolved flags | Eligible; keep all records in one split. Report group sizes so repeated copies remain visible. |
| More than one target label | Exclude the entire group from the initial single-label benchmark. Do not majority-vote, relabel or retain only the convenient label. |
| Unresolved relationship or content review | Quarantine the affected component until resolved before freeze. |

Keep accepted groups intact even when an exclusion makes class balance inconvenient.
Row-level metrics must be accompanied by group-aware reporting in the experiment plan.

This initial grouping covers the five-target benchmark. It does not certify separation
from the other source categories. Before any excluded category is used as an unsupported
evaluation set, extend duplicate checks across both populations and keep related groups
out of conflicting roles. A Surgery-labelled copy is not automatically an independent OOD case.

## 7. Protect final-test independence during review

Maintain a review-exposure ledger: document/group ID, reviewer, review purpose and date.
Any text C examines substantively for rule design or later model decisions is reserved
for training/development, including its full eventual duplicate component. Do not put
those reviewed cases into C's locked final test. Machine-only checksums and aggregate
count inspection are distinct from substantive document review.

D coordinates access to final annotation material. If review exposure leaves too few
independent groups for a credible final set, report the limitation and seek a revised
evaluation arrangement; do not claim an untouched test set or invent additional data.

## 8. Later split procedure and manifests

After exclusions and review, measure eligible documents and independent groups per class,
component-size distributions and development-reserved groups. Select feasible train,
validation and test proportions and a seed from that evidence, recording them before
any model run. No fixed percentage is assumed in this proposal.

Allocate whole groups with class stratification where feasible. A proposed deterministic
assignment is to process larger groups first, break ties with the recorded seed, and
assign each to the split that best reduces predeclared per-class count deficits while
respecting development reservations and required class support. Document the objective,
tie-breaking and actual deviations. If constraints cannot be met, stop for review rather
than split a group, omit a class silently or search for a seed that improves model results.
Group-aware stratification balances competing constraints and is not guaranteed to give
perfect proportions. [scikit-learn grouped splitting guidance](https://scikit-learn.org/stable/modules/cross_validation.html#stratifiedgroupkfold)

Proposed future C-owned records under `data/mtsamples/manifests/`:

| Record | Required contents |
| --- | --- |
| `documents.jsonl` | Source checksum/row ID, document ID, label mapping, source/prepared digests, eligibility and exclusion/review flags. No report bodies. |
| `duplicate-edges.jsonl` | Endpoint IDs, relation type, comparison version, scores where applicable, decision and reviewer reference. |
| `groups.jsonl` | Group ID, sorted members, target-label set, conflict flag, eligibility and development reservation. |
| `exclusions.jsonl` | Document/group IDs, primary reason, additional flags and decision provenance. |
| `review-exposure.jsonl` | IDs, reviewer, purpose and access date; no copied clinical text. |
| `train.jsonl`, `validation.jsonl`, `test.jsonl` | Document ID, group ID, label and source/prepared identity. |
| `split-metadata.json` | Source/grouping/configuration hashes, seed, proportions, actual counts, software/code versions, freeze status and checks. |

These are proposed local data records, not alternative shared API schemas. D must review
the handoff fields before consuming them for assignments. Text stays in approved local
ignored storage; a manifest is not authorization to redistribute raw or cleaned reports.

## 9. C-002 acceptance checklist for later execution

- Every input row is accounted for; exclusions reconcile with totals and class counts.
- Text digests and source mappings are reproducible; retained text is never silently altered.
- Every accepted duplicate edge has both endpoints in the same group.
- Every eligible document belongs to one group and exactly one split.
- Train/validation/test document-ID and group-ID intersections are empty.
- Conflicting and unresolved groups are absent from all benchmark splits.
- Class support, achieved proportions and all review-exposure restrictions are checked.
- Fixed input/configuration produces identical manifests, independent of input row ordering.
- Deterministic synthetic cases cover exact copies, whitespace/Unicode changes, cross-label
  conflicts, transitive chains, shared-template negatives, short text and repeatable IDs.
- A remaining-near-match inspection records the method's limitations; no universal
  duplicate-detection guarantee is claimed.

The backlog's future verification target is
`uv run --directory services/classifier python -m pytest tests/test_splits.py`.
It is not available or executed by this documentation package. No groups, seeds, numeric
similarity thresholds or split manifests were created while writing this proposal.
