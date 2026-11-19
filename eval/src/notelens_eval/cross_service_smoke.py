"""Verify the D evaluator can consume all three key-free service interfaces."""

import argparse
import json
import sys

from notelens_contracts.v1 import validate_record
from notelens_extraction.contracts import validate_extraction, validate_generation
from notelens_extraction.demo import request

from .mock_http import post_mock


def check_services(*, rag_port: int, classifier_port: int, extraction_port: int) -> dict:
    """Run the supported synthetic profiles without forwarding text to RAG."""
    extract_request = request()
    document = extract_request["document"]
    question = "What does the document say about chest pain and the patient's age?"
    classification = post_mock(classifier_port, "/v1/classify", extract_request,
                               require_no_store=True)
    validate_record("ClassificationResult", classification, document=document)
    if (classification["doc_id"], classification["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
        raise ValueError("Classifier response substituted the prepared document identity.")
    if classification["status"] != "supported":
        raise ValueError("The classifier smoke requires the supported mock profile.")

    extraction = post_mock(extraction_port, "/v1/extract", extract_request, require_no_store=True)
    validate_extraction(extraction, document)
    if extraction["extraction_status"] != "completed" or extraction["summary"]["status"] != "completed":
        raise ValueError("The extraction smoke requires completed extraction and summary.")
    answer = post_mock(extraction_port, "/v1/document-answer", {**extract_request, "question": question},
                       require_no_store=True)
    validate_generation(answer, document, answer=True)
    if answer["route"] != "document" or answer["evidence_state"] != "partial":
        raise ValueError("The document smoke requires the supported partial answer.")

    literature_request = {"schema_version": "1.0.0", "question": "What is the synthetic demo topic?"}
    retrieval = post_mock(rag_port, "/v1/retrieve", literature_request)
    validate_record("RetrievalResult", retrieval)
    literature_answer = post_mock(rag_port, "/v1/literature-answer", literature_request)
    validate_record("AnswerResult", literature_answer)
    if (retrieval["state"] != "sufficient" or literature_answer["route"] != "literature"
            or literature_answer["evidence_state"] != "sufficient"
            or not literature_answer["sources"]
            or any(source["kind"] != "literature" for source in literature_answer["sources"])):
        raise ValueError("The RAG smoke requires sufficient literature-only evidence.")
    provenance = literature_answer["retrieval_provenance"]
    if provenance is None or any(provenance[key] != retrieval[key]
                                 for key in ("corpus_version", "index_version", "retriever_version")):
        raise ValueError("Literature answer provenance differs from the retrieval profile.")

    return {"mode": "mock", "input": "synthetic", "checks": {
        "/v1/classify": classification["status"],
        "/v1/extract": extraction["extraction_status"],
        "/v1/document-answer": answer["evidence_state"],
        "/v1/retrieve": retrieval["state"],
        "/v1/literature-answer": literature_answer["evidence_state"],
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rag-port", type=int, default=8001)
    parser.add_argument("--classifier-port", type=int, default=8002)
    parser.add_argument("--extraction-port", type=int, default=8003)
    try:
        print(json.dumps(check_services(**vars(parser.parse_args())), sort_keys=True))
    except ValueError as exc:
        print(f"Mock smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
