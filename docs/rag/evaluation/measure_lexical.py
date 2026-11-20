"""Measure a local BM25 baseline on the exact A-owned development proposals."""

import hashlib
import json
from pathlib import Path
from statistics import mean
from unicodedata import unidata_version

from notelens_rag.embeddings import identity
from notelens_rag.hybrid import BM25_B, BM25_K1, LEXICAL_DEPTH, BM25Passages
from notelens_rag.hybrid_smoke import topic_metrics
from notelens_rag.ingestion import load_corpus


def evaluate_lexical(root):
    proposal_bytes = (root / 'docs/rag/qa-proposals.json').read_bytes()
    proposals = json.loads(proposal_bytes)
    corpus = load_corpus(repository_root=root)
    if proposals['partition'] != 'development_candidate' or proposals['corpus_version'] != corpus.corpus_version:
        raise ValueError('The development proposals must match the prepared corpus.')

    ranker = BM25Passages(corpus.passages)
    cases = []
    for case in proposals['cases']:
        ranked_ids = ranker.rank(case['question'])
        positions = {key: rank for rank, key in enumerate(ranked_ids, start=1)}
        top_five = [{'passage_id': key, 'topic_id': corpus.by_id[key].topic_id, 'title': corpus.by_id[key].title}
                    for key in ranked_ids[:5]]
        references = case['proposed_required_topic_ids']
        parts = []
        for part in case['parts']:
            evidence = list(dict.fromkeys(row['passage_id'] for row in part['evidence']))
            ranks = [positions.get(key) for key in evidence]
            parts.append({'requested_fact': part['requested_fact'], 'reference_status': part['status'],
                          'cited_passages': [{'passage_id': key, 'rank_within_pool': rank}
                                             for key, rank in zip(evidence, ranks, strict=True)],
                          'all_cited_passages_at_5': all(rank is not None and rank <= 5 for rank in ranks) if evidence else None})
        cases.append({'case_id': case['id'], 'source_shape': case['source_shape'],
                      'expected_coverage_in_prior_review': case['answerability'], 'proposed_topic_ids': references,
                      'topic_metrics': topic_metrics(top_five, references) if references else None,
                      'more_than_five_proposed_topics': len(set(references)) > 5,
                      'top_five': top_five, 'reference_parts': parts})

    groups = {}
    for group in ('single_topic', 'multi_topic', 'no_supported_topic'):
        rows = [row for row in cases if row['source_shape'] == group]
        metrics = [row['topic_metrics'] for row in rows if row['topic_metrics'] is not None]
        evidence_hits = [part['all_cited_passages_at_5'] for row in rows for part in row['reference_parts']
                         if part['all_cited_passages_at_5'] is not None]
        groups[group] = {'case_count': len(rows), 'rankings_with_topic_reference': len(metrics),
            'mean_topic_recall_at_5': mean(row['recall_at_5'] for row in metrics) if metrics else None,
            'topic_mrr_at_5': mean(row['reciprocal_rank_at_5'] for row in metrics) if metrics else None,
            'all_required_topics_at_5_cases': sum(row['all_required_topics_at_5'] for row in metrics) if metrics else None,
            'reference_parts_with_cited_passages': len(evidence_hits),
            'reference_parts_with_all_cited_passages_at_5': sum(evidence_hits)}

    configuration = {'algorithm': 'bm25-passage-words-v1', 'k1': BM25_K1, 'b': BM25_B,
                     'diagnostic_pool': LEXICAL_DEPTH, 'cutoff': 5, 'unicode_data_version': unidata_version,
                     'corpus_version': corpus.corpus_version}
    return {'format_version': 'rag-lexical-proposal-evaluation-v1', 'proposal_sha256': hashlib.sha256(proposal_bytes).hexdigest(),
            'configuration': configuration, 'retriever_version': identity(configuration), 'groups': groups,
            'scope': 'Exact candidate-development questions over the prepared canonical corpus. Topic and passage labels await independent review.',
            'new_provider_calls': 0, 'cases': cases}


if __name__ == '__main__':
    print(json.dumps(evaluate_lexical(Path(__file__).resolve().parents[3]), indent=2, allow_nan=False))
