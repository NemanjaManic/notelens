"""Test Responses integration through the extraction service with an offline transport."""

import json
from unittest.mock import Mock

import pytest

from notelens_extraction.demo import request
from notelens_extraction.errors import ServiceError
from notelens_extraction.openai_trial import DEMO_QUESTION, MODEL, JSON_INPUT_PREFIX, OpenAITrialProvider, OpenAIResponsesProvider, source_span_hints, align_unique_spans
from notelens_extraction.evidence import EvidenceError
from notelens_extraction.providers import FakeProvider
from notelens_extraction.service import Diagnostics, run


def envelope(text):
    return {"object": "response", "model": MODEL, "status": "completed", "output": [
        {"type": "reasoning"},
        {"type": "message", "role": "assistant", "status": "completed", "content": [
            {"type": "output_text", "text": text}
        ]},
    ]}


@pytest.mark.parametrize("input_format", ["text", "messages"])
@pytest.mark.parametrize(("operation", "question", "definition"), [
    ("extract", None, "ExtractionResult"),
    ("answer", DEMO_QUESTION, "AnswerResult"),
])
def test_trial_runs_frozen_contract_and_evidence_checks(operation, question, definition, input_format):
    payload = request(question)
    record = json.loads(FakeProvider().generate(operation, payload, "", repair=False))
    record["mode"] = "live"
    provenance = ([record["extraction_provenance"], record["summary"]["result"]["provenance"]]
                  if operation == "extract" else record["components"])
    for component in provenance:
        component.update(mode="live", provider="openai", model=MODEL)
    send = Mock(return_value=envelope(json.dumps(record)))
    provider = OpenAIResponsesProvider(send, model=MODEL, max_output_tokens=2048, input_format=input_format)
    result, diagnostics = run(payload, operation, provider)
    assert result == record
    assert diagnostics == {"attempts": 1, "raw_validation_failures": 0, "repairs": 0}
    send.assert_called_once()
    parameters = send.call_args.args[0]
    if input_format == "text":
        assert parameters["input"].startswith(JSON_INPUT_PREFIX)
        assert json.loads(parameters["input"].removeprefix(JSON_INPUT_PREFIX)) == payload
    else:
        assert parameters["input"][0]["role"] == "user"
        assert parameters["input"][0]["content"][0]["type"] == "input_text"
        input_text = parameters["input"][0]["content"][0]["text"]
        assert input_text.startswith(JSON_INPUT_PREFIX)
        assert json.loads(input_text.removeprefix(JSON_INPUT_PREFIX)) == payload
    assert parameters["model"] == MODEL and parameters["max_output_tokens"] == 2048
    assert parameters["store"] is False and parameters["tools"] == []
    contract = json.loads(parameters["instructions"].split("Frozen output contract: ", 1)[1])
    assert contract["$ref"] == f"#/$defs/{definition}"
    assert definition in contract["$defs"]


@pytest.mark.parametrize("response", [
    {"status": "incomplete"},
    {**envelope("{}"), "model": "unexpected"},
    {**envelope("{}"), "output": [
        {"type": "message", "role": "assistant", "status": "completed",
         "content": [{"type": "refusal", "refusal": "private provider detail"}]},
    ]},
    envelope("{}"),
    envelope('{"mode":"live","mode":"mock"}'),
    envelope('{"value":NaN}'),
])
def test_trial_rejects_bad_response_without_retry(response):
    send = Mock(return_value=response)
    diagnostics = Diagnostics()
    with pytest.raises(ServiceError) as failure:
        run(request(), "extract", OpenAITrialProvider(send, max_output_tokens=100), diagnostics=diagnostics)
    assert failure.value.status == 502
    assert "private provider detail" not in failure.value.message
    assert diagnostics.attempts == 1
    send.assert_called_once()


def test_trial_rejects_other_valid_questions_before_transport():
    send = Mock()
    with pytest.raises(ServiceError) as failure:
        run(request("A modified question"), "answer", OpenAITrialProvider(send, max_output_tokens=100))
    assert failure.value.status == 422
    send.assert_not_called()


def test_input_derived_span_hints_preserve_non_bmp_and_repeated_lines():
    text = "\U0001fa7a\nRepeated sentence.\nRepeated sentence."
    hints = source_span_hints({"document": {"text": text}})
    spans = json.loads(hints.split("not reference answers): ", 1)[1].split("\nUse these", 1)[0])
    assert spans[1] == {"start": 2, "end": 20, "quote": "Repeated sentence."}
    assert spans[2] == {"start": 21, "end": 39, "quote": "Repeated sentence."}
    assert all(text[s["start"]:s["end"]] == s["quote"] for s in spans)


def test_unique_quote_alignment_preserves_claims_and_original_response():
    raw = {"claim": "Unchanged", "evidence": {"start": 9, "end": 14, "quote": "cough"}}
    aligned, count = align_unique_spans(raw, "\U0001fa7a cough")
    assert count == 1 and aligned["evidence"] == {"start": 2, "end": 7, "quote": "cough"}
    assert aligned["claim"] == raw["claim"] and raw["evidence"]["start"] == 9


def test_repeated_quote_alignment_keeps_valid_position_and_rejects_ambiguity():
    raw = {"start": 6, "end": 11, "quote": "cough"}
    assert align_unique_spans(raw, "cough cough") == (raw, 0)
    with pytest.raises(EvidenceError):
        align_unique_spans({**raw, "start": 2}, "cough cough")
    with pytest.raises(EvidenceError):
        align_unique_spans(raw, "No matching evidence")
