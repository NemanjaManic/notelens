"""Promptfoo provider for the shared five-route loopback smoke."""

import json
import os

from notelens_eval.cross_service_smoke import check_services


def call_api(prompt: str, options: dict, context: dict) -> dict:
    try:
        report = check_services(rag_port=int(os.environ["NOTELENS_SMOKE_RAG_PORT"]),
                                classifier_port=int(os.environ["NOTELENS_SMOKE_CLASSIFIER_PORT"]),
                                extraction_port=int(os.environ["NOTELENS_SMOKE_PORT"]))
    except (KeyError, ValueError) as exc:
        return {"error": str(exc)}
    return {"output": json.dumps(report, sort_keys=True)}
