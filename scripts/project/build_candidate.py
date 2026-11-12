"""Reproduce the review-only P2 candidate from unchanged P1 inputs."""

from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from check_contracts import ROOT, read_json


CANDIDATE = ROOT / "contracts/candidates/p2-rc1"
LABELS = ["Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology", "Neurology", "Urology"]
NO_ANSWER = "The available sources do not support an answer."
NO_SUMMARY = "The available document evidence does not support a summary."
REQUEST_ID = "11111111-1111-4111-8111-111111111111"
FALLBACK_ID = "22222222-2222-4222-8222-222222222222"
REVIEW_FILES = [
    "scripts/project/build_candidate.py", "scripts/project/check_candidate.py",
    "scripts/project/tests/test_candidate.py", "docs/team/classifier-scaffold-p2.md",
    "scripts/project/check_contracts.py", "scripts/project/tests/test_contracts.py",
    "scripts/project/README.md", "scripts/project/pyproject.toml", "scripts/project/uv.lock",
    "docs/decisions/contract-p2-proposal.md", "docs/platform/interface-review.md",
    "docs/team/contract-reviews/p1/README.md",
    "docs/team/contract-reviews/p1/member-a-response-to-b.md",
    "docs/team/contract-reviews/p1/member-c-response-to-b.md",
    "docs/team/contract-reviews/p1/member-d-response-to-b.md",
    "contracts/candidates/p2-rc1/README.md",
    "contracts/candidates/p2-rc1/reviews/member-c-p2-review-and-next-dependencies.md",
    "contracts/candidates/p2-rc1/reviews/member-c-response-to-b-p2-clarifications.md",
]


def ref(name):
    return {"$ref": "#/$defs/" + name}


def string():
    return {"type": "string", "minLength": 1}


def nullable(value):
    return {"anyOf": [value, {"type": "null"}]}


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def condition(properties, then):
    return {"if": {"properties": properties, "required": list(properties)}, "then": then}


def schemas():
    schema = deepcopy(read_json(ROOT / "contracts/v1/schema.json"))
    schema["$id"] = "urn:notelens:contracts:candidates:p2-rc1"
    schema["title"] = "NoteLens P2 RC1 review candidate"
    schema["$comment"] = "REVIEW ONLY. P1 remains canonical; no owner approval, freeze, or activation is asserted."
    d = schema["$defs"]
    d["RequestId"] = {"type": "string", "format": "uuid", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"}
    d["LanguageValidation"] = obj({
        "outcome": {"enum": ["accepted", "rejected", "inconclusive"]},
        "language": nullable({"const": "en"}), "policy_version": string(),
        "reason": {"enum": [None, "unsupported_language", "language_inconclusive"]},
    })
    d["LanguageValidation"]["allOf"] = [
        condition({"outcome": {"const": "accepted"}}, {"properties": {"language": {"const": "en"}, "reason": {"const": None}}}),
        condition({"outcome": {"const": "rejected"}}, {"properties": {"language": {"const": None}, "reason": {"const": "unsupported_language"}}}),
        condition({"outcome": {"const": "inconclusive"}}, {"properties": {"language": {"const": None}, "reason": {"const": "language_inconclusive"}}}),
    ]
    d["PreparedDocument"]["properties"]["language_validation"] = ref("LanguageValidation")
    d["PreparedDocument"]["required"].append("language_validation")
    d["PreparedDocument"]["allOf"] = [{"properties": {"language_validation": {"properties": {"outcome": {"const": "accepted"}}}}}]
    classification = d["ClassificationResult"]
    classification["properties"].update({
        "classification_execution": {"enum": ["skipped", "performed"]},
        "model_version": nullable(string()),
        "score_kind": nullable({"enum": ["probability", "decision_score"]}),
        "scope_policy_version": nullable(string()),
        "scope_reason": nullable({"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}),
    })
    classification["required"].extend(["classification_execution", "scope_policy_version", "scope_reason"])
    classification["allOf"] = [
        condition({"status": {"const": "supported"}}, {"properties": {"category": {"enum": LABELS}}}),
        condition({"status": {"enum": ["uncertain", "unsupported"]}}, {"properties": {"category": {"const": None}}}),
        condition({"classification_execution": {"const": "performed"}}, {"properties": {
            "model_version": string(), "score_kind": {"enum": ["probability", "decision_score"]},
            "scores": {"minItems": 5, "maxItems": 5}}}),
        condition({"classification_execution": {"const": "skipped"}}, {"properties": {
            "status": {"const": "unsupported"}, "model_version": {"const": None},
            "score_kind": {"const": None}, "scores": {"maxItems": 0}}}),
        condition({"status": {"const": "unsupported"}}, {"properties": {
            "scope_policy_version": string(), "scope_reason": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}}}),
        condition({"status": {"enum": ["supported", "uncertain"]}}, {"properties": {
            "classification_execution": {"const": "performed"}, "scope_policy_version": {"const": None}, "scope_reason": {"const": None}}}),
        condition({"score_kind": {"const": "probability"}}, {"properties": {"scores": {"items": {
            "allOf": [ref("ClassificationScore"), {"properties": {"score": {"minimum": 0, "maximum": 1}}}]}}}}),
    ]
    provenance = obj({
        "component_id": string(), "service": {"enum": ["rag", "extraction"]},
        "operation": {"enum": ["extract", "summarize", "document-answer", "literature-answer"]},
        "mode": {"enum": ["mock", "live"]}, "output_version": string(), "prompt_version": string(),
        "provider": string(), "model": string(), "configuration_version": string(),
        "corpus_version": nullable(string()), "index_version": nullable(string()), "retriever_version": nullable(string()),
    })
    provenance["allOf"] = [
        condition({"service": {"const": "rag"}}, {"properties": {
            "operation": {"const": "literature-answer"}, **{key: string() for key in ("corpus_version", "index_version", "retriever_version")}}}),
        condition({"service": {"const": "extraction"}}, {"properties": {
            "operation": {"enum": ["extract", "summarize", "document-answer"]},
            **{key: {"const": None} for key in ("corpus_version", "index_version", "retriever_version")}}}),
    ]
    d["ComponentProvenance"] = provenance
    for name in ("Claim", "DocumentSource", "LiteratureSource"):
        d[name]["properties"]["component_id"] = string()
        d[name]["required"].append("component_id")
    # RetrievalPassage is a retrieved source, not an executed answer-generation component.
    item = d["ExtractionItem"]
    item["properties"]["assertion"]["enum"].append("unknown")
    item["properties"].update({"mention": ref("EvidenceSpan"), "component_id": string(),
                                "procedure_status": {"enum": [None, "planned", "ordered", "performed", "cancelled", "hypothetical", "unknown"]}})
    item["required"].extend(["mention", "component_id", "procedure_status"])
    item["allOf"] = [{"if": {"properties": {"type": {"const": "procedure"}}},
                       "then": {"properties": {"procedure_status": {"type": "string"}}},
                       "else": {"properties": {"procedure_status": {"const": None}}}}]
    d["Summary"]["properties"]["provenance"] = nullable(ref("ComponentProvenance"))
    d["Summary"]["required"].append("provenance")
    d["Summary"]["allOf"].append(condition({"evidence_state": {"enum": ["sufficient", "partial"]}},
                                             {"properties": {"provenance": ref("ComponentProvenance")}}))
    d["SummaryOutcome"] = obj({"status": {"enum": ["completed", "failed"]}, "result": nullable(ref("Summary")), "error": nullable(ref("ErrorDetail"))})
    d["SummaryOutcome"]["allOf"] = [
        condition({"status": {"const": "completed"}}, {"properties": {"result": ref("Summary"), "error": {"const": None}}}),
        condition({"status": {"const": "failed"}}, {"properties": {"result": {"const": None}, "error": ref("ErrorDetail")}}),
    ]
    extraction = d["ExtractionResult"]
    extraction["properties"].update({"mode": {"enum": ["mock", "live", "mixed"]},
        "summary": ref("SummaryOutcome"), "extraction_status": {"enum": ["completed", "partial", "failed"]},
        "extraction_error": nullable(ref("ErrorDetail")), "warnings": {"type": "array", "items": string()},
        "extraction_provenance": nullable(ref("ComponentProvenance")), "prompt_version": nullable(string())})
    extraction["required"].extend(["extraction_status", "extraction_error", "warnings", "extraction_provenance"])
    extraction["allOf"] = [
        condition({"extraction_status": {"const": "failed"}}, {"properties": {"items": {"maxItems": 0}, "extraction_error": ref("ErrorDetail")}}),
        condition({"extraction_status": {"const": "completed"}}, {"properties": {"extraction_error": {"const": None}}}),
        condition({"extraction_status": {"const": "partial"}}, {"properties": {"items": {"minItems": 1}, "warnings": {"minItems": 1}}}),
        {"not": {"properties": {"extraction_status": {"const": "failed"}, "summary": {"properties": {"status": {"const": "failed"}}}}, "required": ["extraction_status", "summary"]}},
    ]
    d["Clarification"] = obj({"code": {"const": "ambiguous_reference"}, "message": string()})
    answer = d["AnswerResult"]
    answer["properties"].update({"mode": {"enum": ["mock", "live", "mixed"]},
        "prompt_version": nullable(string()),
        "components": {"type": "array", "items": ref("ComponentProvenance")},
        "attempted_routes": {"type": "array", "items": {"enum": ["document", "literature"]}, "minItems": 1, "uniqueItems": True},
        "clarification": nullable(ref("Clarification"))})
    answer["required"].extend(["components", "attempted_routes", "clarification"])
    answer["allOf"].extend([
        condition({"clarification": {"type": "object"}}, {"properties": {"route": {"const": "none"}, "evidence_state": {"const": "insufficient"}, "claims": {"maxItems": 0}, "sources": {"maxItems": 0}}}),
        condition({"route": {"const": "mixed"}}, {"properties": {"attempted_routes": {"minItems": 2}}}),
    ])
    d["RetrievalResult"]["properties"]["state"]["enum"] = ["sufficient", "insufficient"]
    d["RetrievalResult"]["properties"].pop("error")
    d["RetrievalResult"]["properties"]["corpus_version"] = string()
    d["RetrievalResult"]["required"].append("corpus_version")
    d["RetrievalResult"]["allOf"] = [condition({"state": {"const": "sufficient"}}, {"properties": {"passages": {"minItems": 1}}})]
    for name in ("RetrievalRequest", "DocumentQuestionRequest"):
        d[name]["properties"]["question"]["pattern"] = r"\S"
    d["ErrorEnvelope"]["properties"]["request_id"] = ref("RequestId")
    d["LivenessResult"] = obj({"schema_version": {"const": "1.0.0"}, "service": {"enum": ["rag", "classifier", "extraction"]},
                               "status": {"const": "alive"}, "mode": {"enum": ["mock", "live"]}, "version": string()})
    d["HealthResult"]["properties"].update({"model_version": nullable(string()), "reason": nullable(string())})
    d["HealthResult"]["required"].extend(["model_version", "reason"])
    d["HealthResult"]["allOf"] = [
        condition({"status": {"const": "not_ready"}}, {"properties": {"reason": string()}}),
        condition({"status": {"const": "ok"}}, {"properties": {"reason": {"const": None}}}),
        condition({"mode": {"const": "mock"}}, {"properties": {"model_version": {"const": None}}}),
        condition({"mode": {"const": "live"}, "service": {"const": "classifier"}, "status": {"const": "ok"}}, {"properties": {"model_version": string()}}),
    ]
    api = deepcopy(read_json(ROOT / "contracts/v1/openapi.json"))
    api["info"]["title"] = "NoteLens P2 RC1 review candidate"
    api["info"]["description"] = "REVIEW ONLY: not frozen; P1 is unchanged. No HTTP implementation is supplied."
    api["x-candidate-id"] = "p2-rc1"
    parameter = {"name": "X-Request-ID", "in": "header", "required": True,
                 "description": "Canonical lowercase UUID. Reject missing, malformed or duplicate headers before processing.",
                 "schema": {"$ref": "./schema.json#/$defs/RequestId"}}
    response_header = {"description": "Echo the valid request ID. Invalid-input-ID errors use a new diagnostic UUID matching the error envelope.",
                       "required": True, "schema": {"$ref": "./schema.json#/$defs/RequestId"}}
    for path in api["paths"].values():
        post = path["post"]
        post["parameters"] = [deepcopy(parameter)]
        post["responses"]["500"] = deepcopy(post["responses"]["503"])
        post["responses"]["500"]["description"] = "Unexpected internal failure; safe English internal_error envelope."
        for response in post["responses"].values():
            response["headers"] = {"X-Request-ID": deepcopy(response_header)}
    for route, definition in [("/health/live", "LivenessResult"), ("/health/ready", "HealthResult")]:
        responses = {"200": {"description": "Process liveness." if definition == "LivenessResult" else "Ready in the explicitly declared mode.",
                             "content": {"application/json": {"schema": {"$ref": "./schema.json#/$defs/" + definition}}}}}
        if definition == "HealthResult":
            responses["503"] = {"description": "Not ready; this health endpoint returns HealthResult, not a business ErrorEnvelope.",
                                "content": {"application/json": {"schema": {"$ref": "./schema.json#/$defs/HealthResult"}}}}
        api["paths"][route] = {"get": {"operationId": "service_liveness" if definition == "LivenessResult" else "service_readiness",
            "security": [{"ServiceToken": []}],
            "servers": [{"url": "{serviceBaseUrl}", "variables": {"serviceBaseUrl": {"default": "http://127.0.0.1:8002", "description": "Select the local service origin; not a deployed URL."}}}],
            "description": "Shared health shape for all three services. No request ID required; no model/provider calls or request-body retention.",
            "responses": responses}}
    return schema, api


def component(service="extraction", operation="document-answer", component_id="d-answer", mode="mock"):
    return {"component_id": component_id, "service": service, "operation": operation, "mode": mode,
            "output_version": "fixture-output-v0", "prompt_version": "fixture-prompt-v0", "provider": "fixture-provider",
            "model": "fixture-model", "configuration_version": "fixture-config-v0",
            **{key: "fixture-" + key.replace("_", "-") if service == "rag" else None for key in ("corpus_version", "index_version", "retriever_version")}}


def language(outcome="accepted"):
    return {"outcome": outcome, "language": "en" if outcome == "accepted" else None,
            "policy_version": "fixture-language-policy-v0", "reason": {"accepted": None, "rejected": "unsupported_language", "inconclusive": "language_inconclusive"}[outcome]}


def rendered(value, fallback):
    return "\n\n".join(claim["text"] for claim in value["claims"]) if value["claims"] else fallback


def namespace_mixed(value):
    """Construct review fixtures with owner-prefixed IDs; never infer medical text."""
    prefixes={record["component_id"]: "a:" if record["service"]=="rag" else "d:" for record in value["components"]}
    source_ids={source["source_id"]:prefixes[source["component_id"]]+source["source_id"] for source in value["sources"]}
    for claim in value["claims"]:
        prefix=prefixes[claim["component_id"]]
        claim["claim_id"]=prefix+claim["claim_id"]
        claim["source_ids"]=[source_ids.get(key,prefix+key) for key in claim["source_ids"]]
        claim["component_id"]=prefix+claim["component_id"]
    for source in value["sources"]:
        source["source_id"]=source_ids[source["source_id"]]
        source["component_id"]=prefixes[source["component_id"]]+source["component_id"]
    for record in value["components"]:
        record["component_id"]=prefixes[record["component_id"]]+record["component_id"]
    value["answer_version"]="notelens-compose-v1"
    value["prompt_version"]=None


def upgrade(payload, definition):
    value = deepcopy(payload)
    if definition == "PreparedDocument":
        value["language_validation"] = language()
    elif definition in {"ClassificationRequest", "ExtractionRequest", "DocumentQuestionRequest"}:
        value["document"] = upgrade(value["document"], "PreparedDocument")
    elif definition == "ClassificationResult":
        skipped = value["status"] == "unsupported" and not value["scores"]
        value["classification_execution"] = "skipped" if skipped else "performed"
        value["scope_policy_version"] = "fixture-scope-policy-v0" if value["status"] == "unsupported" else None
        value["scope_reason"] = "outside_supported_scope" if value["status"] == "unsupported" else None
        if skipped:
            value["model_version"] = value["score_kind"] = None
        elif value["status"] == "uncertain" and not value["scores"]:
            value["scores"] = [{"category": label, "score": float(index)} for index, label in enumerate(LABELS)]
    elif definition in {"DocumentSource", "LiteratureSource", "Source"}:
        value["component_id"] = "a-answer" if value["kind"] == "literature" else "d-answer"
    elif definition == "Claim":
        value["component_id"] = "d-answer"
    elif definition == "ExtractionItem":
        evidence = value["evidence"][0]
        match = re.search(re.escape(value["name"]), evidence["quote"], re.I)
        if match is None:
            raise ValueError("An explicit fixture mention location is required")
        value["mention"] = {"start": evidence["start"] + match.start(), "end": evidence["start"] + match.end(), "quote": match.group()}
        value["component_id"] = "d-extract"
        value["procedure_status"] = None
    elif definition in {"Summary", "AnswerResult"}:
        for source in value["sources"]:
            source["component_id"] = "a-answer" if source["kind"] == "literature" else "d-answer"
        source_map = {source["source_id"]: source for source in value["sources"]}
        for claim in value["claims"]:
            source = next((source_map[key] for key in claim["source_ids"] if key in source_map), None)
            claim["component_id"] = source["component_id"] if source else "d-answer"
        if definition == "Summary":
            value["provenance"] = component(operation="summarize") if value["claims"] else None
            value["text"] = rendered(value, NO_SUMMARY)
        else:
            ids = {source["component_id"] for source in value["sources"]} | {claim["component_id"] for claim in value["claims"]}
            value["components"] = [component("rag", "literature-answer", key) if key == "a-answer" else component(component_id=key) for key in sorted(ids)]
            value["attempted_routes"] = ["document", "literature"] if value["route"] in {"mixed", "none"} else [value["route"]]
            value["clarification"] = None
            value["text"] = rendered(value, NO_ANSWER)
            if value["route"]=="mixed":
                namespace_mixed(value)
            elif value["components"]:
                for record in value["components"]:
                    record["output_version"]=value["answer_version"]
                    record["prompt_version"]=value["prompt_version"]
            else:
                value["prompt_version"]=None
    elif definition == "ExtractionResult":
        value["items"] = [upgrade(item, "ExtractionItem") for item in value["items"]]
        value["summary"] = {"status": "completed", "result": upgrade(value["summary"], "Summary"), "error": None}
        value.update(extraction_status="completed", extraction_error=None, warnings=[],
                     extraction_provenance=component(operation="extract", component_id="d-extract"))
        value["extraction_provenance"]["output_version"]=value["extractor_version"]
        value["extraction_provenance"]["prompt_version"]=value["prompt_version"]
    elif definition == "RetrievalResult":
        value["corpus_version"] = "fixture-corpus-v0"
    elif definition == "ErrorEnvelope":
        value["request_id"] = REQUEST_ID
    elif definition == "HealthResult":
        value.update(model_version=None, reason=None)
    return value


def fixtures():
    directory = ROOT / "contracts/v1/fixtures"
    manifest = deepcopy(read_json(directory / "manifest.json"))
    old = read_json(directory / "payloads.json")
    documents = {key: upgrade(value, "PreparedDocument") for key, value in read_json(directory / "documents.json").items()}
    references = deepcopy(read_json(directory / "references.json"))
    payloads = {}
    for case in manifest["cases"]:
        payloads[case["id"]] = upgrade(old[case["id"]], case["definition"]) if case["kind"] == "payload" else deepcopy(old[case["id"]])
        if case["id"] in {"retrieval-error", "retrieval-error-without-detail"}:
            paths = ["/state"] + ([""] if "error" in payloads[case["id"]] else [])
            case["expected"] = [{"rule": "STRUCTURE", "path": path} for path in sorted(paths)]
        if case["id"] == "retrieval-success-with-error":
            case["expected"] = [{"rule": "STRUCTURE", "path": ""}]
    def add(case_id, definition, payload, document=None, reference=None, rule=None, path=""):
        case = {"id": case_id, "kind": "payload", "definition": definition,
                "expected": [{"rule": rule, "path": path}] if rule else [], "scenarios": []}
        if document: case["document"] = document
        if reference: case["reference"] = reference
        manifest["cases"].append(case)
        payloads[case_id] = deepcopy(payload)
    def changed(case_id, new_id, definition, mutate, rule=None, path="", document=None):
        value = deepcopy(payloads[case_id]); mutate(value)
        add(new_id, definition, value, document=document, rule=rule, path=path)
    add("request-id-valid", "RequestId", REQUEST_ID)
    add("language-accepted", "LanguageValidation", language())
    add("language-inconclusive", "LanguageValidation", language("inconclusive"))
    add("language-rejected", "LanguageValidation", language("rejected"))
    add("component-extraction", "ComponentProvenance", component())
    add("component-literature", "ComponentProvenance", component("rag", "literature-answer", "a-answer"))
    add("summary-outcome-completed", "SummaryOutcome", payloads["extraction-valid"]["summary"], "offset")
    failed = {"status": "failed", "result": None, "error": {"code": "provider_unavailable", "message": "The summary service is unavailable.", "retryable": True}}
    add("summary-outcome-failed", "SummaryOutcome", failed)
    clarification = {"code": "ambiguous_reference", "message": "Please name the condition or topic you mean."}
    add("clarification-valid", "Clarification", clarification)
    add("liveness-valid", "LivenessResult", {"schema_version": "1.0.0", "service": "classifier", "status": "alive", "mode": "mock", "version": "fixture-service-v0"})
    changed("health-valid", "health-not-ready", "HealthResult", lambda x: x.update(mode="live", status="not_ready", reason="Model is not configured."))
    changed("health-valid", "health-live-ready", "HealthResult", lambda x: x.update(service="classifier", mode="live", model_version="fixture-model-v0"))
    changed("health-valid", "health-false-live-ready", "HealthResult", lambda x: x.update(service="classifier", mode="live"), rule="STRUCTURE", path="/model_version")
    changed("document-valid", "document-language-inconclusive", "PreparedDocument", lambda x: x.update(language_validation=language("inconclusive")), rule="STRUCTURE", path="/language_validation/outcome")
    changed("classification-uncertain", "classification-uncertain-empty", "ClassificationResult", lambda x: x.update(scores=[]), rule="STRUCTURE", path="/scores", document="offset")
    changed("classification-unsupported", "classification-skipped-fake-model", "ClassificationResult", lambda x: x.update(model_version="unused-model"), rule="STRUCTURE", path="/model_version", document="offset")
    changed("classification-unsupported", "classification-skipped-fake-scores", "ClassificationResult", lambda x: x.update(scores=deepcopy(payloads["classification-probability"]["scores"])), rule="STRUCTURE", path="/scores", document="offset")
    changed("classification-supported", "classification-wrong-order", "ClassificationResult", lambda x: x["scores"].reverse(), rule="CATEGORY_ORDER", path="/scores", document="offset")
    changed("classification-supported", "classification-named-state-not-status", "ClassificationResult", lambda x: x.update(state=x.pop("status")), rule="STRUCTURE", document="offset")
    changed("classification-supported", "classification-unsupported-performed", "ClassificationResult", lambda x: x.update(status="unsupported", category=None, scope_policy_version="fixture-scope-policy-v0", scope_reason="outside_supported_scope"), document="offset")
    changed("classification-unsupported", "classification-real-unsupported-unapproved", "ClassificationResult", lambda x: x.update(mode="live"), rule="SCOPE_POLICY_UNAPPROVED", path="/scope_policy_version", document="offset")
    changed("extraction-item-valid", "extraction-unknown-assertion", "ExtractionItem", lambda x: x.update(assertion="unknown"), document="offset")
    changed("extraction-item-valid", "mention-wrong-quote", "ExtractionItem", lambda x: x["mention"].update(quote="Wrong quote"), rule="SPAN_QUOTE", path="/mention", document="offset")
    changed("extraction-item-valid", "mention-outside-evidence", "ExtractionItem", lambda x: x.update(mention={"start":7,"end":21,"quote":"No chest pain."}), rule="MENTION_EVIDENCE", path="/mention", document="offset")
    procedure_text = "Colonoscopy is planned for next week."
    procedure_doc = deepcopy(documents["offset"])
    procedure_doc.update(doc_id="fixture-procedure", text=procedure_text, text_sha256=hashlib.sha256(procedure_text.encode("utf-8")).hexdigest())
    documents["procedure"] = procedure_doc
    procedure = deepcopy(payloads["extraction-item-valid"])
    procedure.update(entity_id="planned-procedure", type="procedure", name="Colonoscopy", assertion="confirmed", temporality="unknown", subject="unknown", procedure_status="planned",
                     mention={"start":0,"end":11,"quote":"Colonoscopy"}, evidence=[{"start":0,"end":len(procedure_text),"quote":procedure_text}])
    references["planned-procedure"] = {"attributes": {"/procedure_status":"planned"}}
    add("procedure-planned", "ExtractionItem", procedure, "procedure", "planned-procedure")
    wrong = deepcopy(procedure); wrong["procedure_status"] = "performed"
    add("procedure-plan-not-performed", "ExtractionItem", wrong, "procedure", "planned-procedure", rule="REFERENCE_ATTRIBUTE", path="/procedure_status")
    for status in ["ordered", "performed", "cancelled", "hypothetical", "unknown"]:
        doc = deepcopy(procedure_doc)
        text = "Procedure mention: Colonoscopy. Recorded procedure status: " + status + "."
        doc.update(doc_id="fixture-procedure-"+status,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest())
        documents["procedure-"+status] = doc
        value=deepcopy(procedure); start=text.index("Colonoscopy")
        value.update(procedure_status=status, mention={"start":start,"end":start+11,"quote":"Colonoscopy"}, evidence=[{"start":0,"end":len(text),"quote":text}])
        add("procedure-"+status,"ExtractionItem",value,"procedure-"+status)
    changed("extraction-item-valid", "symptom-with-procedure-status", "ExtractionItem", lambda x: x.update(procedure_status="performed"), rule="STRUCTURE", path="/procedure_status", document="offset")
    changed("extraction-valid", "analysis-summary-failed-findings-kept", "ExtractionResult", lambda x: x.update(summary=failed), document="offset")
    changed("extraction-valid", "analysis-extraction-partial", "ExtractionResult", lambda x: x.update(extraction_status="partial",warnings=["Some findings could not be validated."]), document="offset")
    changed("extraction-valid", "analysis-extraction-failed-summary-kept", "ExtractionResult", lambda x: x.update(extraction_status="failed",items=[],extraction_error=failed["error"],extraction_provenance=None,prompt_version=None), document="offset")
    changed("analysis-summary-failed-findings-kept", "analysis-both-sections-failed", "ExtractionResult", lambda x: x.update(extraction_status="failed",items=[],extraction_error=failed["error"]), rule="STRUCTURE", document="offset")
    changed("extraction-valid", "analysis-missing-extraction-provenance", "ExtractionResult", lambda x: x.update(extraction_provenance=None,prompt_version=None), rule="ITEM_COMPONENT", path="/extraction_provenance", document="offset")
    changed("summary-valid", "summary-unclaimed-text", "Summary", lambda x: x.update(text=x["text"]+" An additional statement."), rule="TEXT_CLAIMS", path="/text", document="offset")
    changed("answer-document", "answer-unclaimed-text", "AnswerResult", lambda x: x.update(text=x["text"]+" An additional statement."), rule="TEXT_CLAIMS", path="/text", document="offset")
    changed("answer-none", "answer-clarification", "AnswerResult", lambda x: x.update(clarification=clarification,text=clarification["message"]))
    changed("answer-mixed-sufficient", "answer-mixed-origins", "AnswerResult", lambda x: (x["components"][0].update(mode="live"),x.update(mode="mixed")), document="offset")
    changed("answer-mixed-origins", "answer-mixed-origins-hidden", "AnswerResult", lambda x: x.update(mode="live"), rule="MODE_PROVENANCE", path="/mode", document="offset")
    changed("answer-document", "answer-dangling-component", "AnswerResult", lambda x: x["claims"][0].update(component_id="missing"), rule="CLAIM_COMPONENT", path="/claims/0/component_id", document="offset")
    changed("answer-document", "answer-conflicting-prompt-version", "AnswerResult", lambda x: x.update(prompt_version="different-prompt"), rule="ROOT_VERSION", path="/prompt_version", document="offset")
    collision=deepcopy(payloads["answer-mixed-sufficient"])
    for source in collision["sources"]:
        prefix="a:" if source["kind"]=="literature" else "d:"
        old_id=source["source_id"]; source["source_id"]=prefix+"shared-source"
        for claim in collision["claims"]:
            claim["source_ids"]=[source["source_id"] if key==old_id else key for key in claim["source_ids"]]
    for claim in collision["claims"]:
        claim["claim_id"]=("a:" if claim["scope"]=="general_information" else "d:")+"shared-claim"
    add("answer-prefixed-local-id-collisions","AnswerResult",collision,"offset")
    crossed=deepcopy(collision);crossed["claims"][0]["source_ids"]=["d:shared-source","a:shared-source"]
    add("answer-cross-component-citation","AnswerResult",crossed,"offset",rule="CLAIM_COMPONENT",path="/claims/0/component_id")
    changed("answer-literature", "answer-missing-corpus-version", "AnswerResult", lambda x: x["components"][0].update(corpus_version=None), rule="STRUCTURE", path="/components/0/corpus_version")
    changed("retrieval-request-valid", "question-whitespace", "RetrievalRequest", lambda x: x.update(question=" \t\n"), rule="STRUCTURE", path="/question")
    add("request-id-invalid", "RequestId", "not-a-uuid", rule="STRUCTURE")
    return {"manifest.json": manifest, "payloads.json": payloads, "documents.json": documents, "references.json": references}


def transport_fixtures():
    error = {"schema_version":"1.0.0","request_id":REQUEST_ID,"error":{"code":"validation_failure","message":"The request is invalid.","retryable":False}}
    fallback_error=deepcopy(error);fallback_error["request_id"]=FALLBACK_ID
    def case(name, request, response, status=200, body=None, expected=None):
        return {"id":name,"request_headers":request,"response_headers":response,"status":status,"body":body,
                "expected":expected or [],"disposition":"accepted_result" if status==200 else "failed_call"}
    valid=[["X-Request-ID",REQUEST_ID]];fallback=[["X-Request-ID",FALLBACK_ID]]
    cases=[case("success-echo",valid,valid),case("failure-echo",valid,valid,422,error),
           case("missing-id-fallback",[],fallback,400,fallback_error),
           case("malformed-id-fallback",[["X-Request-ID","invalid"]],fallback,400,fallback_error),
           case("duplicate-id-fallback",valid+[["x-request-id",REQUEST_ID]],fallback,400,fallback_error),
           case("missing-response-id",valid,[],expected=["RESPONSE_ID"]),
           case("mismatched-response-id",valid,fallback,expected=["CORRELATION_MISMATCH"]),
           case("invalid-request-success",[],fallback,expected=["INVALID_REQUEST_SUCCESS"]),
           case("unsafe-response-id",[],[["X-Request-ID","invalid"]],400,fallback_error,expected=["RESPONSE_ID"]),
           case("error-body-id-mismatch",valid,valid,422,fallback_error,expected=["ERROR_CORRELATION"])]
    return {"cases":cases}


def encoded(value):
    return (json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8")


def assets():
    schema,api=schemas()
    result={"schema.json":encoded(schema),"openapi.json":encoded(api)}
    result.update({"fixtures/"+name:encoded(value) for name,value in fixtures().items()})
    result["transport-cases.json"]=encoded(transport_fixtures())
    base={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
          for path in sorted((ROOT/"contracts/v1").rglob("*")) if path.is_file()}
    manifest={"candidate_id":"p2-rc1","wire_version":"1.0.0","status":"awaiting_review",
              "p1_files":base,"generated_files":{name:hashlib.sha256(data).hexdigest() for name,data in sorted(result.items())},
              "review_files":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in REVIEW_FILES}}
    result["candidate.json"]=encoded(manifest)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="verify reproducibility without writing")
    args=parser.parse_args(argv)
    try:
        outputs=assets()
        if args.check:
            bad=[name for name,data in outputs.items() if not (CANDIDATE/name).is_file() or (CANDIDATE/name).read_bytes()!=data]
            if bad:
                print("FAIL: candidate drift: "+", ".join(bad));return 1
            print("PASS: candidate regeneration and review-file digests match");return 0
        for name,data in outputs.items():
            path=CANDIDATE/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        print(f"Wrote {len(outputs)} review-only candidate files; P1 unchanged")
        return 0
    except Exception:
        print("FAIL: CANDIDATE_BUILD; input/review files are missing or invalid; no payload details emitted")
        return 1


if __name__=="__main__":
    sys.exit(main())
