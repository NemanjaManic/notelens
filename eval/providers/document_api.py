"""Promptfoo Python provider for the actual local mock API, not a fake response."""

import json
import os
from notelens_eval.mock_http import post_mock
from notelens_extraction.contracts import validate_generation
from notelens_extraction.demo import request


def call_api(prompt: str, options: dict, context: dict) -> dict:
    try:
        port = int(os.getenv("NOTELENS_SMOKE_PORT", "8003"))
    except ValueError:
        return {"error": "Invalid loopback smoke port."}
    payload = request(prompt)
    try:
        result = post_mock(port, "/v1/document-answer", payload,
                           token=os.getenv("NOTELENS_SERVICE_TOKEN"), require_no_store=True)
    except ValueError as exc:
        return {"error": str(exc)}
    try:
        validate_generation(result, payload["document"], answer=True)
        return {"output": json.dumps(result, ensure_ascii=True)}
    except ValueError:
        return {"error": "Local document API returned invalid evidence."}
