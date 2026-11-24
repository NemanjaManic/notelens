"""Private quote protocol; trusted code constructs the unchanged public contract.

The model selects semantics and source quotes. No reference labels, model-provided
IDs, hashes or numeric code-point offsets are accepted into the public result.
"""

from .evidence import EvidenceError, resolve_quote
from .providers import NO_ANSWER

VERSION = "d-quote-hints-v2"
PROMPT_VERSION = "d-quote-hints-prompts-v1"


def object_schema(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


QUOTE = object_schema({"quote": {"type": "string"}, "occurrence": {"type": "integer"}})
ENTITY = object_schema({
    "type": {"type": "string", "enum": ["diagnosis", "symptom", "procedure"]},
    "mention_quote": {"type": "string"}, "mention_occurrence": {"type": "integer"},
    "assertion": {"type": "string", "enum": ["confirmed", "suspected", "negated", "unknown"]},
    "temporality": {"type": "string", "enum": ["current", "historical", "unknown"]},
    "subject": {"type": "string", "enum": ["patient", "family", "other", "unknown"]},
    "procedure_status": {"type": ["string", "null"],
                         "enum": ["planned", "ordered", "performed", "cancelled", "hypothetical", "unknown", None]},
    "evidence": {"type": "array", "items": QUOTE},
})
SCHEMAS = {
    "extract": object_schema({"entities": {"type": "array", "items": ENTITY},
                              "summary_quotes": {"type": "array", "items": QUOTE}}),
    "answer": object_schema({
        "evidence_state": {"type": "string", "enum": ["sufficient", "partial", "insufficient"]},
        "out_of_scope": {"type": "boolean"},
        "quotes": {"type": "array", "items": QUOTE},
        "gaps": {"type": "array", "items": {"type": "string"}},
    }),
}


def validate_private(value, schema):
    """Validate the small private schema independently of provider enforcement."""
    types = {"object": dict, "array": list, "string": str, "integer": int,
             "boolean": bool, "null": type(None)}
    allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
    if not any(type(value) is types[name] for name in allowed):
        raise EvidenceError("Invalid private provider field type.")
    if "enum" in schema and value not in schema["enum"]:
        raise EvidenceError("Invalid private provider label.")
    if isinstance(value, dict):
        if set(value) != set(schema["properties"]):
            raise EvidenceError("Missing or unexpected private provider fields.")
        for key, child in value.items():
            validate_private(child, schema["properties"][key])
    elif isinstance(value, list):
        for child in value:
            validate_private(child, schema["items"])


def provenance(operation, component, model, prompt_version=PROMPT_VERSION):
    return {"component_id": component, "service": "extraction", "operation": operation,
            "mode": "live", "output_version": VERSION, "prompt_version": prompt_version,
            "provider": "openai", "model": model, "configuration_version": VERSION,
            "corpus_version": None, "index_version": None, "retriever_version": None}


def spans(document, hints):
    result = []
    for hint in hints:
        result.append(resolve_hint(document["text"], hint["quote"], hint["occurrence"]))
    return result


def resolve_hint(text, quote, occurrence):
    # A unique literal quote identifies its occurrence without any model number.
    # Only repeated quotes need the explicitly selected, validated occurrence.
    try:
        return resolve_quote(text, quote)
    except EvidenceError:
        return resolve_quote(text, quote, occurrence)


def claims_and_sources(document, evidence, component):
    unique = {(span["start"], span["end"]): span for span in evidence}
    claims, sources = [], []
    for index, span in enumerate(sorted(unique.values(), key=lambda s: s["start"])):
        sid = f"{component}-source-{index}"
        sources.append({"source_id": sid, "kind": "document", "doc_id": document["doc_id"],
                        "text_sha256": document["text_sha256"], "evidence": span, "component_id": component})
        claims.append({"claim_id": f"{component}-claim-{index}", "text": span["quote"],
                       "scope": "document_fact", "source_ids": [sid], "component_id": component})
    return claims, sources


def build_item(entity, document, index):
    evidence = spans(document, entity["evidence"])
    if not evidence:
        raise EvidenceError("An entity requires explicit source evidence.")
    first = evidence[0]
    local = resolve_hint(first["quote"], entity["mention_quote"], entity["mention_occurrence"])
    mention = {**local, "start": first["start"] + local["start"], "end": first["start"] + local["end"]}
    status = (entity["procedure_status"] or "unknown") if entity["type"] == "procedure" else None
    return {"entity_id": f"entity-{index}", "type": entity["type"],
            "name": mention["quote"], "mention": mention, "evidence": evidence,
            **{k: entity[k] for k in ("assertion", "temporality", "subject")}, "procedure_status": status,
            "component_id": "d-extract"}


def build_extraction(hints, document, model, prompt_version=PROMPT_VERSION):
    items, rejected = [], 0
    for index, entity in enumerate(hints["entities"]):
        try:
            items.append(build_item(entity, document, index))
        except EvidenceError:
            rejected += 1
    summary = {"status": "failed", "result": None, "error": {
        "code": "insufficient_evidence", "message": "The document does not support a quoted summary.", "retryable": False}}
    if hints["summary_quotes"]:
        try:
            selected = spans(document, hints["summary_quotes"])
            claims, sources = claims_and_sources(document, selected, "d-summary")
            summary = {"status": "completed", "error": None, "result": {
                "language": "en", "text": "\n\n".join(c["text"] for c in claims),
                "claims": claims, "sources": sources, "evidence_state": "sufficient", "warnings": [],
                "provenance": provenance("summarize", "d-summary", model, prompt_version)}}
        except EvidenceError:
            # A summary failure must not discard independently valid extraction.
            summary = {"status": "failed", "result": None, "error": {
                "code": "validation_failure", "message": "Summary quotes did not resolve to the selected document.", "retryable": False}}
    if rejected and not items and summary["status"] == "failed":
        raise EvidenceError("Neither extraction nor summary contains validated evidence.")
    extraction_status = ("partial" if items else "failed") if rejected else "completed"
    error = {"code": "validation_failure", "message": "Some candidate mentions lacked resolvable source evidence.",
             "retryable": False} if rejected else None
    return {"schema_version": "1.0.0", "mode": "live", "doc_id": document["doc_id"],
            "text_sha256": document["text_sha256"], "items": items, "summary": summary,
            "extractor_version": VERSION, "prompt_version": prompt_version, "extraction_status": extraction_status,
            "extraction_error": error,
            "warnings": [f"{rejected} candidate mention(s) could not be grounded; extraction is incomplete."] if rejected else [],
            "extraction_provenance": provenance("extract", "d-extract", model, prompt_version)}


def build_answer(hints, document, model, prompt_version=PROMPT_VERSION):
    selected = spans(document, hints["quotes"])
    state = hints["evidence_state"]
    if (state == "insufficient") != (not selected) or (hints["out_of_scope"] and selected):
        raise EvidenceError("Private answer state contradicts its source support.")
    if state == "partial" and not any(gap.strip() for gap in hints["gaps"]):
        raise EvidenceError("A partial answer must identify its missing information.")
    claims, sources = claims_and_sources(document, selected, "d-answer")
    warnings = list(hints["gaps"])
    if hints["out_of_scope"]:
        warnings.append("The request is outside the supported document-evidence scope.")
    return {"schema_version": "1.0.0", "mode": "live", "language": "en",
            "text": "\n\n".join(c["text"] for c in claims) if claims else NO_ANSWER,
            "claims": claims, "sources": sources, "evidence_state": state, "warnings": warnings,
            "route": "document" if claims else "none", "answer_version": VERSION,
            "prompt_version": prompt_version if claims else None,
            "components": [provenance("document-answer", "d-answer", model, prompt_version)] if claims else [],
            "attempted_routes": ["document"], "clarification": None, "retrieval_provenance": None}


def build(operation, hints, document, model, prompt_version=PROMPT_VERSION):
    validate_private(hints, SCHEMAS[operation])
    return (build_extraction if operation == "extract" else build_answer)(hints, document, model, prompt_version)
