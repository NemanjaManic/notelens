"""Promptfoo Python provider for the actual local mock API, not a fake response."""

import json
import os
import uuid
from http.client import HTTPConnection, HTTPException

from notelens_contracts.v1 import validate_exchange
from notelens_extraction.contracts import validate_generation
from notelens_extraction.demo import request


def call_api(prompt: str, options: dict, context: dict) -> dict:
    try:
        port = int(os.getenv("NOTELENS_SMOKE_PORT", "8003"))
    except ValueError:
        return {"error": "Invalid loopback smoke port."}
    if not 1 <= port <= 65535:
        return {"error": "Invalid loopback smoke port."}
    payload = request(prompt)
    headers = {"Content-Type": "application/json", "X-Request-ID": str(uuid.uuid4())}
    if os.getenv("NOTELENS_SERVICE_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['NOTELENS_SERVICE_TOKEN']}"
    path = "/v1/document-answer"
    connection = HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request("POST", path, body=json.dumps(payload).encode("utf-8"), headers=headers)
        with connection.getresponse() as response:
            if response.status != 200:
                return {"error": "Local document API did not return HTTP 200."}
            response_headers = response.getheaders()
            cache_control = response.headers.get_all("Cache-Control", [])
            if not any(directive.strip().lower() == "no-store"
                       for value in cache_control for directive in value.split(",")):
                return {"error": "Local document API response is missing no-store."}
            result = json.load(response)
        if not isinstance(result, dict):
            return {"error": "Local document API response must be a JSON object."}
        if validate_exchange({"path": path, "request_headers": list(headers.items()),
                              "response_headers": response_headers, "status": 200,
                              "body": result, "disposition": "accepted_result"}):
            return {"error": "Local document API response does not match the request ID."}
        if result.get("mode") != "mock":
            return {"error": "This smoke profile requires explicit mock mode."}
        validate_generation(result, payload["document"], answer=True)
        return {"output": json.dumps(result, ensure_ascii=True)}
    except (OSError, ValueError, HTTPException):
        return {"error": "Local document API failed or returned invalid evidence."}
    finally:
        connection.close()
