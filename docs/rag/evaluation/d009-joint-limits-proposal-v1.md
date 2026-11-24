# D-009 joint limits proposal

Prepared: 2026-11-24. Owner: Nemanja (A), for B/D confirmation. Status: **proposal only; execution and operator authorization remain false**.

The latest user target is **15:00 Europe/Belgrade on 2026-11-24**, superseding the earlier 16:00 target. This records the user's target; it does not claim separate tutor confirmation or completion before submission.

## Source and scope

B supplied `D009-B-final-runtime-preflight-9fc7c33.json`, SHA-256 `57e33b2b78df1b98ea4c5c334a66d18f00f7dbb014f68e4c323439a9361a5a01`, for app candidate `9fc7c333ca74971768e1df13ed6238798c48e90e`.

B reports 73 Chrome checks with mocks, plus a separate synthetic rehearsal using local service doubles: 26 cases, exactly 16 extractions, 16 document answers and 16 literature requests. Reopens and citation visits did not repeat extraction; overflow was blocked before dispatch. This proposal does not independently repeat those checks or turn them into provider-backed evidence.

One final pass contains 8 document-only, 8 literature-only, 8 mixed and 2 out-of-scope cases, with 16 distinct documents. There is no model or prompt tuning on final cases. Final extraction F1 remains explicitly **unmeasured** because separate final reference annotations are missing.

## Maximum request and token inventory

| Component | Generations | Input tokens per generation | Output tokens per generation | Aggregate generation input | Aggregate generation output |
| --- | ---: | ---: | ---: | ---: | ---: |
| D extraction and document answers | 32 | 64,000 proposed | 12,288 | 2,048,000 | 393,216 |
| A question decomposition | 16 | 4,096 | 512 | 65,536 | 8,192 |
| A support selection | 16 | 20,000 | 512 | 320,000 | 8,192 |
| A literature composition | 16 | 4,096 | 512 | 65,536 | 8,192 |
| **Combined generations** | **80** | | | **2,499,072** | **417,792** |

A additionally reserves at most 16 query embeddings, 128 input tokens each, or 2,048 embedding input tokens. No corpus or index embedding is included. A uses `text-embedding-3-small`, 1,536 dimensions, question-only vector retrieval, top five passages.

A has up to 48 additional free input-token counting requests. This gives 112 A provider HTTP requests: 16 embeddings, 48 generations and 48 counts. Across A and D there are 96 potentially chargeable requests and 144 known provider HTTP requests. **D's additional counting or other provider requests remain unconfirmed and must be added.** These are maximum reservations, not actual usage.

The 32 D generation bound requires exactly one generation for each of 16 extractions and 16 document-answer operations, without hidden summary, repair, retry or judge calls. B's synthetic application dispatch count does not prove that D's provider adapter makes only one generation per operation.

D's proposed profile is `gpt-6-luna`, reasoning `low`, messages input, `quote_hints` output and `coverage_v2`; A uses `gpt-6-luna`, reasoning `none`. The classifier remains the local C-008 fitted model.

## Proposed new cost ceiling

The parent agent verified the official rates on 2026-11-24: generation input USD 0.10, cache-write upper input USD 0.125, generation output USD 0.50, and embedding input USD 0.02 per million tokens. The calculation uses the higher cache-write rate for all generation input, no cache discount, and a conservative 1.10 regional multiplier for the subtotal. Account-specific pricing still needs operator confirmation. Sources: [GPT-6 Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna), [embedding pricing](https://developers.openai.com/api/docs/models/text-embedding-3-small), [token counting](https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens).

| Scope | Conservative modeled upper, USD | Proposed new subcap, USD |
| --- | ---: | ---: |
| D, 32 calls at 64,000 input / 12,288 output | 0.4978688 | 0.50 |
| A generations and query embeddings | 0.075584256 | 0.08 |
| **Combined** | **0.573453056** | **0.58** |

The earlier D input limit of 65,536 yields USD 0.5046272 and therefore exceeds a USD 0.50 D subcap. **D must confirm that the complete exact payloads fit 64,000 tokens without truncation.** If not, this proposal must change before execution; the limit must not silently drop content.

The proposed USD 0.58 ceiling equals the separate USD 0.50 D and USD 0.08 A reservations. It covers API usage under the stated profile, not unlisted paid operations, hosting or inferred taxes. Historical budgets remain closed. No new cap is approved by this document.

## Timeout and stop proposal

| Component | Maximum known requests | Proposed absolute deadline per request | Sum of request deadlines |
| --- | ---: | ---: | ---: |
| A, including free counting | 112 | 15 s | 1,680 s / 28 min |
| D generations | 32 | 30 s | 960 s / 16 min |
| **Known provider work** | **144** | | **2,640 s / 44 min** |

The **44-minute number is a sum of known sequential provider deadlines**, not a completion-time estimate or a proven total runtime. It excludes unknown D counting calls, local classification/retrieval, preparation, validation, HTTP/rendering overhead, startup and shutdown. For example, 32 additional D count requests at 30 seconds add 16 minutes, reaching 60 minutes before local overhead.

Propose a **60-minute global absolute hard stop** with an operator watchdog and tested cancellation. SDK timeouts alone do not establish an absolute wall-clock bound. B proposes a 120-second web HTTP timeout; the final configured service path must be checked against it.

There are zero automatic retries and zero structural repair generations. Stop on the first unexpected transport, provider, validation, accounting or pricing error. A valid expected partial or refusal response is a recorded result and is not an infrastructure error. Stop new dispatch, cancel remaining work, retain completed outputs and usage, and retain reservations for in-flight requests whose final usage is unknown. Do not restart or replay automatically.

Submitted-document retention remains limited to 60 minutes in server memory. A run deadline does not extend retention; the operator must process documents just in time or expire them as required.

## Required owner and team confirmations

1. **D:** exact serialized input payloads fit 64,000 tokens without truncation; confirm the model/profile, one-shot generation multiplicity, any additional count/provider requests and their deadlines. The default two-attempt offline repair must not remain active in the final live profile.
2. **A/D and operator:** confirm actual account rates, model access and live authenticated readiness. A rate or usage mismatch must stop before subsequent dispatch. Key-free checks are not live readiness.
3. **B:** accepted exact app SHA, complete runnable profile, per-component timeouts, counted non-duplicating dispatch, cancellation and global watchdog. B's supplied evidence identifies a pushed candidate; it is not team freeze acceptance.
4. **Custodians/D:** reconcile the received v2 versus declared v3 manifest and pin the authoritative 26-case runtime inventory. Only runtime inputs go to the authorized operator; scoring remains evaluator-only.
5. **Team/user:** explicitly approve the joint freeze, new USD 0.58 combined cap, per-owner subcaps, deadlines and Goran as operator before provider execution. Goran is currently proposed, not authorized.

The machine-readable [proposal](d009-joint-limits-proposal-v1.json) keeps those approval fields false. A's final runtime SHA-256 supplied by the parent is `0c67e932084b75806541bbb49d5e04e0c154635302f09897f8689d0f29ca6ab5`; the joint handoff must bind the final approved policy and configuration identities as well.

## Verification boundary

This is an arithmetic and inventory review from supplied metadata and the parent's verified pricing snapshot. No final questions or scoring contents were opened, no provider requests were made, and no commit, push, deployment or new human/team acceptance is claimed.
