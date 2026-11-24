# D-009 A live launcher: approved-scope v2 handoff

**App pin superseded on 2026-11-24**: Goran requested the tested whole-stack
watchdog commit `d846dcfee5a066dc180a59dbf0c1ed8888809f38`. Use the
[v3 reconciliation and private corpus handoff](d009-watchdog-reconciliation-v3.md)
for current launcher/template checksums. The approved bounds below are unchanged.

Prepared: 2026-11-24. Owner: Nemanja (A). Operator designated by the user: Goran.
Status: A launcher supplied; scope approved; technical activation inputs pending.
This supersedes the v1 15-second proposal without changing the model or prompts.
No further scope approval is requested for these bounds.

## Approved execution envelope

The user relayed Milica's approval of one frozen 26-case pass: eight document-only,
eight literature-only, eight mixed and two out-of-scope cases; 16 documents.
The combined new API ceiling is USD 0.58, split D USD 0.50 / A USD 0.08.
Historical ledgers stay closed and unchanged. There are zero automatic retries
or structural repair generations, no corpus re-embedding and no final-case tuning.

| Operation | Max HTTP calls | Input tokens per generation/embedding call | Output tokens per generation call | Absolute operation deadline |
| --- | ---: | ---: | ---: | ---: |
| D extraction + document answers | 32 | 64,000 | 12,288 | 30 s |
| A query embedding | 16 | 128 | 0 | 30 s |
| A question parts | 16 | 4,096 | 512 | 30 s |
| A support selection | 16 | 20,000 | 512 | 30 s |
| A literature answer | 16 | 4,096 | 512 | 30 s |
| A free input counts | Up to 48 | Matching generation payload | 0 | 30 s |

This launcher uses the 48 input-count allowance. Maximum A HTTP requests are 112;
the **whole-system maximum is 144**, not 112. No additional D count, model-test,
judge or other provider operation is included in that final-pass ceiling.
Health/readiness checks are local service checks and make no model request.

A generation totals: 451,072 input and 24,576 output tokens. Embedding input:
2,048 tokens. Combined generation totals: 2,499,072 input and 417,792 output.
The documented conservative rate calculation remains D USD 0.4978688 +
A USD 0.075584256 = USD 0.573453056, within the approved USD 0.58 allocation.
The operator verifies exact payload bounds and applicable account rates before
dispatch, without truncation or opening a second tuning/evaluation round.

One A branch may wait for seven 30-second provider operations: 210 seconds.
Set B's `http_timeout_ms` to **240000**, which the selected bounded client already
accepts through its existing configuration. No B source edit is made by A.
The serial provider timeout sum is 144 x 30 = 4,320 seconds (72 minutes), so the
approved **3,600-second global hard stop is binding**. Completion is not promised.
Stop on the first unexpected error or global deadline and preserve partial work.

## Exact supplied A pins

- App candidate: `9fc7c333ca74971768e1df13ed6238798c48e90e`.
- RAG baseline: `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4`.
- New launcher SHA-256: `20d5413834172eb4ed15f7439eba27212ee16af4c13f1f3acc6c2b6ea8084341`.
- A-011 manifest SHA-256: `d0502196edabc1301b06b55f2d1ddb1f888ac678b51502227d0f9a0fd5a67685`.
- Passage artifact SHA-256: `4915adc09d6719f84e3315f8a0ea0ac37bc363d8b1a178c6d14f449aac85c938`.
- Corpus version: `2922f29e08b74bf668272c33a7f3f0599d8d16fc90d2242976e3d4476010579b`.
- Index version: `209656e7be0e9db1885407de4fef824b5e0209c78a7d2fdc71e418c7a3d4a146`.

The unchanged baseline pins all three generation prompts and the embedding space.
Generation remains `gpt-6-luna`, reasoning `none`, Standard/default tier;
embeddings remain `text-embedding-3-small`, 1,536 dimensions; vector top five,
question-only retrieval. The old manifest's historical `not_run` status is
preserved. The new policy/receipt describes the separately approved final attempt.

PR #35 is D's integration PR, with inspected head
`20385b9c7b83382f5cea9e9a6fdf1fb91d4263ab`; it is not the app candidate SHA.
A did not approve, merge or impersonate Goran's code-owner review. Metadata-only
digests computed from that exact PR head, without exposing or copying scoring
content, are:

- `eval/config/d009-final-freeze-candidate-v2.json`:
  `699bd95c747d67679d0a74ba9a3077b919422b28ba62a74e947e63a465c01713`.
- `eval/references/qa/d009-reconciled-candidate-identity-v1.manifest.json`:
  `3c1cf38c209f68e41262f961bc59b9b67e43260e65a6bdc58cc591c9990e17f3`.

These are candidate config/identity digests, not an invented final scoring hash.
D/custodian binds the actual final reference identity into the final receipt;
reference contents remain separately held by D.

## Exact Windows commands

Run from the A service repository root with its existing locked environment,
prepared corpus and existing index. No new dependency or index build is needed.

```powershell
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/config/d009-final-policy.template.json
```

The template now records scope approval and Goran's assignment. It deliberately
leaves `pricing_confirmed=false` and the 16 `question_sha256` entries empty.
`preflight_blocked` therefore means technical activation inputs are absent,
not that another scope approval is being requested.

Goran materializes the local operator policy with the exact 16 literature-branch
question hashes (SHA-256 of each UTF-8 question string, preserving multiplicity),
confirmed account pricing, the approved run ID and a fresh matching receipt path.
Keep the pinned app, launcher, freeze and all approved bounds unchanged. The
approval ID `user-relayed-milica-d009-2026-11-24` labels the received user-relayed
scope decision; it is not a fabricated external signature.

Configure server-side `OPENAI_API_KEY`, `NOTELENS_RAG_SERVICE_TOKEN`,
`NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=true` and
`NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS=true`, without sharing their secret values.
Then use the already approved scope with the completed policy:

```powershell
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/.cache/final/approved-policy.json --serve --port 8001
```

The service binds `127.0.0.1:8001` and requires bearer authentication.
`/health/live` and `/health/ready` make no provider request. The ready response
must have `service=rag`, `mode=live`, `status=ok`, `model_version=gpt-6-luna`.
Use the same bearer token in B's RAG client. Confirm model access for the actual
operator account; the presence of a key or a key-free test is not that confirmation.

## Receipts, outputs and remaining technical inputs

A enforces a 3,600-second admission/dispatch cutoff from service startup. The
selected B controller must additionally enforce the approved whole-stack watchdog
and stop owned processes. This is an existing launch condition, not new scope.

A returns the complete contract JSON and `X-Request-ID` over HTTP. The operator
collector must map each request to the frozen `case_id`/version, preserve the raw
HTTP status and full JSON before app composition, and return results/errors to D.
A's durable receipt retains request IDs, question/output hashes, attempts, usage,
reservations and stop codes without logging question/document bodies. Preserve
uncertain in-flight reservations; do not restart or reset a stopped attempt.

On the inspected A process, no service bearer or process API key is configured;
the final private policy and 16 branch hashes have not been supplied. A does not
claim authenticated operator readiness or access to Goran's private environment.
Supply those technical inputs to activate the existing approved profile; do not
send secrets or scoring references into chat or retrieval.

Final extraction F1 and independent semantic risk remain explicitly unmeasured,
as accepted. A's prior completion target of 15:00 Europe/Belgrade remains the
user's stated target; the 60-minute bound does not guarantee completion by it.
No paid dispatch, final result, PR approval/merge, commit or push occurred while
preparing this handoff.

## Executed verification

The unchanged focused command passed **100 tests** again after the approved
30-second alignment, including the 19 existing final-runtime checks:

```powershell
uv run --locked --offline --extra indexing --directory services/rag python -B -m pytest tests/test_final_runtime.py tests/test_contract.py tests/test_answers.py tests/test_failures.py --basetemp .cache/test-runs/approved-scope-UNIQUE-ID
```

Default preflight checked the 56 historical file pins and 617-passage corpus and
reported `approved_policy=true`, `provider_timeout_seconds=30`,
`provider_calls=0`, `preflight_blocked`. The blocked status reflects missing
technical inputs only. The policy template SHA-256 is
`0af119c48df50f0dffcbb9cef3995f12d87d722ebe886a9e32969f3ae7de15ff`.
The earlier separate Chroma readback verified all 617 existing passages; no index
or corpus bytes were changed. No browser/live-provider/final-QA run is inferred.
