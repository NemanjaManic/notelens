# D-009: A contribution to CQ review and final execution limits

Prepared: 2026-11-24. Owner: Nemanja (A). Status: proposal only; joint execution is not ready.

The user confirmed one frozen 26-case pass with no model tuning. No new paid execution is authorized.
The supplied archive contains metadata and public development review only. No final question or scoring content was opened.

## Receipt and original ratings

Archive SHA-256: `b1fdf1593839ee0c60ce45afe6723dffd7b9fd8c3599af801c969caec5a1b9bd`. All four supplied checksum entries match.
Original D review SHA-256: `a588cbe0abd49c175d49bfa599ff8f13e625378cc89062a84d8fdd91942dfe9a`; all 35 CSV scores match its Markdown table.
The original remains Draft (2026-11-19); no new human or independent-review status is inferred.
The JSON preserves the original review and CSV verbatim as UTF-8 strings, all ratings, and exact claim/source traces.

| Case | Source support | Required facts | Extra facts | Uncertainty/context | Evidence gaps | Scope/safety | Clarity/English |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CQ-01 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| CQ-03 | 1 | 2 | 2 | 2 | 1 | 2 | 2 |
| CQ-05 | 2 | 2 | 1 | 2 | 2 | 2 | 2 |
| CQ-07 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| CQ-09 | 2 | 2 | 2 | 2 | 2 | 2 | 1 |

Scores: 2 meets, 1 minor issue, 0 major issue, U unable to judge. Corrected ratings remain unmeasured.
CQ-05 original severity adjudication is separate from review of its narrower correction.

## Exact original and authored corrected claims

Claims are copied exactly from the verified public live receipt. Corrections are authored examples, not fresh model outputs.

### CQ-03

What is carpal tunnel syndrome, and which nerve is affected?

Original:

- `rag-claim-1`: Carpal tunnel syndrome is a common condition involving numbness, tingling, weakness, or pain in the wrist or hand when a wrist nerve becomes squeezed.
- `rag-claim-2`: The affected nerve is the median nerve, which passes through the carpal tunnel into the hand.

Corrected:

- `rag-claim-1`: Carpal tunnel syndrome is a common condition involving numbness, tingling, weakness, or pain in the wrist or hand when a wrist nerve becomes squeezed.
- `rag-claim-2`: The affected nerve is the median nerve, which passes through the carpal tunnel into the hand.

Corrected citation mapping (original mapping is retained in JSON):

- `rag-claim-1` / `e1`: [Carpal Tunnel Syndrome](https://medlineplus.gov/carpaltunnelsyndrome.html), `mplus-179-8fb8eee731c70e4ffb842cabdc701dc740992214baa9dc75fee3cda7f21cb7a5`, code points `[33, 253)`.
  Exact quote: Carpal tunnel syndrome is the name for a group of problems that includes numbness, tingling, weakness, or pain in your wrist or hand. It's a very common condition that happens when a nerve in your wrist becomes squeezed.
- `rag-claim-2` / `e2`: [Carpal Tunnel Syndrome](https://medlineplus.gov/carpaltunnelsyndrome.html), `mplus-179-8fb8eee731c70e4ffb842cabdc701dc740992214baa9dc75fee3cda7f21cb7a5`, code points `[255, 574)`.
  Exact quote: The carpal tunnel is a narrow opening between the bones in your wrist and the ligament that holds them together. A nerve, called the median nerve, runs from your lower arm through the carpal tunnel and into your hand. This nerve provides feeling to your thumb and first three fingers. It also helps you move your thumb.
- `rag-claim-2` / `e3`: [Carpal Tunnel Syndrome](https://medlineplus.gov/carpaltunnelsyndrome.html), `mplus-179-8fb8eee731c70e4ffb842cabdc701dc740992214baa9dc75fee3cda7f21cb7a5`, code points `[754, 973)`.
  Exact quote: If the tendons become swollen or irritated inside the carpal tunnel, they may press on the nerve. The squeezed nerve may not work well, which can lead to numbness, weakness, and other symptoms of carpal tunnel syndrome.

### CQ-05

What is jaundice, and what causes its yellow color?

Original:

- `rag-claim-1`: Jaundice causes the skin and the whites of the eyes to turn yellow.
- `rag-claim-2`: Too much bilirubin, a yellow chemical in hemoglobin, causes the yellow color associated with jaundice.

Corrected:

- `rag-claim-1`: Jaundice causes the skin and the whites of the eyes to turn yellow.
- `rag-claim-2`: The yellow color occurs when too much bilirubin builds up.

Corrected citation mapping (original mapping is retained in JSON):

- `rag-claim-1` / `e1`: [Jaundice](https://medlineplus.gov/jaundice.html), `mplus-4452-b97b175cba872607d6c4fc8776617ef02e6414a6aada185598f9682e894efb3c`, code points `[0, 452)`.
  Exact quote: Jaundice causes your skin and the whites of your eyes to turn yellow. Too much bilirubin causes jaundice. Bilirubin is a yellow chemical in hemoglobin, the substance that carries oxygen in your red blood cells. As red blood cells break down, your body builds new cells to replace them. The old ones are processed by the liver. If the liver cannot handle the blood cells as they break down, bilirubin builds up in the body and your skin may look yellow.
- `rag-claim-2` / `e2`: [Jaundice](https://medlineplus.gov/jaundice.html), `mplus-4452-b97b175cba872607d6c4fc8776617ef02e6414a6aada185598f9682e894efb3c`, code points `[0, 452)`.
  Exact quote: Jaundice causes your skin and the whites of your eyes to turn yellow. Too much bilirubin causes jaundice. Bilirubin is a yellow chemical in hemoglobin, the substance that carries oxygen in your red blood cells. As red blood cells break down, your body builds new cells to replace them. The old ones are processed by the liver. If the liver cannot handle the blood cells as they break down, bilirubin builds up in the body and your skin may look yellow.

### CQ-09

What symptoms can occur with a urinary tract infection?

Original:

- `rag-claim-1`: Symptoms that may occur with a urinary tract infection include pain or burning during urination, fever, tiredness or shakiness, frequent urges to urinate, lower-belly pressure, bad-smelling or cloudy or reddish urine, and back or side pain below the ribs.

Corrected:

- `rag-claim-1`: Symptoms that may occur with a urinary tract infection include pain or burning during urination, fever, tiredness or shakiness, frequent urges to urinate, lower-belly pressure, urine that smells bad or looks cloudy or reddish, and back or side pain below the ribs.

Corrected citation mapping (original mapping is retained in JSON):

- `rag-claim-1` / `e1`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[241, 274)`.
  Exact quote: You may have a UTI if you notice:
- `rag-claim-1` / `e2`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[276, 310)`.
  Exact quote: - Pain or burning when you urinate
- `rag-claim-1` / `e3`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[311, 343)`.
  Exact quote: - Fever, tiredness, or shakiness
- `rag-claim-1` / `e4`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[344, 370)`.
  Exact quote: - An urge to urinate often
- `rag-claim-1` / `e5`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[371, 401)`.
  Exact quote: - Pressure in your lower belly
- `rag-claim-1` / `e6`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[402, 452)`.
  Exact quote: - Urine that smells bad or looks cloudy or reddish
- `rag-claim-1` / `e7`: [Urinary Tract Infections](https://medlineplus.gov/urinarytractinfections.html), `mplus-448-627d210443969169881a4c80a793e1b536391eb1c73d827bc53a60eb539059b4`, code points `[453, 495)`.
  Exact quote: - Pain in your back or side below the ribs

## Proposed A request and token ceilings

These are maximum reservations, not measured usage or a promise that every stage will run.
Conditions: one literature-answer operation for each of 8 literature-only + 8 mixed cases; no duplicate retrieve call, re-render, preview, repair, retry, corpus embedding or scoring-model call.
The other 8 document-only and 2 out-of-scope cases must make zero A calls, verified before execution.

| Operation | Max requests | Input tokens/request | Input tokens/total | Output tokens/total |
| --- | ---: | ---: | ---: | ---: |
| Query embedding | 16 | 128 | 2,048 | 0 |
| question_parts | 16 | 4,096 | 65,536 | 8,192 |
| support | 16 | 20,000 | 320,000 | 8,192 |
| answer | 16 | 4,096 | 65,536 | 8,192 |

Totals: at most 16 embeddings + 48 generations; generation input <=451,072 tokens, output <=24,576 tokens; embedding input <=2,048 tokens.
Each generation is preceded by an input-count request: at most 48 additional free counting requests, or 112 provider HTTP requests in total (64 potentially chargeable).
Each generation is capped at 512 output tokens, reasoning none, Standard/default tier. Unsupported, empty-evidence and first-error paths may reduce the totals.

## Price and duration proposal

Official rates checked on 2026-11-24: GPT-6 Luna input $0.10, cache-write upper $0.125, output $0.50; text-embedding-3-small input $0.02, all per million tokens.
The upper calculation uses the cache-write rate for every generation input, no cache discount, and a conservative 10% regional allowance for the entire subtotal.

`((451072 * 0.125 + 24576 * 0.50 + 2048 * 0.02) / 1000000) * 1.10 = USD 0.075584256`

**Proposed new A-only cap: USD 0.08. It is not approved or shared with D. Historical budgets remain closed.**
This is an API-usage reservation; provider billing is unmeasured. No hosting or tax amount is inferred.

Propose a 30-second timeout plus an absolute deadline for each embedding, counting and generation operation; zero SDK/HTTP/application retries and zero structural repairs.
112 operations x 30 seconds gives a 3,360-second (56-minute) sequential provider timeout sum.
Propose a separate enforced 3,600-second (60-minute) A wall-clock stop limit including local work. It is a cutoff, not an execution-time forecast.
Existing SDK timeouts alone do not prove an absolute wall-clock bound. The final operator profile must implement and demonstrate cancellation and accounting for in-flight calls.

Stop on the first unexpected transport/provider/validation/usage/pricing error or exceeded limit. Record a valid expected partial/refusal response and continue; do not treat it as an infrastructure failure.
Reserve each attempt before sending; keep completed outputs and usage and mark uncertain in-flight costs as reserved. No automatic restart, replay or budget release after failure.

Price sources:

- [gpt-6-luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [4936856-understanding-and-counting-tokens](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens)

## What still prevents a joint executable freeze

- Metadata names v2 as received and v3 as custodian-declared, with v3 bytes not received. D/custodian must reconcile the authoritative manifest, 26 case identities and replacement receipt before releasing runtime inputs to the operator. Scoring stays evaluator-only.
- B must supply the final app SHA, B-009 evidence, designated operator and a ready bounded live profile. The last local source inspection is not a new B acceptance.
- The current local web client has a 5-second service timeout and accepts mock mode only; its consumer rejects live records. It cannot serve as the final live profile unchanged.
- D must supply the chosen provider/model, extraction and document-answer token limits, request/counting multiplicity and timeouts. The current local D service is mock-only, and its default offline repair bound is two attempts. The proposed live policy requires one attempt.
- A/B need a counted synthetic dry run on the exact chosen profile proving 16 A calls, zero A calls for the remaining routes, no separate retrieve duplication and no render-triggered processing. A numerical inventory check is not that dry run.
- A ceiling of 32 D generations is conditional on exactly 16 extraction operations plus 16 document-answer operations, one generation each, no hidden summary/repair/judge calls and no re-extraction during rendering. Sixteen distinct documents alone do not prove this.
- Joint new cost limit and wall deadline remain unset until those D/B bounds exist. Neither zero nor USD 0.08 is a valid whole-system total. If D is proven to use 32 one-shot generations, the conditional billable ceiling is 16 embeddings + 80 generations, with D counting requests added separately.
- The operator must enforce the existing in-memory 60-minute submitted-document retention, processing documents just in time if necessary; the run deadline does not extend retention.
- Exact submission time on 2026-11-24 must come from the tutor. Midnight and completion before submission are not assumed.

Final extraction F1 remains explicitly unmeasured because separate final reference annotations are missing; record this scope decision in the joint report.

## Reproduction and verification

From the repository root, with the existing RAG environment and pinned public corpus:

```powershell
& ./services/rag/.venv/Scripts/python.exe -B ./docs/rag/evaluation/prepare_d009_handoff.py --metadata-zip 'C:/Users/Nemanja/Downloads/D009-metadata-and-original-CQ-review-v1.zip'
```

The utility has no provider client or execution switch. It checks ZIP checksums, all 35 original ratings, the original live receipt, canonical citation slices, all 56 freeze hashes and Decimal accounting, then writes only A-owned handoff artifacts.
This is offline inventory validation, not the B counted runtime dry run, final scoring, independent corrected-answer review or a Spec Kit implementation workflow.
