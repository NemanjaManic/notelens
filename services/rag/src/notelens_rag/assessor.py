"""Versioned Luna assessment prompt and offline-only Responses SDK integration."""

from dataclasses import dataclass, field
import hashlib
from importlib.resources import files
import json
import math

import httpx2 as httpx
import openai

from .diagnostics import ValidationDiagnostic, safe_diagnostic
from .support import SupportDecision, SupportError, evaluate_support, support_context_sha256


MODEL = 'gpt-6-luna'
PROMPT_VERSION = 'literature-support-assessment-v1'


class AssessmentError(ValueError):
    """A fixed diagnostic; never expose provider, question or passage bodies."""

    def __init__(self, code='invalid_assessment', *, diagnostic=None):
        self.code = code
        self.diagnostic = (diagnostic if type(diagnostic) is ValidationDiagnostic else ValidationDiagnostic())
        super().__init__('The literature support assessment could not be completed safely.')


def _require(condition, code='invalid_assessment', *, stage='validation', rule='validation_failed', path='/'):
    if not condition:
        raise AssessmentError(code, diagnostic=ValidationDiagnostic(stage=stage, rule=rule, path=path))


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


class _InvalidJSON(ValueError):
    def __init__(self, rule):
        self.rule = rule


def _strict_json(value, *, stage='response', path='/'):
    def pairs(items):
        result = {}
        for key, child in items:
            if key in result:
                raise _InvalidJSON('json_duplicate_key')
            result[key] = child
        return result
    def reject_constant(value):
        raise _InvalidJSON('json_nonfinite')
    try:
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='strict')
        return json.loads(value, object_pairs_hook=pairs, parse_constant=reject_constant)
    except _InvalidJSON as error:
        raise AssessmentError('invalid_upstream', diagnostic=ValidationDiagnostic(
            stage=stage, rule=error.rule, path=path)) from None
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise AssessmentError('invalid_upstream', diagnostic=ValidationDiagnostic(
            stage=stage, rule='json_invalid', path=path)) from None


def _object(properties):
    return {'type': 'object', 'additionalProperties': False,
            'properties': properties, 'required': list(properties)}


@dataclass(frozen=True, slots=True)
class AssessmentParameters:
    max_output_tokens: int
    reasoning_effort: str
    timeout_seconds: float

    def __post_init__(self):
        _require(type(self.max_output_tokens) is int and self.max_output_tokens > 0, 'configuration_required')
        _require(self.reasoning_effort in ('none', 'low', 'medium', 'high', 'xhigh', 'max'), 'configuration_required')
        _require(type(self.timeout_seconds) in (int, float) and math.isfinite(self.timeout_seconds)
                 and self.timeout_seconds > 0, 'configuration_required')


@dataclass(frozen=True, slots=True)
class PreparedAssessment:
    context_sha256: str
    prompt_sha256: str
    instructions: str = field(repr=False)
    input_json: str = field(repr=False)
    schema_json: str = field(repr=False)
    inputs_json: str = field(repr=False)
    prompt_version: str = PROMPT_VERSION


@dataclass(frozen=True, slots=True)
class ModelAssessment:
    decision: SupportDecision
    prompt_sha256: str
    configuration_version: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    mode: str = 'mock'
    model: str = MODEL
    prompt_version: str = PROMPT_VERSION


def prepare_assessment(request, candidates, requirements):
    """Prepare immutable evidence input without a key, SDK client or network call."""
    try:
        inputs_json = _json({'request': request, 'candidates': candidates, 'requirements': requirements})
        inputs_json.encode('utf-8', errors='strict')
        snapshot = _strict_json(inputs_json)
        request, candidates, requirements = (snapshot[key] for key in ('request', 'candidates', 'requirements'))
        digest = support_context_sha256(request, candidates, requirements)
    except SupportError as error:
        value = safe_diagnostic(error)
        raise AssessmentError('support_context_invalid', diagnostic=ValidationDiagnostic(
            stage=value['stage'], rule=value['rule'], path=value['path'])) from None
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise AssessmentError('support_context_invalid') from None
    _require(bool(candidates['passages']), 'no_candidates')
    try:
        instructions = files('notelens_rag').joinpath('prompts/support-assessment-v1.txt').read_bytes().decode('utf-8')
    except (OSError, UnicodeError):
        raise AssessmentError('configuration_required') from None
    quote = _object({'passage_id': {'type': 'string', 'enum': [p['passage_id'] for p in candidates['passages']]},
        'start': {'type': 'integer'}, 'end': {'type': 'integer'}, 'quote': {'type': 'string'}})
    part = _object({'requirement_id': {'type': 'string', 'enum': [p['requirement_id'] for p in requirements]},
        'status': {'type': 'string', 'enum': ['supported', 'not_supported', 'conflicting']},
        'reason': {'type': 'string'}, 'evidence': {'type': 'array', 'items': quote}})
    schema = _object({'requirements_cover_question': {'type': 'boolean'},
        'assessment': _object({'format_version': {'type': 'string', 'enum': ['rag-support-assessment-v1']},
            'context_sha256': {'type': 'string', 'enum': [digest]},
            'parts': {'type': 'array', 'items': part}})})
    payload = {'question': request['question'], 'requirements': requirements, 'context_sha256': digest,
        'passages': [{key: p[key] for key in ('passage_id', 'title', 'text')} for p in candidates['passages']]}
    return PreparedAssessment(digest, hashlib.sha256(instructions.encode('utf-8')).hexdigest(),
                              instructions, _json(payload), _json(schema), inputs_json)


def checked_assessment_response(raw_bytes, prepared, parameters, *, mode='mock'):
    _require(mode in ('mock', 'live'), 'configuration_required')
    response = _strict_json(raw_bytes, stage='response', path='/response')
    _require(isinstance(response, dict) and response.get('object') == 'response'
             and response.get('model') == MODEL, 'invalid_upstream',
             stage='response', rule='response_identity', path='/response')
    _require(response.get('status') == 'completed' and response.get('error') is None
             and response.get('incomplete_details') is None, 'assessment_incomplete',
             stage='response', rule='response_incomplete', path='/response/status')
    output = response.get('output')
    _require(isinstance(output, list) and bool(output), 'invalid_upstream',
             stage='response', rule='response_output', path='/response/output')
    texts = []
    for index, item in enumerate(output):
        location = f'/response/output/{index}'
        _require(isinstance(item, dict), 'invalid_upstream', stage='response', rule='response_item', path=location)
        if item.get('type') == 'reasoning':
            continue
        _require(item.get('type') == 'message' and item.get('role') == 'assistant'
                 and item.get('status') == 'completed', 'invalid_upstream',
                 stage='response', rule='response_item', path=location)
        content = item.get('content')
        _require(isinstance(content, list) and len(content) == 1
                 and isinstance(content[0], dict), 'invalid_upstream',
                 stage='response', rule='response_content', path=location+'/content')
        _require(content[0].get('type') != 'refusal', 'assessment_refused',
                 stage='response', rule='response_refusal', path=location+'/content/0')
        _require(content[0].get('type') == 'output_text' and isinstance(content[0].get('text'), str),
                 'invalid_upstream', stage='response', rule='response_text', path=location+'/content/0/text')
        texts.append(content[0]['text'])
    _require(len(texts) == 1, 'invalid_upstream',
             stage='response', rule='response_text_count', path='/response/output')
    usage = response.get('usage')
    _require(isinstance(usage, dict) and all(type(usage.get(key)) is int and usage[key] >= 0
                 for key in ('input_tokens', 'output_tokens', 'total_tokens')), 'invalid_upstream',
             stage='response', rule='usage_shape', path='/response/usage')
    _require(usage['total_tokens'] == usage['input_tokens'] + usage['output_tokens'], 'invalid_upstream',
             stage='response', rule='usage_total', path='/response/usage/total_tokens')
    _require(usage['output_tokens'] <= parameters.max_output_tokens, 'invalid_upstream',
             stage='response', rule='usage_limit', path='/response/usage/output_tokens')
    result = _strict_json(texts[0], stage='assessment')
    _require(isinstance(result, dict) and set(result) == {'requirements_cover_question', 'assessment'},
             stage='assessment', rule='model_output_shape')
    _require(type(result['requirements_cover_question']) is bool,
             stage='assessment', rule='coverage_flag_type', path='/requirements_cover_question')
    _require(result['requirements_cover_question'], 'requirements_incomplete',
             stage='assessment', rule='requirements_incomplete', path='/requirements_cover_question')
    inputs = _strict_json(prepared.inputs_json)
    try:
        decision = evaluate_support(inputs['request'], inputs['candidates'], inputs['requirements'], result['assessment'])
    except SupportError as error:
        value = safe_diagnostic(error)
        path = value['path']
        if value['stage'] == 'assessment':
            path = '/assessment' + (path if path != '/' else '')
        raise AssessmentError('invalid_assessment', diagnostic=ValidationDiagnostic(
            stage=value['stage'], rule=value['rule'], path=path)) from None
    configuration = {'adapter': 'offline-luna-responses-v1' if mode == 'mock' else 'bounded-luna-responses-v1',
        'mode': mode, 'model': MODEL,
        'prompt_version': PROMPT_VERSION, 'prompt_sha256': prepared.prompt_sha256,
        'max_output_tokens': parameters.max_output_tokens, 'reasoning_effort': parameters.reasoning_effort,
        'timeout_seconds': parameters.timeout_seconds, 'max_retries': 0,
        'store': False, 'tools': [], 'truncation': 'disabled'}
    version = hashlib.sha256(_json(configuration).encode('utf-8')).hexdigest()
    return ModelAssessment(decision, prepared.prompt_sha256, version,
                           usage['input_tokens'], usage['output_tokens'], usage['total_tokens'], mode=mode)


def assessment_request(prepared, parameters):
    """Use the same immutable input/schema for counting and eventual generation."""
    return {'model': MODEL, 'instructions': prepared.instructions, 'input': prepared.input_json,
        'text': {'format': {'type': 'json_schema', 'name': 'notelens_support_assessment',
                          'strict': True, 'schema': _strict_json(prepared.schema_json)}},
        'reasoning': {'effort': parameters.reasoning_effort},
        'max_output_tokens': parameters.max_output_tokens,
        'store': False, 'stream': False, 'background': False, 'truncation': 'disabled',
        'tools': [], 'tool_choice': 'none'}


def assessment_count_request(prepared, parameters):
    payload = assessment_request(prepared, parameters)
    return {key: value for key, value in payload.items()
            if key not in ('max_output_tokens', 'store', 'stream', 'background')}


class OfflineLunaAssessor:
    """Exercise the actual SDK only through a mandatory in-memory MockTransport.

    There is deliberately no live client factory, credential loading or execution
    switch. A separately approved bounded live gateway is required before model
    activation. Fixture parameters are not approved production defaults.
    """

    def __init__(self, *, transport, parameters):
        _require(isinstance(transport, httpx.MockTransport)
                 and isinstance(parameters, AssessmentParameters), 'configuration_required')
        self.parameters = parameters
        self._client = openai.OpenAI(api_key='offline-fixture-key', base_url='https://api.openai.com/v1',
            timeout=parameters.timeout_seconds, max_retries=0,
            http_client=openai.DefaultHttpxClient(transport=transport, trust_env=False))

    def close(self):
        self._client.close()

    def assess(self, request, candidates, requirements):
        prepared = prepare_assessment(request, candidates, requirements)
        try:
            raw = self._client.responses.with_raw_response.create(**assessment_request(prepared, self.parameters))
        except openai.APITimeoutError:
            raise AssessmentError('timeout') from None
        except openai.RateLimitError:
            raise AssessmentError('rate_limit') from None
        except (openai.AuthenticationError, openai.PermissionDeniedError):
            raise AssessmentError('provider_authentication') from None
        except openai.APIError:
            raise AssessmentError('provider_unavailable') from None
        return checked_assessment_response(raw.http_response.content, prepared, self.parameters)
