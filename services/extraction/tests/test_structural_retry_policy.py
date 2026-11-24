"""Explicit opt-in structural retries retain strict output and spend checks."""
import json
from decimal import Decimal
from unittest.mock import Mock

import pytest

from notelens_extraction.approved_provider import ServiceBudget
from notelens_extraction.demo import request
from notelens_extraction.errors import ServiceError
from notelens_extraction.openai_transport import ResponsesTransport
from notelens_extraction.openai_trial import MODEL
from notelens_extraction.providers import FakeProvider
from notelens_extraction.service import run
from test_approved_provider import live_fixture


class ScriptedLive:
    mode = 'live'
    structural_retries = 1

    def __init__(self, first):
        self.first = first
        self.calls = []

    def generate(self, operation, payload, instructions, *, repair):
        self.calls.append(repair)
        if len(self.calls) == 1:
            if isinstance(self.first, Exception):
                raise self.first
            return self.first
        return json.dumps(live_fixture(json.loads(FakeProvider().generate(operation, payload, instructions, repair=False))))


def test_opt_in_retries_invalid_structure_without_mock_repair():
    provider = ScriptedLive('not JSON')
    result, diagnostics = run(request(), 'extract', provider)
    assert result['mode'] == 'live'
    assert provider.calls == [False, False]
    assert diagnostics == {'attempts': 2, 'raw_validation_failures': 1, 'repairs': 1}


@pytest.mark.parametrize('failure', [ServiceError(504,'timeout','timeout'),
    ServiceError(503,'provider_unavailable','provider failure'),
    ServiceError(429,'rate_limit','rate limit'), ServiceError(422,'configuration_required','configuration')])
def test_operational_failures_never_retry(failure):
    provider = ScriptedLive(failure)
    with pytest.raises(ServiceError) as caught:
        run(request(), 'extract', provider)
    assert caught.value is failure
    assert provider.calls == [False]


def policy():
    return {'model':MODEL,'max_input_tokens':64000,'max_output_tokens':512,
        'max_provider_calls':2,'remaining_budget_usd':'0.50',
        'input_usd_per_million_tokens':'0.1375','output_usd_per_million_tokens':'0.55',
        'input_reservation':'serialized_utf8_upper_bound_v1'}


def test_dynamic_reservation_remains_positive_exact_and_enforces_call_cap():
    budget = ServiceBudget(policy())
    payload = {'model':MODEL,'max_output_tokens':512}
    first = budget.reserve(payload,'same-request')
    second = budget.reserve(payload,'same-request')
    assert Decimal(first['reserved_usd']) > 0
    assert Decimal(second['cumulative_reserved_usd']) == 2 * Decimal(first['reserved_usd'])
    with pytest.raises(ServiceError):
        budget.reserve(payload,'same-request')


def test_durable_reservation_precedes_dispatch_and_records_usage_without_secrets(tmp_path):
    receipt=tmp_path/'receipt.jsonl'
    connect=Mock()
    response=connect.return_value.getresponse.return_value
    response.status=200
    response.getheader.return_value='req_offline'
    response.read.return_value=b'{"usage":{"input_tokens":4,"output_tokens":2,"total_tokens":6}}'
    def dispatch(*args, **kwargs):
        rows=receipt.read_text().splitlines()
        assert json.loads(rows[-1])['event']=='reserved_before_dispatch'
    connect.return_value.request.side_effect=dispatch
    transport=ResponsesTransport(api_key='secret-canary',budget=ServiceBudget(policy()),receipt=receipt,
                                connect=connect,durable_accounting=True)
    transport({'model':MODEL,'max_output_tokens':512})
    rows=[json.loads(line) for line in receipt.read_text().splitlines()[1:]]
    assert [row['event'] for row in rows]==['reserved_before_dispatch','outcome']
    assert rows[-1]['usage']['total_tokens']==6
    assert rows[-1]['provider_request_id']=='req_offline'
    assert 'secret-canary' not in receipt.read_text()
