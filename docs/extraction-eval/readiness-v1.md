# Member D integration readiness check

Date: 2026-11-12. Scope: Member D's local service and read-only inspection of
B-owned draft contracts. This is an owner-local mock readiness check, not acceptance
of the frozen contract or cross-service integration.

## Run

From the repository root in PowerShell:

```powershell
./eval/.venv/Scripts/python.exe -m notelens_eval.readiness
```

The command uses the existing D evaluation environment, starts a temporary loopback
service in mock mode, sends only committed synthetic demo requests and shuts down the
service. It writes the detailed machine-readable result to the ignored
`eval/reports/local/readiness/results.json`; the report omits request text.

## Results

- JSON Schema Draft 2020-12 validation passed.
- All 60 OpenAPI `$ref` references resolved; operation IDs are unique. D's two POST
  operations point to the expected request and response definitions in the canonical
  schema file.
- The extraction request and question fixtures have the same prepared document ID,
  canonical text and digest and both pass their draft request schemas.
- The local service passed 14 HTTP checks: health/schema/mock mode; no-store and draft
  headers; extraction schema, document identity and exact evidence; document-answer
  schema and source identity; generation diagnostics; correlation IDs; safe 422 error
  envelope; oversized text rejection; unsupported language; malformed JSON; invalid
  configured token; changed text with stale digest; and opaque document ID propagation.
- `python -m pytest eval/tests -q`: 25 passed.
- `python -m pytest services/extraction/tests -q`: 42 passed, one existing
  Starlette/httpx deprecation warning.
- `git diff --check`: passed.

The local check confirms D's mock transport conforms to the currently available
provisional schema for these fixtures. It does not prove general semantic support,
production readiness or agreement by B/A/C.

The negative cases also confirm that `doc_id` is an opaque identifier independent of
the text SHA-256: a replacement ID with unchanged text is accepted and echoed in
document sources; changed text with the old digest is rejected. Non-English text
returns the service-specific `unsupported_language` code; malformed JSON, invalid
question, oversized text and invalid configured credentials use draft error codes.
These mappings still require B's contract review.

## Findings and open integration items

No `services/rag` or `services/classifier` runtime packages were present in this
checkout when checked. Therefore A↔D answer composition, C→B/D classification
handoff, frontend session/expiry behavior, and a true all-service run remain untested.
B still owns contract freeze, bindings, root integration/startup, and shared fixtures.
The readiness output records cross-service status as `not_run` explicitly.

The shared contract remains labeled draft, and readiness does not freeze it. The
previous D-to-B handoff still needs answers on planned/cancelled procedure states,
whether mention spans become shared fields, correlation behavior after a document
switch, health endpoint documentation, canonicalization for repeated leading BOM,
safe status/error mapping, auth and operational controls. These are B/team decisions;
D must adapt its service after they are recorded.

The existing small catalog mock intentionally misses most concepts. A real provider
and its model, spending ceiling, retention terms and retry/deadline controls are not
approved. No live request, human annotation, clinical review, actual C split/manifest,
or A corpus/retrieval evaluation was run.

## Remaining Member D work, by dependency

| Work | Can proceed now? | Needed to finish |
| --- | --- | --- |
| D-001 annotation ontology and support rubric | Draft exists; acceptance pending | Team review of ontology, matching and semantic-support rules |
| D-010 independent eval scaffold | Local provisional package exists | Frozen shared records/bindings and foundation integration |
| D-004 extraction and D-005 answers | Offline mock service exists | B contract/foundation decisions; approved provider and semantic evaluation for real behavior |
| D-002 select real annotation documents; D-003 publish assignments | No | C-002 permitted canonical docs/manifests, stable group/split IDs and access policy |
| D-012 annotations; D-013 adjudication | No | Frozen assignments, independent human submissions, A/B/C inputs and adjudicator decisions |
| D-006 shared evaluator | Local offline suite exists | A/C adapters, actual retrieval/coverage/risk metrics, approved frozen records and live profile gates |
| D-007 cross-module QA | Synthetic document QA exists | A's reviewed corpus and B/A/D agreement on approximately 80 source-grounded cases and split |
| D-008 judge calibration/review | No | Development references, separate human reviewers; budget approval before live judging |
| D-011 thresholds | No | Actual development measurement and named team decisions; no thresholds inferred from mocks |
| D-009 final report | No | Frozen gate, A/C/B delivery, human review and approved final configuration |

## Most useful next actions before first integration

1. B records contract decisions, freezes canonical schema/version and supplies bindings
   plus shared positive/negative fixtures. D then reruns this readiness check against
   that version and updates any adapter differences.
2. A and C publish their owner-local mock services and sample requests/responses. B
   connects the three Python services through the frontend/orchestrator; D can add
   A/C fixture cases to an evaluation smoke after those artifacts exist.
3. C supplies the permitted C-002 source/split/group manifests and access policy so
   D can propose actual annotation IDs without crossing splits.
4. The team settles the required provider and operating limits before any live request.

The readiness tool and its tests are D-owned. It makes no changes to the shared
contract, A/C services, B orchestration or another member's annotation directories.
