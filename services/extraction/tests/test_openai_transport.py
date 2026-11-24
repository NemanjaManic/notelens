"""Exercise the real HTTP boundary with a fake connection and reviewed test bounds."""

import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from unittest.mock import Mock

import pytest

from notelens_extraction.demo import request
from notelens_extraction.errors import ServiceError
from notelens_extraction.openai_trial import MODEL, OpenAITrialProvider
from notelens_extraction.openai_transport import ResponsesTransport, TrialBudget, request_sha256
from notelens_extraction.service import generation_instructions, run


def transport_for(tmp_path, payloads, *, rate="1", input_bound=100, status=200):
    connect = Mock()
    response = connect.return_value.getresponse.return_value
    response.status = status
    response.read.return_value = b'{"status":"completed"}'
    budget = TrialBudget({request_sha256(payload): input_bound for payload in payloads},
                         input_usd_per_million=Decimal(rate), output_usd_per_million=Decimal(rate))
    transport = ResponsesTransport(api_key="offline-test", budget=budget,
                                   receipt=tmp_path / "receipt", connect=connect)
    return transport, connect, budget


def test_total_budget_is_reserved_before_contact(tmp_path):
    first = {"model": MODEL, "max_output_tokens": 100}
    second = {**first, "max_output_tokens": 101}
    transport, connect, _ = transport_for(tmp_path, [first, second], rate="500", status=503)
    with pytest.raises(ServiceError, match="unsuccessful"):
        transport(first)  # Reserves exactly USD 0.10 despite ambiguous provider outcome.
    with pytest.raises(ServiceError, match="budget"):
        transport(second)
    with pytest.raises(ServiceError, match="attempt limit"):
        transport(first)
    connect.assert_called_once()


def test_concurrent_requests_share_one_attempt_limit(tmp_path):
    payloads = [{"model": MODEL, "max_output_tokens": limit} for limit in range(100, 108)]
    transport, connect, _ = transport_for(tmp_path, payloads)

    def attempt(payload):
        try:
            transport(payload)
            return True
        except ServiceError as error:
            assert "attempt limit" in error.message
            return False

    with ThreadPoolExecutor(max_workers=8) as executor:
        assert sum(executor.map(attempt, payloads)) == 3
    assert connect.call_count == 3


def test_exact_synthetic_request_and_receipt(tmp_path):
    prepare = OpenAITrialProvider(Mock(), max_output_tokens=500)
    payload = prepare.prepare("extract", request(), generation_instructions("extract")[0])
    transport, connect, budget = transport_for(tmp_path, [payload])
    with pytest.raises(ServiceError, match="reviewed cost bound"):
        transport({**payload, "instructions": "modified"})
    connect.assert_not_called()

    connection = connect.return_value
    connection.getresponse.return_value.read.return_value = json.dumps({
        "model": MODEL, "object": "response", "status": "completed", "output": [
            {"type": "message", "role": "assistant", "status": "completed",
             "content": [{"type": "output_text", "text": "{}"}]},
        ],
    }).encode()
    with pytest.raises(ServiceError, match="Generated output failed validation"):
        run(request(), "extract", OpenAITrialProvider(transport, max_output_tokens=500))
    connect.assert_called_once_with("api.openai.com", timeout=30)
    assert connection.request.call_args.args == ("POST", "/v1/responses")
    assert json.loads(connection.request.call_args.kwargs["body"]) == payload
    connection.close.assert_called_once()

    with pytest.raises(FileExistsError):
        ResponsesTransport(api_key="offline-test", budget=budget,
                           receipt=tmp_path / "receipt", connect=connect)
    assert "offline-test" not in (tmp_path / "receipt").read_text()


def test_timeout_is_sanitized_and_not_retried(tmp_path):
    payload = {"model": MODEL, "max_output_tokens": 100}
    transport, connect, _ = transport_for(tmp_path, [payload])
    connect.return_value.getresponse.side_effect = TimeoutError("private upstream message")
    with pytest.raises(ServiceError) as failure:
        transport(payload)
    assert failure.value.status == 504
    assert "private" not in failure.value.message
    with pytest.raises(ServiceError, match="attempt limit"):
        transport(payload)
    connect.assert_called_once()


def test_non_success_preserves_safe_operator_diagnostics_without_public_leak(tmp_path):
    payload = {"model": MODEL, "max_output_tokens": 100}
    transport, connect, _ = transport_for(tmp_path, [payload], status=400)
    response = connect.return_value.getresponse.return_value
    response.read.return_value = json.dumps({"error": {
        "type": "invalid_request_error", "param": "input",
        "message": "private document text and credential", "code": "private-token",
    }}).encode()
    with pytest.raises(ServiceError) as failure:
        transport(payload)
    assert failure.value.provider_diagnostics == {
        "http_status": 400, "provider_error_type": "invalid_request_error", "provider_error_param": "input"}
    assert "private" not in repr(failure.value)
    assert "http_status" not in json.dumps(failure.value.envelope("request"))
    assert failure.value.retryable is False
    with pytest.raises(ServiceError, match="attempt limit"):
        transport(payload)
    connect.assert_called_once()


@pytest.mark.parametrize("raw", [b'not json', b'x' * 8193,
    b'{"error":{"type":"secret","code":"secret","param":"secret","message":"secret"}}'])
def test_invalid_error_bodies_keep_status_only(tmp_path, raw):
    payload = {"model": MODEL, "max_output_tokens": 100}
    transport, connect, _ = transport_for(tmp_path, [payload], status=401)
    connect.return_value.getresponse.return_value.read.return_value = raw
    with pytest.raises(ServiceError) as failure:
        transport(payload)
    assert failure.value.provider_diagnostics == {"http_status": 401}
    assert "secret" not in repr(failure.value)
    connect.return_value.close.assert_called_once()
