"""Keep the proposed query allowance inactive and preserve failure reservations."""

from decimal import Decimal
import json

import pytest

from notelens_rag.embeddings import EmbeddingError
from notelens_rag.qa_vector_trial import MAX_USD, ProposalQuerySession, _scope_digest
from notelens_rag.retrieval import RetrievalError

from test_query_smoke import Encoder, Ranking, trial


def scope_with_approval():
    scope = {'format_version': 'qa-test-only', 'execution_approved': True, 'approval': None}
    scope['approval'] = {'actor': 'Nemanja (A)', 'date': '2026-11-18', 'scope_sha256': _scope_digest(scope)}
    return scope


def extension(trial, scope, provider=None):
    _, _, registry, path, factory = trial
    return ProposalQuerySession(trial_scope=scope, retriever=Ranking(), registry=registry, cache_dir=path/'extra',
                                encoder=Encoder(), provider_factory=provider or factory)


@pytest.mark.parametrize('change,limit', [
    ('pending', MAX_USD), ('scope_drift', MAX_USD), ('actor_drift', MAX_USD), ('larger_limit', Decimal('0.01')),
])
def test_pending_or_mismatched_scope_does_not_touch_new_or_prior_state(trial, change, limit):
    original, calls, _, path, _ = trial
    original.run('0', execute=True, budget_usd=Decimal('0.01'))
    prior = (path/'usage.json').read_bytes()
    scope = scope_with_approval()
    if change == 'pending':
        scope.update(execution_approved=False, approval=None)
    if change == 'scope_drift':
        scope['format_version'] = 'changed'
    if change == 'actor_drift':
        scope['approval']['actor'] = 'Fixture reviewer'
    runner = extension(trial, scope)
    with pytest.raises(RetrievalError) as error:
        runner.run('0', execute=True, budget_usd=limit)
    assert error.value.code == 'qa_vector_approval_required'
    assert len(calls) == 1 and (path/'usage.json').read_bytes() == prior
    assert not (path/'extra').exists()


def test_approved_extra_cache_replays_without_reusing_prior_allowance(trial):
    original, calls, _, path, _ = trial
    original.run('0', execute=True, budget_usd=Decimal('0.01'))
    prior = (path/'usage.json').read_bytes()
    runner = extension(trial, scope_with_approval())
    first = runner.run('0', execute=True, budget_usd=MAX_USD)
    saved = (runner.folder/'usage.json').read_bytes()
    again = runner.run('0')
    assert first['query_embedding']['provider_calls_this_run'] == 1
    assert again['query_embedding'] == {'cache_hit': True, 'provider_calls_this_run': 0}
    assert again['query_run_budget']['max_usd'] == str(MAX_USD)
    assert len(calls) == 2 and (path/'usage.json').read_bytes() == prior
    assert (runner.folder/'usage.json').read_bytes() == saved


def test_provider_failure_blocks_later_attempts_and_retains_the_reservation(trial):
    attempts = []

    def provider(budget):
        class Fails:
            mode = 'mock'

            def embed(self, texts):
                budget.reserve(len(texts[0].encode()))
                attempts.append(texts[0])
                raise EmbeddingError('timeout', 'Synthetic timeout.')

            def close(self):
                pass

        return Fails()

    runner = extension(trial, scope_with_approval(), provider)
    with pytest.raises(EmbeddingError):
        runner.run('0', execute=True, budget_usd=MAX_USD)
    path = runner.folder/'usage.json'
    saved = path.read_bytes()
    ledger = json.loads(saved)
    assert ledger['attempts'] == [{'question_id': '0', 'status': 'failed'}]
    assert ledger['reserved_tokens'] == len(attempts[0].encode()) and ledger['confirmed_tokens'] == 0
    with pytest.raises(RetrievalError) as error:
        runner.run('1', execute=True, budget_usd=MAX_USD)
    assert error.value.code == 'qa_vector_trial_stopped'
    assert len(attempts) == 1 and path.read_bytes() == saved
