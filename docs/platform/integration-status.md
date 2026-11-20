# B-005 classifier integration status

**Status, 2026-11-20.** B-005 remains open. This branch adds a server-side classifier
test client and a loopback HTTP suite. The application and hosted CI continue in mock
mode. Literature, extraction and document answers stay on their existing mocks while
A-008 and D-005 are open.

## Published classifier evidence

The branch starts from `origin/main` at `f8bba16`. Sara's published
`origin/member-c/classification` advanced to `9fc84e9`. Her branch marks C-006 complete and
records 60 focused HTTP and contract tests and seven loopback probes against the installed
classifier from `7181a1abdf7831bb247510821c886b0e031d5de0`. The probes covered readiness,
repeatable supported and uncertain results, and both no-model 503 responses. C-007 still
lists B's integration and D's evaluator verification as pending.
[C-006 and C-007 evidence](https://github.com/NemanjaManic/notelens/blob/9fc84e9afc1ce7045dff653cb57bb9db1a29c300/docs/ml/integration.md#c-007-owner-local-check-2026-11-20)

Sara's recorded development candidate has manifest SHA-256
`e79fff1c8c8c3b1b14afa32d02bc44f94680bf09902cb82cfa5e4dd71b967f5f` and model version
`c005-frozen-uncertainty-v1-3e9f40bac00e5550203b299efc55b450b81ac904e7c35d46582be80514c66dbc`.
The bundle is absent from B's checkout. The fitted check requires Sara to confirm the
reviewed classifier commit, the approved bundle access or supervised run, the manifest
digest and model version, the exact locked Windows launch, and approved smoke examples.
Use the approved public or synthetic examples only. Preserve C-002's restricted access
to reports and source mappings, and keep the final test locked.

## Local fixture check

From the repository root with the locked Node workspaces installed:

```powershell
$env:NOTELENS_CLASSIFIER_TEST_PROFILE = 'fixture'
& ./node_modules/.bin/tsc.cmd --noEmit --project apps/web/tests/tsconfig.integration.json
node --test apps/web/tests/integration/classifier-http.test.ts
```

The fixture binds an ephemeral port on `127.0.0.1`, generates a temporary bearer token and
returns frozen v1 `mock` results for two synthetic documents. On Node 24.22.1, all 11
tests passed, including authenticated readiness, the readiness 503, repeatable supported
and uncertain outcomes with the expected category and five ordered scores, unique
business request IDs, and document ID and SHA-256 binding. Negative checks covered a
wrong bearer token, mismatched success and error correlation, wrong document ID and
digest, and rejection of mock results by the fitted profile. The suite closes the listener
after the run.

The local production build, default mock smoke and B-008 HTTP and log audit also passed.
The frozen contract and generated binding checks, CI workflow policy check, and 369
existing web regressions passed locally. Hosted CI was outside this local check.

## Joint fitted-model verification

Once Sara confirms the handoff, start the pinned classifier with the reviewed artifact
using her locked Windows startup instructions. The runner connects only to
`127.0.0.1`. Use the same temporary local bearer token in the classifier process and
the Node test process through `NOTELENS_CLASSIFIER_SERVICE_TOKEN`. Keep the token
out of command arguments, files, chat and logs.

Prepare a local UTF-8 JSON file without a BOM from the approved English samples. It has
`supported` and `uncertain` objects. Each has `text` and `source_kind`, with source kind
`synthetic_text` or `public_text`. The supported example also has the expected v1
`category`. The runner prepares canonical text and computes each SHA-256 before sending
the classification request.

```powershell
$env:NOTELENS_CLASSIFIER_TEST_PROFILE = 'fitted'
$env:NOTELENS_CLASSIFIER_TEST_PORT = '<classifier loopback port>'
$env:NOTELENS_CLASSIFIER_TEST_MODEL_VERSION = '<reviewed model version>'
$env:NOTELENS_CLASSIFIER_TEST_EXAMPLES = '<path to approved examples JSON>'
node --test apps/web/tests/integration/classifier-http.test.ts
```

In this profile, wire mode `live` means fitted local inference. The joint run must confirm
authenticated readiness and the pinned model version, repeatable supported and uncertain
classification with matching identities and request IDs, and rejection of unauthorized
calls and unexpected model versions. Confirm with Sara which startup, redacted log and
shutdown checks should be repeated jointly and which C-007 evaluator checks D will run.
The fitted profile is pending this handoff.
