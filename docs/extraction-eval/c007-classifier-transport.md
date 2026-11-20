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
directory. The classifier branch and its history provide configuration and
verification records. The model bundle was unavailable in the D environment.
The shared run used a separate TF-IDF and Logistic Regression pipeline fitted on
five synthetic tokens, following C's `model_bundle` test fixture. The C-005
artifact check remains pending receipt of the trusted bundle.

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
