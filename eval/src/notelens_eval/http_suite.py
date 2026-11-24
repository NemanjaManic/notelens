"""Run the D synthetic suite through the actual loopback service in mock mode."""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from collections import Counter
from http.client import HTTPConnection, HTTPException
from pathlib import Path

from notelens_contracts.v1 import validate_exchange

from .run import EVAL_ROOT
from .suite import evaluate_suite, render_report, validate_references

TEST_TOKEN = "notelens-local-http-suite-token"


def _call(port: int, path: str, request: dict, request_id: str) -> tuple[dict | None, dict]:
    headers = {
        "Content-Type": "application/json", "Authorization": f"Bearer {TEST_TOKEN}",
        "X-Request-ID": request_id,
    }
    counters = {"attempts": "X-Generation-Attempts", "raw_validation_failures": "X-Raw-Validation-Failures",
                "repairs": "X-Validation-Repairs"}
    diagnostics = {"http_status": None, "request_id_matches": False, **dict.fromkeys(counters, 0)}

    def failure(reason):
        diagnostics["technical_error"] = reason
        return None, diagnostics

    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("POST", path, body=json.dumps(request, ensure_ascii=False).encode("utf-8"), headers=headers)
        with connection.getresponse() as response:
            diagnostics["http_status"] = response.status
            diagnostics["request_id_matches"] = response.headers.get_all("X-Request-ID", []) == [request_id]
            if not diagnostics["request_id_matches"]:
                return failure("request_id_mismatch")
            if response.status != 200 and not 400 <= response.status < 600:
                return failure("unexpected_http_status")
            try:
                result = json.load(response)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return failure("invalid_response_json")
            if not isinstance(result, dict):
                return failure("invalid_response_body")
            for key, header in counters.items():
                values = response.headers.get_all(header, ["0"])
                try:
                    if len(values) != 1:
                        return failure("invalid_generation_diagnostics")
                    value = int(values[0])
                except ValueError:
                    return failure("invalid_generation_diagnostics")
                if value < 0:
                    return failure("invalid_generation_diagnostics")
                diagnostics[key] = value
            if response.status != 200:
                issues = validate_exchange({"path": path, "status": response.status, "body": result,
                                            "request_headers": list(headers.items()), "response_headers": response.getheaders(),
                                            "disposition": "failed_call"})
                return failure("invalid_error_envelope" if issues else result["error"]["code"])
            if result.get("mode") != "mock":
                return failure("non_mock_response")
    except (OSError, HTTPException):
        return failure("loopback_transport_error")
    finally:
        connection.close()
    return result, diagnostics


def _ready(port: int) -> bool:
    connection = HTTPConnection("127.0.0.1", port, timeout=0.5)
    try:
        connection.request("GET", "/health/ready", headers={"Authorization": f"Bearer {TEST_TOKEN}"})
        with connection.getresponse() as response:
            if response.status != 200:
                return False
            health = json.load(response)
            return (isinstance(health, dict) and health.get("mode") == "mock"
                    and health.get("service") == "extraction" and health.get("status") == "ok")
    except (OSError, HTTPException, ValueError):
        return False
    finally:
        connection.close()


def produce_http(references: dict) -> dict:
    """Generate predictions over HTTP; only request fields reach the service."""
    validate_references(references)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NOTELENS_MODE": "mock", "NOTELENS_SERVICE_TOKEN": TEST_TOKEN}
    env.pop("NOTELENS_EXTRACTION_MOCK_NOT_READY", None)
    process = subprocess.Popen(
        [sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)],
        cwd=EVAL_ROOT.parent, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            if _ready(port):
                break
            if process.poll() is not None:
                raise RuntimeError("Local extraction service exited before HTTP evaluation.")
            time.sleep(0.1)
        else:
            raise RuntimeError("Local extraction service did not become ready in mock mode.")

        predictions = []
        for case in references["cases"]:
            extract_request = {"schema_version": case["request"]["schema_version"],
                               "document": case["request"]["document"]}
            extraction, extraction_stats = _call(port, "/v1/extract", extract_request,
                                                  str(uuid.uuid4()))
            answers = []
            for qa in case["qa"]:
                answer_request = {**extract_request, "question": qa["question"]}
                answer, stats = _call(port, "/v1/document-answer", answer_request,
                                      str(uuid.uuid4()))
                answers.append({"id": qa["id"], "result": answer, "diagnostics": stats})
            predictions.append({"id": case["id"], "result": extraction,
                                "diagnostics": extraction_stats, "qa": answers})
        return {"kind": "synthetic_mock_predictions", "version": "d-http-mock-predictions-v1",
                "transport": "loopback-http", "cases": predictions}
    finally:
        process.terminate()
        process.wait(timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all D synthetic cases through the actual local mock HTTP API")
    parser.add_argument("--references", type=Path, default=EVAL_ROOT / "fixtures/extraction-qa-synthetic-v1.json")
    parser.add_argument("--output", type=Path, default=EVAL_ROOT / "reports/local/http-suite")
    args = parser.parse_args()
    references = json.loads(args.references.read_text(encoding="utf-8"))
    predictions = produce_http(references)
    report = evaluate_suite(references, predictions)
    transport_records = [p["diagnostics"] for p in predictions["cases"]]
    transport_records += [a["diagnostics"] for p in predictions["cases"] for a in p["qa"]]
    failures = Counter(r["technical_error"] for r in transport_records if "technical_error" in r)
    report["transport"] = {
        "mode": "mock", "requests": len(transport_records),
        "http_200": sum(r["http_status"] == 200 for r in transport_records),
        "technical_failures": failures.total(), "failure_reasons": dict(failures),
        "request_ids_matched": sum(r["request_id_matches"] for r in transport_records),
        "request_text_in_report": False,
        "references_sent_to_provider": False,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "predictions.json").write_text(json.dumps(predictions, indent=2) + "\n", encoding="utf-8")
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "report.md").write_text(render_report(report), encoding="utf-8")
    print(json.dumps({"documents": report["counts"]["documents"], "qa": report["counts"]["qa"],
                      "http_requests": report["transport"]["requests"], "http_200": report["transport"]["http_200"],
                      "technical_failures": report["transport"]["technical_failures"],
                      "completeness": report["answer_completeness"], "output": str(args.output)}))
    validation = report["record_validation"]
    return int(bool(failures or validation["schema_invalid"] or validation["evidence_or_relationship_invalid"]))


if __name__ == "__main__":
    raise SystemExit(main())
