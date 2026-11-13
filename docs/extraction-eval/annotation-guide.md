# Annotation Guide: Extraction and Evidence

- **Owner:** D / Milica
- **Date:** 2026-11-11
**Status:** D's completed proposal for team review; synthetic training examples only. No assignments,
annotations, clinical validation, frozen references or team approval are implied.

This guide is D's D-001 proposal for the four-person NoteLens team. The team must review
and adopt the procedures before actual assignments. The frozen shared API is owned by B;
annotation rules below do not change that API.

## Frozen contract mapping (2026-11-13)

The frozen `contracts/v1` ExtractionItem has a required exact `mention` span and separate
supporting `evidence` spans, each using half-open Unicode code-point offsets and exact
canonical quotes. Annotate one record per contiguous mention occurrence. The mention
span identifies the named concept; evidence includes the context needed to judge
assertion, time, subject and procedure state. Repeated mentions remain separate records.
Discontinuous mentions are not represented as one mention span; record supported
contiguous occurrences separately and raise unresolved cases for review.

The API assertion values are `confirmed`, `suspected`, `negated`, and `unknown`.
Use `unknown` only when the source cannot justify one of the other values; do not use it
for a processing or annotation failure. Procedure items require `procedure_status` from
`planned`, `ordered`, `performed`, `cancelled`, `hypothetical`, or `unknown`; non-procedure
items require null. Procedure state is independent of assertion, temporality, and subject.
For example, a confirmed plan remains planned, not performed.

The D-owned practice data and linter still contain historical proposal wording from
before this freeze. Treat this guide as the proposed annotation policy and the canonical
schema as the wire definition; update the practice set before using it to train annotators.
The matching convention for relaxed boundaries and the semantic source-support rubric
remain proposals for the team to adopt. No team agreement, actual assignment, annotation,
or clinical validation is implied here.

## 1. Purpose and boundaries

Annotate what an assigned English source document explicitly says about diagnoses,
symptoms and procedures. Preserve uncertainty, negation, time and the person referred
to. The goal is a reproducible human-reviewed reference for evaluating extraction,
not clinical diagnosis or clinical validation. Do not use outside literature to add
facts, infer missing diagnoses or codes, or reconcile contradictions by guessing.

Use only documents supplied through the agreed, permitted dataset workflow. Do not
upload real personal reports, paste source documents into chat, or copy raw dataset
content into a public repository before C's provenance and reuse review. Synthetic
examples below are safe to share. A public dataset release is not automatically
approved for redistribution.

## 2. Before working on an assignment

1. Wait for D's frozen assignment manifest and access instructions after C publishes
   group-disjoint C-002 manifests. Do not self-select a final-test document.
2. Confirm your document ID, group ID, split, reference/guide version and whether the
   work is a primary annotation or an independent review. If a document is missing,
   inaccessible or mismatched, stop and report its ID, not its text.
3. Use the exact prepared canonical text and its recorded SHA-256. Do not normalize,
   edit or replace text while annotating; offsets must refer to that exact version.
4. Before model selection C receives only development assignments and reviews.
   No final-reference content or feedback should be used in model/prompt/threshold
   selection. D and the team must settle final-set access before real assignments.
5. Save only in your own `eval/annotations/member-<alias>/` path. Do not edit another
   member's primary or review file. The final submission format and permitted storage
   are to be agreed before actual source material is copied into repository files.

## 3. What counts as an entity

Annotate each explicit **mention** as a distinct candidate, even if the same words
appear more than once. A mention is a source occurrence, not a deduplicated disease
concept. Do not infer an entity solely from an interpretation of test results or
general medical knowledge.

| Type | Annotate | Do not infer |
| --- | --- | --- |
| `diagnosis` | An explicitly named condition or disease, including negated, suspected, historical and family mentions. | A new diagnosis from symptoms, tests or a classifier specialty label. |
| `symptom` | An explicitly stated symptom or subjective complaint, including a denial. | A symptom that is merely common for a named diagnosis. |
| `procedure` | An explicitly named clinical procedure or intervention; record whether the source says it was performed, planned, cancelled or uncertain. | That a planned, ordered or hypothetical procedure was performed. |

Use the shortest continuous source span that identifies the mention without changing
the source words. Exclude surrounding assertion cues such as `denies` from the
mention span, but include them in a separate evidence span. For nested or overlapping
mentions, record each distinct supported concept when needed and flag the boundary
for review; do not create duplicates merely by selecting a longer version of the same
concept. Ambiguous category or boundary: record a question and ask D; do not guess.

The annotation unit follows the frozen `ExtractionItem`: each contiguous occurrence
has a separate mention span. Distinct overlapping concepts may have separate records;
do not duplicate the same concept occurrence by extending its boundary. How relaxed
overlap scoring handles nested mentions remains a team decision.

## 4. Assertion, time, subject and procedure state

Record the three dimensions independently, based on the source context. They are
attributes of the mention, not a statement about medical truth. Use the frozen API
values below; an unresolved annotation question is kept separately from model failure.

| Dimension | Values and guidance |
| --- | --- |
| `assertion` | `confirmed`: explicitly stated as present or performed; `suspected`: explicitly uncertain, possible, probable or being considered; `negated`: explicitly denied or ruled out; `unknown`: source context cannot justify one of those three values. Do not use `unknown` for a processing failure. |
| `temporality` | `current`: explicitly current in the relevant narrative context; `historical`: explicitly prior/history; `unknown`: timing is not established. Past tense alone may need surrounding context: flag ambiguity. |
| `subject` | `patient`, `family`, `other`, or `unknown`. Do not turn a relative's condition into the patient's. Do not infer a subject when the context is insufficient. |
| Procedure status | For procedure items use `planned`, `ordered`, `performed`, `cancelled`, `hypothetical`, or `unknown`; for non-procedure items use null. This is independent of assertion, time and subject. |

Keep annotator questions in the separate unresolved-question field; do not encode them
as an entity label. Evidence must include enough context to support all
assigned attributes, which may require multiple exact spans if the context is separate.
The meaning of uncertain and overlapping status cues remains subject to team review.

## 5. Exact mentions and evidence

For each mention record its source text and interval and at least one separate evidence
interval/quote. Both use zero-based, half-open Unicode **code-point** indices:
`0 <= start < end <= len(canonical_text)` and `canonical_text[start:end] == quote`.
The evidence may equal the whole sentence when necessary to preserve denial, subject
or uncertainty. A correct quote is not automatically evidence that supports the label:
check meaning and context separately.

Count decoded Unicode code points, not UTF-8 bytes or JavaScript UTF-16 code units.
When a browser highlights spans, B converts the wire/code-point index to UTF-16. For
duplicate text, record the actual intended occurrence and its own offsets. Never use
the first matching occurrence as a substitute for the selected one.

### Synthetic walkthroughs

These examples illustrate proposed decisions; they are not real annotations or
clinical ground truth. Mention intervals are for the exact displayed text, including
punctuation and spaces. Evidence is the complete sentence unless otherwise stated.

| Canonical text | Mention and interval | Proposed annotation / reason |
| --- | --- | --- |
| `The patient denies chest pain.` | `chest pain` `[19,29)` | `symptom`, `negated`, subject `patient`; timing is `unknown` unless context establishes current. Evidence `[0,30)` includes `denies`. |
| `The patient's mother has diabetes.` | `diabetes` `[25,33)` | `diagnosis`, `confirmed`, subject `family`; `unknown` timing unless context establishes it. Evidence is the complete sentence. |
| `The patient had an appendectomy in 2018.` | `appendectomy` `[19,31)` | `procedure`, `confirmed`, `historical`, `patient`; `procedure_status=performed`. Evidence is the complete sentence. |
| `Pneumonia is suspected.` | `Pneumonia` `[0,9)` | `diagnosis`, `suspected`; subject and time are `unknown` without additional context. Evidence `[0,23)`. |
| `Colonoscopy is planned for next week.` | `Colonoscopy` `[0,11)` | `procedure`, `confirmed`, `unknown` temporality, `unknown` subject, `procedure_status=planned`. A confirmed plan is not a performed procedure. |
| `🩺 No chest pain. No chest pain.` | first `No chest pain.` `[2,16)`; second `[17,31)` | Two evidence occurrences, each negated. The emoji is one Unicode code point; a browser uses a different UTF-16 position. Mention `chest pain` boundaries must be recorded separately for each occurrence. |

If the input contains contradictory statements, annotate both with their own spans and
contexts. Do not decide which one is clinically true. If no source supports a
requested fact, record no positive evidence for it.

### Team practice and answer key

The [synthetic practice examples](annotation-training-examples.json) contain 16
invented English documents and 18 proposed mention annotations, including both
occurrences in the repeated-denial example. They are a draft exercise and answer key,
not measured model output, human-reviewed ground truth, a shared API contract or a
real assignment.

Before an assigned record is sent for independent review, run the D-owned structural
draft linter and inspect unresolved questions. After the independent record is
preserved, the [comparison tool](annotation-tooling.md#independent-submission-comparison)
can organize exact-boundary and attribute differences for human adjudication. Neither
tool decides semantic completeness or clinical truth.

For practice, read each `canonical_text` and identify the mentions, type, assertion,
temporality, subject and evidence before comparing with `mentions`. For each span,
check that slicing the text with the listed code-point offsets returns its `quote`.
The SHA-256 identifies the exact UTF-8 bytes of that synthetic canonical text. The
practice records use frozen assertion and procedure-status values. Bare ambiguous mentions use `unknown`; plans and cancellations retain independent procedure status. Bring policy disagreements to the team.

These examples include proposed answers, so they are appropriate for training and
rule discussion only. Do not score them as an independent or final benchmark.

To check the synthetic file locally from the repository root, run:

```powershell
python -B docs/extraction-eval/check_training_examples.py
```

The check needs only Python 3.11 or newer and its standard library. It verifies draft
record fields, document hashes, exact code-point slices, distinct mention spans and
source-present ICD evidence. It reports counts and error locations without printing
the text or quotes. It does not verify clinical correctness, semantic support, the
shared API schema, real annotations or a running extraction service. Use it only for
the accompanying synthetic training file; do not use user-submitted reports as input.

### Practice scenario index

| Example ID | What to examine | Proposed answer or discussion point |
| --- | --- | --- |
| `denial` | A symptom the patient denies. | Mark the symptom as negated; preserve the patient's identity. |
| `family_history` | A condition stated about the patient's mother. | Attribute the condition to family, not the patient. |
| `historical_procedure` | A procedure explicitly performed in 2018. | Keep historical time and the performed note separate. |
| `suspected_diagnosis` | A diagnosis explicitly described as suspected. | Preserve suspicion; do not infer patient or time. |
| `planned_procedure` | A colonoscopy planned for next week. | Do not call it performed; use confirmed assertion, unknown temporality and planned procedure status. |
| `repeated_denial` | Two identical statements after an emoji. | Record two separate occurrences with code-point positions. |
| `current_condition` | An explicitly current condition. | Preserve the word `currently`; do not invent an ICD code. |
| `historical_diagnosis` | An illness explicitly mentioned in 2018. | Keep it historical; do not present it as current. |
| `family_negation` | A family member denies a diagnosis. | Negation and family subject both apply. |
| `negation_scope` | A denied symptom and a reported symptom in the same sentence. | The denial applies to fever, not automatically to cough. |
| `contradictory_mentions` | A denial followed by a reported symptom. | Preserve both claims and their different evidence; do not clinically reconcile them. |
| `cancelled_procedure` | A planned procedure that was cancelled. | Use confirmed assertion and cancelled procedure status; do not infer that the procedure occurred. |
| `explicit_icd` | A code explicitly present beside a diagnosis. | Copy only the source code and its exact evidence; code presence is not clinical validation. |
| `no_inferred_icd` | A diagnosis with no source code. | Leave ICD absent rather than guessing one. |
| `no_supported_mentions` | A sentence with no diagnosis, symptom or procedure. | A completed synthetic review may return no mentions; that differs from a failed or incomplete review. |
| `uncertain_subject` | A symptom mentioned without identifying whose symptom it is. | Subject remains unknown; assertion interpretation is flagged for review. |

For a team walkthrough, assign a few synthetic examples independently, compare the
answers and record disagreements about boundaries or context. Only after each person
has recorded an initial answer should they consult the proposed answer key and discuss
differences. These practice examples do not count toward the 40-document annotation
target or the independent reviews required for the actual reference set.

### Reading a proposed record

For `negation_scope`, the proposed record has two mentions: `fever` is `negated`
and `cough` is `confirmed` as a reported symptom. Both use the same complete source
sentence as context, but their mention intervals are different. This illustrates why
a valid source quotation must still be examined for whether it supports each claim.

For `explicit_icd`, the `icd` object in this practice record includes an exact
source-present code and its own evidence interval. It is a synthetic annotation
example, not an external validation that the code is clinically correct. The
`no_inferred_icd` example deliberately has no `icd` object.

For `no_supported_mentions`, the empty list reflects a complete review of one
short synthetic sentence. It does not define how a production service reports an
incomplete or failed extraction; that interface decision remains open with B.

## 6. Proposed independent submission format

This is a **draft local annotation record**, not a frozen JSON Schema or public API.
D will publish the final field names and paths with assignments after team review and
data-permission checks. Do not submit an empty or synthetic template as a real review.

For each document record:

- assignment ID, document ID, duplicate-group ID, split/portion, text SHA-256,
  canonicalization version, guide version, annotator alias and submission version;
- each mention's local ID, type, exact mention span/quote, assertion, temporality,
  subject, exact evidence span(s)/quotes and any source-present ICD code and evidence;
- separate unresolved questions, source-supported procedure-status notes and reasons
  for ambiguity, without adding invented facts;
- an explicit statement that the complete assigned document was reviewed, or a
  documented incomplete reason; distinguish no mentions from incomplete work.

Suggested paths after assignment: primary submissions under
`eval/annotations/member-c/primary/` and independent reviews under
`eval/annotations/member-c/reviews/` for C; other members use their own alias paths.
The assignment manifest will define exact filenames and storage permissions. These
paths are proposals and create no assignment or permission to commit source text.

## 7. Independent review and adjudication

1. The primary annotator reads the whole assigned document and submits a versioned
   record in their own path. Flag uncertain cases rather than guessing.
2. A distinct reviewer independently annotates the assigned document in their own
   path, without seeing the primary annotations first. After that independent record
   is preserved, compare the records under the agreed review workflow. At least ten
   documents are planned for independent secondary review across the team.
3. Record differences in category, span, assertion, temporality, subject, missing or
   extra mention, and evidence support. Do not overwrite either person's work.
4. D adjudicates into a separate versioned reference with input submission IDs,
   the decision and rationale. Unresolvable items stay flagged; seek qualified expert
   input where needed rather than inventing agreement.
5. Freeze reference and assignment versions after review. A human-reviewed set is not
   clinically validated unless a qualified clinical expert has actually confirmed it.

For C before classifier model selection, both primary documents **and independent
review documents** must come from the agreed development portion. Do not expose C to
final reference decisions, final examples or selection feedback. If the planned counts
or split balance cannot be met, report the conflict to the team before assignment.

## 8. Matching and evaluation proposal

Before real scoring, D and the team must approve and freeze the matching rules and
record versions. The following is a concrete proposal, not an accepted shared metric:

1. Match within the same document and entity type. Treat repeated occurrences as
   separate candidates; use mention offsets rather than name strings alone.
2. **Exact**: both mention interval boundaries and type must match. **Relaxed**:
   same type and overlapping mention intervals, with overlap defined as a non-empty
   intersection. Report exact and relaxed separately; the relaxed proposal may be too
   permissive and must be reviewed on development examples before freeze.
3. Use a maximum-cardinality one-to-one matching over eligible predicted/reference
   pairs; use maximum total overlap to resolve cardinality ties, then a documented
   stable offset/ID order for any remaining tie. One prediction cannot satisfy two
   reference mentions and vice versa. Apply exact and relaxed matching independently.
4. For each mode, TP is the matched pair count, FP the unmatched predictions and FN
   the unmatched references. Precision is TP/(TP+FP), recall TP/(TP+FN), and F1 is
   their harmonic mean. Report raw counts and explicitly mark undefined denominators
   as not applicable; do not silently replace them with perfect scores.
5. On matched pairs, separately report assertion, temporality and subject accuracy,
   each with its evaluated-pair denominator and excluded/unresolved counts. Define
   whether the report uses exact or relaxed matches and show it explicitly.
6. Report schema validity, exact quote/offset validity and unsupported-item rate
   separately from entity matching. Agree how reviewers mark support and handle
   unresolved cases and zero denominators. A supported quote must also support the
   item's assertion, time and subject.

No numeric substantive thresholds or actual performance measurements are chosen
here. The separate project requirement is 100% structural and quote/offset validity on
the defined acceptance suite. Freeze final references and selected configurations;
do not tune on final examples.

For a simple illustrative calculation, suppose there are two reference mentions
and three predictions, and the agreed matching finds exactly one one-to-one match.
Then TP = 1, FP = 2 and FN = 1. Precision is 1/3, recall is 1/2, and F1 is 0.4.
This is an arithmetic example only, not a measurement of NoteLens.

## 9. Items requiring team decisions

- D/team: approve definitions for unknown assertion and procedure states, including
  contradictory, missing-context and transition cases.
- D/team: approve exact/relaxed matching rules for overlapping and nested mentions.
- D/C: permitted source access, actual assignment IDs, split/group mapping and how
  C's development-only access will be enforced and checked.
- D/team: review the draft matching policy, annotation format, primary/reviewer
  workflow, adjudication and practical protection of D's own final-set exposure.
- D/C/B: agree the versioned classification output and metric handoff. A separate
  D-to-C handoff is being prepared; B remains the owner of shared contracts.

No real assignment, external message, commit, push, model invocation or data
acquisition is authorized merely by this guide.
