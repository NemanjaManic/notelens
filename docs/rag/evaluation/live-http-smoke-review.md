# Development review of five live RAG answers

Recorded on 2026-11-20 from the feedback supplied as D's review of the
[five-case live run](live-http-smoke.md). The supplied file is dated 2026-11-19
and marked draft. It uses `d-answer-review-rubric-v1` and scores the original
answers against their excerpts. All five coverage verdicts were full. The
feedback lists four minor deductions and zero critical errors.

| Case | D's feedback on the original | Authored development revision |
| --- | --- | --- |
| CQ-01 | Meets all dimensions. | Retain the answer and citations. |
| CQ-03 | Source support and evidence gaps each scored 1. | Attach the compression excerpt to `rag-claim-2` alongside `e2`. |
| CQ-05 | Extra facts scored 1. The proposed severity awaits adjudication. | Replace `rag-claim-2` with “The yellow color occurs when too much bilirubin builds up.” Retain `e2`. |
| CQ-07 | Meets all dimensions. | Retain the answer and citations. |
| CQ-09 | Clarity and English scored 1. | Use “urine that smells bad or looks cloudy or reddish” in `rag-claim-1`. Retain the same evidence links. |

## Citation correction for CQ-03

The supplementary excerpt is from `mplus-179-8fb8eee731c70e4ffb842cabdc701dc740992214baa9dc75fee3cda7f21cb7a5`
at exact Unicode code-point offsets `[754, 973)`. The original `e2`, at
`[255, 574)`, identifies the nerve and its path. The additional span links
the nerve in that context to the compression described in the question.
[MedlinePlus Carpal Tunnel Syndrome](https://medlineplus.gov/carpaltunnelsyndrome.html)

## Corpus follow-up for CQ-05

Flag the pinned Jaundice passage for corpus review. Its aside about bilirubin
and hemoglobin was reproduced in the original answer. The MedlinePlus bilirubin
test page describes bilirubin as a substance produced during the breakdown of
old red blood cells. The revised answer only uses the relevant supported fact
about bilirubin buildup and yellow color.
[MedlinePlus Bilirubin Blood Test](https://medlineplus.gov/lab-tests/bilirubin-blood-test/)

## Verification and status

Replayed the five authored examples through the support and answer validators
using the cited passages from the pinned corpus. Five frozen `AnswerResult`
payloads, eight claim texts and 20 exact citation links passed. All 119 focused
answer, support and evidence-selection tests passed offline. The original live
receipt matched SHA-256
`9c5a16ef6020ba4963ae4f3be20aab2ac85a8a65d6a3a7da35de6ec536d7509a`.
The replay made zero API calls. The revisions await follow-up review and
CQ-05 remains open for adjudication.

Supplied feedback SHA-256
`a588cbe0abd49c175d49bfa599ff8f13e625378cc89062a84d8fdd91942dfe9a`.
These known questions stay in development. D-007 and the final held-out
evaluation remain open.
