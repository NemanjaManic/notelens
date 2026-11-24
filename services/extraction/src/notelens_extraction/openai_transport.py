"""Prepaid reservations and single-attempt HTTPS for the synthetic Responses trial."""

import hashlib
import http.client
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from threading import Lock

from .errors import ServiceError
from .openai_trial import MODEL, OpenAITrialProvider

MAX_COST = Fraction(1, 10)
MAX_CALLS = 3
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_ERROR_BYTES = 8192


def provider_failure(response) -> ServiceError:
    """Keep bounded, allowlisted operator diagnostics outside the public envelope."""
    diagnostics = {"http_status": response.status}
    # Do not retain upstream free text, document content, headers or credentials.
    # Unknown values are omitted rather than copied into a private/public log.
    try:
        raw = response.read(MAX_ERROR_BYTES + 1)
        body = json.loads(raw) if len(raw) <= MAX_ERROR_BYTES else None
        error = body.get("error") if isinstance(body, dict) else None
        if isinstance(error, dict):
            allowed = {
                "type": {"invalid_request_error", "authentication_error", "permission_error", "rate_limit_error", "server_error"},
                "code": {"invalid_api_key", "model_not_found", "insufficient_quota", "rate_limit_exceeded", "unsupported_parameter", "invalid_value"},
                "param": {"input", "model", "max_output_tokens", "reasoning", "reasoning.effort", "text.format", "tools", "tool_choice"},
            }
            for field, values in allowed.items():
                value = error.get(field)
                if isinstance(value, str) and value in values:
                    diagnostics["provider_error_" + field] = value
    except (ValueError, UnicodeError, RecursionError, TypeError, OSError, http.client.HTTPException):
        pass
    return ServiceError(503, "provider_unavailable", "The Responses request was unsuccessful.",
                        provider_diagnostics=diagnostics)


def request_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def request_sha256(payload: dict) -> str:
    return hashlib.sha256(request_bytes(payload)).hexdigest()


def blocked(message: str) -> ServiceError:
    return ServiceError(503, "configuration_required", message)


class TrialBudget:
    """Reserve full input and output ceilings before any network attempt."""

    def __init__(self, approved_input_bounds: dict[str, int], *,
                 input_usd_per_million: Decimal, output_usd_per_million: Decimal):
        rates = (input_usd_per_million, output_usd_per_million)
        if any(not isinstance(rate, Decimal) or not rate.is_finite() or rate <= 0 for rate in rates):
            raise ValueError("Positive reviewed token rates are required.")
        if not approved_input_bounds or any(
                type(bound) is not int or bound <= 0 for bound in approved_input_bounds.values()):
            raise ValueError("Reviewed input token bounds are required.")
        self._bounds = dict(approved_input_bounds)
        self._input_rate, self._output_rate = map(Fraction, rates)
        self._attempted: set[str] = set()
        self._reserved = Fraction(0)
        self._lock = Lock()

    def reserve(self, payload: dict, digest: str) -> None:
        input_limit = self._bounds.get(digest)
        output_limit = payload.get("max_output_tokens")
        if payload.get("model") != MODEL or input_limit is None or type(output_limit) is not int or output_limit <= 0:
            raise blocked("The exact Responses request lacks a reviewed cost bound.")
        cost = (input_limit * self._input_rate + output_limit * self._output_rate) / 1_000_000
        with self._lock:
            if digest in self._attempted or len(self._attempted) >= MAX_CALLS:
                raise blocked("The Responses trial attempt limit was reached.")
            if self._reserved + cost > MAX_COST:
                raise blocked("The Responses trial budget would be exceeded.")
            self._attempted.add(digest)
            self._reserved += cost


class ResponsesTransport:
    """Send only reserved requests to a fixed endpoint, without retries or redirects."""

    def __init__(self, *, api_key: str, budget: TrialBudget, receipt: Path,
                 timeout_seconds: int = 30, connect=http.client.HTTPSConnection,
                 receipt_label: str = "NoteLens synthetic extraction Responses trial"):
        if not api_key or not api_key.isascii() or not api_key.isprintable() or any(c.isspace() for c in api_key):
            raise ValueError("A valid server-side credential is required.")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
            raise ValueError("The socket timeout must be between 1 and 60 seconds.")
        # A receipt is never removed or reused, including after a crash.
        with receipt.open("x", encoding="ascii") as handle:
            handle.write(receipt_label + "\n")
        self._api_key = api_key
        self._budget = budget
        self._timeout = timeout_seconds
        self._connect = connect

    def __call__(self, payload: dict) -> dict:
        body = request_bytes(payload)
        self._budget.reserve(payload, hashlib.sha256(body).hexdigest())
        connection = None
        try:
            connection = self._connect("api.openai.com", timeout=self._timeout)
            connection.request("POST", "/v1/responses", body=body, headers={
                "Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json",
            })
            response = connection.getresponse()
            if response.status != 200:
                raise provider_failure(response)
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ServiceError(502, "internal_error", "The Responses payload exceeded the size limit.")
            return json.loads(raw)
        except TimeoutError:
            raise ServiceError(504, "timeout", "The Responses request timed out.") from None
        except (OSError, http.client.HTTPException):
            raise ServiceError(503, "provider_unavailable", "The Responses request failed.") from None
        except (ValueError, UnicodeError, RecursionError):
            raise ServiceError(502, "internal_error", "The Responses payload was invalid.") from None
        finally:
            if connection is not None:
                connection.close()


def trial_provider(*, api_key: str, budget: TrialBudget, receipt: Path,
                   max_output_tokens: int) -> OpenAITrialProvider:
    transport = ResponsesTransport(api_key=api_key, budget=budget, receipt=receipt)
    return OpenAITrialProvider(transport, max_output_tokens=max_output_tokens)
