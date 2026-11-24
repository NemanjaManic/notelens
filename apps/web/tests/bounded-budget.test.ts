import assert from 'node:assert/strict';
import { test } from 'node:test';
import { boundedEvaluation } from '../src/lib/clients/bounded-evaluation.ts';

function budget() {
  delete (globalThis as typeof globalThis & { notelensBoundedEvaluation?: unknown }).notelensBoundedEvaluation;
  const result = boundedEvaluation({
    NOTELENS_BOUNDED_EVALUATION: 'provider-backed', NOTELENS_DEMO_RUN: 'offline-regression',
    NOTELENS_BOUNDED_RAG_TOKEN: 'offline-rag', NOTELENS_BOUNDED_EXTRACTION_TOKEN: 'offline-d',
    NOTELENS_BOUNDED_HTTP_TIMEOUT_MS: '1000', NOTELENS_SESSION_ORIGIN: 'http://localhost:3000',
    NOTELENS_BOUNDED_LIMITS: JSON.stringify({ extract: 2, 'document-answer': 2, 'literature-answer': 1 }),
  });
  assert.ok(result);
  return result.budget;
}

test('an unsupported literature gap does not block the next document extraction', async () => {
  const ledger = budget();
  assert.equal((await ledger.dispatch('literature-answer', undefined, async () => ({ kind: 'unsupported' }))).kind, 'unsupported');
  let dispatched = false;
  const next = await ledger.dispatch('extract', 'new-source', async () => { dispatched = true; return { kind: 'accepted' }; });
  assert.equal(dispatched, true);
  assert.equal(next.kind, 'accepted');
});

for (const kind of ['unavailable', 'invalid']) {
  test(`${kind} still stops subsequent provider dispatch`, async () => {
    const ledger = budget();
    await ledger.dispatch('literature-answer', undefined, async () => ({ kind }));
    let dispatched = false;
    const next = await ledger.dispatch('extract', 'source', async () => { dispatched = true; return { kind: 'accepted' }; });
    assert.equal(dispatched, false);
    assert.equal(next.kind, 'unavailable');
  });
}

test('unsupported literature consumes its allowance and cannot bypass the request cap', async () => {
  const ledger = budget();
  await ledger.dispatch('literature-answer', undefined, async () => ({ kind: 'unsupported' }));
  let dispatched = false;
  const next = await ledger.dispatch('literature-answer', undefined, async () => { dispatched = true; return { kind: 'accepted' }; });
  assert.equal(dispatched, false);
  assert.equal(next.kind, 'unavailable');
});

test('unsupported on a document operation remains an unexpected error', async () => {
  const ledger = budget();
  await ledger.dispatch('document-answer', undefined, async () => ({ kind: 'unsupported' }));
  let dispatched = false;
  await ledger.dispatch('extract', 'source', async () => { dispatched = true; return { kind: 'accepted' }; });
  assert.equal(dispatched, false);
});
