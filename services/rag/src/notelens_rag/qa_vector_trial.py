"""Evaluate exact public QA proposals using cached vectors and a separate trial scope."""

import argparse
from decimal import Decimal
import hashlib
import json
from statistics import mean
import sys

from .embeddings import DIMENSIONS, MODEL, PRICE_PER_MILLION, count_tokens, identity, local_tokenizer, plan_corpus
from .hybrid import HybridRetriever
from .hybrid_smoke import topic_metrics
from .indexing import load_index, read_json
from .ingestion import load_corpus, owned_file, repository_directory
from .query_smoke import CACHE_DIRECTORY, REGISTRY, PublicQuerySession
from .retrieval import CandidateRetriever, RetrievalError, require


SCOPE_PATH = 'docs/rag/evaluation/vector-proposal-scope.json'
PROPOSAL_PATH = 'docs/rag/qa-proposals.json'
NEW_CACHE = 'services/rag/.cache/qa-vector-trial'
NEW_IDS = ('A-QA-05', 'A-QA-06', 'A-QA-07', 'A-QA-08', 'A-QA-09')
MAX_USD = Decimal('0.00001')


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _scope_digest(scope):
    return identity({key: value for key, value in scope.items() if key not in ('approval', 'execution_approved')})


def _approved(scope):
    approval = scope.get('approval')
    return (scope.get('execution_approved') is True and isinstance(approval, dict)
            and approval.get('actor') == 'Nemanja (A)' and approval.get('scope_sha256') == _scope_digest(scope)
            and isinstance(approval.get('date'), str) and bool(approval['date']))


class ProposalQuerySession(PublicQuerySession):
    """Keep the additional vector cache and allowance distinct from the completed trial."""

    def __init__(self, *, trial_scope, **kwargs):
        super().__init__(**kwargs)
        self.trial_scope = dict(trial_scope)
        self.scope['approval_scope_sha256'] = _scope_digest(self.trial_scope)

    def run(self, question_id, *, execute=False, budget_usd=None):
        if execute:
            require(_approved(self.trial_scope) and budget_usd == MAX_USD, 'qa_vector_approval_required',
                    'The exact additional public embedding scope is pending approval.')
        return super().run(question_id, execute=execute, budget_usd=budget_usd)

    def _budget(self, *, execute, budget_usd):
        budget = super()._budget(execute=execute, budget_usd=budget_usd)
        require(budget.max_usd == MAX_USD, 'query_budget_invalid', 'The additional query allowance changed.')
        if execute:
            require(all(row['status'] == 'confirmed' for row in budget.ledger['attempts']),
                    'qa_vector_trial_stopped', 'An incomplete or failed prior attempt stops the trial.')
        return budget


def _forbidden(_budget):
    raise AssertionError('The comparison path may only reuse validated cached vectors.')


def _metrics(result, proposal):
    passages = result['passages'][:5]
    targets = proposal['proposed_required_topic_ids']
    returned_ids = {row['passage_id'] for row in passages}
    supported = [part for part in proposal['parts'] if part['evidence']]
    return {'top_five': [{key: p[key] for key in ('passage_id', 'topic_id')} for p in passages],
            'topic_metrics': topic_metrics(passages, targets) if targets else None,
            'reference_parts': len(supported),
            'reference_parts_with_all_citations_at_5': sum(
                {evidence['passage_id'] for evidence in part['evidence']} <= returned_ids for part in supported)}


def _compare(scope, index, encoder, cases, existing, reused, new_registry, old_cache, new_cache):
    # The prior complete ledger is pinned in the scope, and neither replay path executes.
    completed = set()
    if (new_cache / 'usage.json').is_file():
        completed = {a['question_id'] for a in read_json(new_cache / 'usage.json')['attempts']
                     if a['status'] == 'confirmed'}
    results = {case['id']: {'case_id': case['id'], 'source_shape': case['source_shape'],
                           'more_than_five_proposed_topics': len(set(case['proposed_required_topic_ids'])) > 5}
               for case in cases}
    configurations = {}
    for name, ranker in (('vector', CandidateRetriever(index)), ('hybrid', HybridRetriever(index))):
        configurations[name] = ranker.retriever_version
        original = PublicQuerySession(retriever=ranker, registry=existing, cache_dir=old_cache,
                                      encoder=encoder, provider_factory=_forbidden)
        extra = ProposalQuerySession(trial_scope=scope, retriever=ranker, registry=new_registry,
                                     cache_dir=new_cache, encoder=encoder, provider_factory=_forbidden)
        for case in cases:
            identifier = case['id']
            if identifier in reused:
                result = original.run(reused[identifier])
            elif identifier in completed:
                result = extra.run(identifier)
            else:
                results[identifier][name] = None
                continue
            require(result['query_embedding'] == {'cache_hit': True, 'provider_calls_this_run': 0},
                    'query_cache_invalid', 'A confirmed cached query is required.')
            results[identifier][name] = _metrics(result, case)

    groups = {}
    for group in ('single_topic', 'multi_topic', 'no_supported_topic'):
        group_cases = [row for row in results.values() if row['source_shape'] == group]
        for name in configurations:
            evaluated = [row[name] for row in group_cases if row[name] is not None]
            topics = [row['topic_metrics'] for row in evaluated if row['topic_metrics'] is not None]
            groups.setdefault(group, {})[name] = {'cases': len(group_cases), 'ranked': len(evaluated),
                'mean_topic_recall_at_5': mean(row['recall_at_5'] for row in topics) if topics else None,
                'topic_mrr_at_5': mean(row['reciprocal_rank_at_5'] for row in topics) if topics else None,
                'all_required_topics_at_5_cases': sum(row['all_required_topics_at_5'] for row in topics) if topics else None,
                'reference_parts': sum(row['reference_parts'] for row in evaluated),
                'reference_parts_with_all_citations_at_5': sum(row['reference_parts_with_all_citations_at_5'] for row in evaluated)}
    return {'record_format_version': 'public-qa-vector-comparison-v1', 'scope_sha256': _scope_digest(scope),
            'retriever_versions': configurations, 'groups': groups, 'results': list(results.values()),
            'new_provider_calls': 0}


def run(action='inspect', repository_root=None):
    require(action in ('inspect', 'compare', 'execute'), 'validation_failure', 'Select a trial action explicitly.')
    root = repository_directory(repository_root)
    scope = read_json(owned_file(root, SCOPE_PATH, 'docs/rag'))
    if action == 'execute':
        require(_approved(scope), 'qa_vector_approval_required', 'The exact additional public embedding scope is pending approval.')
    proposal_path = owned_file(root, PROPOSAL_PATH, 'docs/rag')
    registry_path = owned_file(root, REGISTRY, 'docs/rag')
    old_cache = owned_file(root, CACHE_DIRECTORY, 'services/rag/.cache')
    new_cache = owned_file(root, NEW_CACHE, 'services/rag/.cache')
    prior_ledger = old_cache / 'usage.json'
    require(scope.get('format_version') == 'rag-qa-vector-trial-v1'
            and scope.get('question_ids') == list(NEW_IDS) and scope.get('max_usd') == str(MAX_USD)
            and scope.get('model') == MODEL and scope.get('dimensions') == DIMENSIONS
            and scope.get('timeout_seconds') == 30 and scope.get('max_attempts_per_question') == 1
            and scope.get('automatic_retries') == 0
            and scope.get('reference_usd_per_million_tokens') == str(PRICE_PER_MILLION)
            and _digest(proposal_path) == scope.get('proposal_sha256')
            and _digest(registry_path) == scope.get('prior_registry_sha256')
            and _digest(prior_ledger) == scope.get('prior_query_ledger_sha256'),
            'qa_vector_scope_changed', 'The approved QA inputs or earlier query history changed.')
    proposals, existing, prior = (read_json(path) for path in (proposal_path, registry_path, prior_ledger))
    cases = proposals['cases']
    old_questions = {row['question']: row['question_id'] for row in existing['cases']}
    reused = {case['id']: old_questions[case['question']] for case in cases if case['question'] in old_questions}
    new_cases = [case for case in cases if case['id'] not in reused]
    require(len(cases) == 9 and tuple(case['id'] for case in new_cases) == NEW_IDS
            and proposals['partition'] == 'development_candidate' and proposals['language'] == 'en',
            'qa_vector_scope_changed', 'The exact question set is invalid.')
    new_registry = {'registry_version': 'qa-proposals-five-new-questions-v1', 'language': 'en', 'public_development_only': True,
                    'cases': [{'question_id': case['id'], 'question': case['question']} for case in new_cases]}
    encoder = local_tokenizer()
    token_counts = {case['id']: count_tokens(case['question'], encoder) for case in new_cases}
    total = sum(token_counts.values())
    require(total == scope.get('input_tokens') and total == 83, 'qa_vector_scope_changed', 'The expected input token count changed.')
    corpus = load_corpus(repository_root=root)
    index = load_index(corpus, repository_root=root, plan=plan_corpus(corpus, encoder=encoder))
    require(index.spec['mode'] == 'live' and corpus.corpus_version == proposals['corpus_version']
            and index.spec['index_version'] == scope.get('index_version')
            and index.spec['embedding_space_version'] == scope.get('embedding_space_version'),
            'qa_vector_scope_changed', 'The prepared QA data and verified embedding space differ.')
    if action == 'inspect':
        return {'scope_sha256': _scope_digest(scope), 'execution_approved': _approved(scope),
                'cached_exact_question_ids': reused, 'new_questions': token_counts, 'input_tokens': total,
                'estimated_new_cost_usd': format(total * PRICE_PER_MILLION / 1_000_000, 'f'), 'new_limit_usd': str(MAX_USD),
                'prior_reserved_tokens': prior['reserved_tokens'], 'new_provider_calls': 0}
    if action == 'compare':
        return _compare(scope, index, encoder, cases, existing, reused, new_registry, old_cache, new_cache)
    session = ProposalQuerySession(trial_scope=scope, retriever=CandidateRetriever(index), registry=new_registry,
                                   cache_dir=new_cache, encoder=encoder)
    outcomes = []
    for identifier in NEW_IDS:
        response = session.run(identifier, execute=True, budget_usd=MAX_USD)
        outcomes.append({'case_id': identifier, **response['query_embedding']})
    return {'scope_sha256': _scope_digest(scope), 'cases': outcomes, 'limits': response['query_run_budget']}


def main():
    parser = argparse.ArgumentParser(description='Inspect and compare the QA proposal vectors or run the approved five-query batch.')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--compare', action='store_true')
    actions.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    try:
        value = run('execute' if args.execute else 'compare' if args.compare else 'inspect')
        print(json.dumps(value, indent=2, allow_nan=False))
        return 0
    except RetrievalError as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error)}), file=sys.stderr)
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'qa_vector_trial_failed',
                          'message': 'The trial stopped safely.'}), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
