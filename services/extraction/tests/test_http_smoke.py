"""Exercise an actual loopback server process and CLI, then clean up that process."""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

from notelens_extraction.contracts import validate_schema
from notelens_extraction.demo import request


def test_actual_cli_and_http_process():
    demo = subprocess.run([sys.executable, "-m", "notelens_extraction.cli", "demo"], capture_output=True, text=True, check=True)
    validate_schema(json.loads(demo.stdout), "ExtractionResult", document=request()["document"])
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NOTELENS_MODE": "mock"}
    env.pop("NOTELENS_SERVICE_TOKEN", None)
    process = subprocess.Popen([sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(base + "/health/ready", timeout=0.3) as response:
                    assert json.load(response)["mode"] == "mock"
                break
            except (OSError, urllib.error.URLError):
                if process.poll() is not None:
                    raise AssertionError("Local service process exited before readiness.")
                time.sleep(0.1)
        else:
            raise AssertionError("Local service process did not become ready.")
        payload = request("What does the document say about chest pain?")
        request_id = str(uuid.uuid4())
        call = urllib.request.Request(base + "/v1/document-answer", data=json.dumps(payload).encode(),
                                      headers={"Content-Type": "application/json", "X-Request-ID": request_id})
        with urllib.request.urlopen(call, timeout=3) as response:
            answer = json.load(response)
            assert answer["evidence_state"] == "sufficient"
            assert response.headers["X-Request-ID"] == request_id
            validate_schema(answer, "AnswerResult", document=payload["document"])
    finally:
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
        assert "The patient denies" not in stdout + stderr
