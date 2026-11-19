import json
import runpy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from notelens_extraction.service import run


PROVIDER = Path(__file__).resolve().parents[1] / "providers/document_api.py"
CALL_API = runpy.run_path(str(PROVIDER))["call_api"]
QUESTION = "What does the document say about chest pain?"


@pytest.mark.parametrize("scenario", ["valid", "wrong-id", "missing-id", "duplicate-id",
                                     "missing-no-store", "non-object", "redirect"])
def test_offline_provider_checks_loopback_http_exchange(monkeypatch, scenario):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            requests.append(self.path)
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            result, _ = run(payload, "answer")
            body = json.dumps([] if scenario == "non-object" else result).encode("utf-8")
            self.send_response(302 if scenario == "redirect" else 200)
            if scenario == "redirect":
                self.send_header("Location", "/redirected")
            request_id = self.headers["X-Request-ID"]
            if scenario != "missing-id":
                self.send_header("X-Request-ID", "00000000-0000-4000-8000-000000000001"
                                 if scenario == "wrong-id" else request_id)
            if scenario == "duplicate-id":
                self.send_header("X-Request-ID", request_id)
            if scenario != "missing-no-store":
                self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            requests.append(self.path)
            self.send_error(404)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        monkeypatch.setenv("NOTELENS_SMOKE_PORT", str(server.server_port))
        monkeypatch.delenv("NOTELENS_SERVICE_TOKEN", raising=False)
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        try:
            result = CALL_API(QUESTION, {}, {})
        finally:
            server.shutdown()
            thread.join()

    assert requests == ["/v1/document-answer"]
    if scenario == "valid":
        assert json.loads(result["output"])["evidence_state"] == "sufficient"
    else:
        assert set(result) == {"error"}


def test_offline_provider_reports_invalid_port(monkeypatch):
    monkeypatch.setenv("NOTELENS_SMOKE_PORT", "not-a-port")
    assert CALL_API(QUESTION, {}, {}) == {"error": "Invalid loopback smoke port."}
