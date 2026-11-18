"""Validate supplied per-part judgments; never infer semantic support from scores."""

from dataclasses import dataclass, field
import hashlib
import json

from notelens_contracts.v1 import ContractValidationError, validate_record

from .diagnostics import ValidationDiagnostic


POLICY_VERSION = 'supplied-support-judgments-v1'


class SupportError(ValueError):
    """Fixed diagnostics that never include source, question or assessor text."""

    def __init__(self, code='assessment_invalid', *, rule='validation_failed', path='/'):
        self.code = code
        self.diagnostic = ValidationDiagnostic(
            stage='context' if code == 'support_context_invalid' else 'assessment', rule=rule, path=path)
        super().__init__('The supplied support assessment or its bound context is invalid.')


@dataclass(frozen=True, slots=True)
class SupportQuote:
    passage_id: str
    start: int
    end: int
    quote: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class PartReview:
    requirement_id: str
    status: str
    reason: str = field(repr=False)
    evidence: tuple[SupportQuote, ...]


@dataclass(frozen=True, slots=True)
class SupportDecision:
    coverage: str
    supported_requirement_ids: tuple[str, ...]
    missing_requirement_ids: tuple[str, ...]
    conflicting_requirement_ids: tuple[str, ...]
    context_sha256: str
    parts: tuple[PartReview, ...] = field(repr=False)
    policy_version: str = POLICY_VERSION
    semantic_support_independently_verified: bool = False
    wire_mapping_applied: bool = False


def _require(condition, code='assessment_invalid', *, rule='validation_failed', path='/'):
    if not condition:
        raise SupportError(code, rule=rule, path=path)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _snapshot(value, code):
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=False, allow_nan=False).encode('utf-8')
        return json.loads(encoded), hashlib.sha256(encoded).hexdigest()
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError):
        raise SupportError(code, rule='json_value') from None


def _context(request, candidates, requirements):
    snapshot, digest = _snapshot({'policy_version': POLICY_VERSION, 'request': request,
        'candidates': candidates, 'requirements': requirements}, 'support_context_invalid')
    request, candidates, requirements = (snapshot[name] for name in
                                         ('request', 'candidates', 'requirements'))
    try:
        validate_record('RetrievalRequest', request)
    except ContractValidationError:
        raise SupportError('support_context_invalid', rule='context_request', path='/request') from None
    code = 'support_context_invalid'
    _require(isinstance(candidates, dict), code, rule='context_shape', path='/candidates')
    _require(candidates.get('record_format_version') == 'rag-candidate-ranking-v1'
             and candidates.get('status') == 'ranked_candidates'
             and candidates.get('answerability') == 'not_assessed'
             and candidates.get('mode') in ('mock', 'live'), code, rule='context_shape', path='/candidates')
    _require(candidates.get('question_sha256') == hashlib.sha256(
        request['question'].encode('utf-8')).hexdigest(), code,
        rule='context_binding', path='/candidates/question_sha256')
    _require(all(_text(candidates.get(key)) for key in
                 ('corpus_version', 'index_version', 'retriever_version', 'score_note')), code,
             rule='context_shape', path='/candidates')
    top_k, passages = candidates.get('top_k'), candidates.get('passages')
    _require(type(top_k) is int and 1 <= top_k <= 5, code, rule='context_shape', path='/candidates/top_k')
    _require(isinstance(passages, list) and len(passages) <= top_k, code,
             rule='context_shape', path='/candidates/passages')
    for index, passage in enumerate(passages):
        try:
            validate_record('RetrievalPassage', passage)
        except ContractValidationError:
            raise SupportError(code, rule='context_passage', path=f'/candidates/passages/{index}') from None
    _require(len({p['passage_id'] for p in passages}) == len(passages)
             and len({p['source_id'] for p in passages}) == len(passages), code,
             rule='context_passage', path='/candidates/passages')
    _require(isinstance(requirements, list) and bool(requirements), code,
             rule='context_requirements', path='/requirements')
    _require(all(isinstance(part, dict) and set(part) == {'requirement_id', 'description'}
                 and _text(part['requirement_id']) and _text(part['description'])
                 for part in requirements), code, rule='context_requirements', path='/requirements')
    _require(len({part['requirement_id'] for part in requirements}) == len(requirements), code,
             rule='context_requirements', path='/requirements')
    return candidates, requirements, digest


def support_context_sha256(request, candidates, requirements):
    """Bind a future review to exact inputs, versions and declared question parts."""
    return _context(request, candidates, requirements)[2]


def assess_empty_candidates(request, candidates, requirements):
    """Return a bound missing-evidence decision after a successful empty search."""
    candidates, requirements, digest = _context(request, candidates, requirements)
    _require(not candidates['passages'], 'support_context_invalid', rule='context_shape',
             path='/candidates/passages')
    parts = tuple(PartReview(part['requirement_id'], 'not_supported',
                           'The completed search returned no passages.', ()) for part in requirements)
    return SupportDecision('none', (), tuple(part.requirement_id for part in parts), (), digest, parts)


def evaluate_support(request, candidates, requirements, assessment):
    """Derive internal coverage from complete, supplied judgments and exact quotes.

    The caller supplies the question decomposition and semantic judgments. This
    function verifies neither their clinical meaning nor their completeness with
    respect to the natural-language question. It does not call a model, generate
    an answer, map to canonical retrieval states, log bodies or persist content.
    """
    candidates, requirements, digest = _context(request, candidates, requirements)
    assessment = _snapshot(assessment, 'assessment_invalid')[0]
    _require(isinstance(assessment, dict) and set(assessment) == {
        'format_version', 'context_sha256', 'parts'}, rule='assessment_shape')
    _require(assessment['format_version'] == 'rag-support-assessment-v1',
             rule='assessment_format', path='/format_version')
    _require(assessment['context_sha256'] == digest, rule='assessment_binding', path='/context_sha256')
    parts = assessment['parts']
    _require(isinstance(parts, list), rule='parts_shape', path='/parts')
    _require(len(parts) == len(requirements), rule='parts_count', path='/parts')
    expected_ids = {part['requirement_id'] for part in requirements}
    sources = {p['passage_id']: p for p in candidates['passages']}
    reviews = {}
    for part_index, part in enumerate(parts):
        location = f'/parts/{part_index}'
        _require(isinstance(part, dict) and set(part) == {
            'requirement_id', 'status', 'reason', 'evidence'}, rule='part_shape', path=location)
        key, status = part['requirement_id'], part['status']
        _require(isinstance(key, str) and key in expected_ids,
                 rule='requirement_reference', path=location+'/requirement_id')
        _require(key not in reviews, rule='duplicate_requirement', path=location+'/requirement_id')
        _require(status in ('supported', 'not_supported', 'conflicting'), rule='part_status', path=location+'/status')
        _require(_text(part['reason']), rule='reason_empty', path=location+'/reason')
        evidence = part['evidence']
        _require(isinstance(evidence, list), rule='evidence_shape', path=location+'/evidence')
        _require((status == 'not_supported' and not evidence)
                 or (status == 'supported' and len(evidence) >= 1)
                 or (status == 'conflicting' and len(evidence) >= 2),
                 rule='evidence_policy', path=location+'/evidence')
        checked_quotes, spans = [], set()
        for quote_index, quote in enumerate(evidence):
            quote_location = location+f'/evidence/{quote_index}'
            _require(isinstance(quote, dict) and set(quote) == {
                'passage_id', 'start', 'end', 'quote'}, rule='quote_shape', path=quote_location)
            passage_id, start, end = quote['passage_id'], quote['start'], quote['end']
            _require(isinstance(passage_id, str) and passage_id in sources,
                     rule='source_reference', path=quote_location+'/passage_id')
            text = sources[passage_id]['text']
            _require(type(start) is int, rule='offset_type', path=quote_location+'/start')
            _require(type(end) is int, rule='offset_type', path=quote_location+'/end')
            _require(0 <= start < end <= len(text), rule='offset_bounds', path=quote_location)
            _require(_text(quote['quote']), rule='quote_empty', path=quote_location+'/quote')
            _require(text[start:end] == quote['quote'], rule='quote_mismatch', path=quote_location+'/quote')
            span = (passage_id, start, end)
            _require(span not in spans, rule='duplicate_evidence', path=quote_location)
            spans.add(span)
            checked_quotes.append(SupportQuote(passage_id, start, end, quote['quote']))
        reviews[key] = PartReview(key, status, part['reason'], tuple(checked_quotes))
    _require(set(reviews) == expected_ids, rule='requirement_coverage', path='/parts')
    ordered = tuple(reviews[part['requirement_id']] for part in requirements)
    supported = tuple(part.requirement_id for part in ordered if part.status == 'supported')
    missing = tuple(part.requirement_id for part in ordered if part.status != 'supported')
    conflicting = tuple(part.requirement_id for part in ordered if part.status == 'conflicting')
    coverage = 'full' if not missing else ('partial' if supported else 'none')
    return SupportDecision(coverage, supported, missing, conflicting, digest, ordered)
