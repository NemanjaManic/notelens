"""D-owned contract and local-transport readiness probe; shared contracts remain B-owned."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from notelens_extraction.contracts import SCHEMA_PATH, schema, validate_extraction, validate_generation, validate_schema
from notelens_extraction.demo import request as demo_answer
from notelens_extraction.evidence import validate_span, validate_text

ROOT = Path(__file__).resolve().parents[3]
OPENAPI_PATH = ROOT / "contracts/v1/openapi.json"
FIXTURE_EXTRACT = ROOT / "services/extraction/fixtures/demo-request.json"
FIXTURE_ANSWER = ROOT / "services/extraction/fixtures/demo-question.json"


def _ref_target(ref: str) -> tuple[Path, str]:
    file_part, fragment = ref.split("#", 1) if "#" in ref else (ref, "")
    path = (SCHEMA_PATH.parent / file_part).resolve() if file_part else SCHEMA_PATH.resolve()
    if path not in {SCHEMA_PATH.resolve(), OPENAPI_PATH.resolve()}:
        raise ValueError("Contract reference points outside the v1 contract directory.")
    return path, fragment.removeprefix("/")


def inspect_contracts() -> dict:
    schema_obj = schema()
    Draft202012Validator.check_schema(schema_obj)
    openapi = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    refs: list[str] = []

    def visit(value):
        if isinstance(value, dict):
            ref = value.get("$ref")
            if ref:
                refs.append(ref)
                try:
                    path, fragment = _ref_target(ref)
                    target = json.loads(path.read_text(encoding="utf-8"))
                    node = target
                    for segment in fragment.split("/") if fragment else []:
                        node = node[segment.replace("~1", "/").replace("~0", "~")]
                    if not isinstance(node, dict):
                        raise ValueError("Reference target is not an object")
                except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
                    errors.append(f"unresolved_ref:{ref}:{type(exc).__name__}")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(openapi)
    if openapi.get("openapi") != "3.1.1":
        errors.append("unexpected_openapi_version")
    operations = {}
    for path, path_item in openapi.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head", "trace"}:
                continue
            operation_id = operation.get("operationId")
            if not operation_id or operation_id in operations:
                errors.append(f"missing_or_duplicate_operation_id:{operation_id}")
            else:
                operations[operation_id] = (path, method.lower())
    expected = {
        "extraction_extract": ("/v1/extract", "post", "ExtractionRequest", "ExtractionResult"),
        "extraction_document_answer": ("/v1/document-answer", "post", "DocumentQuestionRequest", "AnswerResult"),
    }
    checked = []
    for operation_id, (path, method, input_name, output_name) in expected.items():
        actual = operations.get(operation_id)
        if actual != (path, method):
            errors.append(f"operation_mismatch:{operation_id}:{actual}")
            continue
        operation = openapi["paths"][path][method]
        try:
            request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
            response_ref = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            for ref, name in ((request_ref, input_name), (response_ref, output_name)):
                target_path, fragment = _ref_target(ref)
                if target_path.resolve() != SCHEMA_PATH.resolve() or fragment != f"$defs/{name}":
                    errors.append(f"wrong_schema_binding:{operation_id}:{ref}")
            checked.append(operation_id)
        except (KeyError, ValueError) as exc:
            errors.append(f"missing_operation_schema:{operation_id}:{type(exc).__name__}")
    return {"status": "pass" if not errors else "fail", "schema_draft": schema_obj.get("$schema"),
            "openapi_version": openapi.get("openapi"), "schema_sha256": hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest(),
            "openapi_sha256": hashlib.sha256(OPENAPI_PATH.read_bytes()).hexdigest(),
            "openapi_refs": len(refs), "resolved_refs": len(refs) - sum("unresolved_ref:" in e for e in errors),
            "checked_d_operations": checked, "errors": errors,
            "contract_status": "draft-provisional; no freeze implied"}


def _validate_fixture(request: dict, expected_input: str, operation: str) -> dict:
    validate_schema(request, expected_input)
    document = request["document"]
    validate_text(document["text"], document["text_sha256"])
    return document


def _validate_success(payload: dict, document: dict, operation: str) -> None:
    if operation == "extract":
        validate_extraction(payload, document)
        return
    validate_schema(payload, "AnswerResult")
    validate_generation(payload, document, answer=True)


def _http_json(base: str, path: str, *, payload: dict | None = None, headers: dict | None = None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, json.loads(exc.read())


def probe_http() -> dict:
    extract_request = json.loads(FIXTURE_EXTRACT.read_text(encoding="utf-8"))
    answer_request = json.loads(FIXTURE_ANSWER.read_text(encoding="utf-8"))
    extract_doc = _validate_fixture(extract_request, "ExtractionRequest", "extract")
    answer_doc = _validate_fixture(answer_request, "DocumentQuestionRequest", "answer")
    if extract_doc != answer_doc:
        raise ValueError("The D extraction demo request and question must use the same prepared document.")
    document = extract_doc
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NOTELENS_MODE": "mock"}
    env.pop("NOTELENS_SERVICE_TOKEN", None)
    process = subprocess.Popen([sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)],
                               cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    checks = []

    def record(name: str, ok: bool, detail: str):
        checks.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})
        if not ok:
            raise AssertionError(f"Readiness check failed: {name}")

    try:
        for _ in range(100):
            try:
                status, headers, health = _http_json(base, "/health")
                if status == 200:
                    break
            except (OSError, urllib.error.URLError):
                if process.poll() is not None:
                    raise RuntimeError("D service exited before readiness.")
                time.sleep(0.1)
        else:
            raise RuntimeError("D service failed to become ready.")
        validate_schema(health, "HealthResult")
        record("health_schema_and_mock_mode", health["status"] == "ok" and health["mode"] == "mock", health["service"])
        record("health_headers", headers.get("x-contract-status") == "draft-provisional" and headers.get("cache-control") == "no-store", "provisional and no-store headers")

        status, headers, extraction = _http_json(base, "/v1/extract", payload=extract_request,
                                                  headers={"x-request-id": "readiness-extract-v1"})
        _validate_success(extraction, document, "extract")
        schema_check = Draft202012Validator({"$ref": "#/$defs/ExtractionResult", "$defs": schema()["$defs"]}, format_checker=FormatChecker())
        schema_check.validate(extraction)
        record("extract_schema_identity_and_evidence", status == 200 and extraction["doc_id"] == document["doc_id"],
               f"{len(extraction['items'])} item(s); text body omitted from report")
        record("extract_headers_and_generation_diagnostics", headers.get("x-request-id") == "readiness-extract-v1"
               and headers.get("x-contract-status") == "draft-provisional" and headers.get("cache-control") == "no-store"
               and all(k in headers for k in ("x-generation-attempts", "x-raw-validation-failures", "x-validation-repairs")),
               "request correlation, draft status, no-store, generation counters")

        status, headers, answer = _http_json(base, "/v1/document-answer", payload=answer_request,
                                              headers={"x-request-id": "readiness-answer-v1"})
        _validate_success(answer, document, "answer")
        record("answer_schema_identity_and_evidence", status == 200 and answer["route"] in {"document", "none"},
               f"{len(answer['claims'])} claim(s); text body omitted from report")
        record("answer_headers_and_generation_diagnostics", headers.get("x-request-id") == "readiness-answer-v1"
               and headers.get("x-contract-status") == "draft-provisional" and headers.get("cache-control") == "no-store"
               and all(k in headers for k in ("x-generation-attempts", "x-raw-validation-failures", "x-validation-repairs")),
               "request correlation, draft status, no-store, generation counters")

        status, headers, bad = _http_json(base, "/v1/document-answer", payload={**answer_request, "question": "   "})
        validate_schema(bad, "ErrorEnvelope")
        record("invalid_question_error_envelope", status == 422 and bad["error"]["code"] == "validation_failure"
               and headers.get("x-request-id") == bad["request_id"], "422 safe error envelope and correlation")
        status, headers, bad = _http_json(base, "/v1/extract", payload=extract_request,
                                           headers={"x-request-id": "bad id with spaces"})
        # The valid request succeeds; an invalid inbound correlation ID is replaced safely.
        validate_schema(bad, "ExtractionResult")
        record("invalid_correlation_id_replaced", status == 200 and headers.get("x-request-id") != "bad id with spaces",
               "untrusted request ID replaced by generated correlation ID")
        return {"status": "pass", "mode": "mock", "checks": checks,
                "contract_status": "draft-provisional", "documents": 1,
                "request_text_included": False, "provider": "deterministic synthetic fake"}
    finally:
        process.terminate()
        process.wait(timeout=10)


def run_readiness() -> dict:
    contract = inspect_contracts()
    transport = probe_http()
    return {"label": "Member D local integration readiness; not cross-service integration acceptance",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "contract_inspection": contract, "transport": transport,
            "cross_service": {"status": "not_run", "reason": "A and C runtime fixture packages are not present in this checkout; B owns shared integration and shared contract changes."},
            "live_provider": "not run; no provider/model is approved",
            "human_or_clinical_review": "not performed",
            "limits": ["Draft contracts can be structurally checked but are not frozen or accepted.",
                       "Mock mode confirms transport/schema/evidence behavior only, not model quality or semantic support."]}


def main() -> int:
    output = ROOT / "eval/reports/local/readiness"
    output.mkdir(parents=True, exist_ok=True)
    try:
        report = run_readiness()
    except Exception as exc:
        report = {"label": "Member D local integration readiness; not cross-service integration acceptance",
                  "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": "fail",
                  "safe_failure": f"{type(exc).__name__}: {exc}", "request_text_included": False}
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        raise
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"label": report["label"], "contracts": report["contract_inspection"]["status"],
                      "transport": report["transport"]["status"], "cross_service": report["cross_service"]["status"],
                      "output": "eval/reports/local/readiness/results.json"}))
    return 0 if report["contract_inspection"]["status"] == "pass" and report["transport"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

