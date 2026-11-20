"""Prepare one explicitly reauthorized CQ-01 attempt with immutable prior accounting."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

from .assessment_trial import (
    CACHE as ORIGINAL_CACHE, AssessmentError, PublicAssessmentTrial, _cost, _money,
    _require, load_public_trial, read_assessment_settings,
)
from .diagnostics import safe_diagnostic
from .embeddings import identity
from .indexing import IndexBuildError, exclusive_build, read_json
from .ingestion import owned_file


PROPOSAL = 'docs/rag/assessment-retry-proposal.json'
CACHE = 'services/rag/.cache/assessment-retry-cq01-v1'
QUESTION_ID = 'CQ-01'


class PublicAssessmentRetry(PublicAssessmentTrial):
    """Reuse the checked trial execution path; never unhalt or edit the old ledger."""

    max_attempts = 1
    ledger_format = 'assessment-retry-usage-v1'

    def __init__(self, plan, cases, prior_folder, retry_plan, folder, **kwargs):
        super().__init__(plan, cases, folder, **kwargs)
        self.prior_folder, self.retry_plan = Path(prior_folder), deepcopy(retry_plan)
        self._validate_retry()

    def _validate_retry(self):
        proposal = self.retry_plan
        _require(isinstance(proposal, dict)
                 and proposal.get('format_version') == 'public-luna-assessment-retry-v1'
                 and proposal.get('question_id') == QUESTION_ID
                 and type(proposal.get('max_new_attempts')) is int
                 and proposal['max_new_attempts'] == 1, 'retry_scope_invalid')
        _require(_money(proposal.get('cumulative_max_usd')) == _money(self.plan['limits']['max_usd']),
                 'retry_scope_invalid')
        prior = proposal.get('prior_trial')
        _require(isinstance(prior, dict) and prior.get('scope_sha256') == super().scope_sha256,
                 'retry_scope_invalid')
        digest = prior.get('ledger_sha256')
        _require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) is not None,
                 'retry_scope_invalid')
        _require(0 <= _money(prior.get('confirmed_usd')) <= _money(prior.get('reserved_usd'))
                 <= _money(proposal['cumulative_max_usd']), 'retry_scope_invalid')
        _require(self.folder.resolve() != self.prior_folder.resolve(), 'retry_scope_invalid')

    @property
    def scope_sha256(self):
        proposal = {key: value for key, value in self.retry_plan.items()
                    if key not in ('execution_approved', 'approval')}
        return identity({'format': 'bounded-assessment-retry-v1', 'mode': self.mode,
                         'original_scope_sha256': super().scope_sha256, 'retry_proposal': proposal})

    def _prior_usage(self):
        """Verify the pinned original bytes and retain both reservation and confirmed usage."""
        try:
            prior = self.retry_plan['prior_trial']
            path = self.prior_folder/'usage.json'
            _require(hashlib.sha256(path.read_bytes()).hexdigest() == prior['ledger_sha256'],
                     'retry_history_invalid')
            original = PublicAssessmentTrial(self.plan, self.cases, self.prior_folder,
                mode=self.mode, client_factory=self.client_factory)
            ledger = original._ledger()
            attempts = ledger['attempts']
            _require(ledger['halted'] is True and len(attempts) == 1
                     and attempts[0]['question_id'] == QUESTION_ID and attempts[0]['status'] == 'failed',
                     'retry_history_invalid')
            _require(_money(ledger['reserved_usd']) == _money(prior['reserved_usd'])
                     and _money(ledger['confirmed_usd']) == _money(prior['confirmed_usd']),
                     'retry_history_invalid')
            return _money(ledger['reserved_usd']), _money(ledger['confirmed_usd'])
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('retry_history_invalid') from None

    def _ledger(self):
        ledger = super()._ledger()
        prior = self.retry_plan['prior_trial']
        if (self.folder/'usage.json').exists():
            _require(ledger.get('prior_trial') == prior, 'retry_history_invalid')
        else:
            ledger['prior_trial'] = deepcopy(prior)
        return ledger

    def preflight(self):
        self._validate_retry()
        reserved, confirmed = self._prior_usage()
        maximum = _cost(self.plan, self.plan['limits']['max_input_tokens'], self.parameters.max_output_tokens)
        return {'scope_sha256': self.scope_sha256,
            'execution_approved': self.retry_plan.get('execution_approved') is True,
            'model': self.plan['model'], 'question_id': QUESTION_ID, 'max_new_attempts': 1,
            'parameters': self.plan['parameters'], 'max_input_tokens': self.plan['limits']['max_input_tokens'],
            'cumulative_max_usd': self.retry_plan['cumulative_max_usd'],
            'carried_reserved_usd': str(reserved), 'carried_confirmed_usd': str(confirmed),
            'maximum_new_reservation_usd': str(maximum),
            'maximum_combined_reservation_usd': str(reserved + maximum),
            'price_basis': 'Recorded reference prices; not actual billing or a fresh price check.',
            'original_ledger_verified': True, 'provider_calls': 0}

    def _authorize(self, execute, budget_usd):
        approval = self.retry_plan.get('approval')
        _require(execute is True and self.retry_plan.get('execution_approved') is True
                 and isinstance(approval, dict)
                 and isinstance(approval.get('actor'), str) and bool(approval['actor'].strip())
                 and isinstance(approval.get('date'), str) and bool(approval['date'].strip())
                 and approval.get('scope_sha256') == self.scope_sha256, 'retry_execution_not_approved')
        _require(budget_usd is not None and _money(budget_usd) == _money(self.retry_plan['cumulative_max_usd']),
                 'budget_not_approved')
        settings = self.settings if self.settings is not None else read_assessment_settings()
        _require(settings.enabled is True and isinstance(settings.api_key, str) and bool(settings.api_key.strip()),
                 'configuration_required')

    def run(self, question_id=QUESTION_ID, *, execute=False, budget_usd=None):
        _require(question_id == QUESTION_ID, 'retry_scope_invalid')
        self._validate_retry()
        self._prior_usage()
        try:
            # Both runners share this original lock; cooperative processes cannot overlap.
            with exclusive_build(self.prior_folder):
                return super().run(question_id, execute=execute, budget_usd=budget_usd)
        except AssessmentError:
            raise
        except (OSError, IndexBuildError, KeyError, TypeError, ValueError):
            raise AssessmentError('retry_state_invalid') from None


def load_public_retry(repository_root=None):
    root, plan, cases = load_public_trial(repository_root)
    proposal = read_json(owned_file(root, PROPOSAL, 'docs/rag'))
    return PublicAssessmentRetry(plan, cases,
        owned_file(root, ORIGINAL_CACHE, 'services/rag/.cache'), proposal,
        owned_file(root, CACHE, 'services/rag/.cache'))


def main():
    parser = argparse.ArgumentParser(description='Inspect or explicitly run one reauthorized public CQ-01 attempt.')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd', help='Cumulative allowance including the preserved original reservation.')
    args = parser.parse_args()
    try:
        session = load_public_retry()
        if args.execute:
            result = session.run(execute=True, budget_usd=args.budget_usd)
            value = result['result']
            print(json.dumps({'question_id': QUESTION_ID, 'coverage': value['decision']['coverage'],
                'cache_hit': result['cache_hit'], 'input_tokens': value['input_tokens'],
                'output_tokens': value['output_tokens']}))
        else:
            print(json.dumps(session.preflight(), indent=2))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error),
                          'diagnostic': safe_diagnostic(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'retry_failed',
                          'message': 'The public assessment retry stopped safely.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
