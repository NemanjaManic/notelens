"""Construct an HTTP provider from an operator's explicit execution policy."""

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from threading import Lock

from .openai_transport import ResponsesTransport, blocked, request_bytes
from .openai_trial import OpenAIResponsesProvider


def positive_integer(policy, name):
    value = policy[name]
    if type(value) is not int or value <= 0:
        raise ValueError(f"A positive {name} is required.")
    return value


def positive_decimal(policy, name):
    value = Decimal(str(policy[name]))
    if not value.is_finite() or value <= 0:
        raise ValueError(f"A positive {name} is required.")
    return Fraction(value)


class ServiceBudget:
    """Reserve worst-case cost under one exclusively claimed execution receipt."""

    def __init__(self, policy):
        self.model = policy["model"]
        self.input_limit = positive_integer(policy, "max_input_tokens")
        self.output_limit = positive_integer(policy, "max_output_tokens")
        self.call_limit = positive_integer(policy, "max_provider_calls")
        self.cost_limit = positive_decimal(policy, "remaining_budget_usd")
        input_rate = positive_decimal(policy, "input_usd_per_million_tokens")
        output_rate = positive_decimal(policy, "output_usd_per_million_tokens")
        self._cost_per_call = (self.input_limit * input_rate + self.output_limit * output_rate) / 1_000_000
        if self._cost_per_call > self.cost_limit:
            raise ValueError("The approved balance cannot cover one worst-case request.")
        self._attempts = 0
        self._reserved = Fraction(0)
        self._lock = Lock()

    def reserve(self, payload, digest):
        # The bound follows the existing reviewed UTF-8-bytes plus framing policy.
        if (payload.get("model") != self.model
                or payload.get("max_output_tokens") != self.output_limit
                or len(request_bytes(payload)) + 1024 > self.input_limit):
            raise blocked("The provider request exceeds its reviewed execution bounds.")
        with self._lock:
            if self._attempts >= self.call_limit:
                raise blocked("The approved provider attempt limit was reached.")
            if self._reserved + self._cost_per_call > self.cost_limit:
                raise blocked("The approved provider balance would be exceeded.")
            self._attempts += 1
            self._reserved += self._cost_per_call


def configured_provider(policy_path: Path, *, api_key: str, service_token: str):
    """Validate all settings before claiming a single-use receipt or sending data."""
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise ValueError("The execution policy must be an object.")
    if (policy.get("version") != "d-extraction-provider-policy-v1"
            or policy.get("approved") is not True
            or policy.get("model_access_confirmed") is not True
            or type(policy.get("automatic_retries")) is not int
            or policy["automatic_retries"] != 0):
        raise ValueError("An approved execution policy with model access and zero retries is required.")
    for name in ("approved_by", "operator", "scope", "model", "receipt_path"):
        if not isinstance(policy.get(name), str) or not policy[name].strip():
            raise ValueError(f"The execution policy requires {name}.")
    if not service_token:
        raise ValueError("A private service bearer token is required for configured generation.")
    timeout = positive_integer(policy, "timeout_seconds")
    if timeout > 60:
        raise ValueError("The timeout must be at most 60 seconds.")
    budget = ServiceBudget(policy)
    receipt = (policy_path.resolve().parent / policy["receipt_path"]).resolve()
    transport = ResponsesTransport(
        api_key=api_key, budget=budget, receipt=receipt, timeout_seconds=timeout,
        receipt_label="NoteLens approved extraction Responses execution",
    )
    return OpenAIResponsesProvider(
        transport, model=policy["model"], max_output_tokens=budget.output_limit,
    )
