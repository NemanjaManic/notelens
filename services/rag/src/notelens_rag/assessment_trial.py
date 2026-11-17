"""Plan a three-public-question Luna trial; generation needs separate approval."""

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import ssl
import sys

from dotenv import dotenv_values
import openai

from .assessor import (MODEL, AssessmentError, AssessmentParameters, _require, _strict_json,
    assessment_count_request, assessment_request, checked_assessment_response, prepare_assessment)
from .diagnostics import safe_diagnostic
from .embeddings import SERVICE_ROOT, identity
from .indexing import IndexBuildError, atomic_json, exclusive_build, read_json
from .ingestion import load_corpus, owned_file, repository_directory


PROPOSAL = 'docs/rag/assessment-trial-proposal.json'
QUESTION_IDS = ('CQ-01', 'CQ-02', 'CQ-08')
CACHE = 'services/rag/.cache/assessment-trial'


@dataclass(frozen=True)
class AssessmentSettings:
    api_key: str | None = field(default=None, repr=False)
    enabled: bool = False


def read_assessment_settings(env_file=None):
    path = Path(env_file) if env_file is not None else SERVICE_ROOT / '.env'
    try:
        values = dict(dotenv_values(path, interpolate=False)) if path.is_file() else {}
    except (OSError, UnicodeError):
        raise AssessmentError('configuration_required') from None
    for key in ('OPENAI_API_KEY', 'NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS'):
        if key in os.environ:
            values[key] = os.environ[key]
    enabled = values.get('NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS') or 'false'
    _require(enabled in ('true', 'false'), 'configuration_required')
    return AssessmentSettings(values.get('OPENAI_API_KEY'), enabled == 'true')


def _money(value):
    try:
        _require(type(value) in (str, int) or isinstance(value, Decimal), 'trial_state_invalid')
        result = Decimal(value)
        _require(result.is_finite() and result >= 0, 'trial_state_invalid')
        return result
    except (InvalidOperation, TypeError, ValueError):
        raise AssessmentError('trial_state_invalid') from None


def _validate_plan(plan, cases):
    _require(plan.get('format_version') == 'public-luna-assessment-trial-v1'
             and plan.get('public_english_only') is True and plan.get('model') == MODEL,
             'trial_scope_invalid')
    _require(tuple(plan.get('question_ids', ())) == QUESTION_IDS and set(cases) == set(QUESTION_IDS),
             'trial_scope_invalid')
    parameters = AssessmentParameters(**plan['parameters'])
    limits = plan['limits']
    _require(type(limits['max_input_tokens']) is int and 0 < limits['max_input_tokens'] <= 20000
             and limits['max_generation_attempts'] == 3
             and type(limits['max_generation_attempts']) is int
             and 0 < _money(limits['max_usd']) <= Decimal('0.02'), 'trial_scope_invalid')
    _require(parameters.max_output_tokens <= 2048 and parameters.reasoning_effort == 'none'
             and parameters.timeout_seconds <= 30, 'trial_scope_invalid')
    _require(_money(plan['prices']['input_usd_per_million']) == Decimal('0.10')
             and _money(plan['prices']['output_usd_per_million']) == Decimal('0.50'), 'trial_scope_invalid')
    _require(all(p.prompt_sha256 == plan['prompt_sha256'] for p in cases.values()), 'trial_scope_invalid')
    return parameters


def _cost(plan, input_tokens, output_tokens):
    return (Decimal(input_tokens)*_money(plan['prices']['input_usd_per_million'])
            + Decimal(output_tokens)*_money(plan['prices']['output_usd_per_million']))/1_000_000


def _client(settings, parameters):
    _require(isinstance(settings.api_key, str) and bool(settings.api_key.strip()), 'configuration_required')
    return openai.OpenAI(api_key=settings.api_key, base_url='https://api.openai.com/v1',
        timeout=parameters.timeout_seconds, max_retries=0,
        http_client=openai.DefaultHttpxClient(verify=ssl.create_default_context(), follow_redirects=False))


def _call(operation, **kwargs):
    try:
        return operation(**kwargs)
    except openai.APITimeoutError:
        raise AssessmentError('timeout') from None
    except openai.RateLimitError:
        raise AssessmentError('rate_limit') from None
    except (openai.AuthenticationError, openai.PermissionDeniedError):
        raise AssessmentError('provider_authentication') from None
    except openai.APIError:
        raise AssessmentError('provider_unavailable') from None


def _count(client, prepared, parameters, limit):
    raw = _call(client.responses.input_tokens.with_raw_response.count,
                **assessment_count_request(prepared, parameters))
    result = _strict_json(raw.http_response.content)
    _require(isinstance(result, dict) and result.get('object') == 'response.input_tokens'
             and type(result.get('input_tokens')) is int and result['input_tokens'] > 0, 'invalid_upstream')
    _require(result['input_tokens'] <= limit, 'input_limit_exceeded')
    return result['input_tokens']


def load_public_trial(repository_root=None):
    root = repository_directory(repository_root)
    plan = read_json(owned_file(root, PROPOSAL, 'docs/rag'))
    sources = {}
    for key in ('results', 'review', 'registry'):
        item = plan['sources'][key]
        path = owned_file(root, item['path'], 'docs/rag')
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], 'trial_scope_invalid')
        sources[key] = read_json(path)
    report, review, registry = (sources[key] for key in ('results', 'review', 'registry'))
    _require(registry.get('public_development_only') is True and registry.get('language') == 'en',
             'trial_scope_invalid')
    corpus = load_corpus(repository_root=root, expected_corpus_version=report['corpus_version'])
    cases = {}
    for identifier in QUESTION_IDS:
        observed = next(row for row in report['results'] if row['question_id'] == identifier)
        reviewed = next(row for row in review['cases'] if row['question_id'] == identifier)
        registered = next(row for row in registry['cases'] if row['question_id'] == identifier)
        question = observed['question']
        _require(question == reviewed['question'] == registered['question'], 'trial_scope_invalid')
        passages = []
        for passage in observed['passages']:
            original = corpus.by_id[passage['passage_id']]
            _require(all(passage[key] == getattr(original, key) for key in
                         ('topic_id', 'passage_id', 'title', 'url'))
                     and passage['source_id'] == original.passage_id
                     and passage['snapshot_date'] == corpus.snapshot_date, 'trial_scope_invalid')
            passages.append({**passage, 'text': original.text})
        candidates = {'record_format_version': 'rag-candidate-ranking-v1', 'status': 'ranked_candidates',
            'mode': 'live', 'answerability': 'not_assessed',
            'question_sha256': hashlib.sha256(question.encode('utf-8')).hexdigest(),
            'passages': passages, 'top_k': report['top_k'], 'signals_used': ['question'],
            **{key: report[key] for key in ('corpus_version', 'index_version', 'retriever_version')},
            'score_note': 'Saved candidate ranking; semantic support not assessed.'}
        # Only requested-part descriptions are supplied; expected verdicts are not model input.
        requirements = [{'requirement_id': f'part-{i+1}', 'description': description}
                        for i, description in enumerate(reviewed['required_parts'])]
        cases[identifier] = prepare_assessment({'schema_version': '1.0.0', 'question': question},
                                             candidates, requirements)
    _validate_plan(plan, cases)
    return root, plan, cases


def count_public_inputs(plan, cases, *, client_factory=None, mode='live'):
    """Explicit free token-count preflight; this function cannot generate responses."""
    parameters = _validate_plan(plan, cases)
    _require(mode in ('mock', 'live'), 'configuration_required')
    _require(mode == 'live' or client_factory is not None, 'configuration_required')
    client = (client_factory or (lambda: _client(read_assessment_settings(), parameters)))()
    rows = []
    try:
        for identifier in QUESTION_IDS:
            prepared = cases[identifier]
            tokens = _count(client, prepared, parameters, plan['limits']['max_input_tokens'])
            rows.append({'question_id': identifier, 'context_sha256': prepared.context_sha256,
                'input_tokens': tokens, 'max_output_tokens': parameters.max_output_tokens,
                'estimated_max_generation_usd': str(_cost(plan, tokens, parameters.max_output_tokens)),
                'request_text_bytes': sum(len(value.encode('utf-8')) for value in
                    (prepared.instructions, prepared.input_json, prepared.schema_json))})
    finally:
        client.close()
    return {'format_version': 'public-luna-input-preflight-v1', 'mode': mode,
        'execution_approved': plan['execution_approved'], 'model': MODEL,
        'prompt_sha256': plan['prompt_sha256'], 'count_calls': len(rows), 'generation_calls': 0,
        'total_input_tokens': sum(row['input_tokens'] for row in rows),
        'maximum_output_tokens_total': len(rows)*parameters.max_output_tokens,
        'estimated_max_generation_usd': str(sum(_money(row['estimated_max_generation_usd']) for row in rows)),
        'proposed_budget_usd': plan['limits']['max_usd'], 'prices': plan['prices'], 'cases': rows}


class PublicAssessmentTrial:
    def __init__(self, plan, cases, folder, *, mode='live', settings=None, client_factory=None):
        self.plan, self.cases = deepcopy(plan), dict(cases)
        self.parameters = _validate_plan(self.plan, self.cases)
        _require(mode in ('mock', 'live'), 'configuration_required')
        _require(mode == 'live' or client_factory is not None, 'configuration_required')
        self.folder, self.mode, self.settings = Path(folder), mode, settings
        self.client_factory = client_factory

    @property
    def scope_sha256(self):
        plan = {k: v for k, v in self.plan.items() if k not in ('execution_approved', 'approval')}
        return identity({'format': 'bounded-assessment-run-v1', 'mode': self.mode,
            'service_tier': 'default', 'plan': plan,
            'contexts': {key: value.context_sha256 for key, value in self.cases.items()}})

    def preflight(self):
        return {'scope_sha256': self.scope_sha256, 'execution_approved': self.plan['execution_approved'],
            'model': MODEL, 'question_ids': list(QUESTION_IDS), 'limits': self.plan['limits'],
            'parameters': self.plan['parameters'], 'provider_calls': 0,
            'input_tokens': 'Not counted locally; use explicit --count-inputs for provider counting.',
            'max_generation_usd_at_input_limits': str(_cost(self.plan,
                3*self.plan['limits']['max_input_tokens'], 3*self.parameters.max_output_tokens))}

    def _ledger(self):
        path = self.folder/'usage.json'
        if not path.exists():
            _require(not any((self.folder/'results').glob('*.json')), 'trial_state_invalid')
            return {'format': 'assessment-usage-v1', 'scope_sha256': self.scope_sha256,
                'max_usd': self.plan['limits']['max_usd'], 'reserved_usd': '0',
                'confirmed_usd': '0', 'halted': False, 'attempts': []}
        ledger = read_json(path)
        _require(ledger.get('format') == 'assessment-usage-v1'
                 and ledger.get('scope_sha256') == self.scope_sha256
                 and _money(ledger.get('max_usd')) == _money(self.plan['limits']['max_usd']), 'trial_state_invalid')
        attempts = ledger.get('attempts')
        _require(isinstance(attempts, list) and len(attempts) <= 3
                 and type(ledger.get('halted')) is bool, 'trial_state_invalid')
        _require(all(isinstance(a, dict) and a.get('question_id') in self.cases
                     and a.get('status') in ('counting', 'reserved', 'confirmed', 'failed') for a in attempts),
                 'trial_state_invalid')
        _require(len({a['question_id'] for a in attempts}) == len(attempts), 'trial_state_invalid')
        reserved = sum(_money(a['reserved_usd']) for a in attempts)
        confirmed = sum(_money(a.get('confirmed_usd', '0')) for a in attempts)
        _require(reserved == _money(ledger.get('reserved_usd')) <= _money(ledger['max_usd'])
                 and confirmed == _money(ledger.get('confirmed_usd')) <= reserved, 'trial_state_invalid')
        for attempt in attempts:
            _require(attempt.get('context_sha256') == self.cases[attempt['question_id']].context_sha256,
                     'trial_state_invalid')
            if _money(attempt['reserved_usd']) > 0:
                tokens = attempt.get('counted_input_tokens')
                _require(type(tokens) is int and 0 < tokens <= self.plan['limits']['max_input_tokens']
                         and _money(attempt['reserved_usd']) == _cost(self.plan, tokens, self.parameters.max_output_tokens),
                         'trial_state_invalid')
        return ledger

    def run(self, question_id, *, execute=False, budget_usd=None):
        _require(question_id in self.cases and type(execute) is bool, 'trial_scope_invalid')
        _validate_plan(self.plan, self.cases)
        # Gate before creating a ledger/client, except for an existing read-only cached result.
        if not (self.folder/'usage.json').exists():
            self._authorize(execute, budget_usd)
        self.folder.mkdir(parents=True, exist_ok=True)
        try:
            with exclusive_build(self.folder):
                return self._run_locked(question_id, execute, budget_usd)
        except AssessmentError:
            raise
        except (IndexBuildError, KeyError, TypeError, ValueError, OSError):
            raise AssessmentError('trial_state_invalid') from None

    def _authorize(self, execute, budget_usd):
        approval = self.plan.get('approval')
        _require(execute is True and self.plan.get('execution_approved') is True
                 and isinstance(approval, dict)
                 and isinstance(approval.get('actor'), str) and bool(approval['actor'].strip())
                 and isinstance(approval.get('date'), str) and bool(approval['date'].strip())
                 and approval.get('scope_sha256') == self.scope_sha256, 'execution_not_approved')
        _require(budget_usd is not None and _money(budget_usd) == _money(self.plan['limits']['max_usd']),
                 'budget_not_approved')
        settings = self.settings if self.settings is not None else read_assessment_settings()
        _require(settings.enabled is True and isinstance(settings.api_key, str)
                 and bool(settings.api_key.strip()), 'configuration_required')

    def _run_locked(self, question_id, execute, budget_usd):
        ledger = self._ledger()
        existing = next((a for a in ledger['attempts'] if a['question_id'] == question_id), None)
        if existing and existing['status'] == 'confirmed':
            cache = self.folder/'results'/f'{question_id}.json'
            _require(cache.is_file() and hashlib.sha256(cache.read_bytes()).hexdigest() == existing['result_sha256'],
                     'trial_cache_invalid')
            result = read_json(cache)
            _require(result['scope_sha256'] == self.scope_sha256 and result['question_id'] == question_id,
                     'trial_cache_invalid')
            return {**result, 'cache_hit': True}
        self._authorize(execute, budget_usd)
        _require(not ledger['halted'] and existing is None
                 and all(a['status'] == 'confirmed' for a in ledger['attempts'])
                 and len(ledger['attempts']) < 3, 'trial_retry_not_approved')
        attempt = {'question_id': question_id, 'context_sha256': self.cases[question_id].context_sha256,
                   'status': 'counting', 'reserved_usd': '0', 'confirmed_usd': '0'}
        ledger['attempts'].append(attempt)
        path = self.folder/'usage.json'
        atomic_json(path, ledger)
        client = None
        try:
            settings = self.settings if self.settings is not None else read_assessment_settings()
            client = (self.client_factory or (lambda: _client(settings, self.parameters)))()
            prepared = self.cases[question_id]
            tokens = _count(client, prepared, self.parameters, self.plan['limits']['max_input_tokens'])
            reservation = _cost(self.plan, tokens, self.parameters.max_output_tokens)
            total = _money(ledger['reserved_usd']) + reservation
            _require(total <= _money(ledger['max_usd']), 'budget_exceeded')
            attempt.update(status='reserved', counted_input_tokens=tokens, reserved_usd=str(reservation))
            ledger['reserved_usd'] = str(total)
            atomic_json(path, ledger)  # Persist before the potentially billable request.
            raw = _call(client.responses.with_raw_response.create,
                        **assessment_request(prepared, self.parameters), service_tier='default')
            body = _strict_json(raw.http_response.content)
            _require(isinstance(body, dict) and body.get('service_tier') == 'default', 'pricing_mode_mismatch')
            result = checked_assessment_response(raw.http_response.content, prepared, self.parameters, mode=self.mode)
            _require(result.input_tokens == tokens, 'input_count_mismatch')
            value = {'scope_sha256': self.scope_sha256, 'question_id': question_id,
                'context_sha256': prepared.context_sha256, 'result': asdict(result)}
            cache = self.folder/'results'/f'{question_id}.json';cache.parent.mkdir(exist_ok=True)
            atomic_json(cache, value)
            charge = _cost(self.plan, result.input_tokens, result.output_tokens)
            attempt.update(status='confirmed', confirmed_usd=str(charge),
                input_tokens=result.input_tokens, output_tokens=result.output_tokens,
                result_sha256=hashlib.sha256(cache.read_bytes()).hexdigest())
            ledger['confirmed_usd'] = str(_money(ledger['confirmed_usd'])+charge)
            atomic_json(path, ledger)
            return {**value, 'cache_hit': False}
        except BaseException as failure:
            if isinstance(failure, AssessmentError):
                attempt['diagnostic'] = safe_diagnostic(failure)
            attempt['status'] = 'failed';ledger['halted'] = True
            atomic_json(path, ledger)
            raise
        finally:
            if client is not None:
                client.close()


def main():
    parser = argparse.ArgumentParser(description='Prepare or explicitly run the three-public-question Luna trial.')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--count-inputs', action='store_true', help='Only free input counting; never generate.')
    action.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd')
    args = parser.parse_args()
    try:
        root, plan, cases = load_public_trial()
        folder = owned_file(root, CACHE, 'services/rag/.cache')
        session = PublicAssessmentTrial(plan, cases, folder)
        if args.count_inputs:
            report = count_public_inputs(plan, cases)
            folder.mkdir(parents=True, exist_ok=True)
            atomic_json(folder/'preflight-counts.json', report)
            print(json.dumps(report, indent=2))
        elif args.execute:
            for identifier in QUESTION_IDS:
                result = session.run(identifier, execute=True, budget_usd=args.budget_usd)
                decision = result['result']['decision']
                print(json.dumps({'question_id': identifier, 'coverage': decision['coverage'],
                    'cache_hit': result['cache_hit'], 'input_tokens': result['result']['input_tokens'],
                    'output_tokens': result['result']['output_tokens']}), flush=True)
        else:
            print(json.dumps(session.preflight(), indent=2))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error),
                          'diagnostic': safe_diagnostic(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'trial_failed',
                          'message': 'The public assessment trial stopped safely.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
