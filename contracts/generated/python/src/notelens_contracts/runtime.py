# Generated from the canonical schema and shared Python semantic validator sources.
from __future__ import annotations
from contextlib import nullcontext
from dataclasses import dataclass
import hashlib, json, math, re, unicodedata
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

class CheckError(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Issue:
    rule: str
    path: str

offline = nullcontext
def deny_remote(uri):
    raise NoSuchResource(ref=uri)

def rendered(value, fallback):
    return "\n\n".join(claim['text'] for claim in value['claims']) if value['claims'] else fallback

builder = SimpleNamespace(LABELS=['Cardiovascular / Pulmonary', 'Orthopedic', 'Gastroenterology', 'Neurology', 'Urology'], NO_ANSWER='The available sources do not support an answer.', NO_SUMMARY='The available document evidence does not support a summary.', rendered=rendered)

def pointer(parts) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)

def at_pointer(value, path: str):
    if path == "":
        return value
    if not path.startswith("/"):
        raise CheckError("REFERENCE_POINTER: expected a JSON pointer")
    try:
        for token in path[1:].split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            value = value[int(token)] if isinstance(value, list) else value[token]
        return value
    except (KeyError, IndexError, ValueError, TypeError):
        raise CheckError("REFERENCE_POINTER: fixture reference does not resolve") from None

class RuntimeValidator:
    def __init__(self):
        self.schema = json.loads(Path(__file__).with_name('schema.json').read_text(encoding='utf-8'))
        self.schema_id = self.schema['$id']
        self.registry = Registry(retrieve=deny_remote).with_resource(self.schema_id, Resource.from_contents(self.schema))

    def _base_validate(self, payload, definition: str, document=None, reference=None) -> list[Issue]:
            if definition not in self.schema.get("$defs", {}):
                raise CheckError("DEFINITION: unknown schema definition")
            validator = Draft202012Validator(
                {"$ref": self.schema_id + "#/$defs/" + definition},
                registry=self.registry, format_checker=FormatChecker())
            with offline():
                errors = list(validator.iter_errors(payload))
            if errors:
                return sorted({Issue("STRUCTURE", pointer(error.absolute_path)) for error in errors})
            issues = []
            if definition == "PreparedDocument":
                document = payload
            elif isinstance(payload, dict) and "document" in payload:
                embedded = payload["document"]
                issues.extend(Issue(issue.rule, "/document" + issue.path)
                              for issue in self.validate(embedded, "PreparedDocument"))
                if issues:
                    return sorted(set(issues))
                if document is not None and (embedded["doc_id"], embedded["text_sha256"]) != (
                        document["doc_id"], document["text_sha256"]):
                    issues.append(Issue("DOCUMENT_IDENTITY", "/document"))
                document = embedded

            if document is not None and definition != "PreparedDocument":
                if self.validate(document, "PreparedDocument"):
                    raise CheckError("DOCUMENT_CONTEXT: context must be a valid prepared document")

            def issue(rule, path):
                issues.append(Issue(rule, path))

            def span(value, path):
                if document is None:
                    raise CheckError("DOCUMENT_CONTEXT: evidence requires document context")
                start, end, quote = value["start"], value["end"], value["quote"]
                if not 0 <= start < end <= len(document["text"]):
                    issue("SPAN_BOUNDS", path)
                elif document["text"][start:end] != quote:
                    issue("SPAN_QUOTE", path)

            def unique(values, key, path):
                ids = [value[key] for value in values]
                if len(ids) != len(set(ids)):
                    issue("DUPLICATE_ID", path)

            def walk(value, path=""):
                if isinstance(value, list):
                    for index, child in enumerate(value):
                        walk(child, path + "/" + str(index))
                    return
                if not isinstance(value, dict):
                    return
                if {"canonicalization_version", "text_sha256", "text"} <= value.keys():
                    text = value["text"]
                    valid_unicode = not any(0xD800 <= ord(char) <= 0xDFFF for char in text)
                    if not valid_unicode:
                        issue("TEXT_UNICODE", path + "/text")
                    elif not text.strip() or "\r" in text or \
                            unicodedata.normalize("NFC", text) != text:
                        issue("TEXT_CANONICAL", path + "/text")
                    if valid_unicode and hashlib.sha256(text.encode("utf-8")).hexdigest() != value["text_sha256"]:
                        issue("TEXT_DIGEST", path + "/text_sha256")
                if {"doc_id", "text_sha256"} <= value.keys() and document is not None:
                    if (value["doc_id"], value["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
                        issue("DOCUMENT_IDENTITY", path)
                if {"start", "end", "quote"} <= value.keys():
                    span(value, path)
                if {"score_kind", "scores"} <= value.keys():
                    categories = [score["category"] for score in value["scores"]]
                    if len(categories) != len(set(categories)):
                        issue("CATEGORY_UNIQUE", path + "/scores")
                if "items" in value and isinstance(value["items"], list):
                    unique(value["items"], "entity_id", path + "/items")
                if "icd" in value:
                    code = value["icd"]["code"]
                    if not re.search(r"(?<![\w.])" + re.escape(code) + r"(?!\w|\.\w)",
                                     value["icd"]["evidence"]["quote"]):
                        issue("ICD_SOURCE", path + "/icd/code")
                if {"claims", "sources"} <= value.keys():
                    unique(value["claims"], "claim_id", path + "/claims")
                    unique(value["sources"], "source_id", path + "/sources")
                    sources = {source["source_id"]: source for source in value["sources"]}
                    for index, claim in enumerate(value["claims"]):
                        claim_path = path + "/claims/" + str(index)
                        if any(key not in sources for key in claim["source_ids"]):
                            issue("CITATION_MISSING", claim_path + "/source_ids")
                        elif claim["scope"] == "document_fact" and not any(
                                sources[key]["kind"] == "document" for key in claim["source_ids"]):
                            issue("CLAIM_PROVENANCE", claim_path + "/source_ids")
                    if value["evidence_state"] == "partial" and not value["warnings"]:
                        issue("PARTIAL_GAP", path + "/warnings")
                if "passages" in value:
                    unique(value["passages"], "source_id", path + "/passages")
                for key, child in value.items():
                    walk(child, path + pointer([key]))

            walk(payload)
            # Gold comparisons apply only to curated fixtures, never to arbitrary clinical text.
            if reference is not None:
                for path, expected in reference.get("attributes", {}).items():
                    if at_pointer(payload, path) != expected:
                        issue("REFERENCE_ATTRIBUTE", path)
                for path, expected in reference.get("spans", {}).items():
                    if at_pointer(payload, path) != expected:
                        issue("REFERENCE_SPAN", path)
            return sorted(set(issues))

    def validate(self, payload, definition, document=None, reference=None):
            # JSON syntax excludes these values; direct Python model results need the same guard.
            finite_issues = []
            def finite_numbers(value, path=""):
                if isinstance(value, float) and not math.isfinite(value):
                    finite_issues.append(Issue("NUMBER_FINITE", path))
                elif isinstance(value, dict):
                    for key, child in value.items():
                        token = str(key).replace("~", "~0").replace("/", "~1")
                        finite_numbers(child, path + "/" + token)
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        finite_numbers(child, path + f"/{index}")
            finite_numbers(payload)
            if finite_issues:
                return sorted(set(finite_issues))
            issues = self._base_validate(payload, definition, document, reference)
            if issues:
                return issues
            issues = []
            def issue(rule, path):
                issues.append(Issue(rule, path))

            def mode_matches(mode, components, path):
                modes = {record["mode"] for record in components}
                expected = "mixed" if len(modes) > 1 else next(iter(modes), None)
                if (expected is not None and mode != expected) or (not modes and mode == "mixed"):
                    issue("MODE_PROVENANCE", path + "/mode")

            def graph(value, records, path):
                ids = [record["component_id"] for record in records]
                if len(ids) != len(set(ids)):
                    issue("DUPLICATE_COMPONENT", path + "/components")
                components = {record["component_id"]: record for record in records}
                sources = {source["source_id"]: source for source in value["sources"]}
                for index, source in enumerate(value["sources"]):
                    record = components.get(source["component_id"])
                    if record is None:
                        issue("SOURCE_COMPONENT", path + f"/sources/{index}/component_id")
                    elif (record["service"] == "rag") != (source["kind"] == "literature"):
                        issue("SOURCE_ORIGIN", path + f"/sources/{index}/component_id")
                for index, claim in enumerate(value["claims"]):
                    record = components.get(claim["component_id"])
                    if record is None:
                        issue("CLAIM_COMPONENT", path + f"/claims/{index}/component_id")
                        continue
                    if any(sources[key]["component_id"] != claim["component_id"] for key in claim["source_ids"]):
                        issue("CLAIM_COMPONENT", path + f"/claims/{index}/component_id")
                    scope = "general_information" if record["service"] == "rag" else "document_fact"
                    if claim["scope"] != scope:
                        issue("COMPONENT_SCOPE", path + f"/claims/{index}/scope")

            def walk(value, path=""):
                if isinstance(value, list):
                    for index, child in enumerate(value):
                        walk(child, path + f"/{index}")
                    return
                if not isinstance(value, dict):
                    return
                if "classification_execution" in value:
                    if value["scores"] and [score["category"] for score in value["scores"]] != builder.LABELS:
                        issue("CATEGORY_ORDER", path + "/scores")
                    if value["status"] == "unsupported" and value["mode"] != "mock":
                        issue("SCOPE_POLICY_UNAPPROVED", path + "/scope_policy_version")
                if "mention" in value:
                    mention = value["mention"]
                    if not any(span["start"] <= mention["start"] < mention["end"] <= span["end"] for span in value["evidence"]):
                        issue("MENTION_EVIDENCE", path + "/mention")
                if {"claims", "sources", "text"} <= value.keys():
                    if "components" in value:
                        records = value["components"]
                        graph(value, records, path)
                        retrieval = value["retrieval_provenance"]
                        mode_matches(value["mode"], records + ([retrieval] if retrieval else []), path)
                        rag_records = [(index, record) for index, record in enumerate(records) if record["service"] == "rag"]
                        if rag_records and retrieval is None:
                            issue("RETRIEVAL_PROVENANCE", path + "/retrieval_provenance")
                        if retrieval:
                            if "literature" not in value["attempted_routes"]:
                                issue("RETRIEVAL_ATTEMPT", path + "/attempted_routes")
                            if retrieval["state"] == "insufficient" and rag_records:
                                issue("RETRIEVAL_GENERATION", path + "/components")
                            for index, record in rag_records:
                                for key in ("corpus_version", "index_version", "retriever_version"):
                                    if record[key] != retrieval[key]:
                                        issue("RETRIEVAL_VERSION", path + f"/components/{index}/{key}")
                        expected = value["clarification"]["message"] if value["clarification"] else builder.NO_ANSWER
                        if value["route"] != "none" and not value["claims"]:
                            issue("ROUTE_SUPPORT", path + "/route")
                        kinds = {source["kind"] for source in value["sources"]}
                        if not kinds <= set(value["attempted_routes"]):
                            issue("ATTEMPTED_ROUTE", path + "/attempted_routes")
                        if any(record["operation"] not in {"document-answer", "literature-answer"} for record in records):
                            issue("ANSWER_OPERATION", path + "/components")
                        if value["route"]=="mixed":
                            if value["prompt_version"] is not None:
                                issue("ROOT_VERSION",path+"/prompt_version")
                            if value["answer_version"]!="notelens-compose-v1":
                                issue("ROOT_VERSION",path+"/answer_version")
                            for record in records:
                                prefix="a:" if record["service"]=="rag" else "d:"
                                related=[record["component_id"]]
                                related.extend(source["source_id"] for source in value["sources"] if source["component_id"]==record["component_id"])
                                related.extend(claim["claim_id"] for claim in value["claims"] if claim["component_id"]==record["component_id"])
                                if any(not key.startswith(prefix) for key in related):
                                    issue("ID_NAMESPACE",path+"/components")
                        elif len(records)==1:
                            if value["answer_version"]!=records[0]["output_version"]:
                                issue("ROOT_VERSION",path+"/answer_version")
                            if value["prompt_version"]!=records[0]["prompt_version"]:
                                issue("ROOT_VERSION",path+"/prompt_version")
                        elif not records and value["prompt_version"] is not None:
                            issue("ROOT_VERSION",path+"/prompt_version")
                    else:
                        records = [value["provenance"]] if value["provenance"] else []
                        graph(value, records, path)
                        expected = builder.NO_SUMMARY
                        if records and (records[0]["service"], records[0]["operation"]) != ("extraction", "summarize"):
                            issue("SUMMARY_OPERATION", path + "/provenance")
                    if value["text"] != builder.rendered(value, expected):
                        issue("TEXT_CLAIMS", path + "/text")
                if "extraction_status" in value:
                    record = value["extraction_provenance"]
                    if value["items"] and (record is None or any(item["component_id"] != record["component_id"] for item in value["items"])):
                        issue("ITEM_COMPONENT", path + "/extraction_provenance")
                    if record and (record["service"], record["operation"]) != ("extraction", "extract"):
                        issue("EXTRACTION_OPERATION", path + "/extraction_provenance")
                    if record and record["output_version"]!=value["extractor_version"]:
                        issue("ROOT_VERSION",path+"/extractor_version")
                    if record and record["prompt_version"]!=value["prompt_version"]:
                        issue("ROOT_VERSION",path+"/prompt_version")
                    if record is None and value["prompt_version"] is not None:
                        issue("ROOT_VERSION",path+"/prompt_version")
                    result = value["summary"]["result"]
                    summary_record = result["provenance"] if result else None
                    mode_matches(value["mode"], [entry for entry in [record, summary_record] if entry], path)
                for key, child in value.items():
                    walk(child, path + "/" + key)
            walk(payload)
            return sorted(set(issues))

VALIDATOR = RuntimeValidator()

class ContractValidationError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__('Contract validation failed: ' + ', '.join(item.rule + '@' + (item.path or '/') for item in issues))

def validate_record(definition, payload, *, document=None, reference=None):
    issues = VALIDATOR.validate(payload, definition, document, reference)
    if issues:
        raise ContractValidationError(issues)
    return payload

def validate_json(definition, text, *, document=None, reference=None):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Nonstandard JSON number')
    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Non-finite JSON number')
        return result
    try:
        payload = json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite)
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ContractValidationError([Issue('JSON_INPUT', '')]) from None
    return validate_record(definition, payload, document=document, reference=reference)


def request_id(headers):
    values = [value for name, value in headers if name.lower() == "x-request-id"]
    if len(values) != 1 or not isinstance(values[0], str):
        return None
    try:
        value = str(UUID(values[0]))
        return value if value == values[0] else None
    except (ValueError, AttributeError):
        return None

def validate_exchange(case, contracts=VALIDATOR):
    incoming = request_id(case["request_headers"])
    outgoing = request_id(case["response_headers"])
    if outgoing is None:
        return ["RESPONSE_ID"]
    # Health fixtures cover authentication errors; business-header admission does not apply.
    if case.get("path") in {"/health/live", "/health/ready"}:
        if case["status"] != 401:
            return ["HEALTH_AUTH_STATUS"]
        challenges = [value for name, value in case["response_headers"] if name.lower() == "www-authenticate"]
        if challenges != ["Bearer"]:
            return ["AUTH_CHALLENGE"]
        body = case["body"]
        if contracts.validate(body, "ErrorEnvelope"):
            return ["ERROR_ENVELOPE"]
        if body["request_id"] != outgoing:
            return ["ERROR_CORRELATION"]
        if body["error"]["code"] != "unauthorized" or body["error"]["retryable"]:
            return ["HEALTH_AUTH_ERROR"]
        if any(name.lower() == "x-request-id" and value == outgoing for name, value in case["request_headers"]):
            return ["HEALTH_AUTH_ID_REUSED"]
        return [] if case["disposition"] == "failed_call" else ["CALL_DISPOSITION"]
    if incoming is None:
        if case["status"] == 200:
            return ["INVALID_REQUEST_SUCCESS"]
        if case["status"] != 400:
            return ["INVALID_REQUEST_STATUS"]
    elif outgoing != incoming:
        return ["CORRELATION_MISMATCH"]
    if case["status"] != 200:
        body = case["body"]
        if contracts.validate(body, "ErrorEnvelope"):
            return ["ERROR_ENVELOPE"]
        if body["request_id"] != outgoing:
            return ["ERROR_CORRELATION"]
        if incoming is None and body["error"]["code"] != "validation_failure":
            return ["INVALID_REQUEST_ERROR"]
    disposition = "accepted_result" if case["status"] == 200 else "failed_call"
    return [] if case["disposition"] == disposition else ["CALL_DISPOSITION"]
