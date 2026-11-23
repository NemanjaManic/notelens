"""OpenAI Responses adapter for an explicitly supplied, budgeted transport."""

import json
from functools import lru_cache
from importlib.resources import files
from typing import Callable

from .demo import request as demo_request
from .errors import ServiceError

MODEL = "gpt-6-luna"
DEMO_QUESTION = "Does the patient report cough?"
DEFINITIONS = {"extract": "ExtractionResult", "answer": "AnswerResult"}


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
        texts.append(block["text"])
    if len(texts) != 1:
        raise invalid_response()
    return texts[0]


class OpenAIResponsesProvider:
    """Prepare document-grounded requests for an explicitly supplied transport."""

    mode = "live"
    configured = True
    provider_name = "openai"

    def __init__(self, send: Callable[[dict], dict], *, model: str, max_output_tokens: int):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An explicitly selected model is required.")
        if type(max_output_tokens) is not int or max_output_tokens <= 0:
            raise ValueError("A positive output token limit is required.")
        self._send = send
        self.model = model
        self._max_output_tokens = max_output_tokens

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        return completion_text(self._send(self.prepare(operation, request, instructions, repair=repair)), model=self.model)

    def prepare(self, operation: str, request: dict, instructions: str, *, repair: bool = False) -> dict:
        if repair or operation not in DEFINITIONS:
            raise ServiceError(422, "validation_failure", "Unsupported provider operation or retry.")
        return {
            "model": self.model,
            "instructions": instructions + "\nSet mode to live and identify the provider as openai "
            f"and the model as {self.model} in component provenance.\n"
            f"Frozen output contract: {output_contract(DEFINITIONS[operation])}",
            "input": json.dumps(request, ensure_ascii=False, separators=(",", ":")),
            "text": {"format": {"type": "json_object"}},
            "max_output_tokens": self._max_output_tokens,
            "reasoning": {"effort": "none"},
            "service_tier": "default",
            "store": False,
            "stream": False,
            "background": False,
            "truncation": "disabled",
            "tools": [],
            "tool_choice": "none",
        }


class OpenAITrialProvider(OpenAIResponsesProvider):
    """Preserve the original trial's exact two-request admission boundary."""

    def __init__(self, send: Callable[[dict], dict], *, max_output_tokens: int):
        super().__init__(send, model=MODEL, max_output_tokens=max_output_tokens)

    def prepare(self, operation: str, request: dict, instructions: str, *, repair: bool = False) -> dict:
        if (repair or operation not in DEFINITIONS
                or request != demo_request(DEMO_QUESTION if operation == "answer" else None)):
            raise ServiceError(422, "validation_failure", "Request is outside the synthetic provider trial.")
        return super().prepare(operation, request, instructions)
