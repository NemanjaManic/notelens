"""Run pinned Promptfoo against temporary loopback mock services."""

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
if os.name == "nt":
    sys.path.insert(0, str(ROOT.parent / "scripts/project"))
    from scaffold_process import owned_process
    sys.path.pop(0)


def wait_for_mock(service: subprocess.Popen, port: int) -> None:
    for _ in range(100):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health/ready", timeout=0.3) as response:
                readiness = json.load(response)
                if readiness["mode"] != "mock" or readiness["status"] != "ok":
                    raise RuntimeError("Smoke requires mock mode.")
            return
        except OSError:
            if service.poll() is not None:
                raise RuntimeError("Local mock service failed to start.")
            time.sleep(0.1)
    raise RuntimeError("Local mock service was not ready.")


def stop(service: subprocess.Popen) -> None:
    service.terminate()
    try:
        service.wait(timeout=10)
    except subprocess.TimeoutExpired:
        service.kill()
        service.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cross-service", action="store_true")
    shared = parser.parse_args().cross_service
    # Reserve distinct loopback ports together, then release them for the children.
    with ExitStack() as reservations:
        ports = []
        for _ in range(3 if shared else 1):
            sock = reservations.enter_context(socket.socket())
            sock.bind(("127.0.0.1", 0))
            ports.append(sock.getsockname()[1])
    port = ports[0]
    env = {**os.environ, "NOTELENS_MODE": "mock", "NOTELENS_SMOKE_PORT": str(port),
           "PROMPTFOO_CONFIG_DIR": str(ROOT / ".promptfoo"), "PROMPTFOO_DISABLE_TELEMETRY": "1",
           "PROMPTFOO_DISABLE_UPDATE": "1",
           "PROMPTFOO_CACHE_ENABLED": "false", "PROMPTFOO_DISABLE_WAL_MODE": "true",
           "PROMPTFOO_PYTHON": sys.executable}
    env.pop("NOTELENS_SERVICE_TOKEN", None)
    env.pop("NOTELENS_EXTRACTION_MOCK_NOT_READY", None)
    (ROOT / ".promptfoo").mkdir(exist_ok=True)
    (ROOT / "reports/local").mkdir(parents=True, exist_ok=True)
    command = ROOT / "node_modules/.bin" / ("promptfoo.cmd" if os.name == "nt" else "promptfoo")
    if not command.exists():
        print("Install the eval-local package lock before running Promptfoo.", file=sys.stderr)
        return 1
    services = [[sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)]]
    config = "promptfooconfig.json"
    report = "promptfoo.json"
    if shared:
        rag_port, classifier_port = ports[1:]
        services_root = ROOT.parent / "services"
        python_relative = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
        rag_python = services_root / "rag" / python_relative
        classifier_python = services_root / "classifier" / python_relative
        if not rag_python.is_file() or not classifier_python.is_file():
            parser.error("Shared smoke requires the local RAG and classifier environments.")
        services.extend([
            [str(rag_python), "-m", "uvicorn", "notelens_rag.main:app", "--host", "127.0.0.1",
             "--port", str(rag_port), "--no-proxy-headers", "--no-access-log"],
            [str(classifier_python), "-m", "notelens_classifier", "--port", str(classifier_port)],
        ])
        env.update({"NOTELENS_SMOKE_RAG_PORT": str(rag_port), "NOTELENS_SMOKE_CLASSIFIER_PORT": str(classifier_port),
                    "NOTELENS_RAG_MODE": "mock", "NOTELENS_RAG_MOCK_SCENARIO": "sufficient",
                    "NOTELENS_RAG_MOCK_READY": "true", "NOTELENS_CLASSIFIER_MODE": "mock",
                    "NOTELENS_CLASSIFIER_MOCK_SCENARIO": "supported"})
        for variable in ("NOTELENS_RAG_SERVICE_TOKEN", "NOTELENS_CLASSIFIER_SERVICE_TOKEN",
                         "NOTELENS_CLASSIFIER_MOCK_READINESS"):
            env.pop(variable, None)
        config = "profiles/promptfoo-shared-smoke.json"
        report = "promptfoo-shared-smoke.json"
    with ExitStack() as running:
        for service_command, service_port in zip(services, ports, strict=True):
            if os.name == "nt":
                service = running.enter_context(owned_process(service_command, cwd=ROOT.parent, env=env,
                                                              stdout=subprocess.DEVNULL))
            else:
                service = subprocess.Popen(service_command, cwd=ROOT.parent, env=env,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                running.callback(stop, service)
            wait_for_mock(service, service_port)
        return subprocess.run([str(command), "eval", "--config", config,
                               "--no-cache", "--no-write", "--no-share", "--no-table",
                               "--no-progress-bar", "--max-concurrency", "1", "--output", f"reports/local/{report}"],
                              cwd=ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
