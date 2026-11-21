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
