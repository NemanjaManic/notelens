"""Prepare one separately approved partial answer using retained public evidence."""

import argparse
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .answer_trial import (INPUT_LIMIT, LIMIT, PARAMETERS, PublicAnswerTrial, _digest,
                          load_answer_trial, prepare_from_history)
from .answers import PARTIAL_POLICY, answer_request, checked_answer_response
from .assessment_trial import AssessmentError, PublicAssessmentTrial, _cost, _money, _require
from .assessor import MODEL, _strict_json
from .embeddings import identity
from .indexing import exclusive_build, read_json
from .ingestion import owned_file, repository_directory


QUESTION_ID = 'CQ-02'
PROPOSAL = 'docs/rag/evaluation/partial-answer-trial-proposal.json'
CACHE = 'services/rag/.cache/answer-trial-cq02'


class PublicPartialAnswerTrial(PublicAnswerTrial):
    """Reuse the single-attempt reservation path with a pinned predecessor."""

    ledger_format = 'public-partial-answer-usage-v1'

    def __init__(self, previous, proposal, folder, *, settings=None, client_factory=None):
        self.previous, self.coverage = previous, previous.coverage
        self.plan = deepcopy(proposal)
        self.parameters = PARAMETERS
        self.folder, self.mode = Path(folder), 'live'
        self.settings, self.client_factory = settings, client_factory
        self.cases = {QUESTION_ID: prepare_from_history(self.coverage, QUESTION_ID)}
        parents = self._history_folders()
        _require(len({path.resolve() for path in (*parents, self.folder)}) == len(parents)+1,
                 'partial_answer_scope_invalid')
        self._validate_preparation()

    def _history_folders(self):
        history = self.coverage
        return (history.original_folder, history.retry_folder, history.previous_folder,
                history.folder, self.previous.folder)

    def _validate_preparation(self):
        prepared = self.cases[QUESTION_ID]
        _require(self.plan.get('format_version') == 'public-partial-answer-trial-v1'
                 and self.plan.get('question_id') == QUESTION_ID and self.plan.get('model') == MODEL
                 and self.plan.get('partial_policy') == PARTIAL_POLICY
                 and self.plan.get('parameters') == asdict(self.parameters)
                 and self.plan.get('limits') == {'max_input_tokens': INPUT_LIMIT, 'max_usd': LIMIT}
                 and self.plan.get('max_attempts') == 1 and self.plan.get('automatic_retries') == 0
                 and self.plan['prices']['input_usd_per_million'] == '0.10'
                 and self.plan['prices']['output_usd_per_million'] == '0.50'
                 and prepared.coverage == 'partial'
                 and self.plan.get('context_sha256') == prepared.context_sha256
                 and self.plan.get('request_sha256') == identity(answer_request(prepared, self.parameters))
                 and self.plan.get('prompt_sha256') == prepared.prompt_sha256,
                 'partial_answer_scope_invalid')
        return self.parameters

    def _prior_usage(self):
        prior = self.previous
        _require(_digest(prior.folder/'usage.json') == self.plan.get('previous_answer_ledger_sha256')
                 and prior.scope_sha256 == self.plan.get('previous_answer_scope_sha256'),
                 'partial_answer_history_invalid')
        prior._validate_preparation()
        ledger = prior._ledger()
        _require(not ledger['halted'] and len(ledger['attempts']) == 1, 'partial_answer_history_invalid')
        attempt, = ledger['attempts']
        cache = prior.folder/'results/CQ-01.json'
        _require(attempt['question_id'] == 'CQ-01' and attempt['status'] == 'confirmed'
                 and _digest(cache) == attempt['result_sha256'] == self.plan.get('previous_answer_result_sha256'),
                 'partial_answer_history_invalid')
        saved = read_json(cache)
        _require(saved['scope_sha256'] == prior.scope_sha256 and saved['question_id'] == 'CQ-01'
                 and saved['context_sha256'] == prior.cases['CQ-01'].context_sha256,
                 'partial_answer_history_invalid')
        return _money(ledger['reserved_usd']), _money(ledger['confirmed_usd'])

    def _checked_response(self, raw_bytes, prepared):
        return checked_answer_response(raw_bytes, prepared, self.parameters, mode=self.mode,
                                       partial_policy=PARTIAL_POLICY)

    def run(self, *, execute=False, budget_usd=None):
        self._validate_preparation()
        self._prior_usage()
        if not (self.folder/'usage.json').exists():
            self._authorize(execute, budget_usd)
        with ExitStack() as stack:
            for folder in self._history_folders():
                stack.enter_context(exclusive_build(folder))
            return PublicAssessmentTrial.run(self, QUESTION_ID, execute=execute, budget_usd=budget_usd)

    def preflight(self):
        reserved, confirmed = self._prior_usage()
        prepared = self.cases[QUESTION_ID]
        inputs = _strict_json(prepared.inputs_json)
        parts = inputs['assessment']['parts']
        descriptions = {part['requirement_id']: part['description'] for part in inputs['requirements']}
        maximum = _cost(self.plan, INPUT_LIMIT, self.parameters.max_output_tokens)
        _require(reserved+maximum <= _money(LIMIT), 'budget_exceeded')
        return {'scope_sha256': self.scope_sha256, 'question_id': QUESTION_ID,
                'question': inputs['request']['question'], 'model': MODEL,
                'execution_approved': self.plan.get('execution_approved') is True,
                'partial_policy': PARTIAL_POLICY, 'prompt_version': prepared.prompt_version,
                'supported_parts': [descriptions[part['requirement_id']] for part in parts if part['status'] == 'supported'],
                'missing_parts': [descriptions[part['requirement_id']] for part in parts if part['status'] != 'supported'],
                'limit_usd': LIMIT, 'max_input_tokens': INPUT_LIMIT,
                'max_output_tokens': self.parameters.max_output_tokens,
                'prior_reserved_reference_usd': str(reserved), 'prior_confirmed_reference_usd': str(confirmed),
                'maximum_new_standard_reference_usd': str(maximum),
                'maximum_total_reference_usd': str(reserved+maximum), 'provider_calls': 0}


def load_partial_answer_trial(repository_root=None):
    root = repository_directory(repository_root)
    proposal = read_json(owned_file(root, PROPOSAL, 'docs/rag'))
    folder = owned_file(root, CACHE, 'services/rag/.cache')
    return PublicPartialAnswerTrial(load_answer_trial(root), proposal, folder)


def main():
    parser = argparse.ArgumentParser(description='Inspect or explicitly run one public partial-answer probe.')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd')
    args = parser.parse_args()
    try:
        trial = load_partial_answer_trial()
        if args.execute:
            saved = trial.run(execute=True, budget_usd=args.budget_usd)
            result = saved['result']
            body = json.loads(result['body_json'])
            print(json.dumps({'question_id': QUESTION_ID, 'cache_hit': saved['cache_hit'],
                'evidence_state': body['evidence_state'], 'claims': len(body['claims']),
                'input_tokens': result['input_tokens'], 'output_tokens': result['output_tokens']}))
        else:
            print(json.dumps(trial.preflight(), indent=2))
        return 0
    except AssessmentError as failure:
        print(json.dumps({'status': 'error', 'code': failure.code, 'message': str(failure)}), file=sys.stderr)
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'partial_answer_trial_failed',
                          'message': 'The public partial-answer trial stopped safely.'}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
