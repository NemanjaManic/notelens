"""Review cached public support and gate one separate, fully supported answer probe."""

import argparse
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from .answers import PARTIAL_POLICY, answer_request, checked_answer_response, prepare_answer, unsupported_answer
from .assessment_trial import AssessmentError, PublicAssessmentTrial, _cost, _count_request, _money, _require, _strict_json
from .assessor import MODEL, AssessmentParameters
from .coverage_trial import load_coverage_trial
from .embeddings import identity
from .indexing import exclusive_build, read_json
from .ingestion import owned_file, repository_directory
from .support import evaluate_support, support_context_sha256


QUESTION_ID = 'CQ-01'
PROPOSAL = 'docs/rag/evaluation/answer-trial-proposal.json'
CACHE = 'services/rag/.cache/answer-trial-cq01'
INPUT_LIMIT = 4096
PARAMETERS = AssessmentParameters(max_output_tokens=512, reasoning_effort='none', timeout_seconds=30)
LIMIT = '0.02'


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_from_history(coverage, question_id, *, mock=False):
    """Validate the retained decision and rebuild its exact evaluation context."""
    stage = coverage._previous_selection() if question_id == QUESTION_ID else coverage
    ledger = stage._ledger()
    attempt, = (row for row in ledger['attempts'] if row['question_id'] == question_id and row['status'] == 'confirmed')
    path = stage.folder / 'results' / f'{question_id}.json'
    _require(_digest(path) == attempt['result_sha256'], 'answer_history_invalid')
    cached = read_json(path)
    prepared = stage.cases[question_id]
    _require(cached['question_id'] == question_id and cached['scope_sha256'] == stage.scope_sha256
             and cached['context_sha256'] == prepared.context_sha256, 'answer_history_invalid')
    value = cached['result']['decision']
    _require(value['context_sha256'] == prepared.context_sha256, 'answer_history_invalid')
    inputs = _strict_json(prepared.inputs_json)
    request, candidates, requirements = (inputs[key] for key in ('request', 'candidates', 'requirements'))
    if mock:
        candidates['mode'] = 'mock'
    verdict = {'format_version': 'rag-support-assessment-v1', 'parts': value['parts'],
               'context_sha256': support_context_sha256(request, candidates, requirements)}
    decision = evaluate_support(request, candidates, requirements, verdict)
    _require(decision.coverage == value['coverage'], 'answer_history_invalid')
    return prepare_answer(request, candidates, requirements, decision)


def _answer_count_request(prepared):
    return {key: value for key, value in answer_request(prepared, PARAMETERS).items()
            if key not in ('max_output_tokens', 'store', 'stream', 'background')}


class PublicAnswerTrial(PublicAssessmentTrial):
    max_attempts = 1
    ledger_format = 'public-answer-usage-v1'

    def __init__(self, coverage, proposal, folder, *, settings=None, client_factory=None):
        self.coverage = coverage
        self.plan = deepcopy(proposal)
        self.parameters = PARAMETERS
        self.folder, self.mode = Path(folder), 'live'
        self.settings, self.client_factory = settings, client_factory
        self.cases = {QUESTION_ID: prepare_from_history(coverage, QUESTION_ID)}
        self._validate_preparation()

    @property
    def scope_sha256(self):
        plan = {key: val for key, val in self.plan.items() if key not in ('approval', 'execution_approved')}
        return identity({'plan': plan, 'mode': self.mode, 'service_tier': 'default'})

    def _validate_preparation(self):
        prepared = self.cases[QUESTION_ID]
        _require(self.plan.get('format_version') == 'public-literature-answer-trial-v1'
                 and self.plan.get('question_id') == QUESTION_ID and self.plan.get('model') == MODEL
                 and self.plan.get('limits') == {'max_input_tokens': INPUT_LIMIT, 'max_usd': LIMIT}
                 and self.plan.get('max_attempts') == 1 and self.plan.get('automatic_retries') == 0
                 and self.plan['prices']['input_usd_per_million'] == '0.10'
                 and self.plan['prices']['output_usd_per_million'] == '0.50'
                 and prepared.coverage == 'full' and self.plan.get('context_sha256') == prepared.context_sha256
                 and self.plan.get('request_sha256') == identity(answer_request(prepared, self.parameters))
                 and self.plan.get('prompt_sha256') == prepared.prompt_sha256, 'answer_scope_invalid')
        return self.parameters

    def _prior_usage(self):
        _require(_digest(self.coverage.folder/'usage.json') == self.plan.get('coverage_ledger_sha256'),
                 'answer_history_invalid')
        ledger = self.coverage._ledger()
        _require(not ledger['halted'] and len(ledger['attempts']) == 2
                 and all(attempt['status'] == 'confirmed' for attempt in ledger['attempts']), 'answer_history_invalid')
        return _money(ledger['reserved_usd']), _money(ledger['confirmed_usd'])

    def _generation_request(self, prepared):
        return answer_request(prepared, self.parameters)

    def _count_input(self, client, prepared):
        return _count_request(client, _answer_count_request(prepared), INPUT_LIMIT)

    def _checked_response(self, raw_bytes, prepared):
        return checked_answer_response(raw_bytes, prepared, self.parameters, mode=self.mode)

    def _authorize(self, execute, budget_usd):
        approval = self.plan.get('approval')
        _require(isinstance(approval, dict) and approval.get('actor') == 'Nemanja (A)', 'execution_not_approved')
        super()._authorize(execute, budget_usd)

    def run(self, *, execute=False, budget_usd=None):
        self._prior_usage()
        if not (self.folder/'usage.json').exists():
            self._authorize(execute, budget_usd)
        history = self.coverage
        with ExitStack() as stack:
            for folder in (history.original_folder, history.retry_folder, history.previous_folder, history.folder):
                stack.enter_context(exclusive_build(folder))
            return super().run(QUESTION_ID, execute=execute, budget_usd=budget_usd)

    def preflight(self):
        reserved, confirmed = self._prior_usage()
        maximum = _cost(self.plan, INPUT_LIMIT, self.parameters.max_output_tokens)
        return {'scope_sha256': self.scope_sha256, 'question_id': QUESTION_ID,
                'execution_approved': self.plan.get('execution_approved') is True,
                'prompt_version': self.cases[QUESTION_ID].prompt_version, 'limit_usd': LIMIT,
                'max_input_tokens': INPUT_LIMIT, 'max_output_tokens': PARAMETERS.max_output_tokens,
                'prior_reserved_reference_usd': str(reserved), 'prior_confirmed_reference_usd': str(confirmed),
                'maximum_new_standard_reference_usd': str(maximum), 'maximum_total_reference_usd': str(reserved+maximum),
                'provider_calls': 0}


def load_answer_trial(repository_root=None):
    root = repository_directory(repository_root)
    proposal = read_json(owned_file(root, PROPOSAL, 'docs/rag'))
    return PublicAnswerTrial(load_coverage_trial(root), proposal, owned_file(root, CACHE, 'services/rag/.cache'))


def offline_review(coverage):
    """Validate authored answer fixtures against the exact verified support spans."""
    draft_claims = {
        'CQ-01': ('Systolic pressure is the pressure when the heart beats.',
                  'Diastolic pressure is the pressure between heartbeats.'),
        'CQ-02': ('COVID-19 is caused by the virus SARS-CoV-2.',),
    }
    rows = []
    for identifier in ('CQ-01', 'CQ-02', 'CQ-08'):
        prepared = prepare_from_history(coverage, identifier, mock=True)
        if prepared.coverage == 'none':
            result = unsupported_answer(prepared)
        else:
            options = _strict_json(prepared.evidence_json)
            first_ids = {}
            for entry in options:
                first_ids.setdefault(entry['requirement_id'], entry['evidence_id'])
            claims = [{'requirement_id': part, 'text': text, 'evidence_ids': [first_ids[part]]}
                      for part, text in zip(first_ids, draft_claims[identifier], strict=True)]
            envelope = {'object': 'response', 'model': MODEL, 'status': 'completed', 'error': None,
                'incomplete_details': None, 'output': [{'type': 'message', 'role': 'assistant',
                    'status': 'completed', 'content': [{'type': 'output_text',
                        'text': json.dumps({'language': 'en', 'claims': claims})}]}],
                'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
            policy = PARTIAL_POLICY if prepared.coverage == 'partial' else None
            result = checked_answer_response(json.dumps(envelope).encode(), prepared, PARAMETERS, partial_policy=policy)
        body = result.body
        rows.append({'question_id': identifier, 'mode': body['mode'], 'evidence_state': body['evidence_state'],
                     'claim_count': len(body['claims']), 'source_count': len(body['sources']),
                     'exact_quote_references': len(_strict_json(result.quote_trace_json)),
                     'gap_warning': next((warning for warning in body['warnings'] if 'requested information:' in warning), None),
                     'origin': 'authored_fixture' if prepared.coverage != 'none' else 'local_abstention'})
    return {'provider_calls': 0, 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description='Inspect or run the bounded single public answer probe.')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--execute', action='store_true')
    action.add_argument('--review', action='store_true')
    parser.add_argument('--budget-usd')
    args = parser.parse_args()
    try:
        trial = load_answer_trial()
        if args.execute:
            saved = trial.run(execute=True, budget_usd=args.budget_usd)
            value = saved['result']
            answer = json.loads(value['body_json'])
            print(json.dumps({'question_id': QUESTION_ID, 'cache_hit': saved['cache_hit'],
                'evidence_state': answer['evidence_state'], 'claims': len(answer['claims']),
                'input_tokens': value['input_tokens'], 'output_tokens': value['output_tokens']}))
        elif args.review:
            trial._prior_usage()
            print(json.dumps(offline_review(trial.coverage), indent=2))
        else:
            print(json.dumps(trial.preflight(), indent=2))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error)}), file=sys.stderr)
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'answer_trial_failed',
                          'message': 'The public answer trial stopped safely.'}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
