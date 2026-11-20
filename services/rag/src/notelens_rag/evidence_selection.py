"""Select canonical evidence by ID; Python alone supplies exact quote coordinates."""

import argparse
from dataclasses import dataclass, field
import hashlib
from importlib.resources import files
import json
import re
import sys

from .assessor import (
    MODEL, AssessmentError, ModelAssessment, OfflineLunaAssessor, PreparedAssessment,
    _json, _object, _require, _strict_json, checked_response_content, prepare_assessment,
)
from .diagnostics import ValidationDiagnostic, safe_diagnostic
from .support import SupportError, _snapshot, evaluate_support


PROMPT_VERSION = 'literature-support-selection-v2'
EVIDENCE_POLICY = 'canonical-nonblank-lines-v1'
SELECTION_FORMAT = 'rag-support-selection-v2'


@dataclass(frozen=True, slots=True)
class PreparedSelection(PreparedAssessment):
    selection_sha256: str = field(kw_only=True)
    catalog_json: str = field(repr=False, kw_only=True)


@dataclass(frozen=True, slots=True)
class SelectionAssessment(ModelAssessment):
    selection_sha256: str = field(kw_only=True)
    evidence_policy_version: str = EVIDENCE_POLICY


def prepare_selection(request, candidates, requirements):
    """Keep complete passage context; offer exact CR/LF-delimited nonblank lines.

    Whitespace inside each line, including leading/trailing whitespace and non-BMP
    characters, is unchanged. Blank lines are not selectable; CR/LF separators
    remain in the complete passage context. IDs are deterministic in passage/line
    order, and the selection fingerprint binds their exact source occurrences.
    """
    base = prepare_assessment(request, candidates, requirements)
    inputs = _strict_json(base.inputs_json, stage='context')
    catalog = []
    for passage in inputs['candidates']['passages']:
        for match in re.finditer(r'[^\r\n]+', passage['text']):
            if match.group().strip():
                catalog.append({'evidence_id': f'e{len(catalog)+1}', 'passage_id': passage['passage_id'],
                    'start': match.start(), 'end': match.end(), 'quote': match.group()})
    _require(bool(catalog), 'no_evidence_options')
    catalog_json = _json(catalog)
    binding = {'policy': EVIDENCE_POLICY, 'context_sha256': base.context_sha256, 'catalog': catalog}
    selection_sha = hashlib.sha256(_json(binding).encode('utf-8')).hexdigest()
    try:
        instructions = files('notelens_rag').joinpath('prompts/support-selection-v2.txt').read_bytes().decode('utf-8')
    except (OSError, UnicodeError):
        raise AssessmentError('configuration_required') from None
    part = _object({'requirement_id': {'type': 'string', 'enum': [p['requirement_id'] for p in inputs['requirements']]},
        'status': {'type': 'string', 'enum': ['supported', 'not_supported', 'conflicting']},
        'reason': {'type': 'string'}, 'evidence_ids': {'type': 'array', 'items': {
            'type': 'string', 'enum': [option['evidence_id'] for option in catalog]}}})
    schema = _object({'requirements_cover_question': {'type': 'boolean'}, 'assessment': _object({
        'format_version': {'type': 'string', 'enum': [SELECTION_FORMAT]},
        'context_sha256': {'type': 'string', 'enum': [base.context_sha256]},
        'selection_sha256': {'type': 'string', 'enum': [selection_sha]},
        'parts': {'type': 'array', 'items': part}})})
    payload = _strict_json(base.input_json)
    payload['selection_sha256'] = selection_sha
    # Coordinates stay server-side; the model sees exact options and complete context.
    payload['evidence_options'] = [{key: option[key] for key in ('evidence_id', 'passage_id', 'quote')}
                                   for option in catalog]
    return PreparedSelection(base.context_sha256, hashlib.sha256(instructions.encode('utf-8')).hexdigest(),
        instructions, _json(payload), _json(schema), base.inputs_json, prompt_version=PROMPT_VERSION,
        selection_sha256=selection_sha, catalog_json=catalog_json)


def _bound_catalog(prepared):
    try:
        _require(type(prepared) is PreparedSelection)
        inputs = _strict_json(prepared.inputs_json, stage='context')
        fresh = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
        _require(fresh == prepared)
        return inputs, _strict_json(fresh.catalog_json, stage='context')
    except (AssessmentError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise AssessmentError('selection_context_invalid', diagnostic=ValidationDiagnostic(
            stage='context', rule='selection_context')) from None


def resolve_selection(prepared, selection):
    """Resolve exact IDs; preserve the original support processor's complete checks."""
    inputs, catalog = _bound_catalog(prepared)
    try:
        selection = _snapshot(selection, 'assessment_invalid')[0]
        _require(isinstance(selection, dict) and set(selection) == {
            'format_version', 'context_sha256', 'selection_sha256', 'parts'},
            stage='assessment', rule='assessment_shape', path='/assessment')
        _require(selection['format_version'] == SELECTION_FORMAT,
                 stage='assessment', rule='assessment_format', path='/assessment/format_version')
        _require(selection['context_sha256'] == prepared.context_sha256,
                 stage='assessment', rule='assessment_binding', path='/assessment/context_sha256')
        _require(selection['selection_sha256'] == prepared.selection_sha256,
                 stage='assessment', rule='selection_binding', path='/assessment/selection_sha256')
        _require(isinstance(selection['parts'], list), stage='assessment', rule='parts_shape', path='/assessment/parts')
        options = {option['evidence_id']: option for option in catalog}
        parts = []
        for index, part in enumerate(selection['parts']):
            location = f'/assessment/parts/{index}'
            _require(isinstance(part, dict) and set(part) == {'requirement_id', 'status', 'reason', 'evidence_ids'},
                     stage='assessment', rule='part_shape', path=location)
            identifiers = part['evidence_ids']
            _require(isinstance(identifiers, list), stage='assessment', rule='evidence_shape', path=location+'/evidence_ids')
            quotes, seen = [], set()
            for quote_index, identifier in enumerate(identifiers):
                path = location+f'/evidence_ids/{quote_index}'
                _require(isinstance(identifier, str) and identifier in options,
                         stage='assessment', rule='evidence_reference', path=path)
                _require(identifier not in seen, stage='assessment', rule='duplicate_evidence', path=path)
                seen.add(identifier)
                option = options[identifier]
                quotes.append({key: option[key] for key in ('passage_id', 'start', 'end', 'quote')})
            parts.append({key: part[key] for key in ('requirement_id', 'status', 'reason')} | {'evidence': quotes})
        assessment = {'format_version': 'rag-support-assessment-v1',
                      'context_sha256': prepared.context_sha256, 'parts': parts}
        return evaluate_support(inputs['request'], inputs['candidates'], inputs['requirements'], assessment)
    except SupportError as error:
        value = safe_diagnostic(error)
        path = value['path'].replace('/evidence', '/evidence_ids', 1)
        if value['stage'] == 'assessment': path = '/assessment'+(path if path != '/' else '')
        raise AssessmentError('invalid_assessment', diagnostic=ValidationDiagnostic(
            stage=value['stage'], rule=value['rule'], path=path)) from None


def checked_selection_response(raw_bytes, prepared, parameters, *, mode='mock'):
    selected, usage = checked_response_content(raw_bytes, parameters, mode=mode)
    decision = resolve_selection(prepared, selected)
    configuration = {'adapter': 'offline-luna-selection-v2' if mode == 'mock' else 'bounded-luna-selection-v2',
        'mode': mode, 'model': MODEL, 'prompt_version': PROMPT_VERSION, 'prompt_sha256': prepared.prompt_sha256,
        'evidence_policy': EVIDENCE_POLICY, 'max_output_tokens': parameters.max_output_tokens,
        'reasoning_effort': parameters.reasoning_effort, 'timeout_seconds': parameters.timeout_seconds,
        'max_retries': 0, 'store': False, 'tools': [], 'truncation': 'disabled'}
    return SelectionAssessment(decision, prepared.prompt_sha256,
        hashlib.sha256(_json(configuration).encode('utf-8')).hexdigest(),
        usage['input_tokens'], usage['output_tokens'], usage['total_tokens'], mode=mode,
        prompt_version=PROMPT_VERSION, selection_sha256=prepared.selection_sha256)


class OfflineSelectionAssessor(OfflineLunaAssessor):
    """V2 SDK integration; inherited construction requires in-memory MockTransport."""

    def assess(self, request, candidates, requirements):
        prepared = prepare_selection(request, candidates, requirements)
        return checked_selection_response(self._raw_response(prepared), prepared, self.parameters)


def main():
    from .assessment_trial import QUESTION_IDS, load_public_trial
    parser = argparse.ArgumentParser(description='Inspect v2 public evidence preparation without a key or provider.')
    parser.add_argument('--question-id', required=True, choices=QUESTION_IDS)
    args = parser.parse_args()
    try:
        _, _, cases = load_public_trial()
        inputs = _strict_json(cases[args.question_id].inputs_json, stage='context')
        prepared = prepare_selection(inputs['request'], inputs['candidates'], inputs['requirements'])
        print(json.dumps({'status': 'prepared_offline', 'question_id': args.question_id,
            'prompt_version': prepared.prompt_version, 'prompt_sha256': prepared.prompt_sha256,
            'selection_sha256': prepared.selection_sha256,
            'evidence_options': len(_strict_json(prepared.catalog_json)),
            'input_json_utf8_bytes': len(prepared.input_json.encode('utf-8')),
            'provider_calls': 0, 'live_execution_available': False}))
        return 0
    except AssessmentError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error),
                          'diagnostic': safe_diagnostic(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'selection_preview_failed',
                          'message': 'The public evidence preparation stopped safely.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
