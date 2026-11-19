"""Real local HTTP health authentication; synthetic credentials only."""

import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import UUID

from notelens_contracts.v1 import validate_exchange, validate_record

TOKEN = "synthetic-health-transport-token"
INCOMING = "11111111-1111-4111-8111-111111111111"


def test_health_auth_and_duplicate_headers_over_real_http():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = os.environ.copy()
    environment.update(NOTELENS_CLASSIFIER_MODE="mock", NOTELENS_CLASSIFIER_MOCK_SCENARIO="supported",
                       NOTELENS_CLASSIFIER_MOCK_READINESS="ready", NOTELENS_CLASSIFIER_SERVICE_TOKEN=TOKEN,
                       PYTHONDONTWRITEBYTECODE="1")
    environment.pop("NOTELENS_CLASSIFIER_MOCK_FAILURE", None)
    process = subprocess.Popen([sys.executable, "-m", "notelens_classifier", "--port", str(port)],
                               cwd=Path(__file__).resolve().parents[1], env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        deadline = time.monotonic() + 20
        while True:
            assert process.poll() is None
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                assert time.monotonic() < deadline, "Local health service did not start"
                time.sleep(0.05)

        def send(route, headers):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                conn.putrequest("GET", route)
                for key, value in headers:
                    conn.putheader(key, value)
                conn.endheaders()
                response = conn.getresponse()
                raw_headers = response.getheaders()
                return response.status, raw_headers, json.loads(response.read())
            finally:
                conn.close()

        for route in ("/health/live", "/health/ready"):
            status, headers, payload = send(route, [("X-Request-ID", "bad"), ("Authorization", "Bearer " + TOKEN)])
            assert status == 200
            validate_record("LivenessResult" if route.endswith("live") else "HealthResult", payload)
            assert not [v for k, v in headers if k.lower() == "x-request-id"]
            ids = set()
            for auth in ([], [("Authorization", "Bearer wrong")],
                         [("Authorization", "Bearer " + TOKEN), ("Authorization", "Bearer wrong")],
                         [("Authorization", "Bearer wrong"), ("Authorization", "Bearer " + TOKEN)]):
                request_headers = [("X-Request-ID", INCOMING), ("X-Request-ID", "bad")] + auth
                status, headers, payload = send(route, request_headers)
                assert status == 401
                result = validate_record("ErrorEnvelope", payload)
                identity = result["request_id"]
                assert str(UUID(identity)) == identity and identity != INCOMING and identity not in ids
                ids.add(identity)
                assert result["error"]["code"] == "unauthorized" and result["error"]["retryable"] is False
                assert [v for k, v in headers if k.lower() == "x-request-id"] == [identity]
                assert [v for k, v in headers if k.lower() == "www-authenticate"] == ["Bearer"]
                assert TOKEN not in json.dumps(payload)
                assert validate_exchange({"path": route, "request_headers": request_headers,
                                          "response_headers": headers, "status": status, "body": payload,
                                          "disposition": "failed_call"}) == []
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=10)
        assert TOKEN not in stdout + stderr and "Traceback" not in stderr
    assert process.poll() is not None
    with socket.socket() as probe:
        probe.settimeout(1)
        assert probe.connect_ex(("127.0.0.1", port)) != 0
