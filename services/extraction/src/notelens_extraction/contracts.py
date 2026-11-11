"""Validate against the repository's single B-owned JSON Schema, currently draft."""

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .evidence import EvidenceError, validate_span, validate_text

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "contracts/v1/schema.json"


@lru_cache
def schema() -> dict:
    result = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(result)
    return result


def validate_schema(value: dict, name: str) -> None:
    # Reference the shared definitions rather than copy or maintain local models.
    definition = {"$ref": f"#/$defs/{name}", "$defs": schema()["$defs"]}
    if next(Draft202012Validator(definition, format_checker=FormatChecker()).iter_errors(value), None):
        raise EvidenceError(f"Record does not satisfy shared {name}.")


def validate_request(request: dict, operation: str) -> dict:
    validate_schema(request, "ExtractionRequest" if operation == "extract" else "DocumentQuestionRequest")
    document = request["document"]
    validate_text(document["text"], document["text_sha256"])
    if operation == "answer" and not request["question"].strip():
        raise EvidenceError("Question must be non-empty.")
    return document


def validate_generation(result: dict, document: dict, *, answer: bool) -> None:
    validate_schema(result, "AnswerResult" if answer else "Summary")
    sources = result["sources"]
    source_ids = [source["source_id"] for source in sources]
    claim_ids = [claim["claim_id"] for claim in result["claims"]]
    if len(source_ids) != len(set(source_ids)) or len(claim_ids) != len(set(claim_ids)):
        raise EvidenceError("Duplicate claim or source identifier.")
    for source in sources:
        if source["kind"] != "document" or source["doc_id"] != document["doc_id"] or source["text_sha256"] != document["text_sha256"]:
            raise EvidenceError("Source does not belong to the selected document.")
        validate_span(document["text"], source["evidence"])
    for claim in result["claims"]:
        if claim["scope"] != "document_fact" or not set(claim["source_ids"]) <= set(source_ids):
            raise EvidenceError("Claim has dangling or non-document support.")
    if answer and result["route"] not in {"document", "none"}:
        raise EvidenceError("D may only return document or none routes.")
    if result["evidence_state"] == "insufficient" and (result["claims"] or result["sources"]):
        raise EvidenceError("Insufficient result must contain no factual claims or sources.")
    if not result["claims"] and result["text"] != "The document does not provide enough supported information to answer this request.":
        raise EvidenceError("A source-free response must use the controlled English limitation.")
    if result["evidence_state"] == "partial" and not result["warnings"]:
        raise EvidenceError("Partial support requires an explicit limitation.")
    if result["evidence_state"] == "partial" and not result["claims"]:
        raise EvidenceError("Partial support requires at least one supported claim.")
    # Provisional conservative support policy: only literal source sentences are
    # accepted as factual generated claims. No semantic-entailment score is implied.
    by_id = {source["source_id"]: source for source in sources}
    for claim in result["claims"]:
        if claim["text"] not in [by_id[s]["evidence"]["quote"] for s in claim["source_ids"]]:
            raise EvidenceError("Provisional generation requires literal supported claims.")
    if result["claims"] and result["text"] != " ".join(c["text"] for c in result["claims"]):
        raise EvidenceError("Displayed text differs from its supported claims.")


def validate_extraction(result: dict, document: dict) -> None:
    validate_schema(result, "ExtractionResult")
    if (result["doc_id"], result["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
        raise EvidenceError("Extraction document identity mismatch.")
    ids = [item["entity_id"] for item in result["items"]]
    if len(ids) != len(set(ids)):
        raise EvidenceError("Duplicate entity identifier.")
    seen = set()
    for item in result["items"]:
        for evidence in item["evidence"]:
            validate_span(document["text"], evidence)
            if item["name"].casefold() not in evidence["quote"].casefold():
                raise EvidenceError("Entity name is absent from its evidence.")
            # These are narrow offline catalog guards, not a general entailment
            # classifier. Unknown passages still require independent support review.
            from .providers import CATALOG
            known = [row for row in CATALOG if row[0] == evidence["quote"] and row[2].casefold() == item["name"].casefold()]
            for _, kind, _, assertion, time, subject in known:
                if (item["type"], item["assertion"], item["temporality"], item["subject"]) != (kind, assertion, time, subject):
                    raise EvidenceError("Item contradicts the known offline catalog context.")
        signature = (item["type"], item["name"].casefold(), item["assertion"], item["temporality"], item["subject"],
                     tuple(sorted((s["start"], s["end"]) for s in item["evidence"])))
        if signature in seen:
            raise EvidenceError("Duplicate entity occurrence.")
        seen.add(signature)
        if "icd" in item:
            validate_span(document["text"], item["icd"]["evidence"])
            if item["icd"]["code"] != item["icd"]["evidence"]["quote"]:
                raise EvidenceError("ICD code differs from literal source evidence.")
            if not any(item["icd"]["code"] in span["quote"] for span in item["evidence"]):
                raise EvidenceError("ICD code is absent from the item's supporting context.")
    validate_generation(result["summary"], document, answer=False)
