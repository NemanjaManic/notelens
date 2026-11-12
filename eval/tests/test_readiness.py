import json

import pytest

from notelens_eval.readiness import FIXTURE_ANSWER, FIXTURE_EXTRACT, inspect_contracts, probe_http, run_readiness
from notelens_extraction.contracts import validate_schema
from notelens_extraction.evidence import EvidenceError


def test_d_openapi_and_shared_draft_schema_are_structurally_bound():
    result = inspect_contracts()
    assert result["status"] == "pass", result["errors"]
    assert set(result["checked_d_operations"]) == {"extraction_extract", "extraction_document_answer"}
    assert result["openapi_refs"] == result["resolved_refs"]
    assert result["contract_status"].startswith("draft")


@pytest.mark.parametrize("fixture, schema_name", [(FIXTURE_EXTRACT, "ExtractionRequest"),
                                                      (FIXTURE_ANSWER, "DocumentQuestionRequest")])
def test_versioned_demo_requests_match_the_draft_contract(fixture, schema_name):
    request = json.loads(fixture.read_text(encoding="utf-8"))
    validate_schema(request, schema_name)


def test_http_readiness_exercises_demos_errors_and_safe_headers():
    report = probe_http()
    assert report["status"] == "pass"
    names = {item["check"] for item in report["checks"]}
    assert len(names) == len(report["checks"])
    assert {"oversized_text_rejected", "unsupported_language_rejected", "malformed_json_rejected",
            "invalid_token_rejected", "stale_digest_pair_rejected", "opaque_document_id_propagated"} <= names
    assert all(item["status"] == "pass" for item in report["checks"])
    assert report["request_text_included"] is False


def test_combined_readiness_keeps_cross_service_gap_explicit():
    report = run_readiness()
    assert report["contract_inspection"]["status"] == report["transport"]["status"] == "pass"
    assert report["cross_service"]["status"] == "not_run"
    assert report["human_or_clinical_review"] == "not performed"


def test_demo_fixture_tampering_is_caught_by_request_hash_validation(monkeypatch):
    from notelens_eval import readiness
    original = readiness.FIXTURE_EXTRACT
    request = json.loads(original.read_text(encoding="utf-8"))
    request["document"]["text"] += " tampered"
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as folder:
        fixture = Path(folder) / "tampered.json"
        fixture.write_text(json.dumps(request), encoding="utf-8")
        monkeypatch.setattr(readiness, "FIXTURE_EXTRACT", fixture)
        with pytest.raises(EvidenceError, match="digest"):
            readiness.probe_http()
