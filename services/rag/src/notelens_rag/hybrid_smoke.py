"""Compare the fixed public development rankings with existing cached vectors."""

from collections import Counter
import hashlib
import json
from statistics import mean
import sys

from .embeddings import identity, plan_corpus
from .hybrid import HybridRetriever
from .indexing import load_index, read_json
from .ingestion import load_corpus, owned_file, repository_directory
from .query_smoke import CACHE_DIRECTORY, REGISTRY, PublicQuerySession
from .retrieval import CandidateRetriever, require


def topic_metrics(passages, targets):
    """Measure target topics by their first appearance within five passages."""
    targets = set(targets)
    if not targets:
        raise ValueError('Topic metrics require at least one reference topic.')
    unique_topics = list(dict.fromkeys(p['topic_id'] for p in passages[:5]))
    positions = [position for position, topic in enumerate(unique_topics, start=1) if topic in targets]
    return {'recall_at_5': len(positions) / len(targets),
            'reciprocal_rank_at_5': 1 / positions[0] if positions else 0.0,
            'all_required_topics_at_5': len(positions) == len(targets)}


def _observations(passages, context_topics, labels):
    passages = passages[:5]
    counts = Counter(labels.get(p['passage_id'], 'unreviewed') for p in passages)
    return {'top_five': [{key: p[key] for key in ('passage_id', 'topic_id')} for p in passages],
        'context_topic_metrics': topic_metrics(passages, context_topics),
        'known_full_evidence': counts['fully_supports_question'],
        'known_partial_evidence': counts['partially_supports_question'],
        'known_related_without_support': counts['related_not_answer_support'],
        'unreviewed_passages': counts['unreviewed']}


def _summary(rows):
    return {'macro_context_topic_recall_at_5': mean(x['context_topic_metrics']['recall_at_5'] for x in rows),
        'context_topic_mrr_at_5': mean(x['context_topic_metrics']['reciprocal_rank_at_5'] for x in rows),
        'all_context_topics_at_5_cases': sum(x['context_topic_metrics']['all_required_topics_at_5'] for x in rows),
        'cases_with_known_full_evidence_at_5': sum(bool(x['known_full_evidence']) for x in rows),
        'cases_with_any_known_evidence_at_5': sum(bool(x['known_full_evidence'] or x['known_partial_evidence']) for x in rows),
        'unreviewed_passages_at_5': sum(x['unreviewed_passages'] for x in rows)}


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_cached_retrievers(repository_root=None):
    root = repository_directory(repository_root)
    registry_path = owned_file(root, REGISTRY, 'docs/rag')
    reference_path = owned_file(root, 'docs/rag/retrieval-content-review.json', 'docs/rag')
    baseline_path = owned_file(root, 'docs/rag/retrieval-smoke-results.json', 'docs/rag')
    registry, reference, historic = (read_json(path) for path in (registry_path, reference_path, baseline_path))
    corpus = load_corpus(repository_root=root)
    index = load_index(corpus, repository_root=root, plan=plan_corpus(corpus))
    cache = owned_file(root, CACHE_DIRECTORY, 'services/rag/.cache')
    baseline, hybrid = CandidateRetriever(index), HybridRetriever(index)
    registry_digest = _digest(registry_path)
    historic_digest = _digest(baseline_path)
    require(reference['source_results_sha256'] == historic_digest
            and reference['question_registry_file_sha256'] == historic['question_registry_file_sha256'] == registry_digest
            and reference['registry_identity'] == historic['registry_identity'] == identity(registry)
            and reference['index_version'] == historic['index_version'] == index.spec['index_version']
            and reference['corpus_version'] == historic['corpus_version'] == corpus.corpus_version
            and reference['retriever_version'] == historic['retriever_version'] == baseline.retriever_version,
            'comparison_scope_changed', 'The public development comparison inputs have changed.')
    tracked = [cache / 'usage.json', *sorted((cache / 'queries').glob('*.json'))]
    before = [_digest(path) for path in tracked]

    def forbidden(_budget):
        raise AssertionError('This comparison can only reuse verified cached query vectors.')

    sessions = {name: PublicQuerySession(retriever=retriever, registry=registry, cache_dir=cache,
                                         provider_factory=forbidden)
                for name, retriever in (('baseline', baseline), ('hybrid', hybrid))}
    past_results = {case['question_id']: case for case in historic['results']}
    reviewed = {case['question_id']: case for case in reference['cases']}
    cases = []
    for case in registry['cases']:
        identifier, targets = case['question_id'], case['context_topic_ids']
        labels = {row['passage_id']: row['assessment'] for row in reviewed[identifier]['passage_reviews']}
        row = {'question_id': identifier, 'context_topic_ids': targets,
               'more_than_five_context_topics': len(set(targets)) > 5}
        for name, session in sessions.items():
            result = session.run(identifier, execute=False)
            require(result['query_embedding'] == {'cache_hit': True, 'provider_calls_this_run': 0},
                    'comparison_cache_invalid', 'A validated cached query vector is required.')
            passages = result['passages']
            if name == 'baseline':
                require([p['passage_id'] for p in passages] == [p['passage_id'] for p in past_results[identifier]['passages']],
                        'comparison_baseline_changed', 'The fixed historical baseline ranking changed.')
            row[name] = _observations(passages, targets, labels)
        cases.append(row)
    require(before == [_digest(path) for path in tracked], 'comparison_cache_invalid',
            'The query ledger or cached vectors changed during the comparison.')
    groups = {'single_context_topic': [row for row in cases if len(set(row['context_topic_ids'])) == 1],
              'multiple_context_topics': [row for row in cases if len(set(row['context_topic_ids'])) > 1]}
    return {'record_format_version': 'public-hybrid-retrieval-comparison-v1', 'question_registry_sha256': registry_digest,
        'baseline_results_sha256': historic_digest, 'prior_passage_review_sha256': _digest(reference_path),
        'corpus_version': corpus.corpus_version, 'index_version': index.spec['index_version'],
        'configurations': {name: {'retriever_version': session.retriever.retriever_version,
                                 **session.retriever.configuration} for name, session in sessions.items()},
        'metrics': {group: {'case_count': len(rows), **{
            name: _summary([row[name] for row in rows]) if rows else None for name in sessions}}
            for group, rows in groups.items()},
        'cache_replays': len(cases) * len(sessions), 'provider_calls': 0, 'new_provider_cost_usd': '0.00',
        'query_ledger_and_vectors_unchanged': True, 'cases': cases}


def main():
    try:
        print(json.dumps(compare_cached_retrievers(), indent=2, allow_nan=False))
    except Exception:
        print('The cached development comparison could not be completed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
