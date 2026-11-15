"""Bounded retrieval experiments on registered public English development questions."""

import argparse
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import sys

from .embeddings import (DIMENSIONS, MODEL, PRICE_PER_MILLION, EmbeddingBatch,
    EmbeddingError, OpenAIEmbedder, count_tokens, identity, local_tokenizer, plan_corpus, read_settings)
from .indexing import (IndexBuildError, PersistentTokenBudget, atomic_json,
                       exclusive_build, load_index, read_json)
from .ingestion import CorpusLoadError, load_corpus, owned_file, repository_directory
from .retrieval import CandidateRetriever, RetrievalError, require


REGISTRY = 'docs/rag/retrieval-smoke-questions.json'
CACHE_DIRECTORY = 'services/rag/.cache/retrieval-smoke'


class PublicQuerySession:
    def __init__(self, *, retriever, registry, cache_dir, encoder=None, provider_factory=None):
        require(registry.get('public_development_only') is True and registry.get('language') == 'en',
                'validation_failure', 'Only the reviewed public English question registry is admitted.')
        self.registry = deepcopy(registry)
        cases = self.registry.get('cases')
        require(isinstance(cases, list) and 1 <= len(cases) <= 10,
                'validation_failure', 'The approved registry contains at most ten questions.')
        require(all(isinstance(case, dict) and isinstance(case.get('question_id'), str)
                    and case['question_id'] and isinstance(case.get('question'), str)
                    and case['question'].strip() for case in cases),
                'validation_failure', 'The public question registry is invalid.')
        self.cases = {case['question_id']: case for case in cases}
        require(len(self.cases) == len(cases), 'validation_failure', 'Public question identifiers must be unique.')
        self.retriever, self.folder = retriever, Path(cache_dir)
        self.encoder = encoder if encoder is not None else local_tokenizer()
        self.provider_factory = provider_factory or self._provider
        self.scope = {'version': 'public-query-run-v1', 'registry_sha256': identity(self.registry),
            'embedding_space_version': retriever.index.spec['embedding_space_version'],
            'mode': retriever.index.spec['mode'], 'model': MODEL, 'dimensions': DIMENSIONS}

    def _provider(self, budget):
        settings = read_settings()
        require(settings.enabled and settings.api_key, 'configuration_required',
                'Enable the approved query run and configure the local server-side key.')
        return OpenAIEmbedder(api_key=settings.api_key, enabled=True, timeout_seconds=30,
                              budget=budget, encoder=self.encoder)

    def _budget(self, *, execute, budget_usd):
        path = self.folder / 'usage.json'
        if path.exists():
            ledger = read_json(path)
            require(ledger.get('scope') == self.scope, 'query_scope_changed',
                    'The saved query allowance belongs to a different registry or embedding space.')
            saved = Decimal(ledger['max_usd'])
            require(saved.is_finite() and 0 < saved <= Decimal('0.01')
                    and Decimal(ledger['price_per_million']) == PRICE_PER_MILLION,
                    'query_budget_invalid', 'The saved query allowance is invalid.')
            if budget_usd is not None:
                require(saved == budget_usd, 'query_budget_invalid', 'The saved allowance cannot be reset or increased.')
            require(isinstance(ledger.get('attempts'), list) and len(ledger['attempts']) <= 10
                    and len({item['question_id'] for item in ledger['attempts']}) == len(ledger['attempts'])
                    and all(item['question_id'] in self.cases and item['status'] in ('attempted', 'failed', 'confirmed')
                            for item in ledger['attempts']) and isinstance(ledger.get('cache_sha256'), dict),
                    'query_budget_invalid', 'The saved query attempt ledger is invalid.')
        else:
            require(execute and budget_usd is not None, 'configuration_required',
                    'A new public query needs explicit execution and an approved budget.')
            ledger = {'scope': self.scope, 'max_usd': str(budget_usd),
                'price_per_million': str(PRICE_PER_MILLION), 'reserved_tokens': 0,
                'confirmed_tokens': 0, 'attempts': [], 'cache_sha256': {}}
            atomic_json(path, ledger)
        budget = PersistentTokenBudget(path, ledger)
        require(type(ledger.get('confirmed_tokens')) is int and 0 <= ledger['confirmed_tokens'] <= budget.reserved_tokens,
                'query_budget_invalid', 'The confirmed query usage is invalid.')
        return budget

    def run(self, question_id, *, execute=False, budget_usd=None):
        require(question_id in self.cases, 'validation_failure', 'Select a registered public development question.')
        require(type(execute) is bool, 'configuration_required', 'Query execution must be explicit.')
        if budget_usd is not None:
            require(isinstance(budget_usd, Decimal) and budget_usd.is_finite()
                    and 0 < budget_usd <= Decimal('0.01'), 'query_budget_invalid',
                    'This public query trial is approved only up to USD 0.01.')
        question = self.cases[question_id]['question']
        tokens = count_tokens(question, self.encoder)
        header = {**self.scope, 'question_id': question_id,
                  'question_sha256': hashlib.sha256(question.encode('utf-8')).hexdigest()}
        cache_key = identity(header)
        self.folder.mkdir(parents=True, exist_ok=True)
        with exclusive_build(self.folder):
            budget = self._budget(execute=execute, budget_usd=budget_usd)
            cache = self.folder / 'queries' / (cache_key + '.json')
            outcome = {'cache_hit': False, 'provider_calls_this_run': 0}
            session = self

            class CachedEmbedder:
                mode = session.scope['mode']

                def embed(self, texts):
                    require(texts == [question], 'validation_failure', 'Only the selected public question may be embedded.')
                    if cache.exists():
                        expected = budget.ledger['cache_sha256'].get(question_id)
                        require(expected is not None and hashlib.sha256(cache.read_bytes()).hexdigest() == expected,
                                'query_cache_invalid', 'The cached public query vector has changed.')
                        payload = read_json(cache)
                        require(payload.get('header') == header and payload.get('input_tokens') == tokens,
                                'query_cache_invalid', 'The cached query identity does not match.')
                        outcome['cache_hit'] = True
                        return session._batch(payload['vector'], tokens)
                    require(execute, 'configuration_required', 'This public query is not cached; explicit execution is required.')
                    attempts = budget.ledger['attempts']
                    require(question_id not in {item['question_id'] for item in attempts}, 'query_retry_not_approved',
                            'This question was already attempted; inspect its state before requesting a retry.')
                    require(len(attempts) < 10, 'query_limit_exceeded', 'The ten-query trial allowance is exhausted.')
                    provider = session.provider_factory(budget)
                    try:
                        require(provider.mode == self.mode, 'configuration_required', 'Provider and query-cache modes differ.')
                        budget.update(attempts=[*attempts, {'question_id': question_id, 'status': 'attempted'}])
                        result = provider.embed(texts)
                        require(result.model == MODEL and len(result.vectors) == 1 and result.input_tokens == tokens,
                                'invalid_upstream', 'The public query embedding identity or usage is invalid.')
                        batch = session._batch(result.vectors[0], tokens)
                        payload = {'header': header, 'input_tokens': tokens, 'vector': list(batch.vectors[0])}
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        atomic_json(cache, payload)
                        budget.update(confirmed_tokens=budget.ledger['confirmed_tokens'] + tokens,
                            attempts=[{**item, 'status': 'confirmed'} if item['question_id'] == question_id else item
                                      for item in budget.ledger['attempts']],
                            cache_sha256={**budget.ledger['cache_sha256'],
                                          question_id: hashlib.sha256(cache.read_bytes()).hexdigest()})
                        outcome['provider_calls_this_run'] = 1
                        return batch
                    except BaseException:
                        budget.update(attempts=[{**item, 'status': 'failed'} if item['question_id'] == question_id else item
                                               for item in budget.ledger['attempts']])
                        raise
                    finally:
                        provider.close()

            ranking = self.retriever.retrieve({'schema_version': '1.0.0', 'question': question}, CachedEmbedder())
            return {**ranking, 'question_id': question_id, 'question': question,
                'registry_sha256': self.scope['registry_sha256'], 'query_embedding': outcome,
                'query_run_budget': {'max_usd': budget.ledger['max_usd'],
                    'reserved_tokens': budget.reserved_tokens, 'confirmed_tokens': budget.ledger['confirmed_tokens'],
                    'attempts_total': len(budget.ledger['attempts']),
                    'reserved_usd': format(Decimal(budget.reserved_tokens) * PRICE_PER_MILLION / 1_000_000, 'f')}}

    @staticmethod
    def _batch(vector, tokens):
        require(isinstance(vector, (tuple, list)) and len(vector) == DIMENSIONS
                and all(type(value) in (int, float) and math.isfinite(value) for value in vector)
                and any(value != 0 for value in vector), 'query_cache_invalid', 'The public query vector is invalid.')
        return EmbeddingBatch((tuple(float(v) for v in vector),), tokens)


def main():
    parser = argparse.ArgumentParser(description='Rank up to five sources for registered public development questions.')
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--question-id')
    selection.add_argument('--all', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd', type=Decimal)
    parser.add_argument('--summary', action='store_true', help='Omit passage bodies from development output.')
    args = parser.parse_args()
    try:
        root = repository_directory(None)
        registry = read_json(owned_file(root, REGISTRY, 'docs/rag'))
        corpus = load_corpus(repository_root=root)
        index = load_index(corpus, repository_root=root, plan=plan_corpus(corpus))
        folder = owned_file(root, CACHE_DIRECTORY, 'services/rag/.cache')
        session = PublicQuerySession(retriever=CandidateRetriever(index), registry=registry, cache_dir=folder)
        selected = list(session.cases) if args.all else [args.question_id]
        results = []
        for identifier in selected:
            result = session.run(identifier, execute=args.execute, budget_usd=args.budget_usd)
            if args.summary:
                result['passages'] = [{key: value for key, value in p.items() if key != 'text'} for p in result['passages']]
            results.append(result)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
        atomic_json(folder / 'last-public-results.json', {'results': results})
        return 0
    except (RetrievalError, EmbeddingError, IndexBuildError, CorpusLoadError) as error:
        print(json.dumps({'status': 'error', 'code': error.code, 'message': str(error)}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'query_trial_failure',
                          'message': 'The public query trial stopped; no payload details are emitted.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
