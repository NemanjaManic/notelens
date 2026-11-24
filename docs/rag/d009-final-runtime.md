# D-009 final RAG runtime: operator handoff

**Superseded profile, 2026-11-24**: The user subsequently relayed Milica's scope
approval with **30-second A provider operations**, a 240-second web timeout and
the USD 0.58 combined cap. Use the [approved-scope v2 handoff](d009-live-approved-handoff-v2.md)
and its v2 archive. The earlier 15-second proposal and v1 archive below remain
historical evidence. No further scope approval is required for the approved
bounds; technical operator readiness and final policy materialization still apply.

Prepared: 2026-11-24. Owner: Nemanja (A).
Scope: executable A-owned runtime preparation; final execution is not authorized.
Latest user completion target: **2026-11-24 15:00 Europe/Belgrade**.

The new [launcher](../../services/rag/src/notelens_rag/final_runtime.py) supplements
the unchanged [A-011 selection](a011-freeze.md). It does not tune the model,
corpus, embedding space, retrieval or prompts on final cases. The old A-011
manifest and its historical final-run status remain unchanged.

## Exact profile and limits

App candidate: `9fc7c333ca74971768e1df13ed6238798c48e90e`.
RAG baseline: `d2f85fbe97ec451ac3eda52a7b48ff101fc99dc4`.
Selection manifest SHA-256:
`d0502196edabc1301b06b55f2d1ddb1f888ac678b51502227d0f9a0fd5a67685`.
The [disabled policy template](../../services/rag/config/d009-final-policy.template.json)
pins the additional launcher bytes separately. Its approval fields are unset.

| Component | Maximum calls | Input tokens per call | Output tokens per call | Absolute provider wait |
| --- | ---: | ---: | ---: | ---: |
| Query embedding | 16 | 128 | 0 | 15 s |
| Question decomposition | 16 | 4,096 | 512 | 15 s |
| Evidence selection | 16 | 20,000 | 512 | 15 s |
| Literature answer | 16 | 4,096 | 512 | 15 s |
| Free input-token count | 48 | Same payload as the corresponding generation | 0 | 15 s |

The 16 literature operations cover eight literature-only and eight mixed cases,
one request per branch. The eight document-only and two out-of-scope cases must
not dispatch to A. There is no extra `/v1/retrieve`, re-embedding, preview,
automatic retry, structural repair or scoring-model allowance.

Totals: at most 16 embeddings and 48 generations, plus 48 free counts; 112
provider HTTP requests, with 64 potentially chargeable requests. Embedding input
is at most 2,048 tokens; generation input 451,072 and generation output 24,576.
Generation uses `gpt-6-luna`, reasoning `none`, Standard/default tier. Embeddings
use `text-embedding-3-small`, 1,536 dimensions. Retrieve question-only vector top
five from the existing 401-topic/617-passage pinned index.

At the documented conservative cache-write/input, output and embedding prices,
including a 10% regional allowance, A's maximum reservation is USD 0.075584256.
The proposed **new A-only cap is USD 0.08**. The earlier 30-second A proposal is
historical; this final candidate requires 15 seconds per provider operation.
No old budget is reopened. Account pricing still requires owner confirmation.

## Key-free preparation on Windows

Use an isolated A service checkout with the unchanged locked dependencies,
prepared corpus and existing index. The final supplemental files can be copied
from this handoff; do not overwrite another owner's implementation.

```powershell
uv --system-certs sync --locked --directory services/rag --python 3.13 --extra indexing --dev
if ($LASTEXITCODE -ne 0) { throw 'Locked RAG setup failed.' }
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/config/d009-final-policy.template.json
```

Installation may require registry access if packages are not cached. The CLI
preflight makes no provider call and does not require a key. With this template,
`preflight_blocked` is the expected result: no approval, operator or authorized
question hashes are supplied. Counts and pins can still be inspected. A successful
offline preflight does not prove account/model access or authenticated live readiness.

## Approval and live startup: operator only

Before startup, D/custodian reconciles the final manifest version and releases
only authorized runtime inputs to the named operator. Scoring references stay
with D and never enter RAG prompts, indexes or retrieval. The operator derives
16 SHA-256 values from the exact UTF-8 `question` strings B will send to A,
preserving multiplicity. These are the literature branch payloads, including
the literature portion of mixed questions, rather than assumed whole-case text.
No final question was accessed during A's preparation.

Create a private policy from the template after one joint sign-off. Record the
approval ID, authorized operator, confirmed pricing, approved=true and the 16
question hashes. Generate a fresh UUID for `run_id` and a new matching receipt
path. Keep app, launcher, selection, limit and retry pins unchanged. Do not use
the template's demonstration UUID for an actual run or delete an old receipt.

The operator configures these values server-side, without posting secret values:
`OPENAI_API_KEY`, `NOTELENS_RAG_SERVICE_TOKEN`,
`NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS=true`, and
`NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS=true`. B must use the same service bearer
token and the approved live client/profile, not the old mock client.

The following command is supplied for that approved operator; it was not executed
with live providers during preparation:

```powershell
& ./services/rag/.venv/Scripts/python.exe -B -m notelens_rag.final_runtime --config ./services/rag/.cache/final/approved-policy.json --serve --port 8001
```

It binds only `127.0.0.1`. Use bearer-authenticated `/health/live` and
`/health/ready` before dispatch; these endpoints make no model request. Readiness
verifies the configured backend/index, while live account/model access remains
the operator's separately recorded responsibility.

## Stop policy, time and receipts

A serial literature request has at most seven provider operations, so its
provider wait sum is at most 105 seconds. B's proposed 120-second HTTP timeout
leaves 15 seconds for local work; it is not a demonstrated latency guarantee.

The A watchdog enforces a 3,600-second admission/dispatch cutoff from service
startup and persists the halt even if idle. It prevents late provider results
from reopening the run. B must enforce the joint 60-minute wall-clock watchdog,
including terminating owned processes; SDK timeouts alone do not establish this.

Reserve before dispatch. Stop at the first unexpected provider, validation,
usage, quota, pricing or deadline error. Valid supported, partial and insufficient
answers remain legitimate outcomes. Keep successful outputs in B's bounded output
channel for D scoring; A's receipt stores request IDs, hashes, usage, attempts,
reservations and stop state without question/document bodies or citation text.
Preserve uncertain in-flight reservations and mark billing unverified. Restart
against an existing receipt is refused; no automatic reset, resume or repeat
final run is authorized.

## Joint proposal and remaining confirmations

B reports 73 mock browser checks and a synthetic 26-case counted rehearsal with
16 extractions, 16 document answers and 16 literature requests, including reopens,
citation visits and pre-dispatch overflow rejection. Those are key-free B records,
not live provider results. A's independent candidate review is recorded separately.

The joint proposal is at most 32 D generations, 48 A generations and 16 query
embeddings, plus 48 A input-count requests. With D input tightened to 64,000
tokens and output 12,288, the modeled D bound is USD 0.4978688; combined with A,
USD 0.573453056 fits the proposed **USD 0.58** (D 0.50 + A 0.08) envelope.
The original D 65,536-input bound would exceed D's USD 0.50 allocation.

D must confirm that every exact serialized payload fits the tighter input bound,
that reasoning tokens are included in its output limit, and that no repair,
hidden summary, judge or extra uncounted request is dispatched. No truncation or
prompt/model tuning is allowed to make a final case fit. Any D counting requests
must be added to the HTTP/time inventory.

With 112 A operations at 15 seconds and 32 D operations at 30 seconds, the serial
provider wait sum is 44 minutes, before local work or additional D requests.
This arithmetic is not a completion forecast. A whole-run 60-minute hard stop and
the user's 15:00 target do not extend submitted-document retention beyond 60
minutes. B/D must preserve the approved in-memory retention and cleanup policy.

Still required: accepted exact app/runtime pins; D payload/time/pricing
confirmation; authoritative final manifest/custody release; Goran's operator
authorization, model access and authenticated service readiness; and explicit
approval of the new combined scope/cap. Final extraction F1 remains explicitly
unmeasured because separate final reference annotations are missing. No final
execution, score, human acceptance, publication or deployment is claimed here.

## Executed verification and exact candidate review

The final focused command passed **100 tests**, including 19 new runtime checks:

```powershell
uv run --locked --offline --extra indexing --directory services/rag python -B -m pytest tests/test_final_runtime.py tests/test_contract.py tests/test_answers.py tests/test_failures.py --basetemp .cache/test-runs/final-reviewed-UNIQUE-ID
```

Default CLI preflight reported `preflight_blocked`, `approved_policy=false`,
`provider_calls=0`, and the complete proposed inventory after checking the
56 unchanged historical file pins and 617-passage corpus. Separate local readback
verified the existing Chroma index's 617 passages and exact selected index version.
The final launcher SHA-256 is
`b3375c6dcab6abfa49bedaa67e32e9c53ae71bf89d8eabb16db854bffba3ec01`.
The disabled policy template SHA-256 is
`95f2aa24d44ea8602c47eb13ca71200e7c1f79a284e3810827af0298bf5c7fe7`.

The exact B candidate was fetched and inspected through Git objects without
changing the working branch. Its dedicated live-mode consumer, service tokens,
timeout configuration and serialized dispatch budget are compatible with A's
interface. The process launcher still loops while the web process is alive with
no enforced whole-stack deadline. The in-app dispatch deadline does not terminate
processes or guarantee cancellation of an in-flight request at the hard cutoff.
B must supply and test that watchdog before joint execution acceptance. These
findings are [agent source review](evaluation/d009-app-review-9fc7c33.md), not a
new browser rehearsal or human/team acceptance of the candidate.

Used the installed `speckit-implement` workflow for A-012 preparation only, with
`SPECIFY_FEATURE_DIRECTORY=specs/001-rag` and `SPECIFY_FEATURE_NO_PERSIST=1`.
The official PowerShell resolver selected that feature; its requirements checklist
has 16 checked and zero unchecked entries. No extension hook configuration exists.
Existing ignore rules cover secrets, environments, caches and local artifacts.
The old frozen files, shared files and other owners' implementations were not edited.
