# Member A literature QA proposals

Nemanja (A), 2026-11-18. Prepared by the coding agent for D's independent review.

The [nine development proposals](qa-proposals.json) contain five single-topic
cases, three multi-topic cases and one case with no supported topic in the
reviewed evidence. Seven questions have full support, one has partial support
and one has no support in that scope. All three multi-topic cases have support
from two distinct topics. Each topic supplies a different requested fact. The
suggested topic sets follow the cited passages. A reviewer can add equivalent
evidence or revise the required topic sets during adjudication.

| Case | Review focus | Proposed topic IDs | Evidence scope |
| --- | --- | --- | --- |
| A-QA-01 | Two blood-pressure definitions | 34 | Full |
| A-QA-02 | COVID-19 cause and contagiousness | 3181 | Partial |
| A-QA-03 | A country/year-specific incidence figure | None | Missing from reviewed candidates |
| A-QA-04 | What an elevated PSA can establish | 6208 | Full |
| A-QA-05 | Acoustic neuroma definition and location | 1624 | Full |
| A-QA-06 | Airways affected by acute bronchitis | 5755 | Full |
| A-QA-07 | Nerves involved in two different conditions | 179, 1624 | Full |
| A-QA-08 | Adhesion definition and another obstruction cause | 3920, 5275 | Full |
| A-QA-09 | Bile storage and the cause of jaundice color | 4643, 4452 | Full |

Four cases carry original MedQuAD references from three XML records. Two
questions narrow original MedQuAD questions. The other two use a record as
provenance for one part of an authored question. The pinned revision, XML path,
question and record IDs and answer hash identify the original material. The
expected facts are short paraphrases grounded in the current MedlinePlus corpus
snapshot. See [MedQuAD and its CC BY 4.0 notice](https://github.com/abachaa/MedQuAD#license).

Each supported part has a passage ID and an exact half-open Unicode range in
both the passage and the topic summary. The SHA-256 of the UTF-8 slice supports
verification without redistributing the full source text or original MedQuAD
answer. The two gap cases describe the passages reviewed by the baseline and
hybrid experiments. D can check alternative corpus sources before accepting the
gap labels. Use the zero-evidence case for abstention review, with no denominator
for topic recall.

D can review each requested fact against the cited slice, check alternatives
and record revised labels separately. Review A-QA-05 and A-QA-07 together for
overlap since they share evidence. Keep all nine public proposals in development
if adopted. Their questions, expected facts and references stay outside the
retrieval index. The author judgments have no independent acceptance yet.

C-002 and D-003 remain open on the reviewed team branches. Assigned document
annotations and independent secondary reviews follow D's publication of the
assignments. Canonical QA and final-set decisions belong to D under D-007.

From the repository root, validate the JSON syntax with:

```powershell
& services/rag/.venv/Scripts/python.exe -B -m json.tool docs/rag/qa-proposals.json
```

The local check passed for all nine cases. It compared 12 evidence references
with both canonical artifacts, verified four MedQuAD references against three
pinned XML records, and checked counts, deduplication and answerability labels.
No model or embedding requests were made for this package.
