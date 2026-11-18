"""Cross-check development proposals against saved RAG rankings and support decisions."""

import hashlib
import json
from pathlib import Path
from statistics import mean

from notelens_rag.hybrid_smoke import topic_metrics


def evaluate_saved(root):
    hashes = {}

    def load(name):
        path = f'docs/rag/{name}.json'
        raw = (root / path).read_bytes()
        hashes[path] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)

    proposals = load('qa-proposals')
    history = load('retrieval-smoke-results')
    review = load('retrieval-content-review')
    first = load('selection-trial-results')
    rest = load('coverage-trial-results')
    if not (proposals['partition'] == 'development_candidate'
            and proposals['corpus_version'] == history['corpus_version'] == review['corpus_version']
            and review['index_version'] == history['index_version']
            and review['source_results_sha256'] == hashes['docs/rag/retrieval-smoke-results.json']
            and first['mode'] == rest['mode'] == 'live'
            and first['configuration_version'] == rest['cases'][0]['configuration_version']
            and first['prompt_sha256'] == rest['prompt_sha256']):
        raise ValueError('The saved development evaluation inputs do not match.')

    rankings = {(row['question_id'], row['question']): row['passages'] for row in history['results']}
    assessments = {(row['question_id'], row['question']): row for row in [first, *rest['cases']]}
    cases = []
    for case in proposals['cases']:
        row = {'case_id': case['id'], 'source_shape': case['source_shape'],
            'expected_coverage': case['answerability'], 'over_five_topics': case['requires_more_than_five_topics'],
            'retrieval': None, 'support_assessment': None}
        if case['origin'] == 'existing_public_development_probe':
            reference, = case['original_references']
            if reference['sha256'] != hashes['docs/rag/retrieval-content-review.json']:
                raise ValueError('The proposal references a different passage review.')
            key = reference['case_id'], case['question']
            passages = rankings[key][:5]
            found = {passage['passage_id'] for passage in passages}
            targets = case['proposed_required_topic_ids']
            part_support = [part for part in case['parts'] if part['status'] == 'supported']
            present = sum({source['passage_id'] for source in part['evidence']} <= found for part in part_support)
            row['retrieval'] = {'source_case_id': key[0], 'returned_passages': len(passages),
                'topic_metrics': topic_metrics(passages, targets) if targets else None,
                'supported_parts_in_reference': len(part_support), 'supported_parts_with_all_cited_passages': present}
            if key in assessments:
                verdict = assessments[key]
                if verdict['observed_cli_exit_code'] != 0 or verdict['configuration_version'] != first['configuration_version']:
                    raise ValueError('A saved support decision has a different execution basis.')
                row['support_assessment'] = verdict['coverage']
        cases.append(row)

    grouped = {}
    for group in ('single_topic', 'multi_topic', 'no_supported_topic'):
        rows = [row for row in cases if row['source_shape'] == group]
        retrieved = [row['retrieval'] for row in rows if row['retrieval'] is not None]
        topic_rows = [item['topic_metrics'] for item in retrieved if item['topic_metrics'] is not None]
        grouped[group] = {'proposed_cases': len(rows), 'saved_rankings': len(retrieved),
            'rankings_with_topic_reference': len(topic_rows),
            'mean_topic_recall_at_5': mean(item['recall_at_5'] for item in topic_rows) if topic_rows else None,
            'topic_mrr_at_5': mean(item['reciprocal_rank_at_5'] for item in topic_rows) if topic_rows else None,
            'all_required_topics_at_5_cases': sum(item['all_required_topics_at_5'] for item in topic_rows) if topic_rows else None,
            'known_supported_parts': sum(item['supported_parts_in_reference'] for item in retrieved),
            'known_supported_parts_with_all_citations_at_5': sum(item['supported_parts_with_all_cited_passages'] for item in retrieved)}

    assessed = [row for row in cases if row['support_assessment'] is not None]
    accepted = [row for row in assessed if row['support_assessment'] in ('full', 'partial')]
    order = {'none': 0, 'partial': 1, 'full': 2}
    overclaims = sum(order[row['support_assessment']] > order[row['expected_coverage']] for row in accepted)
    return {'format_version': 'rag-saved-development-evaluation-v1', 'input_sha256': hashes,
        'corpus_version': proposals['corpus_version'], 'index_version': history['index_version'],
        'retriever_version': history['retriever_version'], 'assessment_prompt_version': first['prompt_version'],
        'assessment_configuration_version': first['configuration_version'], 'groups': grouped,
        'support_decisions': {'assessed': len(assessed), 'would_allow_some_evidence': len(accepted),
            'overstated_coverage_among_accepted': overclaims,
            'potential_coverage': len(accepted) / len(assessed) if assessed else None,
            'observed_overstatement_rate': overclaims / len(accepted) if accepted else None,
            'basis': 'Prior support judgments relative to author-reviewed development labels. No final answer was generated.'},
        'new_provider_calls': 0, 'cases': cases}


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[3]
    print(json.dumps(evaluate_saved(root), indent=2, allow_nan=False))
