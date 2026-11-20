"""Direct loopback HTTP transport for the key-free evaluator."""

import json
import uuid
from http.client import HTTPConnection, HTTPException

from notelens_contracts.v1 import validate_exchange


def post_loopback(port: int, path: str, payload: dict, *, token: str | None = None,
                  require_no_store: bool = False) -> dict:
    """Admit correlated HTTP 200 records from the selected local port."""
    if not 1 <= port <= 65535:
        raise ValueError("Invalid loopback smoke port.")
    headers = {"Content-Type": "application/json", "X-Request-ID": str(uuid.uuid4())}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    connection = HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request("POST", path, body=json.dumps(payload).encode("utf-8"), headers=headers)
        with connection.getresponse() as response:
            if response.status != 200:
                raise ValueError(f"Local API returned HTTP {response.status}; expected 200.")
            response_headers = response.getheaders()
            cache_control = response.headers.get_all("Cache-Control", [])
            if require_no_store and not any(directive.strip().lower() == "no-store"
                                            for value in cache_control for directive in value.split(",")):
                raise ValueError("Local API response is missing no-store.")
            result = json.load(response)
    except (OSError, HTTPException, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Local API failed or returned invalid JSON.") from exc
    finally:
        connection.close()

    if not isinstance(result, dict):
        raise ValueError("Local API response must be a JSON object.")
    if validate_exchange({"path": path, "request_headers": list(headers.items()),
                          "response_headers": response_headers, "status": 200,
                          "body": result, "disposition": "accepted_result"}):
        raise ValueError("Local API response does not match the request ID.")
    return result


def post_mock(port: int, path: str, payload: dict, *, token: str | None = None,
              require_no_store: bool = False) -> dict:
    result = post_loopback(port, path, payload, token=token, require_no_store=require_no_store)
    if result.get("mode") != "mock":
        raise ValueError("This smoke profile requires explicit mock mode.")
    return result
