# D-008 review and calibration

## D-008 closed: approved limited development pilot (2026-11-23)

Milica explicitly approved all six proposed calibration decisions and reported
that the team accepts the reduced-scope limitations. This is coordinator-reported
team acceptance; no individual team reply or signature is invented. D-008 is
closed in that approved scope. The [final report](../../eval/reports/development/d008-limited-pilot-final-v1.json)
and [adopted codebook](../../eval/rubrics/d008-pilot-calibration-v1.json) record the
approval, conventions, sample limits and exact private artifact hashes.

The pilot contains 14 accepted original answer-rating records across seven
paired source/question/response cases and five singly reviewed entity-evidence
items. Initial exact dimension agreement remains **43/49 (87.76%)**, computed
before adjudication. All six calibration disagreements now have accepted
dispositions. No initial rating was overwritten, no new independent rating was
created, and no independent agreement is recomputed from accepted profiles.
The five entity items do not establish paired entity-reviewer agreement.

Accepted decisions: CAL-02 credits the complete age-gap warning and available
facts; CAL-03 credits justified abstention with the specific gap; CAL-04 records
no source-available diagnosis; CAL-05 treats false refusal as a major context
failure; CAL-06 treats the undisclosed available-fact omission as material; and
CAL-07 separates support for the emitted atom from the omitted contradiction.
The adopted benchmark-critical convention flags CAL-05/06/07. It is a pilot
reporting convention, not a clinical harm finding or population error estimate.

The original approximate-40-answer and at-least-20-entity planning volumes were
not achieved. Shortfalls of 26 answer ratings and 15 entity-evidence items are
explicitly accepted in the scope decision. Data are synthetic mocks only. The
initial Milica interface omitted warnings/citations inline while linking exact
responses; this presentation difference limits interpretation of initial
agreement. Earlier reviewer declarations and AI-assistance disclosures remain
part of provenance, not authenticated human authorship.

Original reviews, source/response files and the earlier proposal package remain
preserved. The final private bundle has 30 verified checksum entries. Sara's
feedback stays separate and non-independent. Goran/Nemanja remain released from
new replacement reviews. No provider call, new threshold, unseen-final access,
D-013 reference change or automatic closure of other D tasks occurred. The scope
proposal and preparation history below are historical stages, not open requests.

## Reduced development-pilot scope (2026-11-23)

Milica explicitly selected the reduced delivery scenario and reported that new
eligible reviewer capacity is unavailable. Her scope decision is recorded in the
[scope receipt](../../eval/reports/development/d008-reduced-development-pilot-scope-v1.json).
This authorizes preparation of a limited synthetic mock development calibration
pilot, not a claim that the original review-volume plan was fulfilled. Goran and
Nemanja remain released from new replacement reviews. Sara's feedback remains
separate and non-independent.

D reverified the exact accepted first-round inputs and saved response/source
hashes, reproduced fourteen accepted answer-rating records and seven paired
source/question/response cases, and matched all five accepted entity-evidence
records to their original packet pins. Initial dimension agreement is **43/49
(87.76%)**. It is preserved before adjudication. Dimension-level exact counts are:
clarity/English 7/7, extra facts 7/7, evidence gaps 5/7, required facts 6/7,
scope/safety 6/7, source support 6/7, and uncertainty/context 6/7. No single summed
quality score or new acceptance threshold is introduced.

The five entity-evidence records declare pass for mention/evidence offsets and
semantic support; applicable attribute checks also pass. These are five singly
reviewed items, not five inter-reviewer agreement pairs. The fourteen answer
ratings are not fourteen distinct evaluated answers: they cover seven cases.
CAL-04 and CAL-05 have identical refusal bytes but different source/question
contexts, which remain separate.

The original plan was approximately 40 answer reviews and at least 20 entity-
evidence reviews. This pilot is 26 and 15 records/items below those planning
counts respectively. The sample is small, synthetic and mock-only. It establishes
neither provider-backed quality, unseen-final performance nor clinical validity.
Previously accepted declarations and AI-assistance disclosures remain part of
the provenance; no new blind review or verified human authorship is claimed.

The private `D008-reduced-development-pilot-v1` package preserves the original
ratings and contains a six-case adjudication proposal, not new human or independent
ratings. It proposes counting complete structured warnings, separating justified
abstention from false refusal, a named benchmark-critical omission convention,
and separating support for an emitted atom from an omitted contradiction.
Proposed profiles are explicitly non-human and non-independent and are not used
to recompute independent agreement. See the [analysis](../../eval/reports/development/d008-reduced-pilot-analysis-v1.json).

Remaining: coordinator approval of these concrete calibration conventions and a
recorded team decision adopting the reduced delivery scope. Milica's scope choice
is already recorded and need not be requested again. No team confirmation is
invented. The private package includes `FINAL-REVIEW.txt` and a ready team message
requesting scope adoption, without new scoring work. D-008 remains open pending
those decisions; D-005/D-007/D-011/D-009 gates and D-013's completed freeze are
unaffected. The preparation and reviewer-capacity histories below remain preserved.

## Historical initial preparation

Updated 2026-11-13. Agent implementation evidence only. Rubric remains an
uncalibrated draft; no human reviews, clinical validation or owner approval are claimed.

Use `eval/fixtures/answer-review-template-v1.json` for each separate review.
Keep `human_reviewed=false` and null ratings until a person actually reviews the
canonical document and exact response. Record the document digest and the SHA-256
of the exact UTF-8 response artifact in `response_sha256`, plus response, prompt,
model/mock and rubric versions. Preserve those artifacts through approved access;
never copy real submitted document bodies into the repository. The checker checks
digest syntax, not artifact availability or the truth of a human declaration.

`answerable_from_document` is yes/partly/no/unclear. `response_action` is
answer/partial_answer/abstain/unclear. `critical_error` and `needs_adjudication`
are booleans. Dimension ratings are integers 0/1/2 or U. U is not zero and is
excluded from the numeric denominator. An unresolved review is not silently
converted to a completed review. Supply a timezone-aware completion timestamp
and rationale only after completion.

For a timeout or service failure, use `response_action=operational_error`, leave
dimension ratings null and `human_reviewed=false`. Record a safe error code/run ID
in issue codes/response ID; never count it as abstention or answer quality.

Run from the repository root:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.answer_review eval/fixtures/answer-review-template-v1.json
./eval/.venv/Scripts/python.exe -m pytest eval/tests/test_review_integrity.py -q
```

The read-only CLI accepts separate JSON files or arrays and writes the aggregate
to stdout. It never edits input files. Invalid records and duplicate review IDs
produce a nonzero exit. Reports separate blank, incomplete, operational-error,
invalid and completed declared-human records. They include per-score counts,
U counts, rated denominators, outcome counts and adjudication flags. No report
authenticates human authorship or resolves disagreements automatically.

Before project use, reviewers independently score development examples, retain
the initial records, discuss disagreements and version any rubric revisions.
Preserve a new record/ID for each revised assessment. D may practice on public
synthetic examples independently, but team adoption and calibration require
actual reviewers. Keep final examples for final reporting, never prompt tuning.
The approximate 40-answer and 20-entity/evidence targets remain planned, not done.

## Comparing independent review submissions

Run the review checker on both submissions using
`python -m notelens_eval.answer_review REVIEW_A.json REVIEW_B.json`.
It pairs distinct reviewer aliases only when case, document, response hashes,
mode and versions match. The report includes exact agreement, two-point
disagreement and unable-to-judge counts by dimension. Its adjudication list
identifies score differences, outcome or critical-error disagreements and
pairs explicitly flagged for adjudication.

The checker preserves the original submissions. Pair counts can include
multiple pairs per output when three or more reviewers score it. Synthetic
tests exercise the report format. Actual rubric calibration requires
independent completed reviews and recorded adjudication decisions.

For retained response files, add `--response-artifacts DIRECTORY`. Each completed
review must identify a UTF-8 JSON file named `RESPONSE_ID.json` in that directory.
The checker compares SHA-256 against the exact file bytes, including whitespace.
The report records the number of checked artifacts. Keep restricted outputs in
their approved restricted location. Artifact matching establishes output identity;
human authorship and semantic review still require reviewer confirmation.

## Synthetic rubric practice (2026-11-21)

One agent applied `d-answer-review-rubric-v1` to seven retained mock HTTP answers
and one injected operational failure. The [practice records](../../eval/reviews/d008-synthetic-practice-v1.json)
include each document digest, response digest, scores and a reason for every
dimension rated below 2 or marked `U`. All practice records declare
`human_reviewed=false` and `independent_review=false`. This exercise used zero
provider calls and provides no inter-reviewer agreement measurement.

On 2026-11-22, Milica submitted all 49 dimension scores for the seven synthetic
answers. D verified the response and document digests and saved the scores
with the observed response actions. The original review page linked to each
exact response and omitted warnings and citations from its inline display.
D prepared a full view with both fields visible. Milica confirmed her scores
and reasons for CAL-02 and CAL-03. Her reasons address the main answer, which
omits the age explanation in both cases. Both responses carry the explanation
in a separate structured warning. Preserve her scores and use this difference
to calibrate whether the evidence-gaps dimension credits a separate warning.

Milica supplied the other five rationales and outcome assessments. D verified
all seven completed reviewer records against their exact response bytes and
preserved all 49 scores. Milica marked CAL-05, CAL-06 and CAL-07 as critical.
She requested joint review of the conflicting source statements in CAL-07.
D recorded CAL-02 and CAL-03 as partly answerable and unanswerable respectively
from the missing-age evidence. The treatment of separate warnings and CAL-04's
explicit negative answer remain calibration questions. The first Milica
review is complete. Independent counterpart reviews and team calibration
remain pending.

| Practice case | Outcome | Scoring finding |
| --- | --- | --- |
| Complete answer | Answer | All seven dimensions meet. |
| Correct partial answer | Partial answer | All seven dimensions meet. The question's missing age is named and the available finding is cited. |
| Correct abstention | Abstain | Evidence gaps score 2. Source support, required facts and context are `U` because there is no applicable fact to score. |
| Generic refusal on an unanswerable question | Abstain | Evidence gaps score 1 because the reply leaves the requested diagnosis gap unnamed. |
| False refusal on an answerable question | Abstain | Required facts and evidence gaps score 0. The response action still records what happened. |
| Incomplete answer marked sufficient | Answer | Source support scores 2 for the emitted claim. Required facts and evidence gaps score 0 because a relevant fact was omitted. |
| One side of a contradiction marked sufficient | Answer | Source support scores 2 for the retained quote. Required facts, context and evidence gaps score 0. Severity is flagged for adjudication. |
| Injected HTTP 503 on an unanswerable question | Operational error | The correlated `provider_unavailable` envelope carries no quality scores and earns no rejection credit. |

### Proposed scoring clarifications

- Score required facts against the in-scope evidence available to answer the
  question. A correct partial answer can earn full marks if it covers all
  available required facts and names the unavailable part.
- Use `U` for claim support and factual context when an abstention emits no
  factual claim. Use `U` for required facts when no requested fact is available.
  Use 0 for required facts when an abstention omits available evidence. Score
  the explanation of the abstention under evidence gaps.
- Treat a generic refusal with no unsupported claim as an abstention. Use
  evidence-gaps score 1 when the source lacks the requested fact and the reply
  gives a vague limitation. Use 0 when the refusal hides available evidence or
  a sufficient answer conceals a material omission. The literal gap-phrase
  check remains a separate diagnostic.
- Assess the support for each emitted claim on its own citation. Assess material
  omissions and unresolved contradictions under required facts and context. The
  severity boundary for a one-sided sufficient response remains for adjudication.
- Keep operational failures in their own outcome. Leave all dimensions null
  and retain the correlated error code and run ID.

### Verification

The seven successful responses come from the [21 November HTTP rerun](synthetic-failure-review-v2.md).
The response hashes use the parsed `AnswerResult` in UTF-8 JSON with sorted keys,
compact separators, Unicode preserved and one terminal LF. The injected fault
uses SHA-256 of the exact HTTP error body. The single fixed request ID is
recorded in its practice row.

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.answer_review `
  eval/reviews/d008-synthetic-practice-v1.json
```

The checker reports seven `incomplete` agent practice records, one operational
failure, zero invalid records and zero completed human reviews. The agent scores
are excluded from the human-review denominator. The proposed scoring guidance
awaits independent review before any rubric version or acceptance decision changes.

## Member A and C calibration handoffs

The proposed A packet has seven pinned synthetic document answers and five
separate generated entity-evidence items. It contains the questions, exact
canonical source content, response files, versions and SHA-256 checksums. The
answer files are byte-identical to the retained first-round artifacts. The
entity results are serialized copies of the pinned mock HTTP extraction
records. The packet includes blank forms and excludes gold labels and other
reviewers' scores. Reviewer exposure and self-authorship are declared per
case before scoring and can trigger a replacement.

Sara requested her D-008 review inputs. D prepared a separate Member C packet
using the same seven exact answers, questions and canonical sources, with blank
forms for Sara and a different set of five generated entity-evidence items.
The ten entity-evidence items across A and C are distinct. Both packets use
`d-answer-review-rubric-v1` with `d-answer-review-form-v2`. D verified all 24
checksums in the Member C packet. A and C scoring remain pending.

Sara later reported drafts covering all seven answers and five entity-evidence
items. Her personal review, exposure declaration and final private submission
were pending at that checkpoint. Her subsequent disclosure and the replacement
assignment below supersede this first-round packet for independent calibration.

For new answer intake, validate the current form and the exact reviewed
response files before counting the submissions as complete.

```powershell
./eval/.venv/Scripts/python.exe -B -m notelens_eval.answer_review `
  $reviewFile --require-current-form --response-artifacts $responseDirectory
```

The current form requires a reason and minimum correction for each score
of 0, 1 or U, and a separate component outcome for mixed responses. The reports
show component failures alongside the answer-quality counts. Earlier reviews
are preserved and can be read without the current-form intake flag. These are
first-round packets within the proposed 40 answer and 20 entity-evidence
review targets. The remaining assignments and team calibration await
confirmation.

## Member A technical intake (2026-11-22)

D received Nemanja's private first-round submission and verified all seven
submission checksums and all twenty-four original assignment checksums. The
seven v2 answer forms and five entity-evidence forms match their assigned
source and response pins. All five mention and evidence span pairs were
verified against the exact sources. The package includes Nemanja's full-review
attestation and his declarations of no prior exact-output exposure or
self-authorship. It also discloses that an assistant proposed scores and had
access to related D-007 and annotation-training material. See the
[technical intake record](../../eval/reports/development/member-d-handoff-intake-2026-11-22.json).

Milica explicitly accepted Nemanja's declared independent reviews with recorded
AI assistance on 2026-11-23. The first-round comparison preserves both original
submissions and verifies all fourteen response artifacts. Fourteen valid answer
reviews yield seven matched pairs and exact agreement on 43 of 49 dimension
ratings. CAL-02 through CAL-07 require adjudication of score or outcome differences.
Five additional entity-evidence reviews are accepted from Member A. Independence
relies on the reviewer declarations and the retained AI disclosure. The remaining
rubric decisions, wider review sample and final calibration remain open. See the
[first-round comparison receipt](../../eval/reports/development/d008-first-round-comparison-v1.json).

On 2026-11-23, Sara reaffirmed prior exposure and preparation involvement for all
twelve original items and requested her replacement packet. D reverified its
archive digest and all forty-three file checksums. The seven answer forms and
five entity-evidence forms are blank and ready for the private handoff. The
original disclosed reviews retain their earlier status. Completed replacements,
their exposure declarations and a second reviewer of the same new answers are
pending. See the [resource intake](../../eval/reports/development/team-resource-intake-2026-11-23.json).

## Proposed Member B first round, 2026-11-22

Goran requested counts, rubric version and the review window before confirming
capacity. D prepared a private packet with the same seven exact calibration
answers and three generated entity-evidence items not assigned to A or C.
Only three unused distinct items remain in the retained mock output inventory.
The packet therefore proposes three entity reviews; no additional outputs or
human ratings are invented to fill the wider plan.

Use `d-answer-review-rubric-v1` and `d-answer-review-form-v2`. The proposed
return time is 23 November 2026 at 12:00 Europe/Belgrade, subject to Goran's
capacity confirmation. Scores and gold labels are excluded. All 20 package
checksums and the response/source pins were verified. Across the A, B and C
packets there are 13 distinct entity-evidence items. Additional items are
required for the wider review plan. Capacity, delivery and completed scoring
are pending. See the [packet verification](../../eval/reports/development/d008-member-b-packet-verification-v1.json).

Goran subsequently acknowledged the seven-answer/three-entity scope, rubric v1,
form v2 and proposed 23 November 12:00 Europe/Belgrade return. He will check
capacity, confirm a full or reduced scope and return time, and declare prior
exposure before scoring. This acknowledgement does not confirm capacity,
packet readability, checksum verification or completed reviews.

## Member C exposure disclosure and replacement packet

Sara submitted seven answer and five entity-evidence forms declaring prior
exposure and preparation involvement on every record, with
`independent_review: false`. D preserved the originals privately and verified
all twelve response and source identities against her original packet. The
answer validator reports zero invalid records and zero completed independent
reviews. Its seven `incomplete` states reflect the independence gate; they do
not ask Sara to repair those exposed records into independent reviews. Keep
all twelve as disclosed non-independent feedback, excluded from independent
calibration denominators and reviewer-agreement pairs. See the
[exposure intake](../../eval/reports/development/d008-member-c-exposure-intake-v1.json).

D prepared `D008-member-C-replacement-calibration-v1.zip`, containing seven
new document-answer reviews and five separate entity-evidence reviews. The
unchanged mock service generated fresh outputs over authenticated loopback
HTTP from seven new synthetic document/question combinations. The seven
canonical texts, seven answer hashes and five assigned document/entity pairs
differ from the old packets. Fourteen final-run requests returned HTTP 200,
correlated request IDs and `no-store`, with schema and exact-span checks.
All 43 package checksums and twelve HTML review sections were verified. The
fourteen review-integrity tests passed. No paid provider calls were made.

Use rubric `d-answer-review-rubric-v1` and form `d-answer-review-form-v2`.
The replacement has blank scores and exposure declarations; Sara must confirm
exposure and authorship before scoring. No independent credit or completed
review is inferred from generating a replacement. No new return deadline is
agreed. The previous forms remain preserved without edits.

A second independent reviewer for these exact new answers is not yet assigned.
Do not compare the replacement ratings with the old seven outputs as paired
agreement. Preserve matching case IDs, canonical hashes, exact response hashes
and rubric versions for any future comparison. This packet measures mock
development behavior and does not supply real-model quality evidence. See the
[replacement verification](../../eval/reports/development/d008-member-c-replacement-packet-verification-v1.json).

### Sara's personal replacement review: non-independent feedback (2026-11-23)

D received the preparation-disclosed forms and dated disclosure in
`D008-Milica-non-independent-feedback-v1.zip`. All three checksum entries and
all twelve case/document/response pin sets match the original replacement packet.
The unchanged originals and archive are retained in the restricted local D-008
handoff area; the shareable [intake receipt](../../eval/reports/development/d008-sara-non-independent-feedback-intake-v1.json)
contains metadata and hashes, not sources or ratings.

Sara personally reviewed all seven answers and five entity-evidence items on
2026-11-23 and reports no viewing of the replacement outputs before receiving
the packet. She helped prepare replacement materials; the specific affected
outputs remain unidentified. The assistant drafted ratings and reasons. This
supersedes the earlier pending-personal-review/preparation-disclosure status,
while preserving the older receipts unchanged.

Record all twelve as non-independent feedback. Add zero independent review
credit and zero agreement pairs. The answer validator reports zero invalid and
seven incomplete records due to its independent-review gate and null case-level
authorship declarations; this does not ask Sara to repeat her disclosed review.
Seven answer records have dated completion fields; the dated disclosure covers
the five entity-evidence records. Do not change unknown authorship to false.

**Coordinator release:** Milica subsequently released both Nemanja and Goran
from the proposed independent review of the seven replacement answers. No forms,
availability responses or return dates are now expected from either person for
this assignment. Their prepared packets remain historical artifacts, not active
assignments. Nemanja's earlier exposure disclosure is preserved; no exposure is
inferred for Goran. This release does not waive the two-independent-ratings
requirement or name eligible replacements. D-008 retains an unresolved reviewer-
capacity requirement pending replacement staffing or an explicit approved scope
decision; D-013 remains closed. See the
[release record](../../eval/reports/development/d008-reviewer-release-v1.json).

**Earlier reviewer-status update:** Milica relayed an AI-assisted draft disclosure
attributed to Nemanja reporting prior exposure to all seven exact replacement
answers and involvement in RAG corpus, literature-question and development-output
preparation. Treat all seven proposed independent slots as affected and remove
Nemanja from this independent-review assignment. The draft is not represented
as a newly signed personal attestation. No ratings or independent return date
were supplied. A newer packet/form does not restore independence. His optional
supplementary review is neither approved nor counted. See the
[exposure intake](../../eval/reports/development/d008-nemanja-prior-exposure-intake-v1.json).

Goran's own eligibility remains unconfirmed. If he is eligible for all seven,
one additional eligible reviewer is still needed; otherwise replace each affected
slot so that every case has two eligible independent ratings. The original
packets remain preserved, scores/reference labels withheld, and D-008 open.
Do not invent eligibility or count the same review twice. D-013 remains closed.

Paired independent agreement requires two eligible reviewers for the exact same
seven replacement answers. Goran and Nemanja are proposed candidates, not
confirmed eligible assignees. Each must confirm availability, lack of prior
exposure to these outputs and lack of preparation/authorship involvement before
private assignment. Withhold Sara's ratings and the other reviewer's ratings.
Sara's feedback cannot fill either independent slot. D-008 remains open.

Following Sara's subsequent workflow recommendation, D prepared two separate
private seven-answer-only packets for Goran and Nemanja. Each has the same exact
questions, canonical sources, saved responses/citations/warnings, rubric v1 and
form v2, plus a local reader and a per-case eligibility/AI-assistance declaration.
All 17 common content files match byte-for-byte; each archive's 21 checksum
entries verify. Forms have blank scores and unknown exposure/authorship fields;
independent status must be explicitly set only after truthful eligibility checks.
No reference labels or any submitted ratings are packaged. Preparation is not
delivery, reviewer acceptance or independent completion. See the
[preparation receipt](../../eval/reports/development/d008-two-reviewer-packets-preparation-v1.json).

Before sharing outputs, ask each candidate privately for availability, a return
date/timezone and per-case prior exposure/preparation disclosure. If a case is
affected, assign that slot to another eligible reviewer so the same case still
has two independent ratings. Do not show either reviewer the other's ratings or
Sara's feedback until both initial forms are submitted and verified. Every 0, 1
or U needs a reason and minimum correction. Return forms privately with their
SHA-256, completion date and AI-assistance disclosure. Verify exact case/source/
response/rubric pins and record initial agreement and disagreements before any
joint score discussion. No candidates are confirmed by Sara's proposal alone.

The new calibration family is development-only and is excluded from unseen
final QA, including reworded family variants. Its additional
[source exclusions](../../eval/reports/development/d008-replacement-development-source-exclusions-v1.json)
do not amend the frozen 54-case QA manifest or its 74-candidate inventory.
