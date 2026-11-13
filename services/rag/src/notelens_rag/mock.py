"""Explicit synthetic protocol examples, with no corpus, index or provider access."""


DEMO_QUESTION = "What is the synthetic demo topic?"
STATEMENT = "This synthetic literature fixture demonstrates the NoteLens RAG interface."
MOCK_WARNING = "Synthetic mock response; no real retrieval or model call was made."
DEMO_NOTICE = "Educational demo. Not a doctor. Do not submit real personal medical reports."


def result(operation, scenario):
    source = {"source_id": "mock-source-1", "kind": "literature", "topic_id": "mock-topic-1",
              "passage_id": "mock-passage-1", "title": "Synthetic NoteLens Literature Example",
              "url": "https://example.invalid/notelens/synthetic", "text": STATEMENT,
              "snapshot_date": "2026-11-13"}
    versions = {"corpus_version": "mock-corpus-v1", "index_version": "mock-index-v1",
                "retriever_version": "mock-retriever-v1"}
    if operation == "retrieve":
        sufficient = scenario == "sufficient"
        return {"schema_version": "1.0.0", "mode": "mock",
                "state": "sufficient" if sufficient else "insufficient",
                "passages": [{**source, "score": 1.0}] if sufficient else [], **versions,
                "score_note": "Synthetic fixture score: higher ranks better within mock-retriever-v1; not clinical confidence."}
    body = {"schema_version": "1.0.0", "mode": "mock", "language": "en",
            "text": "The available sources do not support an answer.", "claims": [], "sources": [],
            "evidence_state": "insufficient", "warnings": [MOCK_WARNING, DEMO_NOTICE],
            "route": "none", "answer_version": "rag-mock-v1", "prompt_version": None,
            "components": [], "attempted_routes": ["literature"], "clarification": None}
    if scenario == "clarification":
        message = "Please name the medical topic you mean."
        body.update(text=message, clarification={"code": "ambiguous_reference", "message": message})
    elif scenario == "sufficient":
        component_id = "mock-rag-1"
        body.update(text=STATEMENT, evidence_state="sufficient", route="literature",
                    prompt_version="mock-template-v1",
                    claims=[{"claim_id": "mock-claim-1", "text": STATEMENT,
                             "scope": "general_information", "source_ids": [source["source_id"]],
                             "component_id": component_id}],
                    sources=[{**source, "component_id": component_id}],
                    components=[{"component_id": component_id, "service": "rag",
                                 "operation": "literature-answer", "mode": "mock",
                                 "output_version": "rag-mock-v1", "prompt_version": "mock-template-v1",
                                 "provider": "mock", "model": "static-fixture-v1",
                                 "configuration_version": "mock-default-v1", **versions}])
    return body
