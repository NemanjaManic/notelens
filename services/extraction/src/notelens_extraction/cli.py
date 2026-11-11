"""Local mock CLI. JSON stdout is explicit demo/output, not a routine server log."""

import argparse
import json
import sys
from pathlib import Path

from .demo import request as demo_request
from .config import Settings
from .errors import ServiceError
from .service import run


def main() -> int:
    parser = argparse.ArgumentParser(description="NoteLens provisional mock service CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="Start a mock API on loopback (default port 8003)")
    serve.add_argument("--port", type=int, default=8003)
    demo = commands.add_parser("demo", help="Print a synthetic mock extraction/answer")
    demo.add_argument("--question")
    file_command = commands.add_parser("request", help="Process a permitted fixture JSON")
    file_command.add_argument("path", type=Path)
    file_command.add_argument("--operation", choices=["extract", "answer"], default="extract")
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("notelens_extraction.main:app", host="127.0.0.1", port=args.port, access_log=False)
        return 0
    try:
        if args.command == "demo":
            payload = demo_request(args.question)
            operation = "answer" if args.question is not None else "extract"
        else:
            payload = json.loads(args.path.read_text(encoding="utf-8"))
            operation = args.operation
        result, diagnostics = run(payload, operation, Settings.from_env().provider())
        print(json.dumps(result, ensure_ascii=True, indent=2))
        print(json.dumps({"mode": result["mode"], "diagnostics": diagnostics}), file=sys.stderr)
        return 0
    except ServiceError as exc:
        print(json.dumps(exc.envelope("local-cli")), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("Could not read a valid fixture request.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
