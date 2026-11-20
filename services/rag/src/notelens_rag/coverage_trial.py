"""Prepare two ordered v2 evidence probes; paid execution needs separate approval."""

import argparse
from contextlib import ExitStack
from copy import deepcopy
import hashlib
from pathlib import Path
import json
import re
import sys

from .assessment_trial import (
    CACHE as ORIGINAL_CACHE, AssessmentError, PublicAssessmentTrial, _cost, _money,
    _require, _strict_json, _validate_plan, load_public_trial,
)
from .assessment_retry import CACHE as RETRY_CACHE, PROPOSAL as RETRY_PROPOSAL
from .assessor import assessment_request
from .diagnostics import safe_diagnostic
from .embeddings import identity
from .evidence_selection import EVIDENCE_POLICY, PROMPT_VERSION, PreparedSelection, prepare_selection
from .indexing import IndexBuildError, exclusive_build, read_json
from .ingestion import owned_file
from .selection_trial import CACHE as PREVIOUS_CACHE, PROPOSAL as PREVIOUS_PROPOSAL, PublicSelectionTrial


QUESTION_IDS = ('CQ-02', 'CQ-08')
PROPOSAL = 'docs/rag/coverage-trial-proposal.json'
CACHE = 'services/rag/.cache/coverage-trial-v2'


class PublicCoverageTrial(PublicSelectionTrial):
    """Reuse v2 authorization, quote validation and cumulative ledger handling."""

    max_attempts = 2
    ledger_format = 'coverage-trial-usage-v2'

    def __init__(self, source_plan, source_cases, *, original_folder, retry_plan, retry_folder,
                 previous_proposal, previous_folder, proposal, prepared, folder, **kwargs):
        # The original source context remains three v1 snapshots. This controller
        # then selects exactly two v2 inputs instead of the parent's single CQ-01.
        PublicAssessmentTrial.__init__(self, source_plan, source_cases, folder, **kwargs)
        self.source_cases, self.cases = self.cases, dict(prepared)
        self.original_folder, self.retry_folder, self.previous_folder = map(Path,
            (original_folder, retry_folder, previous_folder))
        self.retry_plan, self.previous_proposal = deepcopy(retry_plan), deepcopy(previous_proposal)
        self.proposal = deepcopy(proposal)
        _require(len({path.resolve() for path in (self.original_folder, self.retry_folder,
                     self.previous_folder, self.folder)}) == 4, 'coverage_scope_invalid')
        self._validate_preparation()

    def _validate_preparation(self):
        parameters = _validate_plan(self.plan, self.source_cases)
        proposal = self.proposal
        _require(parameters == self.parameters and set(self.cases) == set(QUESTION_IDS)
                 and isinstance(proposal, dict) and proposal.get('format_version') == 'public-coverage-trial-v2'
                 and proposal.get('question_ids') == list(QUESTION_IDS)
                 and type(proposal.get('max_new_attempts')) is int and proposal['max_new_attempts'] == 2
                 and type(proposal.get('max_attempts_per_question')) is int and proposal['max_attempts_per_question'] == 1
                 and proposal.get('prompt_version') == PROMPT_VERSION
                 and proposal.get('evidence_policy') == EVIDENCE_POLICY
                 and _money(proposal.get('cumulative_max_usd')) == _money(self.plan['limits']['max_usd']),
                 'coverage_scope_invalid')
        requests = proposal.get('requests')
        _require(isinstance(requests, dict) and set(requests) == set(QUESTION_IDS), 'coverage_scope_invalid')
        for identifier in QUESTION_IDS:
            source = _strict_json(self.source_cases[identifier].inputs_json, stage='context')
            expected = prepare_selection(source['request'], source['candidates'], source['requirements'])
            prepared, bound = self.cases[identifier], requests[identifier]
            _require(type(prepared) is PreparedSelection and prepared == expected and isinstance(bound, dict)
                     and proposal.get('prompt_sha256') == prepared.prompt_sha256
                     and bound.get('context_sha256') == prepared.context_sha256
                     and bound.get('selection_sha256') == prepared.selection_sha256
                     and bound.get('request_sha256') == identity(assessment_request(prepared, parameters)),
                     'coverage_scope_invalid')
        prior = proposal.get('prior_trial')
        _require(isinstance(prior, dict), 'coverage_scope_invalid')
        for key in ('scope_sha256', 'ledger_sha256', 'result_sha256', 'original_ledger_sha256', 'retry_ledger_sha256'):
            _require(isinstance(prior.get(key), str) and re.fullmatch('[0-9a-f]{64}', prior[key]) is not None,
                     'coverage_scope_invalid')
        _require(0 <= _money(prior.get('confirmed_usd')) <= _money(prior.get('reserved_usd'))
                 <= _money(proposal['cumulative_max_usd']), 'coverage_scope_invalid')
        return parameters

    def _previous_selection(self):
        inputs = _strict_json(self.source_cases['CQ-01'].inputs_json, stage='context')
        prepared = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
        return PublicSelectionTrial(self.plan, self.source_cases, original_folder=self.original_folder,
            retry_plan=self.retry_plan, retry_folder=self.retry_folder, proposal=self.previous_proposal,
            prepared=prepared, folder=self.previous_folder, mode=self.mode, client_factory=self.client_factory)

    @property
    def scope_sha256(self):
        proposal = {key: value for key, value in self.proposal.items() if key not in ('execution_approved', 'approval')}
        source = PublicAssessmentTrial(self.plan, self.source_cases, self.original_folder,
            mode=self.mode, client_factory=self.client_factory)
        return identity({'format': 'bounded-coverage-trial-v2', 'mode': self.mode, 'service_tier': 'default',
                         'source_scope_sha256': source.scope_sha256, 'proposal': proposal})

    def _prior_usage(self):
        try:
            prior = self.proposal['prior_trial']
            for folder, key in ((self.original_folder, 'original_ledger_sha256'),
                                (self.retry_folder, 'retry_ledger_sha256'), (self.previous_folder, 'ledger_sha256')):
                _require(hashlib.sha256((folder/'usage.json').read_bytes()).hexdigest() == prior[key],
                         'coverage_history_invalid')
            previous = self._previous_selection()
            _require(previous.scope_sha256 == prior['scope_sha256'], 'coverage_history_invalid')
            ledger = previous._ledger()  # Verifies both earlier ledgers and their inclusive totals.
            _require(ledger['halted'] is False and len(ledger['attempts']) == 1
                     and ledger['attempts'][0]['question_id'] == 'CQ-01'
                     and ledger['attempts'][0]['status'] == 'confirmed', 'coverage_history_invalid')
            cache = self.previous_folder/'results/CQ-01.json'
            _require(hashlib.sha256(cache.read_bytes()).hexdigest() == prior['result_sha256']
                     == ledger['attempts'][0]['result_sha256'], 'coverage_history_invalid')
            value = read_json(cache)
            _require(value['scope_sha256'] == prior['scope_sha256'] and value['question_id'] == 'CQ-01'
                     and value['result']['mode'] == self.mode and value['result']['prompt_version'] == PROMPT_VERSION
                     and _money(ledger['reserved_usd']) == _money(prior['reserved_usd'])
                     and _money(ledger['confirmed_usd']) == _money(prior['confirmed_usd']), 'coverage_history_invalid')
            return _money(ledger['reserved_usd']), _money(ledger['confirmed_usd'])
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('coverage_history_invalid') from None

    def _ledger(self):
        ledger = super()._ledger()
        identifiers = [attempt['question_id'] for attempt in ledger['attempts']]
        _require(identifiers == list(QUESTION_IDS[:len(identifiers)]), 'coverage_order_invalid')
        return ledger

    def _run_locked(self, question_id, execute, budget_usd):
        ledger = self._ledger()
        if not any(attempt['question_id'] == question_id for attempt in ledger['attempts']):
            count = len(ledger['attempts'])
            _require(count < len(QUESTION_IDS) and question_id == QUESTION_IDS[count], 'coverage_order_invalid')
        return super()._run_locked(question_id, execute, budget_usd)

    def run(self, question_id, *, execute=False, budget_usd=None):
        _require(question_id in QUESTION_IDS, 'coverage_scope_invalid')
        self._validate_preparation(); self._prior_usage()
        try:
            with ExitStack() as stack:
                for folder in (self.original_folder, self.retry_folder, self.previous_folder):
                    stack.enter_context(exclusive_build(folder))
                return PublicAssessmentTrial.run(self, question_id, execute=execute, budget_usd=budget_usd)
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('coverage_state_invalid') from None

    def preflight(self):
        self._validate_preparation(); reserved, confirmed = self._prior_usage()
        maximum = len(QUESTION_IDS)*_cost(self.plan, self.plan['limits']['max_input_tokens'], self.parameters.max_output_tokens)
        return {'scope_sha256': self.scope_sha256, 'execution_approved': self.proposal.get('execution_approved') is True,
            'model': self.plan['model'], 'question_ids': list(QUESTION_IDS), 'max_new_attempts': 2,
            'max_attempts_per_question': 1, 'prompt_version': PROMPT_VERSION,
            'prompt_sha256': self.proposal['prompt_sha256'], 'requests': self.proposal['requests'],
            'parameters': self.plan['parameters'], 'max_input_tokens': self.plan['limits']['max_input_tokens'],
            'cumulative_max_usd': self.proposal['cumulative_max_usd'], 'carried_reserved_usd': str(reserved),
            'carried_confirmed_usd': str(confirmed), 'maximum_new_reservation_usd': str(maximum),
            'maximum_combined_reservation_usd': str(reserved+maximum), 'prior_histories_verified': True,
            'input_tokens': 'Not counted; each separately authorized execution must count its exact input.',
            'execution': 'One explicitly selected question per invocation, in declared order; no automatic batch.',
            'price_basis': 'Recorded reference prices, not actual billing or a fresh price check.', 'provider_calls': 0}


def load_coverage_trial(repository_root=None):
    root, plan, source_cases = load_public_trial(repository_root)
    prepared = {}
    for identifier in QUESTION_IDS:
        inputs = _strict_json(source_cases[identifier].inputs_json, stage='context')
        prepared[identifier] = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
    return PublicCoverageTrial(plan, source_cases, original_folder=owned_file(root, ORIGINAL_CACHE, 'services/rag/.cache'),
        retry_plan=read_json(owned_file(root, RETRY_PROPOSAL, 'docs/rag')),
        retry_folder=owned_file(root, RETRY_CACHE, 'services/rag/.cache'),
        previous_proposal=read_json(owned_file(root, PREVIOUS_PROPOSAL, 'docs/rag')),
        previous_folder=owned_file(root, PREVIOUS_CACHE, 'services/rag/.cache'),
        proposal=read_json(owned_file(root, PROPOSAL, 'docs/rag')), prepared=prepared,
        folder=owned_file(root, CACHE, 'services/rag/.cache'))


def main():
    parser = argparse.ArgumentParser(description='Inspect two public v2 coverage probes or explicitly run one approved case.')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--question-id', choices=QUESTION_IDS)
    parser.add_argument('--budget-usd', help='Cumulative allowance including all earlier model attempts.')
    args = parser.parse_args()
    try:
        session = load_coverage_trial()
        if args.execute:
            _require(args.question_id is not None, 'coverage_question_required')
            result = session.run(args.question_id, execute=True, budget_usd=args.budget_usd); value = result['result']
            print(json.dumps({'question_id': args.question_id, 'coverage': value['decision']['coverage'],
                'cache_hit': result['cache_hit'], 'input_tokens': value['input_tokens'], 'output_tokens': value['output_tokens']}))
        else:
            print(json.dumps(session.preflight(), indent=2))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error),
                          'diagnostic': safe_diagnostic(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'coverage_trial_failed',
                          'message': 'The public coverage trial stopped safely.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
