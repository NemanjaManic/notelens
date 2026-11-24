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
        self._input_rate, self._output_rate = input_rate, output_rate
        self._dynamic_input = policy.get("input_reservation") == "serialized_utf8_upper_bound_v1"
        self._lock = Lock()

    def reserve(self, payload, digest):
        # The bound follows the existing reviewed UTF-8-bytes plus framing policy.
        if (payload.get("model") != self.model
                or payload.get("max_output_tokens") != self.output_limit
                or len(request_bytes(payload)) + 1024 > self.input_limit):
            raise blocked("The provider request exceeds its reviewed execution bounds.")
        with self._lock:
            cost = (Fraction((len(request_bytes(payload)) + 1024) * self._input_rate
                    + self.output_limit * self._output_rate) / 1_000_000
                    if self._dynamic_input else self._cost_per_call)
            if self._attempts >= self.call_limit:
                raise blocked("The approved provider attempt limit was reached.")
            if self._reserved + cost > self.cost_limit:
                raise blocked("The approved provider balance would be exceeded.")
            self._attempts += 1
            self._reserved += cost
            return {"attempt": self._attempts,
                    "reserved_usd": str(Decimal(cost.numerator) / Decimal(cost.denominator)),
                    "cumulative_reserved_usd": str(Decimal(self._reserved.numerator) / Decimal(self._reserved.denominator))}


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
    input_format = policy.get("input_format", "text")
    if input_format not in ("text", "messages"):
        raise ValueError("The input format must be text or messages.")
    output_format = policy.get("output_format", "contract")
    if output_format not in ("contract", "quote_hints"):
        raise ValueError("The output format must be contract or quote_hints.")
    prompt_profile = policy.get("prompt_profile", "baseline_v1")
    reasoning_effort = policy.get("reasoning_effort", "none")
    if prompt_profile not in ("baseline_v1", "coverage_v2") or (
            prompt_profile == "coverage_v2" and output_format != "quote_hints"):
        raise ValueError("The prompt profile is incompatible with the output format.")
    if reasoning_effort not in ("none", "low"):
        raise ValueError("The reasoning effort must be none or low.")
    retries = policy.get("structural_retries", 0)
    if type(retries) is not int or retries not in (0, 1):
        raise ValueError("structural_retries must be 0 or 1.")
    if type(policy.get("durable_accounting", False)) is not bool or (retries and not policy.get("durable_accounting")):
        raise ValueError("Structural retries require explicitly enabled durable accounting.")
    if policy.get("input_reservation") not in (None, "serialized_utf8_upper_bound_v1"):
        raise ValueError("Unknown input reservation policy.")
    budget = ServiceBudget(policy)
    receipt = (policy_path.resolve().parent / policy["receipt_path"]).resolve()
    transport = ResponsesTransport(
        api_key=api_key, budget=budget, receipt=receipt, timeout_seconds=timeout,
        receipt_label="NoteLens approved extraction Responses execution",
        **({"durable_accounting": True} if policy.get("durable_accounting") else {}),
    )
    provider = OpenAIResponsesProvider(
        transport, model=policy["model"], max_output_tokens=budget.output_limit,
        input_format=input_format, output_format=output_format,
        prompt_profile=prompt_profile, reasoning_effort=reasoning_effort,
    )
    provider.structural_retries = retries
    return provider
