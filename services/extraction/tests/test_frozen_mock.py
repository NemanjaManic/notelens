"""Frozen D mock and transport regressions."""

import copy
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from notelens_contracts.v1 import validate_record

from notelens_extraction.demo import request
from notelens_extraction.evidence import digest
from notelens_extraction.errors import ServiceError
from notelens_extraction.main import create_app
from notelens_extraction.providers import FakeProvider
from notelens_extraction.service import run


def with_text(text):
    payload = request()
    payload["document"]["text"] = text
    payload["document"]["text_sha256"] = digest(text)
    return payload


def test_mentions_procedure_status_and_unknown_assertion():
    payload = with_text("🩺 No chest pain. No chest pain. Colonoscopy is planned for next week. "
                        "Condition status is unclear.")
    result, _ = run(payload, "extract")
    validate_record("ExtractionResult", result, document=payload["document"])
    denials = [item for item in result["items"] if item["name"] == "chest pain"]
    assert len(denials) == 2
    assert denials[0]["mention"]["start"] != denials[1]["mention"]["start"]
    assert all(item["mention"]["quote"] == "chest pain" for item in denials)
    assert all(item["evidence"][0]["quote"] == "No chest pain." for item in denials)
    procedure = next(item for item in result["items"] if item["type"] == "procedure")
    assert procedure["procedure_status"] == "planned"
    assert procedure["assertion"] == "confirmed"
    assert next(item for item in result["items"] if item["name"] == "Condition")["assertion"] == "unknown"


@pytest.mark.parametrize("state,summary_failed", [
    ("completed", True), ("partial", False), ("failed", False),
])
def test_independent_sections_preserve_success(state, summary_failed):
    payload = request()
    result, _ = run(payload, "extract", FakeProvider(extraction_state=state,
                                                      summary_failed=summary_failed))
    validate_record("ExtractionResult", result, document=payload["document"])
    assert result["extraction_status"] == state
    assert result["summary"]["status"] == ("failed" if summary_failed else "completed")
    assert bool(result["items"]) == (state != "failed")
    assert bool(result["summary"]["result"]) == (not summary_failed)


def test_both_sections_failed_is_operational_error():
    with pytest.raises(ServiceError) as failure:
        run(request(), "extract", FakeProvider(extraction_state="failed", summary_failed=True))
    assert failure.value.status == 503


def test_partial_document_answer_keeps_claims_and_sources():
    payload = request("What does the document say about chest pain and the patient's age?")
    result, _ = run(payload, "answer")
    validate_record("AnswerResult", result, document=payload["document"])
    assert result["evidence_state"] == "partial" and result["claims"] and result["sources"]
    assert result["attempted_routes"] == ["document"]
    assert result["retrieval_provenance"] is None


def test_health_auth_uses_fresh_diagnostic_id_and_ignores_incoming_id():
    client = TestClient(create_app(token="local-test-token"))
    incoming = str(uuid.uuid4())
    first = client.get("/health/ready", headers={"X-Request-ID": incoming})
    second = client.get("/health/ready", headers={"X-Request-ID": incoming})
    for response in (first, second):
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert response.headers["X-Request-ID"] == response.json()["request_id"]
        assert response.json()["error"]["code"] == "unauthorized"
        assert response.json()["error"]["retryable"] is False
        assert response.headers["X-Request-ID"] != incoming
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_post_id_admission_and_strict_json():
    client = TestClient(create_app())
    payload = request()
    missing = client.post("/v1/extract", json=payload)
    assert missing.status_code == 400
    assert missing.headers["X-Request-ID"] == missing.json()["request_id"]
    request_id = str(uuid.uuid4())
    headers = {"X-Request-ID": request_id}
    response = client.post("/v1/extract", json=payload, headers=headers)
    assert response.status_code == 200 and response.headers["X-Request-ID"] == request_id
    validate_record("ExtractionResult", response.json(), document=payload["document"])
    for invalid in ('{"schema_version": 1, "schema_version": 2}', '{"value": NaN}'):
        failure = client.post("/v1/extract", content=invalid, headers=headers)
        assert failure.status_code == 400
        assert failure.headers["X-Request-ID"] == request_id


def test_health_readiness_is_distinct_from_business_errors():
    from notelens_extraction.providers import UnconfiguredLiveProvider

    client = TestClient(create_app(UnconfiguredLiveProvider()))
    response = client.get("/health/ready")
    assert response.status_code == 503
    validate_record("HealthResult", response.json())
    assert response.json()["status"] == "not_ready"


def test_duplicate_request_header_is_rejected_with_diagnostic_id():
    from httpx import ASGITransport, AsyncClient
    import asyncio

    async def call():
        transport = ASGITransport(app=create_app())
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/v1/extract", json=request(), headers=[
                ("X-Request-ID", str(uuid.uuid4())),
                ("X-Request-ID", str(uuid.uuid4())),
            ])

    response = asyncio.run(call())
    assert response.status_code == 400
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_document_identity_is_from_incoming_request():
    payload = with_text("No chest pain.")
    payload["document"]["doc_id"] = "another-synthetic-document"
    original = copy.deepcopy(payload)
    result, _ = run(payload, "extract")
    assert payload == original
    assert result["doc_id"] == original["document"]["doc_id"]
    assert result["summary"]["result"]["sources"][0]["doc_id"] == original["document"]["doc_id"]
