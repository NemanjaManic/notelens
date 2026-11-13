"""Deterministic document mock. No real generation is activated."""

import json
from typing import Protocol

from .errors import ServiceError

PROMPT_VERSION = "d-mock-prompt-v1"
MOCK_VERSION = "d-mock-v1"
NO_SUMMARY = "The available document evidence does not support a summary."
NO_ANSWER = "The available sources do not support an answer."

# Exact sentences are an intentionally narrow synthetic/public mock catalog.
CATALOG = (
    ("The patient denies chest pain.", "symptom", "chest pain", "negated", "unknown", "patient", None),
    ("No chest pain.", "symptom", "chest pain", "negated", "unknown", "unknown", None),
    ("Pneumonia is suspected.", "diagnosis", "Pneumonia", "suspected", "unknown", "unknown", None),
    ("The patient's mother has diabetes.", "diagnosis", "diabetes", "confirmed", "unknown", "family", None),
    ("The patient had an appendectomy in 2018.", "procedure", "appendectomy", "confirmed", "historical", "patient", "performed"),
    ("The patient currently has asthma.", "diagnosis", "asthma", "confirmed", "current", "patient", None),
    ("Colonoscopy is planned for next week.", "procedure", "Colonoscopy", "confirmed", "unknown", "patient", "planned"),
    ("Condition status is unclear.", "diagnosis", "Condition", "unknown", "unknown", "unknown", None),
)


class Provider(Protocol):
    mode: str

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str: ...


def provenance(operation: str, component_id: str) -> dict:
    return {"component_id": component_id, "service": "extraction", "operation": operation,
            "mode": "mock", "output_version": MOCK_VERSION, "prompt_version": PROMPT_VERSION,
            "provider": "literal-fixture", "model": "deterministic-catalog",
            "configuration_version": "d-mock-config-v1", "corpus_version": None,
            "index_version": None, "retriever_version": None}


def passages(document: dict, selected: list[dict], *, operation: str, partial: bool = False) -> dict:
    component = "d-answer" if operation == "document-answer" else "d-summary"
    unique = {(span["start"], span["end"]): span for span in selected}
    sources, claims = [], []
    for index, span in enumerate(sorted(unique.values(), key=lambda value: value["start"])):
        source_id = f"document-source-{index}"
        sources.append({"source_id": source_id, "kind": "document", "doc_id": document["doc_id"],
                        "text_sha256": document["text_sha256"], "evidence": span, "component_id": component})
        claims.append({"claim_id": f"claim-{index}", "text": span["quote"],
                       "scope": "document_fact", "source_ids": [source_id], "component_id": component})
    result = {"language": "en", "text": "\n\n".join(c["text"] for c in claims) if claims else
              (NO_ANSWER if operation == "document-answer" else NO_SUMMARY),
              "claims": claims, "sources": sources,
              "evidence_state": ("partial" if partial else "sufficient") if claims else "insufficient",
              "warnings": ["Deterministic mock catalog; output is limited and not exhaustive."] +
                          (["The document does not provide the requested age."] if partial else [])}
    if operation == "document-answer":
        result.update(schema_version="1.0.0", mode="mock", route="document" if claims else "none",
                      answer_version=MOCK_VERSION, prompt_version=PROMPT_VERSION if claims else None,
                      components=[provenance(operation, component)] if claims else [],
                      attempted_routes=["document"], clarification=None, retrieval_provenance=None)
    else:
        result["provenance"] = provenance(operation, component) if claims else None
    return result


class FakeProvider:
    mode = "mock"

    def __init__(self, *, extraction_state: str = "completed", summary_failed: bool = False):
        if extraction_state not in {"completed", "partial", "failed"}:
            raise ValueError("Unknown mock extraction state.")
        self.extraction_state = extraction_state
        self.summary_failed = summary_failed

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        document = request["document"]
        text = document["text"]
        items = []
        for sentence, kind, name, assertion, time, subject, procedure_status in CATALOG:
            start = 0
            while (found := text.find(sentence, start)) >= 0:
                mention_start = text.find(name, found, found + len(sentence))
                if mention_start < 0:
                    mention_start = text.lower().find(name.lower(), found, found + len(sentence))
                evidence = {"start": found, "end": found + len(sentence), "quote": sentence}
                mention = {"start": mention_start, "end": mention_start + len(name),
                           "quote": text[mention_start:mention_start + len(name)]}
                items.append({"entity_id": f"entity-{mention_start}-{kind}", "type": kind, "name": name,
                              "assertion": assertion, "temporality": time, "subject": subject,
                              "evidence": [evidence], "mention": mention,
                              "component_id": "d-extract", "procedure_status": procedure_status})
                start = found + len(sentence)
        items.sort(key=lambda item: item["mention"]["start"])
        if operation == "extract":
            if self.extraction_state == "failed" and self.summary_failed:
                raise ServiceError(503, "provider_unavailable", "Both analysis sections are unavailable.", True)
            summary = passages(document, [span for item in items for span in item["evidence"]], operation="summarize")
            error = {"code": "provider_unavailable", "message": "The mock section is unavailable.",
                     "retryable": True}
            summary_outcome = ({"status": "failed", "result": None, "error": error} if self.summary_failed
                               else {"status": "completed", "result": summary, "error": None})
            return json.dumps({"schema_version": "1.0.0", "mode": "mock", "doc_id": document["doc_id"],
                               "text_sha256": document["text_sha256"],
                               "items": [] if self.extraction_state == "failed" else items,
                               "summary": summary_outcome,
                               "extractor_version": MOCK_VERSION,
                               "prompt_version": None if self.extraction_state == "failed" else PROMPT_VERSION,
                               "extraction_status": self.extraction_state,
                               "extraction_error": error if self.extraction_state == "failed" else None,
                               "warnings": ["Some findings could not be validated."] if self.extraction_state == "partial" else [],
                               "extraction_provenance": None if self.extraction_state == "failed" else provenance("extract", "d-extract")})
        question = request["question"]
        questions = {
            "What does the document say about chest pain?": "chest pain",
            "What does the document say about pneumonia?": "pneumonia",
            "What does the document say about the patient's family?": "diabetes",
            "Which procedure is mentioned?": "appendectomy",
            "What does the document say about chest pain and the patient's age?": "chest pain",
            "What diagnoses or symptoms are mentioned?": "*",
        }
        topic = questions.get(question)
        selected = [span for item in items if topic == "*" or topic == item["name"].casefold()
                    for span in item["evidence"]]
        result = passages(document, selected, operation="document-answer",
                          partial=bool(selected) and "age" in question)
        return json.dumps(result)


class UnconfiguredLiveProvider:
    mode = "live"

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        raise ServiceError(503, "configuration_required",
                           "Live generation is disabled until an approved provider is configured.")
