import copy
import io
import json
import sys
from email.message import Message

import pytest

from notelens_eval import http_suite
from notelens_eval.run import produce


REQUEST_ID = "123e4567-e89b-42d3-a456-426614174000"
UNAVAILABLE = {"schema_version": "1.0.0", "request_id": REQUEST_ID,
               "error": {"code": "provider_unavailable", "message": "Mock unavailable.", "retryable": True}}


@pytest.mark.parametrize(("status", "request_ids", "counter", "body", "error"), [
    (200, [REQUEST_ID], "2", b'{"mode":"mock"}', None),
    (200, [], "0", b'{"mode":"mock"}', "request_id_mismatch"),
    (200, [REQUEST_ID, REQUEST_ID], "0", b'{"mode":"mock"}', "request_id_mismatch"),
    (200, [REQUEST_ID], "0", b"not json", "invalid_response_json"),
    (200, [REQUEST_ID], "0", b"[]", "invalid_response_body"),
    (200, [REQUEST_ID], "not an integer", b'{"mode":"mock"}', "invalid_generation_diagnostics"),
    (200, [REQUEST_ID], "0", b'{"mode":"live"}', "non_mock_response"),
    (302, [REQUEST_ID], "0", b"{}", "unexpected_http_status"),
    (503, [REQUEST_ID], "0", b'{"error":"invalid"}', "invalid_error_envelope"),
    (503, [REQUEST_ID], "2", json.dumps(UNAVAILABLE).encode(), "provider_unavailable"),
])
def test_http_suite_rejects_unusable_exchanges(monkeypatch, status, request_ids, counter, body, error):
    response = io.BytesIO(body)
    response.status = status
    response.headers = Message()
    for value in request_ids:
        response.headers["X-Request-ID"] = value
    response.headers["X-Generation-Attempts"] = counter
    response.getheaders = response.headers.items
    requests = []
    closures = []

    class Connection:
        def __init__(self, host, port, *, timeout):
            assert (host, port, timeout) == ("127.0.0.1", 8003, 5)

        def request(self, method, path, *, body, headers):
            requests.append((method, path, headers["X-Request-ID"]))

        def getresponse(self):
            return response

        def close(self):
            closures.append(True)

    monkeypatch.setattr(http_suite, "HTTPConnection", Connection)
    result, diagnostics = http_suite._call(8003, "/v1/document-answer", {}, REQUEST_ID)

    assert requests == [("POST", "/v1/document-answer", REQUEST_ID)]
    assert closures == [True]
    assert diagnostics["http_status"] == status
    assert diagnostics["request_id_matches"] == (request_ids == [REQUEST_ID])
    assert diagnostics.get("technical_error") == error
    assert result == (None if error else {"mode": "mock"})
    if counter == "2":
        assert diagnostics["attempts"] == 2


@pytest.mark.parametrize("invalid_exchange", [False, True])
def test_suite_exits_nonzero_for_broken_http_200(monkeypatch, tmp_path, invalid_exchange):
    source = http_suite.EVAL_ROOT / "fixtures/extraction-qa-synthetic-v1.json"
    references = json.loads(source.read_bytes())
    references["cases"] = references["cases"][:1]
    reference_file = tmp_path / "references.json"
    reference_file.write_text(json.dumps(references), encoding="utf-8")
    predictions = produce(references)
    case = predictions["cases"][0]
    for record in [case, *case["qa"]]:
        record["diagnostics"].update(http_status=200, request_id_matches=True)
    answer = case["qa"][0]
    if invalid_exchange:
        answer["result"] = None
        answer["diagnostics"].update(request_id_matches=False, technical_error="request_id_mismatch")
    else:
        answer["result"] = {"mode": "mock"}
    monkeypatch.setattr(http_suite, "produce_http", lambda _: copy.deepcopy(predictions))
    output = tmp_path / "results"
    monkeypatch.setattr(sys, "argv", ["http_suite", "--references", str(reference_file), "--output", str(output)])

    assert http_suite.main() == 1
    report = json.loads((output / "results.json").read_bytes())
    assert report["transport"]["http_200"] == 3
    assert report["transport"]["technical_failures"] == int(invalid_exchange)
    assert report["record_validation"]["schema_invalid"] == int(not invalid_exchange)
    markdown = (output / "report.md").read_text(encoding="utf-8")
    assert "HTTP 200 responses: 3/3." in markdown
    assert f"Failed exchanges: {int(invalid_exchange)}." in markdown
