"""OpenAI Responses adapter for an explicitly supplied, budgeted transport."""

import json
import copy
from functools import lru_cache
from importlib.resources import files
from typing import Callable

from .demo import request as demo_request
from .errors import ServiceError
from .evidence import EvidenceError, resolve_quote, validate_span

MODEL = "gpt-6-luna"
DEMO_QUESTION = "Does the patient report cough?"
DEFINITIONS = {"extract": "ExtractionResult", "answer": "AnswerResult"}
JSON_INPUT_PREFIX = "Return a JSON object for the following canonical request:\n"


def align_unique_spans(value: dict, text: str) -> tuple[dict, int]:
    """Resolve invalid numeric coordinates only for exact, uniquely occurring quotes.

    Correct repeated-quote coordinates are retained; ambiguous or absent quotes
    fail closed. Claims, source identities and quoted text are never rewritten.
    """
    result = copy.deepcopy(value)
    count = 0
    def align(span, context=None):
        nonlocal count
        try:
            validate_span(text, span)
            return
        except EvidenceError:
            pass
        try:
            resolved = resolve_quote(text, span["quote"])
        except EvidenceError:
            quote = span.get("quote")
            if not isinstance(quote, str) or not quote or not context:
                raise
            positions = set()
            for evidence in context:
                validate_span(text, evidence)
                offset = evidence["start"]
                while (found := text.find(quote, offset, evidence["end"])) >= 0:
                    positions.add(found)
                    offset = found + 1
            if len(positions) != 1:
                raise EvidenceError("Mention quote is absent or ambiguous in its selected evidence.")
            start = positions.pop()
            resolved = {"start": start, "end": start + len(quote), "quote": quote}
        span.update(resolved)
        count += 1
    def visit(item):
        nonlocal count
        if isinstance(item, dict):
            if isinstance(item.get("mention"), dict) and isinstance(item.get("evidence"), list):
                for evidence in item["evidence"]:
                    visit(evidence)
                align(item["mention"], item["evidence"])
                for key, child in item.items():
                    if key not in {"mention", "evidence"}:
                        visit(child)
                return
            if {"start", "end", "quote"} <= item.keys():
                align(item)
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
    visit(result)
    return result, count


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate provider JSON key.")
        result[key] = value
    return result


def reject_nonfinite(_value):
    raise ValueError("Nonfinite provider JSON number.")


def source_span_hints(request: dict) -> str:
    """Derive line positions from canonical input, without annotation/reference labels."""
    text = request.get("document", {}).get("text")
    if not isinstance(text, str):
        return ""
    spans = []
    start = 0
    for line in text.splitlines(keepends=True):
        quote = line.rstrip("\n")
        if quote:
            spans.append({"start": start, "end": start + len(quote), "quote": quote})
        start += len(line)
    return ("\nCanonical input-derived Unicode code-point line spans (not reference answers): "
            + json.dumps(spans, ensure_ascii=False, separators=(",", ":"))
            + "\nUse these exact ranges for sentence citations. Mention ranges must select the exact "
            "substring within its sentence; do not count UTF-8 bytes or UTF-16 units. "
            "For summaries, omit document headings and duplicate claims. The summary text must "
            "equal the claim texts joined with exactly two LF characters. Do not prepend extra text.")


@lru_cache
def output_contract(definition: str) -> str:
    definitions = json.loads(
        files("notelens_contracts").joinpath("schema.json").read_text(encoding="utf-8")
    )["$defs"]
    return json.dumps({"$ref": f"#/$defs/{definition}", "$defs": {
        name: definitions[name] for name in sorted(referenced_definitions(definition, definitions))
    }}, separators=(",", ":"))


def referenced_definitions(definition: str, definitions: dict) -> set[str]:
    names = set()
    pending = [definitions[definition]]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            ref = value.get("$ref", "")
            if ref.startswith("#/$defs/"):
                name = ref.removeprefix("#/$defs/")
                if name not in names:
                    names.add(name)
                    pending.append(definitions[name])
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return names | {definition}


def invalid_response() -> ServiceError:
    return ServiceError(502, "internal_error", "Generation returned an invalid Responses envelope.")


def completion_text(response: dict, *, model: str = MODEL) -> str:
    if (not isinstance(response, dict) or response.get("object") != "response"
            or response.get("model") != model or response.get("status") != "completed"
            or response.get("error") is not None or response.get("incomplete_details") is not None
            or not isinstance(response.get("output"), list)):
        raise invalid_response()
    texts = []
    for item in response["output"]:
        if isinstance(item, dict) and item.get("type") == "reasoning":
            continue
        if (not isinstance(item, dict) or item.get("type") != "message"
                or item.get("role") != "assistant" or item.get("status") != "completed"):
            raise invalid_response()
        content = item.get("content")
        if not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict):
            raise invalid_response()
        block = content[0]
        if block.get("type") != "output_text" or not isinstance(block.get("text"), str):
            raise invalid_response()
        if item.get("phase") == "commentary":
            continue
        if item.get("phase") not in (None, "final_answer"):
            raise invalid_response()
        texts.append(block["text"])
    if len(texts) != 1:
        raise invalid_response()
    return texts[0]


class OpenAIResponsesProvider:
    """Prepare document-grounded requests for an explicitly supplied transport."""

    mode = "live"
    configured = True
    provider_name = "openai"

    def __init__(self, send: Callable[[dict], dict], *, model: str, max_output_tokens: int,
                 input_format: str = "text", output_format: str = "contract",
                 prompt_profile: str = "baseline_v1", reasoning_effort: str = "none"):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An explicitly selected model is required.")
        if type(max_output_tokens) is not int or max_output_tokens <= 0:
            raise ValueError("A positive output token limit is required.")
        if input_format not in ("text", "messages"):
            raise ValueError("The input format must be text or messages.")
        if output_format not in ("contract", "quote_hints"):
            raise ValueError("The output format must be contract or quote_hints.")
        if prompt_profile not in ("baseline_v1", "coverage_v2") or (
                prompt_profile == "coverage_v2" and output_format != "quote_hints"):
            raise ValueError("The prompt profile is incompatible with the selected output format.")
        if reasoning_effort not in ("none", "low"):
            raise ValueError("The reviewed reasoning effort must be none or low.")
        self._send = send
        self.model = model
        self._max_output_tokens = max_output_tokens
        self._input_format = input_format
        self._output_format = output_format
        self._prompt_profile = prompt_profile
        self._reasoning_effort = reasoning_effort

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        raw = completion_text(self._send(self.prepare(operation, request, instructions, repair=repair)), model=self.model)
        try:
            value = json.loads(raw, object_pairs_hook=strict_object, parse_constant=reject_nonfinite)
            if self._output_format == "quote_hints":
                from .quote_hints import build
                prompt_version = ("d-quote-hints-prompts-v2" if operation == "extract" and self._prompt_profile == "coverage_v2"
                                  else "d-quote-hints-prompts-v1")
                value = build(operation, value, request["document"], self.model, prompt_version)
            else:
                value, _ = align_unique_spans(value, request["document"]["text"])
            return json.dumps(value, ensure_ascii=False)
        except (ValueError, EvidenceError, TypeError, KeyError):
            raise invalid_response() from None

    def prepare(self, operation: str, request: dict, instructions: str, *, repair: bool = False) -> dict:
        if repair or operation not in DEFINITIONS:
            raise ServiceError(422, "validation_failure", "Unsupported provider operation or retry.")
        text = JSON_INPUT_PREFIX + json.dumps(request, ensure_ascii=False, separators=(",", ":"))
        input_value = text if self._input_format == "text" else [
            {"role": "user", "content": [{"type": "input_text", "text": text}]}]
        payload = {
            "model": self.model,
            "instructions": instructions + source_span_hints(request) + "\nSet mode to live and identify the provider as openai "
            f"and the model as {self.model} in component provenance.\n"
            f"Frozen output contract: {output_contract(DEFINITIONS[operation])}",
            "input": input_value,
            "text": {"format": {"type": "json_object"}},
            "max_output_tokens": self._max_output_tokens,
            "reasoning": {"effort": self._reasoning_effort},
            "service_tier": "default",
            "store": False,
            "stream": False,
            "background": False,
            "truncation": "disabled",
            "tools": [],
            "tool_choice": "none",
        }
        if self._output_format == "quote_hints":
            from .quote_hints import SCHEMAS
            payload["instructions"] = files("notelens_extraction").joinpath(
                "prompts", f"{operation}-quotes-v{'2' if operation == 'extract' and self._prompt_profile == 'coverage_v2' else '1'}.txt"
            ).read_text(encoding="utf-8")
            payload["text"] = {"format": {"type": "json_schema", "name": f"notelens_{operation}_quote_hints_v1",
                                          "strict": True, "schema": copy.deepcopy(SCHEMAS[operation])}}
        return payload


class OpenAITrialProvider(OpenAIResponsesProvider):
    """Preserve the original trial's exact two-request admission boundary."""

    def __init__(self, send: Callable[[dict], dict], *, max_output_tokens: int):
        super().__init__(send, model=MODEL, max_output_tokens=max_output_tokens)

    def prepare(self, operation: str, request: dict, instructions: str, *, repair: bool = False) -> dict:
        if (repair or operation not in DEFINITIONS
                or request != demo_request(DEMO_QUESTION if operation == "answer" else None)):
            raise ServiceError(422, "validation_failure", "Request is outside the synthetic provider trial.")
        # Retain historical pins solely for the already-consumed original trial.
        # Fresh execution uses OpenAIResponsesProvider and newly reviewed pins.
        payload = super().prepare(operation, request, instructions)
        payload["input"] = payload["input"].removeprefix(JSON_INPUT_PREFIX)
        payload["instructions"] = payload["instructions"].replace(source_span_hints(request), "", 1)
        return payload
