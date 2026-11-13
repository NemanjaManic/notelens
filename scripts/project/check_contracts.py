"""Validate the draft NoteLens contract and its synthetic acceptance fixtures.

This is offline tooling, not application ingestion or general clinical verification.
Diagnostics deliberately omit payloads and third-party exception messages.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import socket
import sys
import unicodedata
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from openapi_spec_validator import OpenAPIV31SpecValidator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_SCENARIOS = {
    "invalid-schema", "wrong-digest", "wrong-quote", "unicode-offsets",
    "repeated-span", "dangling-citation", "historical-assertion", "family-subject",
    "source-only-icd", "classification-states", "answer-routes", "retrieval-states",
}
REQUIRED_NEGATIVE_SCENARIOS = REQUIRED_SCENARIOS - {
    "classification-states", "answer-routes", "retrieval-states",
}
CASE_ID = re.compile(r"[a-z][a-z0-9-]{0,79}\Z")
OPERATIONS = {
    "/v1/classify": ("ClassificationRequest", "ClassificationResult"),
    "/v1/extract": ("ExtractionRequest", "ExtractionResult"),
    "/v1/document-answer": ("DocumentQuestionRequest", "AnswerResult"),
    "/v1/retrieve": ("RetrievalRequest", "RetrievalResult"),
    "/v1/literature-answer": ("LiteratureAnswerRequest", "AnswerResult"),
}


class CheckError(Exception):
    """An infrastructure/catalog error with a safe, fixed diagnostic."""


@dataclass(frozen=True, order=True)
class Issue:
    rule: str
    path: str


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


def contained(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise CheckError("LOCAL_PATH: expected a relative fixture path")
    resolved = (base / relative).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise CheckError("LOCAL_PATH: path escapes its permitted directory")
    return resolved


def read_json(path: Path):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(_value):
        raise ValueError("non-finite JSON number")

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number")
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                          parse_constant=reject_constant, parse_float=finite_float)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise CheckError("JSON_INPUT: missing, malformed, or ambiguous JSON file") from None


@contextmanager
def offline():
    """Deny outbound connections, including accidental reference retrieval."""
    def blocked(*_args, **_kwargs):
        raise OSError("Network access is disabled in contract checks")

    with patch.object(socket.socket, "connect", blocked), \
            patch.object(socket.socket, "connect_ex", blocked), \
            patch.object(socket.socket, "sendto", blocked), \
            patch.object(socket, "getaddrinfo", blocked), \
            patch.object(socket, "create_connection", blocked):
        yield


def no_remote_resource(uri):
    raise NoSuchResource(ref=uri)


class Contracts:
    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self.directory = self.root / "contracts/v1"
        self.schema = read_json(self.directory / "schema.json")
        self.api = read_json(self.directory / "openapi.json")
        if not isinstance(self.schema, dict) or not isinstance(self.api, dict):
            raise CheckError("SPECIFICATION: expected schema and OpenAPI objects")
        self.schema_id = self.schema.get("$id")
        if not isinstance(self.schema_id, str) or not self.schema_id.startswith("urn:"):
            raise CheckError("SPECIFICATION: expected the canonical schema identifier")
        self.check_schema(self.schema)
        self.check_refs(self.schema, self.directory / "schema.json")
        self.check_openapi(self.api)
        self.registry = Registry(retrieve=no_remote_resource).with_resource(
            self.schema_id, Resource.from_contents(self.schema))

    @staticmethod
    def check_schema(schema):
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError:
            raise CheckError("SCHEMA_INVALID: schema does not satisfy Draft 2020-12") from None

    def check_refs(self, value, source: Path):
        if isinstance(value, dict):
            if "$ref" in value:
                ref = value["$ref"]
                if not isinstance(ref, str):
                    raise CheckError("REFERENCE: invalid reference value")
                if ref.startswith("#"):
                    target = self.schema if source.name == "schema.json" else self.api
                    at_pointer(target, unquote(ref[1:]))
                elif ref.startswith(self.schema_id + "#"):
                    at_pointer(self.schema, unquote(ref.split("#", 1)[1]))
                else:
                    parsed = urlsplit(ref)
                    if parsed.scheme or parsed.netloc or parsed.query:
                        raise CheckError("REFERENCE: external reference is prohibited")
                    target_path = contained(self.directory, unquote(parsed.path))
                    if target_path != self.directory / "schema.json":
                        raise CheckError("REFERENCE: only the canonical schema file may be referenced")
                    at_pointer(self.schema, unquote(parsed.fragment))
            for child in value.values():
                self.check_refs(child, source)
        elif isinstance(value, list):
            for child in value:
                self.check_refs(child, source)

    def check_openapi(self, api):
        self.check_refs(api, self.directory / "openapi.json")
        if api.get("openapi") != "3.1.1":
            raise CheckError("OPENAPI_INVALID: expected OpenAPI 3.1.1")
        try:
            with offline():
                errors = list(OpenAPIV31SpecValidator(
                    api, base_uri=(self.directory / "openapi.json").as_uri()).iter_errors())
        except Exception:
            raise CheckError("OPENAPI_INVALID: validation or local resolution failed") from None
        if errors:
            raise CheckError("OPENAPI_INVALID: specification validation failed")
        for path, (request, response) in OPERATIONS.items():
            try:
                operation = api["paths"][path]["post"]
                request_schema = operation["requestBody"]["content"]["application/json"]["schema"]
                response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
            except (KeyError, TypeError):
                raise CheckError("OPENAPI_BINDING: required operation binding is missing") from None
            for value, definition in ((request_schema, request), (response_schema, response)):
                if value != {"$ref": "./schema.json#/$defs/" + definition}:
                    raise CheckError("OPENAPI_BINDING: operation must reference its canonical definition")

    def validate(self, payload, definition: str, document=None, reference=None) -> list[Issue]:
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


def load_suite(contracts: Contracts):
    directory = contracts.directory / "fixtures"
    manifest = read_json(directory / "manifest.json")
    payloads = read_json(directory / "payloads.json")
    documents = read_json(directory / "documents.json")
    references = read_json(directory / "references.json")
    if not isinstance(manifest, dict) or set(manifest) != {"catalog_version", "cases"} or \
            manifest["catalog_version"] != 1 or not isinstance(manifest["cases"], list) or not manifest["cases"]:
        raise CheckError("CATALOG: expected a nonempty version-1 fixture catalog")
    if not all(isinstance(value, dict) for value in (payloads, documents, references)):
        raise CheckError("CATALOG: expected fixture object maps")
    for document in documents.values():
        if contracts.validate(document, "PreparedDocument"):
            raise CheckError("CATALOG: invalid document context")
    for reference in references.values():
        if not isinstance(reference, dict) or not reference or set(reference) - {"attributes", "spans"}:
            raise CheckError("CATALOG: invalid reference annotations")
        if not all(isinstance(values, dict) for values in reference.values()):
            raise CheckError("CATALOG: expected pointer-to-value annotation maps")
    ids, positives, scenarios, negative_scenarios = set(), set(), set(), set()
    used_documents, used_references = set(), set()
    for case in manifest["cases"]:
        if not isinstance(case, dict) or set(case) - {
                "id", "kind", "definition", "document", "reference", "expected", "scenarios"} or \
                not {"id", "kind", "expected", "scenarios"} <= case.keys():
            raise CheckError("CATALOG: malformed case metadata")
        case_id = case["id"]
        if not isinstance(case_id, str) or not CASE_ID.fullmatch(case_id) or case_id in ids:
            raise CheckError("CATALOG: invalid or duplicate case identifier")
        ids.add(case_id)
        if case_id not in payloads:
            raise CheckError("CATALOG: payload missing for a case")
        if case["kind"] not in {"payload", "schema", "openapi"}:
            raise CheckError("CATALOG: invalid case kind")
        expected = case["expected"]
        if not isinstance(expected, list) or any(
                not isinstance(item, dict) or set(item) != {"rule", "path"} or
                not all(isinstance(item[key], str) for key in item) or not item["rule"] or
                (item["path"] and not item["path"].startswith("/")) for item in expected):
            raise CheckError("CATALOG: expected exact rule/path outcome list")
        if len({(item["rule"], item["path"]) for item in expected}) != len(expected):
            raise CheckError("CATALOG: duplicate expected diagnostic")
        if not isinstance(case["scenarios"], list) or any(
                not isinstance(tag, str) or not CASE_ID.fullmatch(tag) for tag in case["scenarios"]):
            raise CheckError("CATALOG: invalid scenario tags")
        scenarios.update(case["scenarios"])
        if expected:
            negative_scenarios.update(case["scenarios"])
        if case["kind"] == "payload":
            definition = case.get("definition")
            if definition not in contracts.schema["$defs"]:
                raise CheckError("CATALOG: unknown target definition")
            if not expected:
                positives.add(definition)
        elif "definition" in case or "document" in case or "reference" in case:
            raise CheckError("CATALOG: schema/API cases cannot carry payload context")
        if "document" in case:
            if case["document"] not in documents:
                raise CheckError("CATALOG: missing document context")
            used_documents.add(case["document"])
        if "reference" in case:
            if case["reference"] not in references:
                raise CheckError("CATALOG: missing reference annotations")
            used_references.add(case["reference"])
    if ids != payloads.keys() or used_documents != documents.keys() or used_references != references.keys():
        raise CheckError("CATALOG: orphaned payload, document, or reference")
    if positives != contracts.schema["$defs"].keys() or not REQUIRED_SCENARIOS <= scenarios or \
            not REQUIRED_NEGATIVE_SCENARIOS <= negative_scenarios:
        raise CheckError("CATALOG: incomplete definition or required scenario coverage")
    return manifest["cases"], payloads, documents, references


def run_suite(contracts: Contracts):
    cases, payloads, documents, references = load_suite(contracts)
    failures, positive_count = [], 0
    for case in cases:
        payload = payloads[case["id"]]
        if case["kind"] == "payload":
            actual = contracts.validate(payload, case["definition"],
                                        documents.get(case.get("document")),
                                        references.get(case.get("reference")))
        else:
            try:
                if case["kind"] == "schema":
                    contracts.check_schema(payload)
                else:
                    contracts.check_openapi(payload)
                actual = []
            except CheckError as error:
                actual = [Issue(str(error).split(":", 1)[0], "")]
        expected = sorted(Issue(**item) for item in case["expected"])
        if actual != expected:
            failures.append((case["id"], actual, expected))
        positive_count += not expected
    return len(cases), positive_count, failures


def fixture_digest(directory: Path) -> str:
    # Hash relative filenames and exact bytes, including catalog expectations and documentation.
    entries = {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted(directory.rglob("*")) if path.is_file()}
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def freeze_digests(contracts: Contracts) -> dict:
    return {
        "schema_sha256": hashlib.sha256((contracts.directory / "schema.json").read_bytes()).hexdigest(),
        "openapi_sha256": hashlib.sha256((contracts.directory / "openapi.json").read_bytes()).hexdigest(),
        "fixtures_sha256": fixture_digest(contracts.directory / "fixtures"),
    }


def require_freeze(contracts: Contracts):
    record_path = contracts.directory / "freeze.json"
    if not record_path.is_file():
        raise CheckError("FREEZE_PENDING: no recorded A/B/C/D contract agreement")
    record = read_json(record_path)
    keys = {"schema_version", "schema_sha256", "openapi_sha256", "fixtures_sha256", "approvals"}
    if not isinstance(record, dict) or set(record) != keys:
        raise CheckError("FREEZE_RECORD: malformed freeze record")
    version = contracts.schema["$defs"]["PreparedDocument"]["properties"]["schema_version"]["const"]
    if record["schema_version"] != version or record["schema_version"] != contracts.api["info"]["version"]:
        raise CheckError("FREEZE_VERSION: reviewed version does not match the proposals")
    if any(record[key] != value for key, value in freeze_digests(contracts).items()):
        raise CheckError("FREEZE_DIGEST: reviewed bytes no longer match")
    approvals = record["approvals"]
    if not isinstance(approvals, list) or len(approvals) != 4:
        raise CheckError("FREEZE_APPROVALS: dated A/B/C/D approvals are required")
    members = set()
    for approval in approvals:
        if not isinstance(approval, dict) or set(approval) != {"member", "decision", "date", "evidence"} or \
                not isinstance(approval["member"], str) or approval["member"] not in {"A", "B", "C", "D"} or \
                approval["member"] in members or approval["decision"] != "approved":
            raise CheckError("FREEZE_APPROVALS: missing, duplicate, or unapproved owner")
        members.add(approval["member"])
        try:
            if not isinstance(approval["date"], str) or date.fromisoformat(approval["date"]).isoformat() != approval["date"]:
                raise ValueError
        except ValueError:
            raise CheckError("FREEZE_APPROVALS: expected an ISO approval date") from None
        evidence = approval["evidence"]
        if not isinstance(evidence, str) or not evidence.startswith("docs/decisions/contract-freeze.md#"):
            raise CheckError("FREEZE_EVIDENCE: expected a decision-record section reference")
        relative, fragment = evidence.split("#", 1)
        evidence_path = contained(contracts.root, relative)
        try:
            content = evidence_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise CheckError("FREEZE_EVIDENCE: decision record is missing or unreadable") from None
        anchor = "member-" + approval["member"].lower()
        if fragment != anchor or not re.search(r"^#{1,6} Member " + approval["member"] + r"\s*$", content, re.M):
            raise CheckError("FREEZE_EVIDENCE: owner decision section does not resolve")


def canonical_contracts():
    from frozen_contracts import FrozenContracts
    return FrozenContracts()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-freeze", action="store_true", help="also require recorded owner agreement")
    args = parser.parse_args(argv)
    try:
        with offline():
            contracts = canonical_contracts()
            total, positives, failures = run_suite(contracts)
            for case_id, actual, expected in failures:
                describe = lambda issues: ",".join(item.rule + "@" + (item.path or "/") for item in issues) or "valid"
                print(f"FAIL {case_id}: actual={describe(actual)} expected={describe(expected)}")
            if failures:
                print(f"FAIL: {len(failures)}/{total} fixture outcomes differ")
                return 1
            print(f"PASS: schema/OpenAPI and {total}/{total} fixture outcomes ({positives} positive, {total-positives} negative)")
            if args.require_freeze:
                require_freeze(contracts)
                from check_candidate import check_transport
                count, failures = check_transport(contracts)
                if failures:
                    raise CheckError("TRANSPORT: correlation outcome mismatch")
                print(f"PASS: {count} simulated correlation outcomes; no HTTP server called")
                print("PASS: recorded freeze consistency; human consent must still be reviewed")
            else:
                print("CHECKED: payloads only; use --require-freeze for recorded owner/digest consistency; no HTTP/model evaluation")
    except CheckError as error:
        print("FAIL: " + str(error))
        return 1
    except Exception:
        print("FAIL: CHECK_INFRASTRUCTURE; no payload or exception details emitted")
        return 1
    return 0


if __name__ == "__main__":
    # Canonical validators import this shared module; preserve exception/Issue identity.
    sys.modules["check_contracts"] = sys.modules[__name__]
    sys.exit(main())
