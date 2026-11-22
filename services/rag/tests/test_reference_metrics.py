"""Counterexamples for topic aliases, passage budgets and canonical citations."""

import hashlib

import pytest

from notelens_rag.reference_metrics import alternative_topic_metrics, evidence_at_five, verify_reference


def ranked(*topics):
    return [{'topic_id': topic, 'passage_id': f'{topic}-{i}'} for i, topic in enumerate(topics)]


def test_equivalent_topic_is_an_alternative_not_an_extra_requirement():
    result = alternative_topic_metrics(ranked('6450', 'other'), [['34'], ['6450']])
    assert result['recall_at_5'] == 1.0
    assert result['all_required_topics_at_5'] is True


def test_parts_from_different_complete_sets_do_not_make_a_complete_answer():
    result = alternative_topic_metrics(ranked('a', 'd'), [['a', 'b'], ['c', 'd']])
    assert result['recall_at_5'] == 0.5
    assert result['all_required_topics_at_5'] is False


def test_repeated_chunks_do_not_increase_recall_or_extend_the_passage_budget():
    result = alternative_topic_metrics(ranked('a', 'a', 'a', 'x', 'b', 'c'), [['a', 'b', 'c']])
    assert result['recall_at_5'] == 2 / 3
    assert result['all_required_topics_at_5'] is False


def test_mrr_preserves_unique_topic_rank_convention():
    result = alternative_topic_metrics(ranked('x', 'x', 'a', 'b'), [['a', 'b']])
    assert result['reciprocal_rank_at_5'] == 0.5


def test_no_support_case_has_no_topic_denominator():
    assert alternative_topic_metrics(ranked('related'), []) is None
    assert evidence_at_five(ranked('related'), []) is None


def test_more_than_five_required_topics_is_flagged():
    result = alternative_topic_metrics(ranked('a', 'b', 'c', 'd', 'e'), [list('abcdef')])
    assert result['recall_at_5'] == 5 / 6
    assert result['any_reference_set_over_five_topics'] is True


@pytest.mark.parametrize('sets', [[[]], [['']], [[3]]])
def test_empty_or_invalid_topic_options_are_rejected(sets):
    with pytest.raises(ValueError):
        alternative_topic_metrics([], sets)


def test_related_passage_from_the_right_topic_is_not_the_reviewed_evidence():
    assert evidence_at_five(ranked('179'), [[{'passage_id': 'another-179-passage'}]]) is False


def test_one_complete_evidence_bundle_and_its_context_are_required():
    options = [[{'passage_id': 'a-0'}, {'passage_id': 'b-1'}], [{'passage_id': 'c-2'}]]
    assert evidence_at_five(ranked('a', 'b'), options) is True
    assert evidence_at_five(ranked('a', 'x'), options) is False
    assert evidence_at_five(ranked('a', 'b'), options, [{'passage_id': 'context'}]) is False


def test_an_empty_bundle_cannot_receive_vacuous_evidence_credit():
    with pytest.raises(ValueError):
        evidence_at_five([], [[]])


def citation_fixture():
    text = 'A\U0001f9ec same same'
    passage = {'topic_id': 't', 'start': 20, 'text': text}
    reference = {'passage_id': 'p', 'topic_id': 't', 'passage_start': 8, 'passage_end': 12,
                 'topic_start': 28, 'topic_end': 32,
                 'quote_sha256': hashlib.sha256(b'same').hexdigest()}
    return reference, {'p': passage}


def test_non_bmp_and_second_repeated_quote_use_code_point_coordinates():
    reference, passages = citation_fixture()
    verify_reference(reference, passages)


@pytest.mark.parametrize('change', [
    {'passage_start': 9, 'passage_end': 13},
    {'topic_start': 23, 'topic_end': 27},
    {'quote_sha256': '0' * 64},
    {'topic_id': 'wrong'},
    {'passage_start': True},
])
def test_invalid_or_cross_identity_citations_are_rejected(change):
    reference, passages = citation_fixture()
    with pytest.raises(ValueError):
        verify_reference({**reference, **change}, passages)
