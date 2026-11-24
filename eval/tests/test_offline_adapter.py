import json
import runpy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from notelens_eval import cross_service_smoke
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


@pytest.mark.parametrize("mismatched_retrieval", [False, True])
def test_cross_service_smoke_preserves_inputs_and_checks_provenance(monkeypatch, mismatched_retrieval):
    fixture_path = PROVIDER.parents[2] / "contracts/v1/fixtures/payloads.json"
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    literature_answer = fixtures["answer-literature"]
    provenance = literature_answer["retrieval_provenance"]
    retrieval = {**fixtures["retrieval-sufficient"], **{key: provenance[key] for key in
                 ("corpus_version", "index_version", "retriever_version")}}
    if mismatched_retrieval:
        retrieval["index_version"] = "different-fixture-index"

    def fixture_post(port, path, payload, **options):
        if path in ("/v1/retrieve", "/v1/literature-answer"):
            assert port == 8001 and set(payload) == {"schema_version", "question"}
            return retrieval if path == "/v1/retrieve" else literature_answer
        document = payload["document"]
        if path == "/v1/classify":
            assert port == 8002
            return {**fixtures["classification-supported"], "doc_id": document["doc_id"],
                    "text_sha256": document["text_sha256"]}
        assert port == 8003 and options["require_no_store"]
        result, _ = run(payload, "extract" if path == "/v1/extract" else "answer")
        return result

    monkeypatch.setattr(cross_service_smoke, "post_mock", fixture_post)
    ports = {"rag_port": 8001, "classifier_port": 8002, "extraction_port": 8003}
    if mismatched_retrieval:
        with pytest.raises(ValueError, match="provenance differs"):
            cross_service_smoke.check_services(**ports)
    else:
        assert cross_service_smoke.check_services(**ports)["checks"]["/v1/document-answer"] == "partial"
