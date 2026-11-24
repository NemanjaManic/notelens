"""Start the local-only scaffold with proxy headers and access logs disabled."""

import argparse
from pathlib import Path

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the local NoteLens classifier.")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--development-model", type=Path)
    parser.add_argument("--model-manifest-sha256")
    args = parser.parse_args()
    app = "notelens_classifier.main:app"
    if args.development_model is not None or args.model_manifest_sha256 is not None:
        if args.development_model is None or args.model_manifest_sha256 is None:
            parser.error("Provide both the development model directory and the known manifest checksum.")
        from notelens_classifier.inference import load_model
        from notelens_classifier.main import Settings, create_app

        settings = Settings.from_environment()
        if settings.mode != "live" or not settings.token:
            parser.error("Development model startup requires live mode and a service token.")
        try:
            model = load_model(args.development_model, args.model_manifest_sha256)
            app = create_app(settings, model=model)
        except Exception:
            # Keep artifact paths, package diagnostics and serialized contents out of startup logs.
            parser.error("Could not start with the trusted development model. Verify its checksums and dependencies.")
    uvicorn.run(app, host="127.0.0.1", port=args.port,
                proxy_headers=False, access_log=False)


if __name__ == "__main__":
    main()
