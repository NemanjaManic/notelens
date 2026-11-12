"""Run the D synthetic suite through the actual loopback service in mock mode."""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .run import EVAL_ROOT
from .suite import evaluate_suite, render_report, validate_references

TEST_TOKEN = "notelens-local-http-suite-token"


def _call(base: str, path: str, request: dict, request_id: str) -> tuple[dict | None, dict]:
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    call = urllib.request.Request(base + path, data=payload, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {TEST_TOKEN}",
        "X-Request-ID": request_id,
    })
    try:
        with urllib.request.urlopen(call, timeout=5) as response:
            result = json.load(response)
            headers = response.headers
            status = response.status
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read())
        except (ValueError, UnicodeDecodeError):
            result = None
        headers, status = exc.headers, exc.code
    diagnostics = {
        "http_status": status,
        "request_id_matches": headers.get("X-Request-ID") == request_id,
        "attempts": int(headers.get("X-Generation-Attempts", "0")),
        "raw_validation_failures": int(headers.get("X-Raw-Validation-Failures", "0")),
        "repairs": int(headers.get("X-Validation-Repairs", "0")),
    }
    if status >= 400 and isinstance(result, dict):
        diagnostics["technical_error"] = result.get("error", {}).get("code", "http_error")
        return None, diagnostics
    return result if isinstance(result, dict) else None, diagnostics


def produce_http(references: dict) -> dict:
    """Generate predictions over HTTP; only request fields reach the service."""
    validate_references(references)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NOTELENS_MODE": "mock", "NOTELENS_SERVICE_TOKEN": TEST_TOKEN}
    process = subprocess.Popen(
        [sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)],
        cwd=EVAL_ROOT.parent, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                request = urllib.request.Request(base + "/health", headers={"Authorization": f"Bearer {TEST_TOKEN}"})
                with urllib.request.urlopen(request, timeout=0.5) as response:
                    health = json.load(response)
                if health.get("mode") == "mock" and health.get("service") == "extraction":
                    break
            except (OSError, urllib.error.URLError, ValueError):
                if process.poll() is not None:
                    raise RuntimeError("Local extraction service exited before HTTP evaluation.")
                time.sleep(0.1)
        else:
            raise RuntimeError("Local extraction service did not become ready in mock mode.")

        predictions = []
        for case in references["cases"]:
            extract_request = {"schema_version": case["request"]["schema_version"],
                               "document": case["request"]["document"]}
            extraction, extraction_stats = _call(base, "/v1/extract", extract_request,
                                                  f"http-extract-{case['id']}")
            answers = []
            for qa in case["qa"]:
                answer_request = {**extract_request, "question": qa["question"]}
                answer, stats = _call(base, "/v1/document-answer", answer_request,
                                      f"http-answer-{case['id']}-{qa['id']}")
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
    report["transport"] = {
        "mode": "mock", "requests": len(transport_records),
        "http_200": sum(r["http_status"] == 200 for r in transport_records),
        "technical_failures": sum(r["http_status"] != 200 for r in transport_records),
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
                      "completeness": report["answer_completeness"], "output": str(args.output)}))
    return 0 if report["transport"]["technical_failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
