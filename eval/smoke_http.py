"""Run pinned Promptfoo against a temporary loopback mock service; shut it down."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent


def main() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "NOTELENS_MODE": "mock", "NOTELENS_SMOKE_PORT": str(port),
           "PROMPTFOO_CONFIG_DIR": str(ROOT / ".promptfoo"), "PROMPTFOO_DISABLE_TELEMETRY": "1",
           "PROMPTFOO_CACHE_ENABLED": "false", "PROMPTFOO_DISABLE_WAL_MODE": "true",
           "PROMPTFOO_PYTHON": sys.executable}
    env.pop("NOTELENS_SERVICE_TOKEN", None)
    (ROOT / ".promptfoo").mkdir(exist_ok=True)
    (ROOT / "reports/local").mkdir(parents=True, exist_ok=True)
    command = ROOT / "node_modules/.bin" / ("promptfoo.cmd" if os.name == "nt" else "promptfoo")
    if not command.exists():
        print("Install the eval-local package lock before running Promptfoo.", file=sys.stderr)
        return 1
    service = subprocess.Popen([sys.executable, "-m", "notelens_extraction.cli", "serve", "--port", str(port)],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.3) as response:
                    if json.load(response)["mode"] != "mock":
                        raise RuntimeError("Smoke requires mock mode.")
                break
            except OSError:
                if service.poll() is not None:
                    raise RuntimeError("Local mock service failed to start.")
                time.sleep(0.1)
        else:
            raise RuntimeError("Local mock service was not ready.")
        return subprocess.run([str(command), "eval", "--config", "promptfooconfig.json",
                               "--no-cache", "--no-write", "--no-share", "--no-table",
                               "--no-progress-bar", "--max-concurrency", "1", "--output", "reports/local/promptfoo.json"],
                              cwd=ROOT, env=env, check=False).returncode
    finally:
        service.terminate()
        service.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
