"""Execute P2 RC1 review checks without changing or approving canonical P1."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from uuid import UUID

from referencing import Registry, Resource

from check_contracts import (
    ROOT, CheckError, Contracts, Issue, no_remote_resource, offline, read_json, run_suite,
)
import build_candidate as builder


class CandidateContracts(Contracts):
    def __init__(self):
        self.root = ROOT
        self.directory = builder.CANDIDATE
        self.schema = read_json(self.directory / "schema.json")
        self.api = read_json(self.directory / "openapi.json")
        self.schema_id = self.schema["$id"]
        if self.schema_id != "urn:notelens:contracts:candidates:p2-rc1":
            raise CheckError("CANDIDATE_ID: wrong candidate schema")
        self.check_schema(self.schema)
        self.check_refs(self.schema, self.directory / "schema.json")
        self.check_openapi(self.api)
        self.registry = Registry(retrieve=no_remote_resource).with_resource(
            self.schema_id, Resource.from_contents(self.schema))

    def check_openapi(self, api):
        super().check_openapi(api)
        if api.get("x-candidate-id") != "p2-rc1":
            raise CheckError("CANDIDATE_ID: wrong API candidate")
        for operation in api["paths"].values():
            if "post" not in operation:
                continue
            post = operation["post"]
            params = [p for p in post.get("parameters", []) if p.get("in") == "header" and p.get("name") == "X-Request-ID"]
            if len(params) != 1 or not params[0].get("required") or params[0].get("schema") != {"$ref": "./schema.json#/$defs/RequestId"}:
                raise CheckError("CORRELATION_BINDING: missing required UUID header")
            if "500" not in post["responses"]:
                raise CheckError("ERROR_BINDING: missing internal-error response")
            for response in post["responses"].values():
                header = response.get("headers", {}).get("X-Request-ID", {})
                if not header.get("required") or header.get("schema") != {"$ref": "./schema.json#/$defs/RequestId"}:
                    raise CheckError("CORRELATION_BINDING: missing response UUID header")
        for path, definition in [("/health/live", "LivenessResult"), ("/health/ready", "HealthResult")]:
            try:
                output = api["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
            except KeyError:
                raise CheckError("HEALTH_BINDING: missing health operation") from None
            if output != {"$ref": "./schema.json#/$defs/" + definition}:
                raise CheckError("HEALTH_BINDING: wrong health record")
            auth = api["paths"][path]["get"]["responses"].get("401", {})
            if auth.get("content", {}).get("application/json", {}).get("schema") != {"$ref": "./schema.json#/$defs/ErrorEnvelope"}:
                raise CheckError("HEALTH_AUTH_BINDING: missing health authentication envelope")
            for name, schema in [("X-Request-ID", {"$ref": "./schema.json#/$defs/RequestId"}), ("WWW-Authenticate", {"const": "Bearer"})]:
                header = auth.get("headers", {}).get(name, {})
                if not header.get("required") or header.get("schema") != schema:
                    raise CheckError("HEALTH_AUTH_BINDING: missing diagnostic ID or authentication challenge")

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
        issues = super().validate(payload, definition, document, reference)
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


def request_id(headers):
    values = [value for name, value in headers if name.lower() == "x-request-id"]
    if len(values) != 1 or not isinstance(values[0], str):
        return None
    try:
        value = str(UUID(values[0]))
        return value if value == values[0] else None
    except (ValueError, AttributeError):
        return None


def validate_exchange(case, contracts):
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


def check_transport(contracts):
    catalog = read_json(contracts.directory / "transport-cases.json")
    if not isinstance(catalog, dict) or set(catalog) != {"cases"} or not catalog["cases"]:
        raise CheckError("TRANSPORT_CATALOG: expected nonempty case list")
    counts = Counter(case["id"] for case in catalog["cases"])
    if any(count != 1 for count in counts.values()):
        raise CheckError("TRANSPORT_CATALOG: duplicate case")
    failures = []
    for case in catalog["cases"]:
        actual = validate_exchange(case, contracts)
        if actual != case["expected"]:
            failures.append((case["id"], actual, case["expected"]))
    return len(catalog["cases"]), failures


def verify_candidate():
    for name, expected in builder.assets().items():
        path = builder.CANDIDATE / name
        if not path.is_file() or path.read_bytes() != expected:
            raise CheckError("CANDIDATE_DRIFT: generated assets or reviewed files changed; regenerate and review again")
    manifest = read_json(builder.CANDIDATE / "candidate.json")
    for name, digest in manifest["p1_files"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise CheckError("P1_CHANGED: canonical baseline does not match the candidate")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-freeze", action="store_true")
    args = parser.parse_args(argv)
    try:
        with offline():
            verify_candidate()
            contracts = CandidateContracts()
            total, positives, failures = run_suite(contracts)
            transport_total, transport_failures = check_transport(contracts)
            for case_id, actual, expected in failures:
                describe = lambda values: ",".join(value.rule + "@" + (value.path or "/") for value in values) or "valid"
                print(f"FAIL {case_id}: actual={describe(actual)} expected={describe(expected)}")
            for case_id, actual, expected in transport_failures:
                print(f"FAIL {case_id}: actual={','.join(actual)} expected={','.join(expected)}")
            if failures or transport_failures:
                return 1
            print(f"PASS: candidate schema/API and {total}/{total} payload outcomes ({positives} positive, {total-positives} negative)")
            print(f"PASS: {transport_total}/{transport_total} simulated correlation outcomes; no HTTP server was called")
            if args.require_freeze:
                raise CheckError("CANDIDATE_NOT_CANONICAL: owner approval and promotion are required; F-003/F-009 remain open")
            digest = hashlib.sha256((builder.CANDIDATE / "candidate.json").read_bytes()).hexdigest()
            print("REVIEW ONLY: p2-rc1 manifest SHA256=" + digest)
        return 0
    except CheckError as error:
        print("FAIL: " + str(error)); return 1
    except Exception:
        print("FAIL: CANDIDATE_INFRASTRUCTURE; no payload/exception details emitted"); return 1


if __name__ == "__main__":
    sys.exit(main())
