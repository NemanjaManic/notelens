"""D-owned mock HTTP boundary for the frozen contract."""

import json
import math
import secrets
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import VERSION
from .config import Settings
from .errors import ServiceError
from .service import Diagnostics, run


def _canonical_request_id(request: Request) -> str | None:
    values = [value for name, value in request.headers.raw if name.lower() == b"x-request-id"]
    if len(values) != 1:
        return None
    try:
        value = values[0].decode("ascii")
        return value if str(uuid.UUID(value)) == value else None
    except (UnicodeDecodeError, ValueError):
        return None


def create_app(provider=None, *, token: str | None = None) -> FastAPI:
    settings = Settings.from_env()
    provider = provider or settings.provider()
    token = token if token is not None else settings.service_token
    app = FastAPI(title="NoteLens extraction mock service", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def safe_boundary(request: Request, call_next):
        health = request.url.path in {"/health/live", "/health/ready"}
        request_id = str(uuid.uuid4()) if health else _canonical_request_id(request)
        diagnostic_id = request_id or str(uuid.uuid4())
        request.state.request_id = diagnostic_id
        try:
            if token:
                provided = request.headers.get("Authorization", "")
                if not secrets.compare_digest(provided, f"Bearer {token}"):
                    raise ServiceError(401, "unauthorized", "Valid service authentication is required.")
            elif request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
                raise ServiceError(503, "configuration_required", "Unconfigured mock access is loopback-only.")
            if not health and request_id is None:
                raise ServiceError(400, "validation_failure", "A single canonical X-Request-ID is required.")
            response = await call_next(request)
        except ServiceError as exc:
            response = JSONResponse(exc.envelope(diagnostic_id), status_code=exc.status)
            if exc.status == 401:
                response.headers["WWW-Authenticate"] = "Bearer"
        except Exception:
            response = JSONResponse(ServiceError(500, "internal_error", "An internal service error occurred.").envelope(diagnostic_id), status_code=500)
        response.headers["X-Request-ID"] = diagnostic_id
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health/live")
    def liveness():
        return {"schema_version": "1.0.0", "service": "extraction", "status": "alive",
                "mode": provider.mode, "version": VERSION}

    @app.get("/health/ready")
    def readiness():
        ready = provider.mode == "mock"
        body = {"schema_version": "1.0.0", "service": "extraction",
                "status": "ok" if ready else "not_ready", "mode": provider.mode,
                "version": VERSION, "model_version": None,
                "reason": None if ready else "configuration_required"}
        return JSONResponse(body, status_code=200 if ready else 503)

    async def process(request: Request, operation: str):
        def pairs(values):
            result = {}
            for key, value in values:
                if key in result:
                    raise ValueError("Duplicate JSON field.")
                result[key] = value
            return result

        def reject_number(value):
            raise ValueError("Nonstandard JSON number.")

        def finite_float(value):
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("Non-finite JSON number.")
            return number

        try:
            payload = json.loads((await request.body()).decode("utf-8"),
                                 object_pairs_hook=pairs, parse_constant=reject_number,
                                 parse_float=finite_float)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ServiceError(400, "validation_failure", "Request body must be valid JSON.") from exc
        trace = Diagnostics()
        try:
            result, diagnostics = await run_in_threadpool(run, payload, operation, provider, diagnostics=trace)
        except ServiceError as exc:
            return JSONResponse(exc.envelope(request.state.request_id), status_code=exc.status)
        return JSONResponse(result, headers={"X-Generation-Attempts": str(diagnostics["attempts"])})

    @app.post("/v1/extract")
    async def extract(request: Request):
        return await process(request, "extract")

    @app.post("/v1/document-answer")
    async def answer(request: Request):
        return await process(request, "answer")

    return app


app = create_app()
