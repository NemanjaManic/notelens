"""Compose cited literature answers from bound support; no live activation here."""

from dataclasses import asdict, dataclass, field
import hashlib
from importlib.resources import files

from .assessor import (AssessmentError, OfflineLunaAssessor, PreparedAssessment,
    _json, _object, _require, _strict_json, assessment_request, checked_completion_content)
from .contracts import Contracts
from .mock import DEMO_NOTICE
from .support import SupportDecision, SupportError, evaluate_support


PROMPT_VERSION = 'literature-answer-v1'
ANSWER_VERSION = 'rag-cited-claims-v1'
PARTIAL_POLICY = 'supported-subset-v1'


@dataclass(frozen=True, slots=True)
class PreparedAnswer(PreparedAssessment):
    evidence_json: str = field(repr=False, kw_only=True)
    coverage: str = field(kw_only=True)
    prompt_version: str = PROMPT_VERSION


@dataclass(frozen=True, slots=True)
class LiteratureAnswer:
    body_json: str = field(repr=False)
    quote_trace_json: str = field(repr=False)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    @property
    def body(self):
        return _strict_json(self.body_json)


def prepare_answer(request, candidates, requirements, decision):
    """Revalidate complete support and expose only supported quotes to generation."""
    _require(type(decision) is SupportDecision, 'support_context_invalid')
    assessment = {'format_version': 'rag-support-assessment-v1',
        'context_sha256': decision.context_sha256, 'parts': [asdict(part) for part in decision.parts]}
    # asdict preserves tuples; the existing processor snapshots them as JSON arrays.
    try:
        checked = evaluate_support(request, candidates, requirements, assessment)
    except SupportError:
        raise AssessmentError('support_context_invalid') from None
    _require(checked == decision, 'support_context_invalid')
    try:
        snapshot = _json({'request': request, 'candidates': candidates, 'requirements': requirements,
                          'assessment': assessment})
        snapshot.encode('utf-8', errors='strict')
        instructions = files('notelens_rag').joinpath('prompts/literature-answer-v1.txt').read_bytes().decode('utf-8')
    except (TypeError, ValueError, UnicodeError, OSError):
        raise AssessmentError('configuration_required') from None
    descriptions = {part['requirement_id']: part['description'] for part in requirements}
    evidence = []
    for part in decision.parts:
        if part.status == 'supported':
            for quote in part.evidence:
                evidence.append({'evidence_id': f'e{len(evidence)+1}', 'requirement_id': part.requirement_id,
                                 **asdict(quote)})
    supported = list(decision.supported_requirement_ids)
    claim = _object({'requirement_id': {'type': 'string', 'enum': supported}, 'text': {'type': 'string'},
        'evidence_ids': {'type': 'array', 'items': {'type': 'string', 'enum': [e['evidence_id'] for e in evidence]}}})
    schema = _object({'language': {'type': 'string', 'enum': ['en']},
                      'claims': {'type': 'array', 'items': claim}})
    payload = {'question': request['question'], 'context_sha256': decision.context_sha256,
        'supported_parts': [{'requirement_id': key, 'description': descriptions[key]} for key in supported],
        'evidence': [{'evidence_id': item['evidence_id'], 'requirement_id': item['requirement_id'],
                      'quote': item['quote']} for item in evidence]}
    return PreparedAnswer(decision.context_sha256, hashlib.sha256(instructions.encode()).hexdigest(),
        instructions, _json(payload), _json(schema), snapshot,
        evidence_json=_json(evidence), coverage=decision.coverage)


def _bound(prepared):
    _require(type(prepared) is PreparedAnswer, 'support_context_invalid')
    inputs = _strict_json(prepared.inputs_json)
    try:
        decision = evaluate_support(inputs['request'], inputs['candidates'], inputs['requirements'], inputs['assessment'])
        expected = prepare_answer(inputs['request'], inputs['candidates'], inputs['requirements'], decision)
    except (SupportError, KeyError, TypeError):
        raise AssessmentError('support_context_invalid') from None
    _require(expected == prepared, 'support_context_invalid')
    return inputs, decision


def _partial_gate(decision, partial_policy):
    _require(partial_policy in (None, PARTIAL_POLICY), 'configuration_required')
    _require(decision.coverage != 'partial' or partial_policy == PARTIAL_POLICY,
             'partial_policy_required')


def retrieval_result(prepared, *, partial_policy=None):
    """Map only under an explicit owner-supplied partial gate interpretation."""
    inputs, decision = _bound(prepared)
    _partial_gate(decision, partial_policy)
    candidates = inputs['candidates']
    body = {key: candidates[key] for key in ('mode', 'passages', 'corpus_version', 'index_version',
                                           'retriever_version', 'score_note')}
    body.update(schema_version='1.0.0', state='insufficient' if decision.coverage == 'none' else 'sufficient')
    Contracts().validate('RetrievalResult', body)
    return body


def answer_request(prepared, parameters):
    _bound(prepared)
    _require(prepared.coverage != 'none', 'no_supported_answer')
    payload = assessment_request(prepared, parameters)
    payload['text']['format']['name'] = 'notelens_literature_answer'
    return payload


def _base(prepared, partial_policy):
    inputs, decision = _bound(prepared)
    retrieval = retrieval_result(prepared, partial_policy=partial_policy)
    provenance = {key: retrieval[key] for key in ('mode', 'state', 'corpus_version', 'index_version',
                                                'retriever_version', 'score_note')}
    provenance['service'] = 'rag'
    descriptions = {part['requirement_id']: part['description'] for part in inputs['requirements']}
    warnings = [DEMO_NOTICE]
    for part in decision.parts:
        if part.status != 'supported':
            prefix = 'Conflicting evidence for' if part.status == 'conflicting' else 'The retrieved sources do not support'
            warnings.append(f"{prefix} the requested information: {descriptions[part.requirement_id]}")
    body = {'schema_version': '1.0.0', 'mode': retrieval['mode'], 'language': 'en',
        'text': 'The available sources do not support an answer.', 'claims': [], 'sources': [],
        'evidence_state': 'insufficient', 'warnings': warnings, 'route': 'none',
        'answer_version': ANSWER_VERSION, 'prompt_version': None, 'components': [],
        'attempted_routes': ['literature'], 'clarification': None, 'retrieval_provenance': provenance}
    return inputs, decision, body


def unsupported_answer(prepared):
    _, decision, body = _base(prepared, None)
    _require(decision.coverage == 'none', 'support_context_invalid')
    Contracts().validate('AnswerResult', body)
    return LiteratureAnswer(_json(body), '[]')


def checked_answer_response(raw_bytes, prepared, parameters, *, mode='mock', partial_policy=None):
    inputs, decision, body = _base(prepared, partial_policy)
    _require(decision.coverage != 'none', 'no_supported_answer')
    _require(inputs['candidates']['mode'] == mode, 'configuration_required')
    output, usage = checked_completion_content(raw_bytes, parameters, mode=mode)
    _require(isinstance(output, dict) and set(output) == {'language', 'claims'}
             and output['language'] == 'en' and isinstance(output['claims'], list)
             and bool(output['claims']), 'invalid_answer')
    options = {e['evidence_id']: e for e in _strict_json(prepared.evidence_json)}
    sources = {p['passage_id']: p for p in inputs['candidates']['passages']}
    used_sources, covered, texts, trace = {}, set(), set(), []
    component_id = 'rag-answer-' + prepared.context_sha256[:20]
    for position, claim in enumerate(output['claims']):
        _require(isinstance(claim, dict) and set(claim) == {'requirement_id', 'text', 'evidence_ids'}, 'invalid_answer')
        key, text, ids = claim['requirement_id'], claim['text'], claim['evidence_ids']
        _require(isinstance(key, str) and key in decision.supported_requirement_ids
                 and isinstance(text, str) and bool(text.strip()) and text not in texts
                 and isinstance(ids, list) and bool(ids) and all(isinstance(i, str) for i in ids)
                 and len(set(ids)) == len(ids) and all(i in options and options[i]['requirement_id'] == key for i in ids),
                 'invalid_answer')
        try:
            text.encode('utf-8', errors='strict')
        except UnicodeError:
            raise AssessmentError('invalid_answer') from None
        source_ids = []
        claim_id = f'rag-claim-{position+1}'
        for identifier in ids:
            quote = options[identifier]
            source = sources[quote['passage_id']]
            source_id = source['source_id']
            used_sources[source_id] = {k: v for k, v in source.items() if k != 'score'} | {'component_id': component_id}
            if source_id not in source_ids:
                source_ids.append(source_id)
            trace.append({'claim_id': claim_id, **quote})
        covered.add(key); texts.add(text)
        body['claims'].append({'claim_id': claim_id, 'text': text, 'scope': 'general_information',
                              'source_ids': source_ids, 'component_id': component_id})
    _require(covered == set(decision.supported_requirement_ids), 'answer_incomplete')
    configuration = {'adapter': 'luna-cited-answer-v1', 'mode': mode, 'model': 'gpt-6-luna',
        'prompt_sha256': prepared.prompt_sha256, 'parameters': asdict(parameters), 'max_retries': 0,
        'store': False, 'partial_policy': partial_policy}
    body.update(text='\n\n'.join(c['text'] for c in body['claims']), route='literature',
        evidence_state='sufficient' if decision.coverage == 'full' else 'partial',
        sources=list(used_sources.values()), prompt_version=PROMPT_VERSION,
        components=[{'component_id': component_id, 'service': 'rag', 'operation': 'literature-answer',
            'mode': mode, 'output_version': ANSWER_VERSION, 'prompt_version': PROMPT_VERSION,
            'provider': 'mock' if mode == 'mock' else 'openai', 'model': 'gpt-6-luna',
            'configuration_version': hashlib.sha256(_json(configuration).encode()).hexdigest(),
            **{k: inputs['candidates'][k] for k in ('corpus_version', 'index_version', 'retriever_version')}}])
    if mode == 'mock':
        body['warnings'].append('Simulated model output; no live answer-generation call was made.')
    Contracts().validate('AnswerResult', body)
    return LiteratureAnswer(_json(body), _json(trace), usage['input_tokens'], usage['output_tokens'], usage['total_tokens'])


class OfflineLiteratureGenerator(OfflineLunaAssessor):
    """Actual SDK and frozen wire validation through mandatory MockTransport only."""

    def _request(self, prepared):
        return answer_request(prepared, self.parameters)

    def generate(self, prepared, *, partial_policy=None):
        _, decision = _bound(prepared)
        _partial_gate(decision, partial_policy)
        if decision.coverage == 'none':
            return unsupported_answer(prepared)
        return checked_answer_response(self._raw_response(prepared), prepared, self.parameters,
                                       partial_policy=partial_policy)
