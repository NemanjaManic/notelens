"""Exercise safe failures and independent transient mock requests."""

import asyncio
import builtins
from pathlib import Path

import httpx

import notelens_classifier.main as service
from conftest import REQUEST_ID, prepared


def test_unexpected_exception_does_not_disclose_body_or_token(client, body, caplog, monkeypatch):
    marker = "synthetic-private-marker-do-not-log"
    body["document"] = prepared(marker)
    def fail(*args):
        raise RuntimeError(marker + " synthetic-secret-marker")
    monkeypatch.setattr(service, "mock_result", fail)
    response = client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID})
    assert response.status_code == 500
    assert marker not in response.text + caplog.text
    assert "synthetic-secret-marker" not in response.text + caplog.text


def test_mock_processing_performs_no_file_writes(client, body, monkeypatch):
    original = builtins.open
    def checked_open(file, mode="r", *args, **kwargs):
        assert not any(flag in mode for flag in "wax+"), "Unexpected file write"
        return original(file, mode, *args, **kwargs)
    def forbid(*args, **kwargs):
        raise AssertionError("Unexpected file write")
    monkeypatch.setattr(builtins, "open", checked_open)
    monkeypatch.setattr(Path, "write_text", forbid)
    monkeypatch.setattr(Path, "write_bytes", forbid)
    assert client.post("/v1/classify", json=body, headers={"X-Request-ID": REQUEST_ID}).status_code == 200


def test_concurrent_requests_do_not_share_document_identity():
    async def run():
        app = service.create_app(service.Settings(mode="mock"))
        transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 50000))
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
            docs = [prepared("Synthetic independent note " + str(i), "synthetic-" + str(i)) for i in range(4)]
            replies = await asyncio.gather(*[client.post("/v1/classify",
                json={"schema_version": "1.0.0", "document": doc},
                headers={"X-Request-ID": REQUEST_ID}) for doc in docs])
            for doc, reply in zip(docs, replies):
                assert reply.status_code == 200
                assert reply.json()["doc_id"] == doc["doc_id"]
                assert reply.json()["text_sha256"] == doc["text_sha256"]
        assert not vars(app.state).get("_state")
    asyncio.run(run())
