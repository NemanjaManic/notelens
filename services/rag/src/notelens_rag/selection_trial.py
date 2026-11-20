"""Prepare one v2 CQ-01 model probe with fresh consent and both prior reservations."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

from .assessment_trial import (
    CACHE as ORIGINAL_CACHE, AssessmentError, PublicAssessmentTrial, _cost, _money,
    _require, _strict_json, _validate_plan, load_public_trial, read_assessment_settings,
)
from .assessment_retry import CACHE as RETRY_CACHE, PROPOSAL as RETRY_PROPOSAL, PublicAssessmentRetry
from .assessor import assessment_request
from .diagnostics import safe_diagnostic
from .embeddings import identity
from .evidence_selection import (
    EVIDENCE_POLICY, PROMPT_VERSION, PreparedSelection, checked_selection_response, prepare_selection,
)
from .indexing import IndexBuildError, exclusive_build, read_json
from .ingestion import owned_file


PROPOSAL = 'docs/rag/selection-trial-proposal.json'
CACHE = 'services/rag/.cache/selection-trial-cq01-v2'
QUESTION_ID = 'CQ-01'


class PublicSelectionTrial(PublicAssessmentTrial):
    """Use the tested reserve/count/execute path with a distinct v2 scope and ledger."""

    max_attempts = 1
    ledger_format = 'selection-trial-usage-v2'

    def __init__(self, source_plan, source_cases, *, original_folder, retry_plan, retry_folder,
                 proposal, prepared, folder, **kwargs):
        super().__init__(source_plan, source_cases, folder, **kwargs)
        self.source_cases = self.cases
        self.cases = {QUESTION_ID: prepared}
        self.original_folder, self.retry_folder = Path(original_folder), Path(retry_folder)
        self.retry_plan, self.proposal = deepcopy(retry_plan), deepcopy(proposal)
        _require(len({self.folder.resolve(), self.original_folder.resolve(), self.retry_folder.resolve()}) == 3,
                 'selection_trial_scope_invalid')
        self._validate_preparation()

    def _validate_preparation(self):
        parameters = _validate_plan(self.plan, self.source_cases)
        _require(parameters == self.parameters and set(self.cases) == {QUESTION_ID}, 'selection_trial_scope_invalid')
        prepared = self.cases[QUESTION_ID]
        _require(type(prepared) is PreparedSelection, 'selection_trial_scope_invalid')
        inputs = _strict_json(self.source_cases[QUESTION_ID].inputs_json, stage='context')
        expected = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
        proposal = self.proposal
        _require(prepared == expected and isinstance(proposal, dict)
                 and proposal.get('format_version') == 'public-selection-trial-v2'
                 and proposal.get('question_id') == QUESTION_ID
                 and type(proposal.get('max_new_attempts')) is int and proposal['max_new_attempts'] == 1
                 and proposal.get('prompt_version') == PROMPT_VERSION
                 and proposal.get('evidence_policy') == EVIDENCE_POLICY
                 and proposal.get('prompt_sha256') == prepared.prompt_sha256
                 and proposal.get('selection_sha256') == prepared.selection_sha256
                 and proposal.get('request_sha256') == identity(assessment_request(prepared, parameters)),
                 'selection_trial_scope_invalid')
        _require(_money(proposal.get('cumulative_max_usd')) == _money(self.plan['limits']['max_usd']),
                 'selection_trial_scope_invalid')
        prior = proposal.get('prior_trial')
        _require(isinstance(prior, dict), 'selection_trial_scope_invalid')
        for key in ('scope_sha256', 'ledger_sha256', 'original_ledger_sha256'):
            _require(isinstance(prior.get(key), str) and re.fullmatch('[0-9a-f]{64}', prior[key]) is not None,
                     'selection_trial_scope_invalid')
        _require(0 <= _money(prior.get('confirmed_usd')) <= _money(prior.get('reserved_usd'))
                 <= _money(proposal['cumulative_max_usd']), 'selection_trial_scope_invalid')
        return parameters

    def _previous_retry(self):
        return PublicAssessmentRetry(self.plan, self.source_cases, self.original_folder,
            self.retry_plan, self.retry_folder, mode=self.mode, client_factory=self.client_factory)

    @property
    def scope_sha256(self):
        proposal = {key: value for key, value in self.proposal.items()
                    if key not in ('execution_approved', 'approval')}
        source = PublicAssessmentTrial(self.plan, self.source_cases, self.original_folder,
            mode=self.mode, client_factory=self.client_factory)
        return identity({'format': 'bounded-selection-trial-v2', 'mode': self.mode, 'service_tier': 'default',
                         'source_scope_sha256': source.scope_sha256, 'proposal': proposal})

    def _prior_usage(self):
        try:
            prior = self.proposal['prior_trial']
            original = (self.original_folder/'usage.json').read_bytes()
            latest = (self.retry_folder/'usage.json').read_bytes()
            _require(hashlib.sha256(original).hexdigest() == prior['original_ledger_sha256']
                     and hashlib.sha256(latest).hexdigest() == prior['ledger_sha256'], 'selection_history_invalid')
            retry = self._previous_retry()
            _require(retry.scope_sha256 == prior['scope_sha256'], 'selection_history_invalid')
            ledger = retry._ledger()  # This also validates the first ledger and its carry-forward.
            attempts = ledger['attempts']
            _require(ledger['halted'] is True and len(attempts) == 1
                     and attempts[0]['question_id'] == QUESTION_ID and attempts[0]['status'] == 'failed'
                     and _money(ledger['reserved_usd']) == _money(prior['reserved_usd'])
                     and _money(ledger['confirmed_usd']) == _money(prior['confirmed_usd']), 'selection_history_invalid')
            # The latest ledger already includes the first attempt; never add it twice.
            return _money(ledger['reserved_usd']), _money(ledger['confirmed_usd'])
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('selection_history_invalid') from None

    def _ledger(self):
        ledger = super()._ledger()
        prior = self.proposal['prior_trial']
        if (self.folder/'usage.json').exists():
            _require(ledger.get('prior_trial') == prior, 'selection_history_invalid')
        else:
            ledger['prior_trial'] = deepcopy(prior)
        return ledger

    def _checked_response(self, raw_bytes, prepared):
        return checked_selection_response(raw_bytes, prepared, self.parameters, mode=self.mode)

    def _authorize(self, execute, budget_usd):
        approval = self.proposal.get('approval')
        _require(execute is True and self.proposal.get('execution_approved') is True
                 and isinstance(approval, dict)
                 and isinstance(approval.get('actor'), str) and bool(approval['actor'].strip())
                 and isinstance(approval.get('date'), str) and bool(approval['date'].strip())
                 and approval.get('scope_sha256') == self.scope_sha256, 'selection_execution_not_approved')
        _require(budget_usd is not None and _money(budget_usd) == _money(self.proposal['cumulative_max_usd']),
                 'budget_not_approved')
        settings = self.settings if self.settings is not None else read_assessment_settings()
        _require(settings.enabled is True and isinstance(settings.api_key, str) and bool(settings.api_key.strip()),
                 'configuration_required')

    def run(self, question_id=QUESTION_ID, *, execute=False, budget_usd=None):
        _require(question_id == QUESTION_ID, 'selection_trial_scope_invalid')
        self._validate_preparation()
        self._prior_usage()
        try:
            with exclusive_build(self.original_folder), exclusive_build(self.retry_folder):
                return super().run(question_id, execute=execute, budget_usd=budget_usd)
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('selection_trial_state_invalid') from None

    def preflight(self):
        self._validate_preparation()
        reserved, confirmed = self._prior_usage()
        maximum = _cost(self.plan, self.plan['limits']['max_input_tokens'], self.parameters.max_output_tokens)
        return {'scope_sha256': self.scope_sha256, 'execution_approved': self.proposal.get('execution_approved') is True,
            'model': self.plan['model'], 'question_id': QUESTION_ID, 'max_new_attempts': 1,
            'prompt_version': PROMPT_VERSION, 'prompt_sha256': self.cases[QUESTION_ID].prompt_sha256,
            'selection_sha256': self.cases[QUESTION_ID].selection_sha256, 'request_sha256': self.proposal['request_sha256'],
            'parameters': self.plan['parameters'], 'max_input_tokens': self.plan['limits']['max_input_tokens'],
            'cumulative_max_usd': self.proposal['cumulative_max_usd'], 'carried_reserved_usd': str(reserved),
            'carried_confirmed_usd': str(confirmed), 'maximum_new_reservation_usd': str(maximum),
            'maximum_combined_reservation_usd': str(reserved+maximum), 'prior_ledgers_verified': True,
            'input_tokens': 'Not counted; execution must obtain a fresh provider count before generation.',
            'price_basis': 'Recorded reference prices; not actual billing or a fresh price check.', 'provider_calls': 0}


def load_selection_trial(repository_root=None):
    root, source_plan, source_cases = load_public_trial(repository_root)
    inputs = _strict_json(source_cases[QUESTION_ID].inputs_json, stage='context')
    prepared = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
    return PublicSelectionTrial(source_plan, source_cases,
        original_folder=owned_file(root, ORIGINAL_CACHE, 'services/rag/.cache'),
        retry_plan=read_json(owned_file(root, RETRY_PROPOSAL, 'docs/rag')),
        retry_folder=owned_file(root, RETRY_CACHE, 'services/rag/.cache'),
        proposal=read_json(owned_file(root, PROPOSAL, 'docs/rag')), prepared=prepared,
        folder=owned_file(root, CACHE, 'services/rag/.cache'))


def main():
    parser = argparse.ArgumentParser(description='Inspect or explicitly execute one separately approved CQ-01 v2 probe.')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd', help='Cumulative allowance, including both prior attempts.')
    args = parser.parse_args()
    try:
        session = load_selection_trial()
        if args.execute:
            result = session.run(execute=True, budget_usd=args.budget_usd); value = result['result']
            print(json.dumps({'question_id': QUESTION_ID, 'coverage': value['decision']['coverage'],
                'cache_hit': result['cache_hit'], 'input_tokens': value['input_tokens'], 'output_tokens': value['output_tokens']}))
        else:
            print(json.dumps(session.preflight(), indent=2))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error),
                          'diagnostic': safe_diagnostic(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'selection_trial_failed',
                          'message': 'The public selection trial stopped safely.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
