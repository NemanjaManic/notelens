"""Measure score-only risk on the saved public QA proposals without choosing a threshold."""

import json
import math
from pathlib import Path
from unittest.mock import patch

from run_local_flow import _protected_hashes, cached_retrieval


def summarize(rows, cutoff):
    allowed = [item for item in rows if cutoff is None or item['top_score'] >= cutoff]
    with_support = sum(item['review_coverage'] != 'none' for item in allowed)
    without_support = len(allowed) - with_support
    return {'cutoff': cutoff, 'questions_allowed': len(allowed), 'allowed_with_some_reviewed_support': with_support,
        'allowed_without_reviewed_support': without_support,
        'rejected_with_some_reviewed_support': sum(item['review_coverage'] != 'none' for item in rows) - with_support,
        'cited_parts_retained': sum(cutoff is None or part['minimum_cited_passage_score'] >= cutoff
                                  for item in rows for part in item['reviewed_parts']),
        'allowed_case_fraction': len(allowed) / len(rows),
        'unsupported_fraction_among_allowed': without_support / len(allowed) if allowed else None}


def run(root):
    provider_attempts = []

    def forbidden(*args, **kwargs):
        provider_attempts.append(True)
        raise AssertionError('The diagnostic can only replay cached query vectors.')

    cases, corpus, index, retriever, folders, rank = cached_retrieval(root, forbidden)
    before = _protected_hashes(folders)
    rows, boundaries = [], set()
    with patch('notelens_rag.query_smoke.read_settings', forbidden), patch('socket.create_connection', forbidden):
        for identifier, case in cases.items():
            result = rank(identifier)
            scores = {p['passage_id']: p['score'] for p in result['passages']}
            boundaries.update(scores.values())
            references = []
            for part in case['parts']:
                if not part['evidence']:
                    continue
                cited_ids = {item['passage_id'] for item in part['evidence']}
                references.append({'requested_fact': part['requested_fact'],
                                   'minimum_cited_passage_score': min(scores[key] for key in cited_ids)})
            rows.append({'case_id': identifier, 'review_coverage': case['answerability'], 'top_score': max(scores.values()),
                         'reviewed_parts': references})

    if provider_attempts or before != _protected_hashes(folders) or any((p/'.build.lock').exists() for p in folders):
        raise ValueError('Offline score evaluation changed protected state.')
    # With an inclusive cutoff, a decision changes only between observed scores.
    cutoffs = sorted(boundaries | {math.nextafter(max(boundaries), math.inf)})
    sweep = [summarize(rows, cutoff) for cutoff in cutoffs]
    no_cutoff = summarize(rows, None)
    reviewed_parts = no_cutoff['cited_parts_retained']
    all_citations = max((item for item in sweep if item['cited_parts_retained'] == reviewed_parts),
                        key=lambda item: item['cutoff'])
    avoid_unsupported = min((item for item in sweep if item['allowed_without_reviewed_support'] == 0),
                            key=lambda item: item['cutoff'])
    return {'format_version': 'rag-vector-score-gate-development-v1', 'corpus_version': corpus.corpus_version,
        'index_version': index.spec['index_version'], 'retriever_version': retriever.retriever_version,
        'question_count': len(rows), 'provider_calls': 0, 'cache_state_unchanged': True,
        'reference_basis': 'Owner-local public QA proposals, including one case with missing support in the reviewed passages.',
        'rule_tested': 'Keep each passage at or above the cutoff, and allow a question only if at least one passage remains.',
        'selected_runtime_cutoff': None, 'cases': rows,
        'operating_points': {'no_cutoff': no_cutoff, 'strictest_preserving_all_cited_parts': all_citations,
                             'loosest_rejecting_all_questions_without_reviewed_support': avoid_unsupported},
        'sweep': sweep}


if __name__ == '__main__':
    print(json.dumps(run(Path(__file__).resolve().parents[3]), indent=2, allow_nan=False))
