# Corpus Answerability Review

**Date:** 2026-11-12
**Owner:** Nemanja (A). **Reviewer:** A's coding agent for Nemanja.
**Status:** Exploratory agent assessment; independent human/team review is pending.

## Purpose and scope

This user-approved review checks whether selected English concept questions have
support in the prepared MedlinePlus summaries. It records evidence availability
before passage construction. It does not execute a retriever or an application
answer-generation endpoint, and it does not validate clinical correctness.

The ten questions were authored by the coding agent after inspecting source
material, with two assigned to each project specialty. The selection deliberately
includes a partially covered question and a specific data-gap question. It is
source-informed and is not a random, blind or held-out sample. The outcome counts
are not an estimate of general corpus coverage, answer accuracy or retrieval quality.

This document stays under `docs/rag/`, outside corpus preparation inputs. It is
not a canonical QA dataset, a final-test set, an approved API schema or completion
of A-007/A-008. D's evaluation coordination and independent review remain required
before any formal dataset adoption. Do not index these questions or assessments.

## Inputs and evidence coordinates

- Repository commit reviewed: `222f826cb4aacad20536d4607550ce926fe8901c`.
- Source snapshot date: `2026-11-10`.
- Selection version: `medlineplus-en-topics-v1`.
- Cleaning version: `summary-html-to-text-v1`.
- Local corpus: `data/knowledge/.cache/corpus/cleaned-topics.jsonl` (401 topics; Git-ignored).
- Corpus SHA-256: `2d12d44f9be4f09db3ebaeb969a0335beb621ded7cdb793ccbafdbbfc0658639`.
- [Cleaning manifest](../../data/knowledge/manifests/cleaned-corpus.json).
- Cleaning-manifest SHA-256: `08d77bc6deb9ccb3fbf999adc5507d81f7264f16e101f27021084191d5c3903b`.
- [Snapshot manifest](../../data/knowledge/manifests/snapshot.json) and [preparation evidence](sources.md).

Each excerpt below is an exact slice of a topic's `cleaned_summary`, addressed
by its topic ID. `start` and `end` are half-open Unicode code-point offsets
`[start, end)` in that complete field, not in original HTML, a web page, a patient
document or a future passage. Python string slicing was used to check every quote.
No passage IDs exist yet. Titles/URLs identify the source, but the quoted text
and the agent's assessment establish the reviewed support. Live topic pages can
differ from this pinned snapshot.

Source acknowledgement: Source: MedlinePlus, National Library of Medicine.

## Method and label meanings

- `fully_supported`: the reviewed excerpts cover all parts of this narrowly
  phrased question. This does not claim exhaustive medical coverage.
- `partially_supported`: some requested information is supported and a specific
  missing portion is recorded.
- `missing_in_reviewed_evidence`: the requested information was not located
  using the documented candidate search and passage inspection. It is not proof
  of semantic absence from all possible paraphrases in the entire corpus.

Candidate discovery used title inspection and literal/regular-expression scans
over all 401 cleaned summaries. COVID candidates matched `covid|coronavirus|sars-cov`
(case-insensitive): topic IDs 199, 363, 3181, 5334, 6016 and 6076. The full COVID-19
summary and relevant surrounding paragraphs in the other five topics were read.
Trigeminal candidates matched `\btrigeminal\b`: topic IDs 1574 and 2729;
both complete summaries were read. A separate case-insensitive whole-word scan
for `serbia|serbian|srbija` found zero matching summaries. Other positive cases
were assessed against the displayed definition/symptom/test sections; no broad
semantic absence is inferred from a lexical scan.

## Observed outcomes

| Question | Specialty | Support |
| --- | --- | --- |
| CQ-01 | Cardiovascular / Pulmonary | `fully_supported` |
| CQ-02 | Cardiovascular / Pulmonary | `partially_supported` |
| CQ-03 | Orthopedic | `fully_supported` |
| CQ-04 | Orthopedic | `fully_supported` |
| CQ-05 | Gastroenterology | `fully_supported` |
| CQ-06 | Gastroenterology | `fully_supported` |
| CQ-07 | Neurology | `fully_supported` |
| CQ-08 | Neurology | `missing_in_reviewed_evidence` |
| CQ-09 | Urology | `fully_supported` |
| CQ-10 | Urology | `fully_supported` |

Counts for these ten selected questions: **8 fully supported, 1 partially supported,
1 missing in reviewed evidence**. No quality threshold or pass/fail decision is
introduced. These judgments require independent review before formal acceptance.

## Question-level findings

### CQ-01: Cardiovascular / Pulmonary

**Question:** What is the difference between systolic and diastolic blood pressure?

**Assessment:** The passage explicitly distinguishes pressure during a heartbeat from pressure between beats. Both requested terms are explained.

**Expected behavior:** Explain both terms with this source; do not turn the explanation into a patient-specific interpretation.

**Reviewed topic IDs:** `34`.

Source: [High Blood Pressure](https://medlineplus.gov/highbloodpressure.html), topic `34`.

```json
{
  "case_id": "CQ-01",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "34",
      "title": "High Blood Pressure",
      "url": "https://medlineplus.gov/highbloodpressure.html",
      "field": "cleaned_summary",
      "start": 173,
      "end": 384,
      "quote": "Your blood pressure is highest when your heart beats, pumping the blood. This is called systolic pressure. When your heart is at rest, between beats, your blood pressure falls. This is called diastolic pressure.",
      "role": "support"
    }
  ]
}
```

### CQ-02: Cardiovascular / Pulmonary

**Question:** What causes COVID-19, and how long can an infected person transmit it to others?

**Assessment:** The COVID-19 summary identifies the virus and describes transmission, but it does not specify the duration of infectiousness. Reviewed COVID-related contexts in the five additional topics concern other conditions and do not supply that duration.

**Expected behavior:** Answer the supported cause/transmission portion and explicitly state that the reviewed corpus evidence does not establish the requested duration. Do not fill the gap using model memory or fetched links.

**Reviewed topic IDs:** `3181`, `199`, `363`, `5334`, `6016`, `6076`.

Source: [COVID-19 (Coronavirus Disease 2019)](https://medlineplus.gov/covid19coronavirusdisease2019.html), topic `3181`.

```json
{
  "case_id": "CQ-02",
  "support": "partially_supported",
  "evidence": [
    {
      "topic_id": "3181",
      "title": "COVID-19 (Coronavirus Disease 2019)",
      "url": "https://medlineplus.gov/covid19coronavirusdisease2019.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 233,
      "quote": "COVID-19 (coronavirus disease 2019) is an illness caused by a virus. This virus is a coronavirus called SARS-CoV-2. It spreads when a person who has the infection breathes out droplets and very small particles that contain the virus.",
      "role": "support"
    }
  ]
}
```

### CQ-03: Orthopedic

**Question:** What is carpal tunnel syndrome, and which nerve is affected?

**Assessment:** The definition describes the wrist/hand problem and nerve compression. A separate sentence explicitly names the median nerve.

**Expected behavior:** Explain the definition and name the nerve using both excerpts. Do not infer a diagnosis for a user.

**Reviewed topic IDs:** `179`.

Source: [Carpal Tunnel Syndrome](https://medlineplus.gov/carpaltunnelsyndrome.html), topic `179`.

```json
{
  "case_id": "CQ-03",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "179",
      "title": "Carpal Tunnel Syndrome",
      "url": "https://medlineplus.gov/carpaltunnelsyndrome.html",
      "field": "cleaned_summary",
      "start": 33,
      "end": 253,
      "quote": "Carpal tunnel syndrome is the name for a group of problems that includes numbness, tingling, weakness, or pain in your wrist or hand. It's a very common condition that happens when a nerve in your wrist becomes squeezed.",
      "role": "support"
    },
    {
      "topic_id": "179",
      "title": "Carpal Tunnel Syndrome",
      "url": "https://medlineplus.gov/carpaltunnelsyndrome.html",
      "field": "cleaned_summary",
      "start": 368,
      "end": 472,
      "quote": "A nerve, called the median nerve, runs from your lower arm through the carpal tunnel and into your hand.",
      "role": "support"
    }
  ]
}
```

### CQ-04: Orthopedic

**Question:** What is the difference between a sprain and a strain?

**Assessment:** Both definitions are explicit: the source distinguishes the affected tissues. No treatment advice is needed to answer this question.

**Expected behavior:** Compare the two definitions while preserving the ligament versus muscle/tendon distinction.

**Reviewed topic IDs:** `417`.

Source: [Sprains and Strains](https://medlineplus.gov/sprainsandstrains.html), topic `417`.

```json
{
  "case_id": "CQ-04",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "417",
      "title": "Sprains and Strains",
      "url": "https://medlineplus.gov/sprainsandstrains.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 94,
      "quote": "A sprain is a stretched or torn ligament. Ligaments are tissues that connect bones at a joint.",
      "role": "support"
    },
    {
      "topic_id": "417",
      "title": "Sprains and Strains",
      "url": "https://medlineplus.gov/sprainsandstrains.html",
      "field": "cleaned_summary",
      "start": 324,
      "end": 422,
      "quote": "A strain is a stretched or torn muscle or tendon. Tendons are tissues that connect muscle to bone.",
      "role": "support"
    }
  ]
}
```

### CQ-05: Gastroenterology

**Question:** What is jaundice, and what causes its yellow color?

**Assessment:** The passage describes yellowing of skin/eye whites and explicitly connects it with excess bilirubin, which it describes as yellow.

**Expected behavior:** Explain the term and the source-stated connection to bilirubin, without identifying the cause in a particular patient.

**Reviewed topic IDs:** `4452`.

Source: [Jaundice](https://medlineplus.gov/jaundice.html), topic `4452`.

```json
{
  "case_id": "CQ-05",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "4452",
      "title": "Jaundice",
      "url": "https://medlineplus.gov/jaundice.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 210,
      "quote": "Jaundice causes your skin and the whites of your eyes to turn yellow. Too much bilirubin causes jaundice. Bilirubin is a yellow chemical in hemoglobin, the substance that carries oxygen in your red blood cells.",
      "role": "support"
    }
  ]
}
```

### CQ-06: Gastroenterology

**Question:** What are some causes and symptoms of intestinal obstruction?

**Assessment:** One paragraph supplies examples of causes and the following list supplies symptoms. The question asks for examples, not an exhaustive differential diagnosis.

**Expected behavior:** Use the stated examples and symptom list. Keep this a general explanation, not a diagnosis or a treatment recommendation.

**Reviewed topic IDs:** `5275`.

Source: [Intestinal Obstruction](https://medlineplus.gov/intestinalobstruction.html), topic `5275`.

```json
{
  "case_id": "CQ-06",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "5275",
      "title": "Intestinal Obstruction",
      "url": "https://medlineplus.gov/intestinalobstruction.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 226,
      "quote": "An intestinal obstruction occurs when food or stool cannot move through the intestines. The obstruction can be complete or partial. There are many causes. The most common are adhesions, hernias, cancers, and certain medicines.",
      "role": "support"
    },
    {
      "topic_id": "5275",
      "title": "Intestinal Obstruction",
      "url": "https://medlineplus.gov/intestinalobstruction.html",
      "field": "cleaned_summary",
      "start": 228,
      "end": 389,
      "quote": "Symptoms include:\n\n- Severe abdominal pain or cramping\n- Vomiting\n- Bloating\n- Loud bowel sounds\n- Swelling of the abdomen\n- Inability to pass gas\n- Constipation",
      "role": "support"
    }
  ]
}
```

### CQ-07: Neurology

**Question:** What is an acoustic neuroma, and which early symptoms are described?

**Assessment:** The opening identifies the tumor and affected nerve; the adjoining passage describes possible absent/mild early symptoms and gives examples.

**Expected behavior:** Explain the definition and possible early symptoms. Preserve the qualification that symptoms may be absent.

**Reviewed topic IDs:** `1624`.

Source: [Acoustic Neuroma](https://medlineplus.gov/acousticneuroma.html), topic `1624`.

```json
{
  "case_id": "CQ-07",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "1624",
      "title": "Acoustic Neuroma",
      "url": "https://medlineplus.gov/acousticneuroma.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 349,
      "quote": "An acoustic neuroma is a benign tumor that develops on the nerve that connects the ear to the brain. The tumor usually grows slowly. As it grows, it presses against the hearing and balance nerves. At first, you may have no symptoms or mild symptoms. They can include:\n\n- Loss of hearing on one side\n- Ringing in ears\n- Dizziness and balance problems",
      "role": "support"
    }
  ]
}
```

### CQ-08: Neurology

**Question:** What was the incidence of trigeminal neuralgia in Serbia in 2025, in new cases per 100,000 people?

**Assessment:** Neither reviewed trigeminal-related summary supplies this regional/year-specific statistic. Literal scans of all 401 summaries found no Serbia/Serbian/Srbija mentions. These checks do not prove semantic absence from every possible paraphrase. This deliberately specific boundary question is not a requirement to add national epidemiological data.

**Expected behavior:** Report that this statistic is not available in the reviewed corpus evidence. Do not infer a number from age/risk descriptions or invent an incidence estimate.

**Reviewed topic IDs:** `2729`, `1574`.

Source: [Trigeminal Neuralgia](https://medlineplus.gov/trigeminalneuralgia.html), topic `2729`.

```json
{
  "case_id": "CQ-08",
  "support": "missing_in_reviewed_evidence",
  "evidence": [
    {
      "topic_id": "2729",
      "title": "Trigeminal Neuralgia",
      "url": "https://medlineplus.gov/trigeminalneuralgia.html",
      "field": "cleaned_summary",
      "start": 0,
      "end": 75,
      "quote": "Trigeminal neuralgia (TN) is a type of chronic pain that affects your face.",
      "role": "context_only_not_answer_support"
    }
  ]
}
```

### CQ-09: Urology

**Question:** What symptoms can occur with a urinary tract infection?

**Assessment:** The source provides an explicit symptom list. The modal wording must be retained; symptoms alone do not establish a diagnosis.

**Expected behavior:** Describe the listed possible symptoms with a citation, without asserting that a user has an infection.

**Reviewed topic IDs:** `448`.

Source: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), topic `448`.

```json
{
  "case_id": "CQ-09",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "448",
      "title": "Urinary Tract Infections",
      "url": "https://medlineplus.gov/urinarytractinfections.html",
      "field": "cleaned_summary",
      "start": 241,
      "end": 495,
      "quote": "You may have a UTI if you notice:\n\n- Pain or burning when you urinate\n- Fever, tiredness, or shakiness\n- An urge to urinate often\n- Pressure in your lower belly\n- Urine that smells bad or looks cloudy or reddish\n- Pain in your back or side below the ribs",
      "role": "support"
    }
  ]
}
```

### CQ-10: Urology

**Question:** Does a high PSA blood test result alone confirm prostate cancer?

**Assessment:** The source explicitly says that other things can cause high PSA and separately describes biopsy as diagnostic. The passage supports answering this limited question without interpreting a real result.

**Expected behavior:** Explain that the PSA result alone does not establish the diagnosis according to this source; do not diagnose or prescribe a next step for an individual.

**Reviewed topic IDs:** `112`.

Source: [Prostate Cancer](https://medlineplus.gov/prostatecancer.html), topic `112`.

```json
{
  "case_id": "CQ-10",
  "support": "fully_supported",
  "evidence": [
    {
      "topic_id": "112",
      "title": "Prostate Cancer",
      "url": "https://medlineplus.gov/prostatecancer.html",
      "field": "cleaned_summary",
      "start": 2903,
      "end": 3013,
      "quote": "A high PSA blood level may be a sign of prostate cancer. But many other things can cause high PSA levels, too.",
      "role": "support"
    },
    {
      "topic_id": "112",
      "title": "Prostate Cancer",
      "url": "https://medlineplus.gov/prostatecancer.html",
      "field": "cleaned_summary",
      "start": 3206,
      "end": 3259,
      "quote": "A biopsy is the only way to diagnose prostate cancer.",
      "role": "support"
    }
  ]
}
```

## Interpretation and remaining work

The inspected corpus supplies concrete material for the eight supported questions.
CQ-02 demonstrates why a relevant topic URL does not guarantee a complete answer:
the source identifies the cause but does not establish the requested duration in
the reviewed material. CQ-08 is a regional/year-specific data-gap probe. Its
definition excerpt is explicitly `context_only_not_answer_support`; it must never
be cited as evidence for an incidence number.

The findings support proceeding to a separately approved passage-design proposal.
Preserve the relevant definition/context across passage boundaries and keep source
identity and text offsets traceable. No chunk size, overlap, model, index or
retrieval threshold is selected here. This single-topic question sample does not
cover multi-source answerability, ranking, rejection behavior, topic recall, MRR
or generated-answer quality. Those require their own prerequisites and measurements.

## Checks and limitations

The inspection used one-off, offline Python standard-library commands from the
repository root (`python -B -` through PowerShell). No implementation files or
automated test files were added. Input hashes, exactly ten distinct questions,
two cases per specialty, label counts, source metadata and all quote/offset pairs
were checked against the pinned local artifact. Markdown links and file scope
were also checked; the corpus, manifests, code and task checkboxes remain unchanged.

The exact-slice checks establish quote/offset validity for this document only.
They do not establish semantic support by themselves; support labels are the
coding agent's explicit judgments. Human/team acceptance and clinical validation
have not been performed. No provider calls, link fetching, dependency installation,
service/index build, commit or push is authorized or performed by this package.
