"""Check supplied support judgments without claiming automated semantic accuracy."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
import socket

import pytest

from notelens_rag.support import (
    SupportError, evaluate_support, support_context_sha256,
)


@pytest.fixture
def case(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError('Support evaluation must not access a provider.')
    monkeypatch.setattr(socket, 'create_connection', no_network)
    question = 'What causes synthetic condition A, and how long does it last?'
    text = 'Example \U0001f600. Cause: synthetic agent A.\nRepeated. Repeated.'
    request = {'schema_version': '1.0.0', 'question': question}
    source = {'source_id': 'passage-a', 'kind': 'literature', 'topic_id': '1',
        'passage_id': 'passage-a', 'title': 'Synthetic condition A',
        'url': 'https://example.invalid/a', 'text': text,
        'snapshot_date': '2026-11-10', 'score': 0.49}
    candidates = {'record_format_version': 'rag-candidate-ranking-v1',
        'status': 'ranked_candidates', 'mode': 'mock', 'answerability': 'not_assessed',
        'question_sha256': hashlib.sha256(question.encode()).hexdigest(),
        'passages': [source], 'top_k': 5, 'signals_used': ['question'],
        'corpus_version': 'corpus-v1', 'index_version': 'index-v1',
        'retriever_version': 'retriever-v1', 'score_note': 'Synthetic ranking only.'}
    requirements = [
        {'requirement_id': 'cause', 'description': 'Cause of synthetic condition A'},
        {'requirement_id': 'duration', 'description': 'Duration of synthetic condition A'},
    ]
    start = text.index('Cause:')
    quote = {'passage_id': 'passage-a', 'start': start,
        'end': start + len('Cause: synthetic agent A.'), 'quote': 'Cause: synthetic agent A.'}
    assessment = {'format_version': 'rag-support-assessment-v1',
        'context_sha256': support_context_sha256(request, candidates, requirements),
        'parts': [
            {'requirement_id': 'cause', 'status': 'supported',
             'reason': 'The supplied synthetic review identifies the cause.', 'evidence': [quote]},
            {'requirement_id': 'duration', 'status': 'not_supported',
             'reason': 'The supplied synthetic review found no duration.', 'evidence': []},
        ]}
    return request, candidates, requirements, assessment


def test_partial_decision_keeps_supported_parts_and_explicit_gaps(case):
    decision = evaluate_support(*case)
    assert decision.coverage == 'partial'
    assert decision.supported_requirement_ids == ('cause',)
    assert decision.missing_requirement_ids == ('duration',)
    assert decision.conflicting_requirement_ids == ()
    assert decision.semantic_support_independently_verified is False
    assert decision.wire_mapping_applied is False
    assert decision.parts[1].reason == case[3]['parts'][1]['reason']


def test_full_coverage_requires_all_supplied_parts_supported(case):
    request, candidates, requirements, assessment = case
    requirements = requirements[:1]
    assessment['parts'] = assessment['parts'][:1]
    assessment['context_sha256'] = support_context_sha256(request, candidates, requirements)
    assert evaluate_support(request, candidates, requirements, assessment).coverage == 'full'


def test_related_candidates_without_supported_requested_parts_give_no_coverage(case):
    assessment = case[3]
    assessment['parts'][0].update(status='not_supported', evidence=[])
    decision = evaluate_support(*case)
    assert decision.coverage == 'none'
    assert decision.supported_requirement_ids == ()
    assert decision.missing_requirement_ids == ('cause', 'duration')


def test_empty_candidates_can_only_be_assessed_without_support(case):
    request, candidates, requirements, assessment = case
    candidates['passages'] = []
    assessment['context_sha256'] = support_context_sha256(request, candidates, requirements)
    assessment['parts'][0].update(status='not_supported', evidence=[])
    assert evaluate_support(*case).coverage == 'none'


def test_missing_part_is_an_invalid_assessment_not_an_unsupported_answer(case):
    case[3]['parts'].pop()
    with pytest.raises(SupportError):
        evaluate_support(*case)


@pytest.mark.parametrize('change', ['question', 'hint', 'passage_text', 'score',
    'index_version', 'corpus_version', 'retriever_version', 'requirement_description'])
def test_assessment_cannot_be_reused_for_a_changed_context(case, change):
    request, candidates, requirements, assessment = case
    if change == 'question':
        request['question'] += ' Changed.'
        candidates['question_sha256'] = hashlib.sha256(request['question'].encode()).hexdigest()
    elif change == 'hint':
        request['specialty_hint'] = 'Neurology'
    elif change in {'passage_text', 'score'}:
        candidates['passages'][0]['text' if change == 'passage_text' else 'score'] = (
            'Changed source.' if change == 'passage_text' else 0.9)
    elif change == 'requirement_description':
        requirements[0]['description'] += ' Changed.'
    else:
        candidates[change] += '-changed'
    with pytest.raises(SupportError):
        evaluate_support(*case)


@pytest.mark.parametrize('change', ['unknown', 'duplicate', 'not_assessed', 'blank_reason', 'extra_field'])
def test_unknown_duplicate_unfinished_and_malformed_part_reviews_fail_closed(case, change):
    parts = case[3]['parts']
    if change == 'unknown': parts[0]['requirement_id'] = 'unknown'
    elif change == 'duplicate': parts[1]['requirement_id'] = parts[0]['requirement_id']
    elif change == 'not_assessed': parts[0]['status'] = 'not_assessed'
    elif change == 'blank_reason': parts[0]['reason'] = ' '
    else: parts[0]['extra'] = 'Unexpected field'
    with pytest.raises(SupportError):
        evaluate_support(*case)


@pytest.mark.parametrize('change', ['unknown_passage', 'wrong_quote', 'negative', 'past_end',
    'bool_offset', 'utf16_offset', 'duplicate_quote', 'no_quote', 'unrelated_quote_on_missing'])
def test_bad_or_misattributed_evidence_is_rejected(case, change):
    evidence = case[3]['parts'][0]['evidence']
    quote = evidence[0]
    if change == 'unknown_passage': quote['passage_id'] = 'not-retrieved'
    elif change == 'wrong_quote': quote['quote'] = 'A fact absent from this passage.'
    elif change == 'negative': quote['start'] = -1
    elif change == 'past_end': quote['end'] = 9999
    elif change == 'bool_offset': quote['start'] = True
    elif change == 'utf16_offset': quote['start'] += 1; quote['end'] += 1
    elif change == 'duplicate_quote': evidence.append(deepcopy(quote))
    elif change == 'no_quote': evidence.clear()
    else: case[3]['parts'][1]['evidence'] = [deepcopy(quote)]
    with pytest.raises(SupportError):
        evaluate_support(*case)


def test_repeated_text_is_bound_to_the_explicit_code_point_position(case):
    text = case[1]['passages'][0]['text']
    start = text.rindex('Repeated.')
    case[3]['parts'][0]['evidence'] = [
        {'passage_id': 'passage-a', 'start': start, 'end': start + 9, 'quote': 'Repeated.'}]
    decision = evaluate_support(*case)
    assert decision.parts[0].evidence[0].start == start
    # A mechanically valid quote does not independently verify the supplied meaning.
    assert decision.semantic_support_independently_verified is False


def test_conflicting_fact_is_not_counted_as_supported(case):
    request, candidates, requirements, assessment = case
    candidates['passages'][0]['text'] += '\nCause: synthetic agent B.'
    text = candidates['passages'][0]['text']
    start = text.index('Cause: synthetic agent B.')
    first = deepcopy(assessment['parts'][0]['evidence'][0])
    assessment['parts'][0].update(status='conflicting', evidence=[first,
        {'passage_id': 'passage-a', 'start': start, 'end': len(text),
         'quote': 'Cause: synthetic agent B.'}])
    assessment['context_sha256'] = support_context_sha256(request, candidates, requirements)
    decision = evaluate_support(*case)
    assert decision.coverage == 'none'
    assert decision.conflicting_requirement_ids == ('cause',)
    assert decision.missing_requirement_ids == ('cause', 'duration')


def test_conflict_needs_multiple_distinct_evidence_spans(case):
    case[3]['parts'][0]['status'] = 'conflicting'
    with pytest.raises(SupportError):
        evaluate_support(*case)


def test_result_is_immutable_input_is_unchanged_and_repr_omits_bodies(case):
    original = deepcopy(case)
    decision = evaluate_support(*case)
    assert case == original
    with pytest.raises(FrozenInstanceError): decision.coverage = 'full'
    with pytest.raises(FrozenInstanceError): decision.parts[0].evidence[0].quote = 'Changed'
    assert case[0]['question'] not in repr(decision)
    assert 'synthetic agent A' not in repr(decision)
    assert 'synthetic agent A' not in repr(decision.parts[0].evidence[0])


@pytest.mark.parametrize('change', ['bad_request', 'question_mismatch', 'bad_source',
    'duplicate_source', 'empty_requirements', 'duplicate_requirement', 'bad_candidate_state', 'nan_score'])
def test_invalid_context_is_rejected_without_private_diagnostics(case, change):
    request, candidates, requirements, _ = case
    if change == 'bad_request': request['extra'] = 'PRIVATE_BODY'
    elif change == 'question_mismatch': candidates['question_sha256'] = 'wrong'
    elif change == 'bad_source': candidates['passages'][0]['url'] = 'PRIVATE_BODY'
    elif change == 'duplicate_source': candidates['passages'].append(deepcopy(candidates['passages'][0]))
    elif change == 'empty_requirements': requirements.clear()
    elif change == 'duplicate_requirement': requirements.append(deepcopy(requirements[0]))
    elif change == 'bad_candidate_state': candidates['answerability'] = 'fully_supported'
    else: candidates['passages'][0]['score'] = float('nan')
    with pytest.raises(SupportError) as failure:
        evaluate_support(*case)
    assert 'PRIVATE_BODY' not in str(failure.value)
    assert request['question'] not in str(failure.value)
