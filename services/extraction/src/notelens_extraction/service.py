"""Request-local orchestration with bounded structural repair and safe failures."""

import json
import copy
from dataclasses import dataclass, asdict
from pathlib import Path

from .contracts import validate_extraction, validate_generation, validate_request
from .errors import ServiceError
from .evidence import EvidenceError
from .providers import FakeProvider, Provider


@dataclass
class Diagnostics:
    attempts: int = 0
    raw_validation_failures: int = 0
    repairs: int = 0


def run(request: dict, operation: str, provider: Provider | None = None,
        *, max_attempts: int = 2, diagnostics: Diagnostics | None = None) -> tuple[dict, dict]:
    """Offline attempts default to two; this is not an approved live retry policy."""
    if operation not in {"extract", "answer"} or not 1 <= max_attempts <= 3:
        raise ValueError("Invalid local operation or attempt bound.")
    provider = provider or FakeProvider()
    diagnostics = diagnostics if diagnostics is not None else Diagnostics()
    if isinstance(request, dict):
        doc = request.get("document")
        if isinstance(doc, dict) and isinstance(doc.get("text"), str) and len(doc["text"]) > 100_000:
            raise ServiceError(413, "validation_failure", "Canonical text exceeds 100,000 code points.")
        if isinstance(doc, dict) and doc.get("language") is not None and doc.get("language") != "en":
            raise ServiceError(422, "unsupported_language", "Only English input is supported.")
    try:
        document = validate_request(request, operation)
    except EvidenceError as exc:
        raise ServiceError(422, "validation_failure", str(exc)) from exc
    document = copy.deepcopy(document)
    instructions = (Path(__file__).parent / "prompts" / f"{operation}-v1.txt").read_text(encoding="utf-8")
    definition = "ExtractionResult" if operation == "extract" else "AnswerResult"
    instructions += "\nReturn the frozen NoteLens 1.0.0 " + definition + " record."
    for attempt in range(max_attempts):
        diagnostics.attempts += 1
        try:
            raw = provider.generate(operation, copy.deepcopy(request), instructions, repair=attempt > 0)
            result = json.loads(raw)
            if request["document"] != document:
                raise EvidenceError("Canonical request was modified.")
            if operation == "extract":
                validate_extraction(result, document)
            else:
                validate_generation(result, document, answer=True)
            if result["mode"] != provider.mode:
                raise EvidenceError("Provider mode mismatch.")
            if attempt:
                diagnostics.repairs += 1
            return result, asdict(diagnostics)
        except ServiceError:
            raise
        except TimeoutError as exc:
            raise ServiceError(504, "timeout", "The generation request timed out.", True) from exc
        except ConnectionError as exc:
            raise ServiceError(503, "provider_unavailable", "The generation provider is unavailable.", True) from exc
        except (json.JSONDecodeError, EvidenceError, TypeError) as exc:
            diagnostics.raw_validation_failures += 1
            if attempt + 1 == max_attempts:
                raise ServiceError(502, "internal_error", "Generated output failed validation after bounded repair.") from exc
    raise AssertionError("Unreachable attempt loop.")
