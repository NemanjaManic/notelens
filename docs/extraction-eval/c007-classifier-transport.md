# C-007 evaluator and B-005 classifier transport check

**Checked 2026-11-21.** The classifier service code was pinned to
`7181a1abdf7831bb247510821c886b0e031d5de0` and the B web consumer to
`f8bba16397c49f9e58233a3854ca1c0492244048`. All inputs were synthetic.

## C-005 owner artifact

C's owner receipt in `9fc84e9afc1ce7045dff653cb57bb9db1a29c300` pins the manifest SHA-256
`e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f`
and the model version
`c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc`.
The startup instructions refer to the ignored `.cache/c005-frozen-uncertainty-v1`
directory. During the initial shared check the bundle was unavailable to D,
so the initial run used a separate TF-IDF and Logistic Regression pipeline fitted
on five synthetic tokens, following C's `model_bundle` test fixture. Sara later
provided the pinned bundle. The owner-bundle replay is recorded below.

## Observed results

| Classifier process | Synthetic case | D evaluator | B client and report input |
| --- | --- | --- | --- |
| Mock, `fixture-classifier-v0` | Supported | HTTP 200 twice, `Cardiovascular / Pulmonary` | Accepted, `supported` |
| Mock, `fixture-classifier-v0` | Uncertain | HTTP 200 twice, null category, abstained | Accepted, `uncertain` |
| Fitted local, `d-c007-synthetic-fitted-v1` | Supported | HTTP 200 twice, `Orthopedic` | HTTP 200, rejected by `MOCK_MODE_REQUIRED` |
| Fitted local, `d-c007-synthetic-fitted-v1` | Uncertain | HTTP 200 twice, null category, abstained | HTTP 200, rejected by `MOCK_MODE_REQUIRED` |

All successful classifier responses preserved both document identities and the
five specialty scores in contract order. All six unauthenticated readiness and
classification probes returned HTTP 401. The evaluator rejected an intentionally
wrong mode and model version over HTTP. Frozen-contract regressions covered
incorrect document ID, hash, score order and uncertain category. The Windows
runner confirmed closure of all three temporary ports after each run.

B's `mockServiceClients` sent authenticated HTTP to the classifier. Its
`consumeExchange` returned `mock-mode` for each fitted response. The report model
also withheld both fitted results. The existing consumer is restricted to mock
responses, so the fitted `supported` and `uncertain` states cannot reach the
current report panel. B-005 classifier acceptance remains pending a B client
path that admits fitted results with the same identity and model checks.

The [transport receipt](../../eval/reports/development/c007-classifier-transport-v1.json)
records the locked Python 3.13.7 execution. A separate Python 3.11.7 replay with
its own synthetic bundle produced the same outcomes. The D evaluator passed
113 tests. C's HTTP, contract and inference suites passed 68 tests. The pinned B
consumer passed 221 contract checks, and its report and security suites passed
41 checks. The two HTTP runs used zero model-provider calls.

## Replay with Sara's pinned C-005 bundle

On 2026-11-21, D verified the supplied manifest against C's published SHA-256
and the `model.joblib` bytes against the manifest's artifact SHA-256
`3bbf1c648c6ebd69036ee933c58b7e96cf1a0f5bf60975d1cafe7f59ec09fd6a`.
The installed classifier code matched the pinned C source. Python 3.13.7 and
all four fitted-model dependencies matched the run configuration. The launcher
loaded the verified bundle on temporary authenticated loopback.

| Synthetic case | D evaluator on exact C-005 | B client on pinned `main` |
| --- | --- | --- |
| Supported | Two identical HTTP 200 responses, `supported`, `Orthopedic` | HTTP 200, `MOCK_MODE_REQUIRED`, report state `invalid` |
| Uncertain | Two identical HTTP 200 responses, `uncertain`, null category, recorded as abstained | HTTP 200, `MOCK_MODE_REQUIRED`, report state `invalid` |

Both fitted cases had the published model version, original document ID and
canonical text SHA-256, and five probability scores in contract order. D also
verified request correlation and `no-store`. Readiness reported the expected
version. The evaluator rejected deliberately wrong mode and model-version
expectations. Both mock control states were accepted by B. Six unauthenticated
probes returned HTTP 401 and all three temporary ports closed. The 16 targeted
evaluator tests passed. The run made zero model-provider calls.

The D-side C-007 exact-artifact check passed. B-005 remains open because the
current B web consumer denies fitted responses before either state can appear
in the report panel. The [owner-bundle receipt](../../eval/reports/development/c007-owner-c005-transport-v1.json)
preserves the exact pins and observed outcomes.

## Submitted-text examples for B-005

On 2026-11-22, D verified two English synthetic examples through
`prepareSubmitted` on the pinned B baseline `f8bba16`. Both passed
`franc-6.2.0-en-v1` through the normal synthetic text submission path. D sent
the resulting prepared documents to Sara's pinned C-005 classifier at `7181a1a`.
Each returned HTTP 200 twice with identical results and matching document ID,
canonical text SHA-256, model version and five scores in contract order. The
knee note returned `supported` and `Orthopedic`. The follow-up note returned
`uncertain` and a null category. The run used zero provider calls.

The [example receipt](../../eval/reports/development/c007-b005-admitted-synthetic-examples-v1.json)
contains the exact paste text, expected responses and report states. B's joint
check of the current opt-in app and rendered report remains open.

Goran reported that both exact examples also returned HTTP 201 through the
built app's submitted-text route, with matching canonical digests. D selected
that same pair for the C-005 replay first, using Sara's pinned Windows bundle.
The same inputs are pinned for the C-008 follow-up. See the
[team handoff record](../../eval/reports/development/d-b-team-handoff-intake-v1.json).

## Joint C-005 and C-008 report preflight

Sara offered to host the joint run on Windows and reported verifying both
pinned classifiers over HTTP with D's exact synthetic pair. D independently
replayed that pair through baseline text admission and authenticated fitted
C-005 inference. All four classification requests returned HTTP 200. The two
per case were identical and matched the expected identity, model version and
ordered scores. The knee note was `supported` and `Orthopedic`. The follow-up
note was `uncertain` with a null category, recorded as an abstention.

D verified the supplied C-008 development startup manifest against SHA-256
`affe7af9e2d0f8df46d25642fd2e0cbf0ff3e45f2a8576b9c87cc2cc257d7f32`.
Its parsed fields match the published frozen manifest except for `stage`.
Both pin the same model version and artifact SHA-256. The startup command
uses `.cache/c008-short-text-v1/matched-policy`. The matching model file is
unavailable in the local D workspace, so D's independent C-008 replay is
pending. Sara has both bundles for the hosted run.

Goran subsequently identified opt-in B-005 commit
`9cdab928923056f31dd1f37ab4b569cc638999ab`. His initial report recorded a
C-005 authenticated-readiness blocker and an interrupted C-008 browser capture.

At 22:23 Europe/Belgrade on 2026-11-22 Goran reported the passing Windows
recheck: C-005 first, then C-008 in a fresh session. Both bundles passed six
fitted HTTP checks, including request-ID correlation. All four app submissions
returned HTTP 201. Both models rendered Orthopedic for the supported input and
Specialty uncertain with no assigned specialty for the uncertain input. Goran
verified the recheck receipt against both model pins and found no mismatch.

The authoritative new file is `b005-joint-replay-recheck-receipt.json`.
Sara's earlier attachment was the failed receipt sent by mistake. D received
the passing file with SHA-256
`a7a0412720b243c1aac4cb86e27ad5f64c861b985e60084f06d8502d5c2dda06`
and checked both manifest pins and loaded model versions. All four report rows
have distinct valid document IDs, the exact expected canonical text hashes,
HTTP 201 and the expected rendered labels and assigned-specialty values.
Both fitted probes record six passes, HTTP 200 readiness and successful
request-ID correlation. No receipt mismatch was found.

The classifier integration evidence intake is complete. D verified the owner
receipt against the pins and exact synthetic inputs; D did not rerun the
Windows browser workflow. The receipt supplies correlation outcomes, not raw
request-ID pairs or score vectors. Findings, summaries and answers remain
mocked in these runs, so the broader B-005 task still includes the other
services. The [verification record](../../eval/reports/development/b005-joint-recheck-receipt-verification-v1.json)
and [preflight history](../../eval/reports/development/b005-c005-c008-joint-preflight-v1.json)
preserve the verification scope and earlier reports.

Goran published the platform notes and Windows runbook in documentation commit
[`22ca6a38c9b83fb1616aab2bd5ede73f3a60f9fd`](https://github.com/NemanjaManic/notelens/commit/22ca6a38c9b83fb1616aab2bd5ede73f3a60f9fd).
D fetched the published object, verified its direct parent is the replayed web
commit `9cdab928923056f31dd1f37ab4b569cc638999ab`, and reviewed both changed
documentation files. The published receipt hash, classifier commit, startup
manifest hashes and model versions match the already verified private receipt.
The runbook covers authenticated C-005 readiness and C-008 report capture after
HTTP 201. No runtime code changed in this commit, so D did not repeat runtime
tests for this documentation update. The [documentation review](../../eval/reports/development/b005-published-documentation-review-v1.json)
closes D's outstanding request for the exact published platform documentation pin.

Keep the three platform pins separate: `9cdab928` is the executed classifier
replay, `22ca6a3` publishes its notes and runbook, and `4fb192e` is the separately
reviewed A-008 web-admission fix. These do not close the remaining service
integrations or Nemanja's development measurement.

## Reproduce the evaluator check

Start C's authenticated loopback launcher using the startup instructions in
`docs/ml/integration.md` at the C commit. Set `NOTELENS_CLASSIFIER_SERVICE_TOKEN`
in the evaluator shell to the same local token. For mock mode, start one process
per scenario and use `--mode mock --case supported` or `--mode mock --case uncertain`.
For fitted mode, provide the independently pinned expected version. For example,
with C's approved artifact and the default loopback port:

```powershell
$expectedModel = 'c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc'
./eval/.venv/Scripts/python.exe -m notelens_eval.classifier_http --mode live --model-version $expectedModel --case supported
./eval/.venv/Scripts/python.exe -m notelens_eval.classifier_http --mode live --model-version $expectedModel --case uncertain
```

The check uses two authenticated loopback POSTs per case. It requires matching
request IDs and `Cache-Control: no-store`, validates the returned document ID and
canonical hash, checks score order through the frozen contract, and confirms the
expected mode, fitted version, status and category. An `uncertain` result with a
null category is recorded as an abstention even when all five scores are present.
The command writes a summary to stdout without document text or credentials.
