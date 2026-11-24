# D-004 and D-005 synthetic HTTP failure review

On 2026-11-21, D reran the deterministic loopback suite against
`d-extraction-qa-synthetic-v2`. The service used `d-mock-v1`,
`d-mock-prompt-v1` and `d-mock-answer-v2`. The 24 extractions and 48 answers
returned 72 HTTP 200 responses with matching request IDs. There were zero schema,
evidence, relationship or transport failures. The fresh predictions and results
matched the prior HTTP run byte for byte. This run used zero provider calls.

| Literal check | Passed |
| --- | ---: |
| Evidence state | 37/48 |
| Required facts and answer presence | 35/48 |
| Expected gap disclosures | 25/26 phrases |
| No unexpected claim-linked quote | 48/48 |
| All checks together | 34/48 |

The 25 unanswerable questions received the expected insufficient state. One of
those answers omitted the requested subject of its refusal. Eleven answerable
questions were refused, and two sufficient answers omitted a required source fact.
The 14 failed questions generated 25 failure records across overlapping checks.

## All 14 incomplete answers

| Case / QA | Observed result | Reason and regression expectation |
| --- | --- | --- |
| `confirmed-02 / supported` | Insufficient, no claims | The symptom question has no mock dispatch branch and the cough sentence is outside the exact catalog. A complete response cites the reported cough. |
| `confirmed-03 / supported` | Insufficient, no claims | The diagnosis question falls through the dispatch and the hypertension sentence is outside the catalog. A complete response cites the confirmed diagnosis. |
| `confirmed-04 / supported` | Insufficient, no claims | The plural symptom question falls through and the combined nausea/dizziness sentence is outside the catalog. A complete response preserves both symptoms. |
| `negation-03 / supported` | Insufficient, no claims | The denied-symptom question falls through and the mixed fever/cough sentence is outside the catalog. A complete response identifies fever as denied and preserves the different assertion for cough. |
| `negation-04 / supported` | Insufficient, no claims | The confirmation question falls through and the suspected-migraine sentence is outside the catalog. A complete response cites uncertainty about migraine. |
| `history-02 / supported` | Insufficient, no claims | The historical-diagnosis question falls through and the historical-pneumonia sentence is outside the catalog. A complete response preserves the historical context. |
| `history-03 / supported` | Insufficient, no claims | The subject question falls through and the father's denial sentence is outside the catalog. A complete response identifies the father as the subject. |
| `history-04 / supported` | Insufficient, no claims | The subject-and-history question falls through and the sister's childhood asthma sentence is outside the catalog. A complete response preserves both subject and time. |
| `procedure-02 / supported` | Insufficient, no claims | The occurrence question falls through. The catalog's planned-colonoscopy fixture uses a different exact sentence. A complete response cites the scheduled future procedure. |
| `procedure-03 / supported` | Insufficient, no claims | The performed-biopsy question falls through and the cancellation sentence is outside the catalog. A complete response cites that the biopsy was cancelled before it occurred. |
| `procedure-04 / supported` | Insufficient, no claims | The performed-procedure question falls through and the ultrasound sentence is outside the catalog. A complete response cites the performed ultrasound and its stated time. |
| `complex-03 / supported` | Sufficient, cites the chest-pain denial | The diagnoses-and-symptoms branch returned its recognized item. Cough is outside the catalog and its required quote is absent. A complete response includes both findings. |
| `limited-01 / absent-clinical` | Insufficient, no claims, generic refusal | The diagnosis question falls through with no gap label. The answer appropriately withheld a diagnosis. The fixture also expects an explicit diagnosis gap. |
| `limited-02 / supported` | Sufficient, cites the chest-pain denial | The topic is recognized, and only the denial sentence is in the catalog. A complete response cites the report of chest pain as well and preserves the conflicting statements. |

The mock uses exact sentence matches and a short list of supported question
forms. The 13 fact failures involve quotes absent from that catalog. In the
11 false refusals the question also falls outside the supported dispatch forms.
The 15 extraction mention misses remain a separate finding. The literal checks
establish these fixture discrepancies. Semantic entailment requires separate review.

## Reproduction

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.http_suite `
  --output eval/reports/local/d004-d005-review-v1
```

The local `results.json` SHA-256 is
`9b566a0921e9f97ba3ad715bd56113b87086560430e37579917b554b7bb5784b`.
The local `predictions.json` SHA-256 is
`b68ea41921a54656e399efd2b98963d1e8d6e4134b42d2d0b558272ad7519151`.
