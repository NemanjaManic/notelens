"""Default loopback mock with an explicit, authenticated service-backend boundary."""

from dataclasses import dataclass, field
import hmac
import ipaddress
import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import __version__
from .contracts import ContractError, ContractJsonError, Contracts
from .ingestion import CorpusLoadError, load_corpus
from .mock import DEMO_QUESTION, result as mock_result
from .runtime import RagServiceError


SCENARIOS = {"sufficient", "insufficient", "clarification", "timeout", "rate_limit",
             "provider_unavailable", "internal_error"}
FAILURES = {"timeout": (504, "timeout"), "rate_limit": (429, "rate_limit"),
            "provider_unavailable": (503, "provider_unavailable"), "internal_error": (500, "internal_error")}
QUESTION_REJECTIONS = {
    'unsupported_language': 'Please ask your question in English.',
    'needs_clarification': 'Please ask a self-contained question and name the medical topic you mean.',
    'out_of_scope': 'Please ask for general information from the medical literature.',
}


@dataclass(frozen=True)
class Settings:
    mode: str = "mock"
    service_token: str | None = field(default=None, repr=False)
    scenario: str = "sufficient"
    corpus_manifest: str | None = None
    repository_root: str | None = None
    expected_corpus_version: str | None = None

    def __post_init__(self):
        if self.mode not in {"mock", "live"} or self.scenario not in SCENARIOS:
            raise ValueError("Unsupported server mode or mock scenario.")
        if self.service_token is not None and not self.service_token:
            raise ValueError("A configured service token must not be empty.")

    @classmethod
    def from_environment(cls):
        return cls(mode=os.environ.get("NOTELENS_RAG_MODE", "mock"),
                   service_token=os.environ.get("NOTELENS_RAG_SERVICE_TOKEN"),
                   scenario=os.environ.get("NOTELENS_RAG_MOCK_SCENARIO", "sufficient"),
                   corpus_manifest=os.environ.get("NOTELENS_RAG_CORPUS_MANIFEST"),
                   repository_root=os.environ.get("NOTELENS_RAG_REPOSITORY_ROOT"),
                   expected_corpus_version=os.environ.get("NOTELENS_RAG_EXPECTED_CORPUS_VERSION"))


def create_app(settings=None, *, backend=None):
    configuration = settings if settings is not None else Settings.from_environment()
    if backend is not None:
        if (backend.mode != configuration.mode or not isinstance(backend.model_version, str)
                or not backend.model_version.strip()
                or (configuration.mode == 'live' and configuration.service_token is None)):
            raise ValueError('An explicit backend must match server mode and live authentication.')
    contracts = Contracts()
    app = FastAPI(title="NoteLens RAG mock service", version=__version__,
                  openapi_url=None, docs_url=None, redoc_url=None)
    app.state.mock_result = mock_result
    app.state.prepared_corpus = None
    app.state.corpus_error = None
    app.state.backend = backend
    if configuration.corpus_manifest is not None:
        try:
            app.state.prepared_corpus = load_corpus(repository_root=configuration.repository_root,
                manifest=configuration.corpus_manifest, expected_corpus_version=configuration.expected_corpus_version)
        except CorpusLoadError as failure:
            app.state.corpus_error = str(failure)
    elif configuration.expected_corpus_version is not None:
        app.state.corpus_error = "A corpus manifest must be configured when a corpus version is pinned."

    def checked_response(definition, body, status=200, headers=None):
        contracts.validate(definition, body)
        return JSONResponse(body, status_code=status, headers=headers)

    def error(status, code, identifier, message="The request could not be completed."):
        headers = {"X-Request-ID": identifier}
        if status == 401:
            headers["WWW-Authenticate"] = "Bearer"
        return checked_response("ErrorEnvelope", {
            "schema_version": "1.0.0", "request_id": identifier,
            "error": {"code": code, "message": message, "retryable": False}}, status, headers)

    def authenticated(request):
        if configuration.service_token is not None:
            values = request.headers.getlist("authorization")
            if len(values) != 1:
                return False
            scheme, separator, token = values[0].partition(" ")
            return bool(separator and scheme.lower() == "bearer" and hmac.compare_digest(
                token.encode("utf-8"), configuration.service_token.encode("utf-8")))
        try:
            return (configuration.mode == "mock" and request.client is not None
                    and ipaddress.ip_address(request.client.host).is_loopback)
        except ValueError:
            return False

    def business_id(request):
        values = request.headers.getlist("x-request-id")
        if len(values) != 1:
            return None
        try:
            contracts.validate("RequestId", values[0])
        except ContractError:
            return None
        return values[0]

    @app.get("/health/live")
    async def liveness(request: Request):
        if not authenticated(request):
            return error(401, "unauthorized", str(uuid4()), "Service authentication is required.")
        return checked_response("LivenessResult", {"schema_version": "1.0.0", "service": "rag",
                                "status": "alive", "mode": configuration.mode, "version": __version__})

    @app.get("/health/ready")
    async def readiness(request: Request):
        if not authenticated(request):
            return error(401, "unauthorized", str(uuid4()), "Service authentication is required.")
        ready = (configuration.mode == "mock" if backend is None else await run_in_threadpool(backend.is_ready))
        ready = ready is True and app.state.corpus_error is None
        return checked_response("HealthResult", {
            "schema_version": "1.0.0", "service": "rag", "status": "ok" if ready else "not_ready",
            "mode": configuration.mode, "version": __version__,
            "model_version": None if backend is None or configuration.mode == 'mock' else backend.model_version,
            "reason": None if ready else (app.state.corpus_error or "Retrieval and generation are not ready.")},
            200 if ready else 503)

    async def business(request, operation):
        identifier = business_id(request)
        if identifier is None:
            return error(400, "validation_failure", str(uuid4()), "One canonical UUID X-Request-ID is required.")
        if not authenticated(request):
            return error(401, "unauthorized", identifier, "Service authentication is required.")
        try:
            definition = "RetrievalRequest" if operation == "retrieve" else "LiteratureAnswerRequest"
            try:
                payload = contracts.parse(definition, await request.body())
            except ContractJsonError:
                return error(400, "validation_failure", identifier,
                             "A valid finite JSON body without duplicate keys is required.")
            except ContractError:
                return error(422, "validation_failure", identifier, "The request does not match the contract.")
            if app.state.corpus_error is not None:
                return error(503, "configuration_required", identifier, app.state.corpus_error)
            if backend is not None:
                try:
                    operation_handler = backend.retrieve if operation == 'retrieve' else backend.answer
                    body = await run_in_threadpool(operation_handler, payload)
                except RagServiceError as failure:
                    if failure.code in QUESTION_REJECTIONS:
                        return error(422, 'validation_failure', identifier, QUESTION_REJECTIONS[failure.code])
                    statuses = {'timeout': 504, 'rate_limit': 429, 'provider_unavailable': 503,
                                'configuration_required': 503, 'validation_failure': 422, 'internal_error': 500}
                    code = failure.code if failure.code in statuses else 'internal_error'
                    return error(statuses[code], code, identifier)
                if body.get('mode') != configuration.mode:
                    return error(500, 'internal_error', identifier)
                response_definition = 'RetrievalResult' if operation == 'retrieve' else 'AnswerResult'
                return checked_response(response_definition, body, headers={'X-Request-ID': identifier})
            if configuration.mode != "mock":
                return error(503, "configuration_required", identifier, "Live retrieval and generation are not configured.")
            if payload["question"] != DEMO_QUESTION:
                return error(422, "validation_failure", identifier,
                             "This provisional mock accepts only the documented synthetic fixture question.")
            if configuration.scenario in FAILURES:
                status, code = FAILURES[configuration.scenario]
                return error(status, code, identifier, "A server-configured mock failure was simulated.")
            body = app.state.mock_result(operation, configuration.scenario)
            response_definition = "RetrievalResult" if operation == "retrieve" else "AnswerResult"
            return checked_response(response_definition, body, headers={"X-Request-ID": identifier})
        except Exception:
            # Do not include exception text: it can contain user/provider data.
            return error(500, "internal_error", identifier, "An internal service error occurred.")

    @app.post("/v1/retrieve")
    async def retrieve(request: Request):
        return await business(request, "retrieve")

    @app.post("/v1/literature-answer")
    async def literature_answer(request: Request):
        return await business(request, "literature-answer")

    return app


app = create_app()
