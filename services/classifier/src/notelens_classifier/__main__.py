"""Start the local-only scaffold with proxy headers and access logs disabled."""

import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the local NoteLens classifier mock scaffold.")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    uvicorn.run("notelens_classifier.main:app", host="127.0.0.1", port=args.port,
                proxy_headers=False, access_log=False)


if __name__ == "__main__":
    main()
