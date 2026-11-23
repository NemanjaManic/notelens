"""Private source-quote protocol: frozen wire contract, identity and safe abstention."""
import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from notelens_extraction.demo import request
from notelens_extraction.evidence import digest
from notelens_extraction.errors import ServiceError
from notelens_extraction.main import create_app
from notelens_extraction.openai_trial import MODEL, OpenAIResponsesProvider
from notelens_extraction.providers import NO_ANSWER
from notelens_extraction.quote_hints import build, SCHEMAS, validate_private
from notelens_extraction.service import run


def entity(quote="chest pain", evidence="The patient denies chest pain."):
    return {"type": "symptom", "mention_quote": quote, "mention_occurrence": 0,
            "assertion": "negated", "temporality": "unknown", "subject": "patient",
            "procedure_status": None, "evidence": [{"quote": evidence, "occurrence": 0}]}


def hints():
    return {"entities": [entity()], "summary_quotes": [{"quote": "The patient denies chest pain.", "occurrence": 0}]}


def provider(value):
    envelope = {"object": "response", "model": MODEL, "status": "completed", "output": [{
        "type": "message", "role": "assistant", "status": "completed", "phase": "final_answer",
        "content": [{"type": "output_text", "text": json.dumps(value)}]}]}
    return OpenAIResponsesProvider(Mock(return_value=envelope), model=MODEL,
                                  max_output_tokens=4096, input_format="messages", output_format="quote_hints")


def test_model_only_selects_quotes_server_supplies_identity_and_unicode_positions():
    original = request()
    result, diagnostics = run(original, "extract", provider(hints()))
    assert original == request() and result["doc_id"] == original["document"]["doc_id"]
    item = result["items"][0]
    assert original["document"]["text"][item["mention"]["start"]:item["mention"]["end"]] == "chest pain"
    assert result["summary"]["result"]["text"] == "The patient denies chest pain."
    assert result["extraction_provenance"]["model"] == MODEL
    assert diagnostics == {"attempts": 1, "raw_validation_failures": 0, "repairs": 0}


def test_repeated_mentions_have_explicit_evidence_and_local_occurrence():
    source = request()
    text = "\U0001fa7a No cough.\nReports cough.\nNo cough."
    source["document"].update(text=text, text_sha256=digest(text))
    first, last = entity("cough", "No cough."), entity("cough", "No cough.")
    last["evidence"][0]["occurrence"] = 1
    result, _ = run(source, "extract", provider({"entities": [first, last], "summary_quotes": []}))
    positions = [item["mention"]["start"] for item in result["items"]]
    assert positions == [text.index("cough"), text.rindex("cough")]
    assert result["summary"]["status"] == "failed"


def test_bad_summary_does_not_discard_independently_valid_extraction():
    value = hints()
    value["summary_quotes"][0]["quote"] = "Unsupported summary."
    result, _ = run(request(), "extract", provider(value))
    assert len(result["items"]) == 1
    assert result["extraction_status"] == "completed"
    assert result["summary"]["status"] == "failed"
    assert result["summary"]["error"]["code"] == "validation_failure"


@pytest.mark.parametrize("bad", [
    {**hints(), "doc_id": "model-selected-other-document"},
    {**hints(), "entities": [{**entity(), "mention_occurrence": True}]},
    {**hints(), "entities": [{**entity(), "assertion": "definite"}]},
])
def test_invalid_semantics_and_unresolvable_quotes_fail_without_retry(bad):
    p = provider(bad)
    with pytest.raises(ServiceError):
        run(request(), "extract", p)
    p._send.assert_called_once()


def test_unique_quote_does_not_require_a_model_occurrence_number():
    value = hints()
    value["entities"][0]["mention_occurrence"] = 50
    value["entities"][0]["evidence"][0]["occurrence"] = 50
    value["entities"][0]["procedure_status"] = "performed"
    result, _ = run(request(), "extract", provider(value))
    assert result["items"][0]["mention"]["quote"] == "chest pain"
    assert result["items"][0]["procedure_status"] is None


def test_procedure_without_selected_status_stays_unknown_not_performed():
    value = {"entities": [{**entity("appendectomy", "The patient had an appendectomy in 2018."),
                            "type": "procedure", "assertion": "confirmed", "temporality": "historical"}],
             "summary_quotes": []}
    # Build checks conservative protocol mapping; independent source validation
    # can still reject a status that contradicts known explicit source context.
    result = build("extract", value, request()["document"], MODEL)
    assert result["items"][0]["procedure_status"] == "unknown"


def test_invalid_candidate_is_explicit_partial_not_silent_omission():
    value = hints()
    value["entities"].append({**entity(), "mention_quote": "not present"})
    result, _ = run(request(), "extract", provider(value))
    assert len(result["items"]) == 1 and result["extraction_status"] == "partial"
    assert result["extraction_error"]["code"] == "validation_failure"
    assert result["warnings"] and "incomplete" in result["warnings"][0]


def test_all_invalid_candidates_and_summary_fail_closed():
    value = {"entities": [{**entity(), "mention_quote": "not present"}], "summary_quotes": []}
    with pytest.raises(ServiceError):
        run(request(), "extract", provider(value))


@pytest.mark.parametrize("out_of_scope", [False, True])
def test_missing_fact_and_out_of_scope_have_distinct_warnings_with_safe_text(out_of_scope):
    value = {"evidence_state": "insufficient", "out_of_scope": out_of_scope, "quotes": [],
             "gaps": ["The requested age is not provided."]}
    result, _ = run(request("What is the patient's age?"), "answer", provider(value))
    assert result["route"] == "none" and result["text"] == NO_ANSWER
    assert result["prompt_version"] is None and result["components"] == []
    assert any("outside" in w for w in result["warnings"]) is out_of_scope


def test_partial_answer_keeps_supported_quote_and_explicit_gap():
    value = {"evidence_state": "partial", "out_of_scope": False,
             "quotes": [{"quote": "The patient reports cough.", "occurrence": 0}],
             "gaps": ["The patient's age is not provided."]}
    result, _ = run(request("What does the document say about cough and age?"), "answer", provider(value))
    assert result["text"] == "The patient reports cough." and result["evidence_state"] == "partial"
    assert result["prompt_version"] == result["components"][0]["prompt_version"]
    assert "age" in result["warnings"][0]
    value["gaps"] = []
    with pytest.raises(ServiceError):
        run(request("What about cough and age?"), "answer", provider(value))


def test_strict_private_schema_does_not_copy_full_wire_contract_into_model_prompt():
    payload = provider(hints()).prepare("extract", request(), "Unused legacy contract instructions")
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert "Frozen output contract" not in payload["instructions"]
    assert "$defs" not in json.dumps(payload["text"]["format"]["schema"])
    assert "annotation" not in payload["input"][0]["content"][0]["text"]
    validate_private(hints(), SCHEMAS["extract"])


def test_http_route_exercises_quote_protocol_and_frozen_contract():
    client = TestClient(create_app(provider(hints()), token="offline-quote-test"))
    response = client.post("/v1/extract", json=request(), headers={
        "Authorization": "Bearer offline-quote-test", "X-Request-ID": "c0a30ebf-6664-4bac-8d81-809f504028be"})
    assert response.status_code == 200 and response.json()["mode"] == "live"
    assert response.headers["X-Generation-Attempts"] == "1"


def test_coverage_profile_is_explicit_preserves_baseline_and_versions_each_request():
    old = provider(hints())
    new = OpenAIResponsesProvider(old._send, model=MODEL, max_output_tokens=4096,
                                  input_format="messages", output_format="quote_hints",
                                  prompt_profile="coverage_v2", reasoning_effort="low")
    before = old.prepare("extract", request(), "")
    parameters = new.prepare("extract", request(), "")
    assert parameters["reasoning"]["effort"] == "low"
    assert "COVERAGE" in parameters["instructions"]
    assert before == old.prepare("extract", request(), "")
    legacy, _ = run(request(), "extract", old)
    updated, _ = run(request(), "extract", new)
    assert legacy["prompt_version"] == "d-quote-hints-prompts-v1"
    assert updated["prompt_version"] == "d-quote-hints-prompts-v2"
    assert updated["summary"]["result"]["provenance"]["prompt_version"] == updated["prompt_version"]


@pytest.mark.parametrize("options", [
    {"reasoning_effort": "unreviewed"}, {"prompt_profile": "unreviewed"},
    {"prompt_profile": "coverage_v2", "output_format": "contract"},
])
def test_unreviewed_profile_options_fail_before_transport(options):
    send = Mock()
    with pytest.raises(ValueError):
        OpenAIResponsesProvider(send, model=MODEL, max_output_tokens=2048, **options)
    send.assert_not_called()
