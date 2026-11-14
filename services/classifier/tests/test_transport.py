"""Real loopback HTTP smoke; no health checkpoint, model, or external provider."""

import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

from notelens_contracts.v1 import validate_record

from conftest import REQUEST_ID, prepared


def test_real_uvicorn_start_requests_and_shutdown():
    # The OS-selected port and deadlines below are test-harness controls only.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    environment = os.environ.copy()
    environment.update(NOTELENS_CLASSIFIER_MODE="mock",
                       NOTELENS_CLASSIFIER_MOCK_SCENARIO="supported",
                       PYTHONDONTWRITEBYTECODE="1")
    environment.pop("NOTELENS_CLASSIFIER_SERVICE_TOKEN", None)
    process = subprocess.Popen(
        [sys.executable, "-m", "notelens_classifier", "--port", str(port)],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        deadline = time.monotonic() + 20
        while True:
            assert process.poll() is None, "Local server exited before startup"
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                assert time.monotonic() < deadline, "Local server did not start"
                time.sleep(0.05)

        def post(raw, request_id=REQUEST_ID):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            try:
                connection.request("POST", "/v1/classify", body=raw,
                    headers={"Content-Type": "application/json", "X-Request-ID": request_id})
                response = connection.getresponse()
                return response.status, dict(response.getheaders()), json.loads(response.read())
            finally:
                connection.close()

        for index in range(2):
            document = prepared("Synthetic transport marker 🩺 " + str(index), "transport-" + str(index))
            status, headers, result = post(json.dumps({"schema_version": "1.0.0", "document": document}).encode())
            assert status == 200 and headers["x-request-id"] == REQUEST_ID
            validate_record("ClassificationResult", result, document=document)
            assert result["doc_id"] == document["doc_id"]
            assert result["mode"] == "mock"
        status, headers, result = post(b"{", "invalid")
        assert status == 400 and headers["x-request-id"] != REQUEST_ID
        validate_record("ErrorEnvelope", result)
        assert result["request_id"] == headers["x-request-id"]
        status, headers, result = post(b"{")
        assert status == 400 and headers["x-request-id"] == REQUEST_ID
        validate_record("ErrorEnvelope", result)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            output, errors = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            output, errors = process.communicate(timeout=10)
        assert "Synthetic transport marker" not in output + errors
        assert "Traceback" not in errors
    assert process.poll() is not None
