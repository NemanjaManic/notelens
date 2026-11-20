"""Prepare and check model-proposed question parts through a key-free SDK adapter."""

import hashlib
from importlib.resources import files
import unicodedata

from .assessor import (
    AssessmentError, OfflineLunaAssessor, PreparedAssessment, _json, _object,
    _require, _strict_json, assessment_request, checked_completion_content,
)
from .contracts import ContractError, Contracts


PROMPT_VERSION = 'literature-question-parts-v1'
STATUSES = ('ready', 'unsupported_language', 'needs_clarification', 'out_of_scope')
MAX_PARTS = 8
MAX_DESCRIPTION_LENGTH = 500


def prepare_question_parts(request):
    """Bind only the exact question. No document, concepts or retrieval data is sent."""
    try:
        Contracts().validate('RetrievalRequest', request)
        question = request['question']
        digest = hashlib.sha256(question.encode('utf-8', errors='strict')).hexdigest()
    except (ContractError, UnicodeError):
        raise AssessmentError('validation_failure') from None
    try:
        instructions = files('notelens_rag').joinpath('prompts/question-parts-v1.txt').read_bytes().decode('utf-8')
    except (OSError, UnicodeError):
        raise AssessmentError('configuration_required') from None
    payload = {'question': question, 'question_sha256': digest}
    schema = _object({'question_sha256': {'type': 'string', 'enum': [digest]},
        'status': {'type': 'string', 'enum': list(STATUSES)}, 'parts': {'type': 'array',
            'items': _object({'description': {'type': 'string'}, 'anchor': {'type': 'string'}})}})
    return PreparedAssessment(digest, hashlib.sha256(instructions.encode()).hexdigest(),
        instructions, _json(payload), _json(schema), _json({'schema_version': '1.0.0', 'question': question}),
        prompt_version=PROMPT_VERSION)


def _bound_question(prepared):
    _require(type(prepared) is PreparedAssessment, 'question_context_invalid')
    request = _strict_json(prepared.inputs_json, stage='context')
    _require(prepare_question_parts(request) == prepared, 'question_context_invalid')
    return request['question']


def question_parts_request(prepared, parameters):
    _bound_question(prepared)
    payload = assessment_request(prepared, parameters)
    payload['text']['format']['name'] = 'notelens_question_parts'
    return payload


def checked_question_parts_response(raw_bytes, prepared, parameters):
    """Validate binding and anchors. Semantic completeness requires a separate review."""
    question = _bound_question(prepared)
    output, _ = checked_completion_content(raw_bytes, parameters)
    _require(isinstance(output, dict) and set(output) == {'question_sha256', 'status', 'parts'}
             and output['question_sha256'] == prepared.context_sha256 and output['status'] in STATUSES
             and isinstance(output['parts'], list), 'invalid_question_parts')
    if output['status'] != 'ready':
        _require(not output['parts'], 'invalid_question_parts')
        raise AssessmentError(output['status'])
    _require(1 <= len(output['parts']) <= MAX_PARTS, 'invalid_question_parts')
    parts, seen = [], set()
    for index, part in enumerate(output['parts'], start=1):
        _require(isinstance(part, dict) and set(part) == {'description', 'anchor'}, 'invalid_question_parts')
        description, anchor = part['description'], part['anchor']
        _require(isinstance(anchor, str) and bool(anchor.strip()) and anchor in question
                 and isinstance(description, str) and description == description.strip()
                 and 1 <= len(description) <= MAX_DESCRIPTION_LENGTH
                 and all(unicodedata.category(char) not in ('Cc', 'Cs') for char in description),
                 'invalid_question_parts')
        normalized = ' '.join(description.casefold().split())
        _require(normalized not in seen, 'invalid_question_parts')
        seen.add(normalized)
        parts.append({'requirement_id': f'part-{index}', 'description': description})
    return parts


class OfflineQuestionDecomposer(OfflineLunaAssessor):
    """Callable for the service's requirements step. SDK transport is always mocked."""

    def _request(self, prepared):
        return question_parts_request(prepared, self.parameters)

    def __call__(self, request):
        prepared = prepare_question_parts(request)
        return checked_question_parts_response(self._raw_response(prepared), prepared, self.parameters)
