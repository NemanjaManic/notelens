"""Loopback mock transport; B owns browser/session/expiry enforcement."""

import json
import re
import secrets
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import VERSION
from .config import Settings
from .errors import ServiceError
from .service import Diagnostics, run


def create_app(provider=None, *, token: str | None = None) -> FastAPI:
    settings = Settings.from_env()
    provider = provider or settings.provider()
    token = token if token is not None else settings.service_token
    app = FastAPI(title="NoteLens D provisional service", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def safe_boundary(request: Request, call_next):
        incoming_id = request.headers.get("X-Request-ID", "")
        request_id = incoming_id if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", incoming_id) else uuid.uuid4().hex
        request.state.request_id = request_id
        try:
            if token:
                provided = request.headers.get("Authorization", "")
                if not secrets.compare_digest(provided, f"Bearer {token}"):
                    raise ServiceError(401, "unauthorized", "Valid service authentication is required.")
            elif request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
                raise ServiceError(503, "configuration_required", "Unconfigured mock access is loopback-only.")
            response = await call_next(request)
        except ServiceError as exc:
            response = JSONResponse(exc.envelope(request_id), status_code=exc.status)
        except Exception:
            response = JSONResponse(ServiceError(500, "internal_error", "An internal service error occurred.").envelope(request_id), status_code=500)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Contract-Status"] = "draft-provisional"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health")
    def health():
        return {"schema_version": "1.0.0", "service": "extraction",
                "status": "ok" if provider.mode == "mock" else "not_ready",
                "mode": provider.mode, "version": VERSION}

    async def process(request: Request, operation: str):
        try:
            payload = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ServiceError(400, "validation_failure", "Request body must be valid JSON.") from exc
        trace = Diagnostics()
        try:
            result, diagnostics = await run_in_threadpool(run, payload, operation, provider, diagnostics=trace)
        except ServiceError as exc:
            return JSONResponse(exc.envelope(request.state.request_id), status_code=exc.status,
                                headers={"X-Generation-Attempts": str(trace.attempts),
                                         "X-Raw-Validation-Failures": str(trace.raw_validation_failures),
                                         "X-Validation-Repairs": str(trace.repairs)})
        return JSONResponse(result, headers={"X-Generation-Attempts": str(diagnostics["attempts"]),
                                             "X-Raw-Validation-Failures": str(diagnostics["raw_validation_failures"]),
                                             "X-Validation-Repairs": str(diagnostics["repairs"])})

    @app.post("/v1/extract")
    async def extract(request: Request):
        return await process(request, "extract")

    @app.post("/v1/document-answer")
    async def answer(request: Request):
        return await process(request, "answer")

    return app


app = create_app()
