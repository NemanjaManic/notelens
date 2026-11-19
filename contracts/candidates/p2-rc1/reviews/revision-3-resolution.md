# Revision 3: Remaining Contract Issues and Owner Decisions

**Prepared:** 2026-11-13. **Coordinator:** B.
**Target:** p2-rc1 revision 3, identified by its new Git commit and manifest SHA256.
**Status:** executable candidate pending affected-owner confirmation; P1 unchanged.

## Actual review evidence

| Supplied response | Actual reviewer and target | Recorded disposition |
| --- | --- | --- |
| [A revision-2 response](member-a-p2-revision-2-response.md) | A's coding agent for Nemanja, 2026-11-13; commit 01e96ab6c6a676efb43073a2eca711e89e419030; manifest 2c5043aa375a5aef1b0fa3806e8204284218d7b671c48bd8474ac74330c8affa. Human approval explicitly not recorded. | One blocking change: preserve completed retrieval independently of generation. Other A-side behaviors technically acceptable. |
| [C revision-2 approval](member-c-p2-rc1-revision-2-approval.md) | C explicitly records human approval, 2026-11-13, for that exact revision-2 commit and manifest. | Approved C's interfaces and shared behavior at revision 2; no remaining C blocker there. This approval is retained and is not silently extended to different bytes. |
| [D proposal review](member-d-p2-proposal-review.md) | User confirmed this is D's response. The file does not identify its reviewer or human/agent status. It reviews the 2026-11-12 P2 prose proposal and expressly excludes revision 2. | Proposal-level dispositions only; no executable-candidate acceptance. D's response requests health-401 details and clarification of the language policy. |

The originals are byte-preserved. A's reported local mock/ASGI/corpus checks are A-side
evidence only; B has not executed or independently verified those service artifacts.
C's reported Python 3.11.9 checks are not reproduction of B's locked Python 3.13 environment.

## P2-11: retrieval completed, generation not run

**Disposition:** agreed with A; implemented in revision 3, pending A's confirmation.

AnswerResult now requires nullable retrieval_provenance. A non-null RetrievalProvenance
records service=rag and the actual completed RetrievalResult's mode, state, corpus_version,
index_version, retriever_version and score_note. State is sufficient/insufficient, not an
operational error. These fields must be copied from the completed retrieval; the record
has no provider, model, prompt or generated-answer version fields.

| Execution | Required representation |
| --- | --- |
| Retrieval completed, insufficient evidence, no generator | Non-null retrieval_provenance/state=insufficient; empty components/claims/sources; null prompt_version; route none, evidence_state insufficient. The fixed English evidence-gap notice remains. |
| Document answer retained after insufficient literature retrieval | Preserve D's supported claims, sources and generation component. Retain retrieval_provenance/state=insufficient, both attempted_routes and an explicit literature gap warning. The mixed partial example uses route mixed and the existing composition version/ID-prefix rules. |
| Literature generation actually ran | Keep generation metadata in its A component and a completed sufficient retrieval record. Corpus/index/retriever versions must match between them. |
| Clarification before retrieval | retrieval_provenance=null, no components/claims/sources, null prompt_version. Do not fabricate execution history. |
| Missing retrieval configuration / failed retrieval | A returns the existing non-2xx ErrorEnvelope, not a fake completed search or empty successful A answer. When B preserves a separate supported result after an upstream failure, retrieval_provenance stays null and warnings describe the failure. attempted_routes records an attempted route, not proof of completed retrieval. |

Overall AnswerResult.mode includes actual retrieval and generation modes: all mock means
mock, all live means live, and a combination means mixed. A live search without generation
is live. A mock D answer plus live insufficient retrieval is mixed. All such fixture values
are synthetic protocol illustrations, not evidence that a live search/provider was run.

The checker rejects missing retrieval history for A generation, inconsistent versions,
generation after insufficient retrieval, retrieval without an attempted literature route,
hidden mixed execution modes, and fabricated retrieval history in pre-search clarification.
It cannot independently observe whether a remote search truly ran; actual invocation and
faithful metadata propagation must be checked in A's service and B's integration tests.

## Disposition of D's proposal-level issues

| Issue | B response on the executable candidate | Remaining action |
| --- | --- | --- |
| P2-01, 08, 11, 12, 15, 17 | D's proposal-level acceptance is recorded as such. Relevant behavior is concrete in the schema, API, examples and README; revision 3 adds the retrieval-only metadata above. | D reviews the actual current candidate and confirms its interfaces/shared behavior; no human status is inferred from the older proposal response. |
| P2-10, 13: health 401 | Implemented in revision 2 and unchanged here: unauthorized/retryable=false ErrorEnvelope; fresh canonical diagnostic UUID shared by response X-Request-ID and body request_id; WWW-Authenticate: Bearer. Ignore incoming health IDs, including malformed/duplicate IDs. Business POST ID rules are separate. A's technical review and C's human approval accepted this exact behavior at revision 2. | D confirms the current explicit behavior. No further implementation change is needed for the requested health shape. |
| P2-09: stateless clarification | The current protocol represents ambiguity as clarification.code=ambiguous_reference with an English message, route none, insufficient evidence and no execution metadata. The foundation exercises a deterministic ambiguous-reference fixture. The service receives no inferred conversation history. | Confirm this protocol and the activation boundary below. No measured general ambiguity detector is claimed. |
| P2-14: language method | PreparedDocument requires an accepted en policy record. Rejected/inconclusive outcomes are not admitted. The boundary proposes 422/unsupported_language for rejection and 422/validation_failure for inconclusive input. The fixture policy is explicitly synthetic, not a real detector. | Confirm the fixture-only foundation and separate live-input activation gate; otherwise identify the precise protocol objection. No provider/model/threshold is invented. |

## Activation boundaries: proposed closure for D's clarification

Freeze the wire representation separately from a later live validation method. The
key-free foundation uses versioned, known English public/synthetic fixtures and explicit
scenarios. This permits contract/binding/mock work without pretending that a live language
or ambiguity detector is implemented. It does not approve arbitrary user input by declaration.

Before B-001 enables real submitted text/PDF input, B must select, review and evaluate its
common language-validation method and limitations. Short, mixed-language and terminology-
heavy examples need that policy's own evaluation. No translation or classifier-confidence
language detector is introduced. Before real B-003 question routing, agree and test the
ambiguity trigger using the stateless request; ask for an explicit topic when the referent
cannot be resolved, rather than invent history or a patient condition. Automatic rewriting
and additional paid calls remain outside the agreed behavior.

This is B's concrete proposed resolution, consistent with A's stated activation-gate
position and C's approved boundary. D has not yet accepted this separation; record an
explicit answer rather than infer agreement from silence.

## Verification

Executed on Windows/PowerShell using the unchanged locked Python 3.13.7 tooling
environment, uv 0.13.7 and Node.js v24.22.1:

- `python build_candidate.py --check`: deterministic regeneration passed.
- `python check_candidate.py`: Draft 2020-12/OpenAPI 3.1.1 and all 155 fixture outcomes
  passed (69 positive, 86 deliberately invalid); all 22 simulated correlation cases passed.
  No HTTP server was called.
- `python -m unittest discover -s tests`: 57 tests passed. The added native-object
  regressions first failed against revision 2, then passed after the retrieval fix.
- The full 57-test suite also passed in a fresh temporary review copy containing the
  manifest-listed files and no .cache directory at startup. It reused the locked
  interpreter/dependencies; no new installation or Python 3.11 compatibility is claimed.
- Compared schema definitions to commit 01e96ab: only AnswerResult changed, and
  RetrievalProvenance is the only new definition. Classification, prepared-document,
  health, extraction and summary definitions are identical. OpenAPI differs only in
  x-candidate-revision metadata; the classifier scaffold brief is unchanged.
- P1's full directory, original checker/tests/dependency lock and foundation task markers
  are unchanged. All three incoming reviews were archived byte-for-byte and are hashed
  by candidate.json.
- The candidate freeze guard remains CANDIDATE_NOT_CANONICAL; the suite checks this and
  the absence of a real freeze record. F-003/F-009 remain open.

Run these commands through the locked/offline uv prefix and scripts/project directory
shown in the candidate README. The scoped speckit-implement preparation workflow used
the official PowerShell resolver with specs/000-foundation selected and
SPECIFY_FEATURE_NO_PERSIST=1; its requirements checklist passed 16/16. No extension
hooks were registered. No service, generated-binding, real retrieval/model/provider,
semantic medical-quality or human-acceptance checks were performed by B here.

## Exact remaining approvals and development handoff

Use the [focused review request](../../../../docs/team/p2-revision-3-review-request.md).
A confirms the P2-11 fix and records Nemanja's owner approval. D reviews the actual
candidate, including extraction/summary/document-answer details and the activation-boundary
proposal above. C confirms the current revision after the narrowly scoped delta; its
classification/input/health definitions and classifier brief are unchanged from revision 2.

Only after actual affected-owner agreement: B promotes the accepted candidate and records
F-003, then executes F-009 generation/fixture compatibility, then coordinates owned F-004
scaffolds. C's existing scaffold brief and A/C/D ownership remain in force. A-010/C-009
still require F-003 and F-004; later business tasks retain F-014 and their other prerequisites.
No freeze record, generated package, task completion, main merge, service edit, deployment,
paid activation or F-014 checkpoint is created by this review package.
