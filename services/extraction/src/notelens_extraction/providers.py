"""Provider boundary and deterministic catalog fake. No provider is approved live."""

import json
from typing import Protocol

from .errors import ServiceError
from .evidence import resolve_quote

PROMPT_VERSION = "d-literal-v1"
FAKE_VERSION = "mock-catalog-v1"
CATALOG = (
    ("The patient denies chest pain.", "symptom", "chest pain", "negated", "unknown", "patient"),
    ("No chest pain.", "symptom", "chest pain", "negated", "unknown", "unknown"),
    ("Pneumonia is suspected.", "diagnosis", "Pneumonia", "suspected", "unknown", "unknown"),
    ("The patient's mother has diabetes.", "diagnosis", "diabetes", "confirmed", "unknown", "family"),
    ("The patient had an appendectomy in 2018.", "procedure", "appendectomy", "confirmed", "historical", "patient"),
    ("The patient currently has asthma.", "diagnosis", "asthma", "confirmed", "current", "patient"),
)


class Provider(Protocol):
    mode: str

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        """Return JSON; request contains no evaluation labels or references."""
        ...


def literal_generation(document: dict, evidence: list[dict], *, partial: bool = False) -> dict:
    unique = {(e["start"], e["end"]): e for e in evidence}
    sources, claims = [], []
    for index, span in enumerate(sorted(unique.values(), key=lambda e: e["start"])):
        source_id = f"document-source-{index}"
        sources.append({"source_id": source_id, "kind": "document", "doc_id": document["doc_id"],
                        "text_sha256": document["text_sha256"], "evidence": span})
        claims.append({"claim_id": f"claim-{index}", "text": span["quote"],
                       "scope": "document_fact", "source_ids": [source_id]})
    return {"language": "en", "text": " ".join(c["text"] for c in claims) if claims else "The document does not provide enough supported information to answer this request.",
            "claims": claims, "sources": sources,
            "evidence_state": ("partial" if partial else "sufficient") if claims else "insufficient",
            "warnings": ["Deterministic mock catalog; output is limited and not exhaustive."] +
                        (["The document does not provide the requested age."] if partial else [])}


class FakeProvider:
    """Small explicit offline catalog, not a general extractor or semantic judge.

    Matches recognized literal sentences only and ignores unrelated instructions.
    The provider does not read annotation references or the training-example JSON.
    """

    mode = "mock"

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        document = request["document"]
        text = document["text"]
        items = []
        for sentence, kind, name, assertion, time, subject in CATALOG:
            occurrence = 0
            start = 0
            while (found := text.find(sentence, start)) >= 0:
                span = resolve_quote(text, sentence, occurrence)
                items.append({"entity_id": f"entity-{found}-{kind}", "type": kind, "name": name,
                              "assertion": assertion, "temporality": time, "subject": subject,
                              "evidence": [span]})
                start = found + len(sentence)
                occurrence += 1
        items.sort(key=lambda item: item["evidence"][0]["start"])
        if operation == "extract":
            return json.dumps({"schema_version": "1.0.0", "mode": self.mode,
                               "doc_id": document["doc_id"], "text_sha256": document["text_sha256"],
                               "items": items,
                               "summary": literal_generation(document, [s for i in items for s in i["evidence"]]),
                               "extractor_version": FAKE_VERSION, "prompt_version": PROMPT_VERSION})
        question = request["question"]
        # Deliberately explicit mock questions; ambiguous follow-ups abstain.
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
        result = literal_generation(document, selected, partial=bool(selected) and "age" in question)
        result.update(schema_version="1.0.0", mode=self.mode, route="document" if selected else "none",
                      answer_version=FAKE_VERSION, prompt_version=PROMPT_VERSION)
        return json.dumps(result)


class UnconfiguredLiveProvider:
    mode = "live"

    def generate(self, operation: str, request: dict, instructions: str, *, repair: bool) -> str:
        raise ServiceError(503, "configuration_required",
                           "Live generation is disabled until a provider, model and spending policy are approved.")
