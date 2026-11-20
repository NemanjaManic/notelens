"""F-004 mock HTTP boundary using B's frozen dictionaries and validators."""

from copy import deepcopy
from dataclasses import dataclass, field
from importlib.resources import files
import ipaddress
import json
import os
from secrets import compare_digest
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.requests import ClientDisconnect
from notelens_contracts.v1 import (
    ClassificationRequest, ClassificationResult, PreparedDocument,
    ErrorEnvelope, HealthResult, LivenessResult, ContractValidationError, validate_json, validate_record,
)

MAX_DOCUMENT_CODE_POINTS = 100_000
SERVICE_VERSION = "0.1.0"
SCENARIOS = {
    "supported": "classification-supported",
    "uncertain": "classification-uncertain",
    "unsupported_skipped": "classification-unsupported",
    "unsupported_performed": "classification-unsupported-performed",
}
MOCK_FAILURES = {
    "timeout": (504, "The mock classifier simulated a timeout."),
    "rate_limit": (429, "The mock classifier simulated a rate limit."),
    "provider_unavailable": (503, "The mock classifier simulated provider unavailability."),
}
# Only versioned synthetic fixture templates are retained; never request content.
TEMPLATES = json.loads(files("notelens_classifier").joinpath("mock_results.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Settings:
    mode: str | None = None
    scenario: str = "supported"
    token: str | None = field(default=None, repr=False)
    mock_readiness: str = "ready"
    mock_failure: str | None = None

    def has_mock_configuration(self) -> bool:
        return (self.mode == "mock" and self.scenario in SCENARIOS and
                (self.mock_failure is None or self.mock_failure in MOCK_FAILURES))

    @classmethod
    def from_environment(cls):
        return cls(
            mode=os.getenv("NOTELENS_CLASSIFIER_MODE"),
            scenario=os.getenv("NOTELENS_CLASSIFIER_MOCK_SCENARIO", "supported"),
            token=os.getenv("NOTELENS_CLASSIFIER_SERVICE_TOKEN"),
            mock_readiness=os.getenv("NOTELENS_CLASSIFIER_MOCK_READINESS", "ready"),
            mock_failure=os.getenv("NOTELENS_CLASSIFIER_MOCK_FAILURE"),
        )


def error_response(status: int, code: str, message: str, request_id: str, *,
                   retryable: bool = False) -> JSONResponse:
    payload: ErrorEnvelope = {
        "schema_version": "1.0.0", "request_id": request_id,
        "error": {"code": code, "message": message, "retryable": retryable},
    }
    validate_record("ErrorEnvelope", payload)
    headers = {"X-Request-ID": request_id, "Cache-Control": "no-store"}
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(payload, status_code=status, headers=headers)


def admitted_request_id(request: Request) -> str | None:
    values = request.headers.getlist("x-request-id")
    if len(values) != 1:
        return None
    try:
        return validate_record("RequestId", values[0])
    except ContractValidationError:
        return None


def loopback_peer(request: Request) -> bool:
    try:
        return request.client is not None and ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        return False


def authorization_error(request: Request, settings: Settings, request_id: str):
    if settings.token:
        values = request.headers.getlist("authorization")
        parts = values[0].split() if len(values) == 1 else []
        if len(parts) != 2 or parts[0].lower() != "bearer" or not compare_digest(
                parts[1].encode("utf-8"), settings.token.encode("utf-8")):
            return error_response(401, "unauthorized", "Service authentication is required.", request_id)
    elif settings.mode != "mock" or not loopback_peer(request):
        return error_response(503, "configuration_required", "Service authentication is not configured.", request_id)
    return None


def health_authorization_error(request: Request, settings: Settings):
    """Health ignores all incoming request IDs, including invalid or duplicate IDs."""
    values = request.headers.getlist("authorization")
    parts = values[0].split() if len(values) == 1 else []
    permitted = (len(parts) == 2 and parts[0].lower() == "bearer" and
                 compare_digest(parts[1].encode("utf-8"), settings.token.encode("utf-8"))) if settings.token else (
                     settings.mode == "mock" and loopback_peer(request))
    if not permitted:
        return error_response(401, "unauthorized", "Service authentication is required.", str(uuid4()))
    return None


def mock_result(document: PreparedDocument, scenario: str) -> ClassificationResult:
    result = deepcopy(TEMPLATES[SCENARIOS[scenario]])
    result.update(doc_id=document["doc_id"], text_sha256=document["text_sha256"])
    return result


def input_failure(error: ContractValidationError, raw: bytes, request_id: str):
    if any(issue.rule == "JSON_INPUT" for issue in error.issues):
        return error_response(400, "validation_failure", "The request must contain valid, unambiguous JSON.", request_id)
    # Parsing was already accepted by validate_json. Inspect only the agreed text cap
    # to distinguish 413 from other schema failures; never alter/truncate the input.
    if any(issue.path == "/document/text" for issue in error.issues):
        value = json.loads(raw)
        text = value.get("document", {}).get("text") if isinstance(value, dict) and isinstance(value.get("document"), dict) else None
        if isinstance(text, str) and len(text) > MAX_DOCUMENT_CODE_POINTS:
            return error_response(413, "validation_failure", "The document exceeds 100,000 Unicode code points.", request_id)
    return error_response(422, "validation_failure", "The request does not satisfy the frozen document contract.", request_id)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings.from_environment()
    app = FastAPI(title="NoteLens classifier mock scaffold", version="0.1.0",
                  docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health/live", response_model=None)
    async def liveness(request: Request):
        denied = health_authorization_error(request, settings)
        if denied is not None:
            return denied
        if settings.mode not in ("mock", "live"):
            return error_response(500, "internal_error", "Service configuration is unavailable.", str(uuid4()))
        payload: LivenessResult = {"schema_version": "1.0.0", "service": "classifier", "status": "alive",
                                  "mode": settings.mode, "version": SERVICE_VERSION}
        validate_record("LivenessResult", payload)
        return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @app.get("/health/ready", response_model=None)
    async def readiness(request: Request):
        denied = health_authorization_error(request, settings)
        if denied is not None:
            return denied
        if settings.mode not in ("mock", "live"):
            return error_response(500, "internal_error", "Service configuration is unavailable.", str(uuid4()))
        ready = settings.has_mock_configuration() and settings.mock_readiness == "ready"
        payload: HealthResult = {"schema_version": "1.0.0", "service": "classifier",
                                 "status": "ok" if ready else "not_ready", "mode": settings.mode,
                                 "version": SERVICE_VERSION, "model_version": None,
                                 "reason": None if ready else "Classifier configuration is not ready."}
        validate_record("HealthResult", payload)
        return JSONResponse(payload, status_code=200 if ready else 503, headers={"Cache-Control": "no-store"})

    @app.post("/v1/classify", response_model=None)
    async def classify(request: Request):
        request_id = admitted_request_id(request)
        if request_id is None:
            return error_response(400, "validation_failure", "Provide exactly one canonical UUID X-Request-ID.", str(uuid4()))
        raw = None
        incoming = None
        result = None
        try:
            denied = authorization_error(request, settings, request_id)
            if denied is not None:
                return denied
            raw = await request.body()
            try:
                incoming: ClassificationRequest = validate_json("ClassificationRequest", raw)
            except ContractValidationError as error:
                return input_failure(error, raw, request_id)
            if not settings.has_mock_configuration():
                return error_response(503, "configuration_required", "A usable classifier configuration is not available.", request_id)
            if settings.mock_failure is not None:
                status, message = MOCK_FAILURES[settings.mock_failure]
                return error_response(status, settings.mock_failure, message, request_id, retryable=True)
            # A future inference adapter must check cancellation before real work.
            # This contribution only creates small deterministic synthetic responses.
            result = mock_result(incoming["document"], settings.scenario)
            validate_record("ClassificationResult", result, document=incoming["document"])
            return JSONResponse(result, headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})
        except ClientDisconnect:
            # An interrupted body never reaches classification. The peer may be gone.
            return error_response(400, "validation_failure", "The request body was interrupted.", request_id)
        except Exception:
            # Catch inside the route so server middleware cannot log an exception
            # carrying request content, credentials or invalid model output.
            return error_response(500, "internal_error", "The classifier could not complete the request.", request_id)
        finally:
            raw = incoming = result = None

    return app


app = create_app()
