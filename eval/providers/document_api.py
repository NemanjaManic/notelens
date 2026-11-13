"""Promptfoo Python provider for the actual local mock API, not a fake response."""

import json
import os
import uuid
import urllib.error
import urllib.request

from notelens_extraction.contracts import validate_generation
from notelens_extraction.demo import request


def call_api(prompt: str, options: dict, context: dict) -> dict:
    port = int(os.getenv("NOTELENS_SMOKE_PORT", "8003"))
    if not 1 <= port <= 65535:
        return {"error": "Invalid loopback smoke port."}
    payload = request(prompt)
    headers = {"Content-Type": "application/json", "X-Request-ID": str(uuid.uuid4())}
    if os.getenv("NOTELENS_SERVICE_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['NOTELENS_SERVICE_TOKEN']}"
    call = urllib.request.Request(f"http://127.0.0.1:{port}/v1/document-answer",
                                  data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(call, timeout=10) as response:
            result = json.load(response)
        if result.get("mode") != "mock":
            return {"error": "This smoke profile requires explicit mock mode."}
        validate_generation(result, payload["document"], answer=True)
        return {"output": json.dumps(result, ensure_ascii=True)}
    except (OSError, ValueError, urllib.error.HTTPError):
        return {"error": "Local document API failed or returned invalid evidence."}
