"""D support checks around the frozen generated contract."""

import json
from functools import lru_cache
from pathlib import Path

from notelens_contracts.v1 import ContractValidationError, validate_record
from .evidence import EvidenceError, validate_span, validate_text

SCHEMA_PATH = Path(__file__).resolve().parents[4] / "contracts/v1/schema.json"


@lru_cache
def schema() -> dict:
    """Read the B-owned schema for diagnostics; runtime validation uses the package."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_schema(value: dict, name: str, *, document: dict | None = None) -> None:
    try:
        validate_record(name, value, document=document)
    except ContractValidationError as exc:
        raise EvidenceError(f"Record does not satisfy frozen {name}: " +
                            ", ".join(issue.rule for issue in exc.issues)) from exc


def validate_request(request: dict, operation: str) -> dict:
    validate_schema(request, "ExtractionRequest" if operation == "extract" else "DocumentQuestionRequest")
    document = request["document"]
    validate_text(document["text"], document["text_sha256"])
    if operation == "answer" and not request["question"].strip():
        raise EvidenceError("Question must be non-empty.")
    return document


def validate_generation(result: dict, document: dict, *, answer: bool) -> None:
    validate_schema(result, "AnswerResult" if answer else "Summary", document=document)
    if answer and result["route"] not in {"document", "none"}:
        raise EvidenceError("D may only return document or none routes.")
    for source in result["sources"]:
        if source["kind"] != "document" or (source["doc_id"], source["text_sha256"]) != (
                document["doc_id"], document["text_sha256"]):
            raise EvidenceError("Source does not belong to the selected document.")
        validate_span(document["text"], source["evidence"])
    by_id = {source["source_id"]: source for source in result["sources"]}
    for claim in result["claims"]:
        if claim["scope"] != "document_fact" or not any(
                claim["text"] == by_id[source_id]["evidence"]["quote"]
                for source_id in claim["source_ids"]):
            raise EvidenceError("Mock claim is not a literal document passage.")


def validate_extraction(result: dict, document: dict) -> None:
    validate_schema(result, "ExtractionResult", document=document)
    if (result["doc_id"], result["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
        raise EvidenceError("Extraction document identity mismatch.")
    seen = set()
    for item in result["items"]:
        validate_span(document["text"], item["mention"])
        for span in item["evidence"]:
            validate_span(document["text"], span)
            from .providers import CATALOG
            for sentence, kind, name, assertion, time, subject, status in CATALOG:
                if span["quote"] == sentence and item["name"].casefold() == name.casefold():
                    if (item["type"], item["assertion"], item["temporality"], item["subject"],
                            item["procedure_status"]) != (kind, assertion, time, subject, status):
                        raise EvidenceError("Item contradicts the known mock catalog context.")
        key = (item["type"], item["mention"]["start"], item["mention"]["end"])
        if key in seen:
            raise EvidenceError("Duplicate entity occurrence.")
        seen.add(key)
        if "icd" in item:
            validate_span(document["text"], item["icd"]["evidence"])
            if item["icd"]["code"] != item["icd"]["evidence"]["quote"]:
                raise EvidenceError("ICD code differs from source evidence.")
            if not any(item["icd"]["code"] in span["quote"] for span in item["evidence"]):
                raise EvidenceError("ICD code is absent from the item's supporting context.")
    summary = result["summary"]
    if summary["status"] == "completed":
        validate_generation(summary["result"], document, answer=False)
