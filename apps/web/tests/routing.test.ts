import assert from 'node:assert/strict';
import { test } from 'node:test';
import { randomUUID } from 'node:crypto';
import type { AnswerResult, PreparedDocument } from '@notelens/contracts/v1';
import documents from '../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import payloads from '../../../contracts/v1/fixtures/payloads.json' with { type: 'json' };
import { mockServiceClients } from '../src/lib/clients/mock-services.ts';
import { routeQuestion } from '../src/lib/routing/answer.ts';
import type { RoutedAnswer } from '../src/lib/routing/answer.ts';
import { demoQuestions, selectedDemoQuestion } from '../src/lib/routing/demo-questions.ts';
import type { DemoQuestion } from '../src/lib/routing/demo-questions.ts';
import { questionPlan } from '../src/lib/routing/question-input.ts';
import { boundedBody } from '../src/lib/http/bounded-body.ts';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';

const document = documents.offset as PreparedDocument;
const docAnswer = payloads['answer-document'] as AnswerResult;
const litAnswer = payloads['answer-literature'] as AnswerResult;
const env = {
  NOTELENS_MODE: 'mock', NOTELENS_DEMO_RUN: 'test-run', NOTELENS_DEMO_TOKEN: 'test-only-token',
  NOTELENS_DEMO_RAG_PORT: '8701', NOTELENS_DEMO_CLASSIFIER_PORT: '8702', NOTELENS_DEMO_EXTRACTION_PORT: '8703',
};

function harness(overrides: Record<string, unknown> = {}) {
  const requests: { url: URL; body: Record<string, unknown>; headers: Headers }[] = [];
  const replies: Record<string, unknown> = {
    '/v1/document-answer': docAnswer, '/v1/literature-answer': litAnswer,
    '/v1/classify': payloads['classification-supported'], '/v1/extract': payloads['extraction-valid'], ...overrides,
  };
  const transport: typeof fetch = async (input, init) => {
    const url = new URL(String(input));
    const headers = new Headers(init?.headers);
    requests.push({ url, body: JSON.parse(String(init?.body)), headers });
    assert.equal(init?.method, 'POST');
    assert.equal(init?.cache, 'no-store');
    assert.equal(init?.redirect, 'error');
    assert.ok(init?.signal);
    const requestId = headers.get('x-request-id');
    assert.ok(requestId?.match(/^[a-f0-9-]{36}$/));
    assert.equal(headers.get('authorization'), 'Bearer test-only-token');
    assert.ok(Object.hasOwn(replies, url.pathname), 'unexpected service call');
    const reply = replies[url.pathname];
    if (reply === 'unavailable') {
      return Response.json({
        schema_version: '1.0.0', request_id: requestId,
        error: { code: 'provider_unavailable', message: 'PRIVATE_MOCK_DIAGNOSTIC', retryable: true },
      }, { status: 503, headers: { 'X-Request-ID': requestId! } });
    }
    return Response.json(reply, { headers: { 'X-Request-ID': requestId! } });
  };
  const clients = mockServiceClients(env, transport)!;
  return {
    clients, requests,
    async ask(key: DemoQuestion) {
      return routeQuestion(clients, selectedDemoQuestion(key, true)!.plan, document);
    },
  };
}

test('client/mock-configuration-fails-closed', () => {
  assert.equal(mockServiceClients({ ...env, NOTELENS_MODE: 'live' }), null);
  assert.equal(mockServiceClients({ ...env, NOTELENS_DEMO_RAG_PORT: 'example.test:80' }), null);
  assert.equal(mockServiceClients({ ...env, NOTELENS_DEMO_TOKEN: '' }), null);
});

test('client/classification-and-extraction-correlate-with-document', async () => {
  const h = harness();
  assert.equal((await h.clients.classify(document)).kind, 'accepted');
  assert.equal((await h.clients.extract(document)).kind, 'accepted');
  assert.deepEqual(h.requests.map(({ url }) => url.href), [
    'http://127.0.0.1:8702/v1/classify', 'http://127.0.0.1:8703/v1/extract',
  ]);
  assert.deepEqual(h.requests[0].body.document, document);
  assert.notEqual(h.requests[0].headers.get('x-request-id'), h.requests[1].headers.get('x-request-id'));
});

test('routing/document-and-literature-call-only-their-owner', async () => {
  const h = harness();
  assert.equal((await h.ask('document')).route, 'document');
  assert.equal((await h.ask('literature')).route, 'literature');
  assert.deepEqual(h.requests.map(({ url }) => url.href), [
    'http://127.0.0.1:8703/v1/document-answer', 'http://127.0.0.1:8701/v1/literature-answer',
  ]);
  assert.deepEqual(h.requests[0].body.document, document);
  assert.equal('history' in h.requests[0].body, false);
  assert.deepEqual(Object.keys(h.requests[1].body).sort(), ['question', 'schema_version']);
});

test('routing/mixed-collisions-retain-claim-source-component-links', async () => {
  const sourceId = docAnswer.sources[0].source_id;
  const claimId = docAnswer.claims[0].claim_id;
  const componentId = docAnswer.components[0].component_id;
  const literature = {
    ...litAnswer, sources: litAnswer.sources.map(source => ({ ...source, source_id: sourceId, component_id: componentId })),
    claims: litAnswer.claims.map(claim => ({ ...claim, claim_id: claimId, source_ids: [sourceId], component_id: componentId })),
    components: litAnswer.components.map(component => ({ ...component, component_id: componentId })),
  };
  const h = harness({ '/v1/literature-answer': literature });
  const answer = await h.ask('mixed');
  assert.equal(answer.route, 'mixed');
  assert.equal(answer.state, 'sufficient');
  for (const { origin, result } of answer.branches) {
    assert.equal(result.kind, 'accepted');
    const { sources, claims, components } = result.record;
    assert.equal(sources[0].kind, origin);
    assert.deepEqual(claims[0].source_ids, [sources[0].source_id]);
    assert.equal(claims[0].claim_id, `${origin}:${claimId}`);
    assert.equal(sources[0].source_id, `${origin}:${sourceId}`);
    assert.equal(claims[0].component_id, components[0].component_id);
    assert.equal(sources[0].component_id, components[0].component_id);
  }
  assert.equal(docAnswer.sources[0].source_id, sourceId);
});

test('routing/partial-literature-preserves-gap-and-citation', async () => {
  const warning = 'The available literature does not cover the second topic.';
  const h = harness({ '/v1/literature-answer': { ...litAnswer, evidence_state: 'partial', warnings: [warning] } });
  for (const key of ['literature', 'mixed'] as const) {
    const answer = await h.ask(key);
    assert.equal(answer.route, key);
    assert.equal(answer.state, 'partial');
    const literature = answer.branches.find(item => item.origin === 'literature')?.result;
    assert.equal(literature?.kind, 'accepted');
    assert.deepEqual(literature.record.warnings, [warning]);
    assert.deepEqual(literature.record.claims[0].source_ids, [literature.record.sources[0].source_id]);
    assert.deepEqual(literature.record.retrieval_provenance, litAnswer.retrieval_provenance);
  }
});

test('routing/insufficient-literature-preserves-document-claims', async () => {
  const fixture = payloads['answer-literature-insufficient-no-generation'];
  const h = harness({ '/v1/literature-answer': {
    ...fixture, mode: 'mock', retrieval_provenance: { ...fixture.retrieval_provenance, mode: 'mock' },
  } });
  const mixed = await h.ask('mixed');
  assert.equal(mixed.route, 'document');
  assert.equal(mixed.state, 'partial');
  assert.equal(mixed.branches[1].result.kind, 'accepted');
  assert.equal(mixed.branches[1].result.record.evidence_state, 'insufficient');
  const literature = await h.ask('literature');
  assert.equal(literature.route, 'none');
  assert.equal(literature.state, 'insufficient');
});

test('routing/live-or-gapless-partial-literature-withholds-that-branch', async () => {
  for (const reply of [payloads['answer-literature-insufficient-no-generation'], {
    ...litAnswer, evidence_state: 'partial', warnings: [],
  }]) {
    const h = harness({ '/v1/literature-answer': reply });
    const answer = await h.ask('mixed');
    assert.equal(answer.route, 'document');
    assert.equal(answer.state, 'partial');
    assert.deepEqual(answer.branches[1].result, { kind: 'invalid' });
  }
});

test('routing/literature-outage-preserves-document-and-hides-diagnostics', async () => {
  const h = harness({ '/v1/literature-answer': 'unavailable' });
  const answer = await h.ask('mixed');
  assert.equal(answer.route, 'document');
  assert.equal(answer.state, 'partial');
  assert.deepEqual(answer.branches[1].result, { kind: 'unavailable' });
  assert.ok(!JSON.stringify(answer).includes('PRIVATE_MOCK_DIAGNOSTIC'));
  assert.equal((await h.ask('literature')).state, 'unavailable');
});

test('routing/stale-document-citations-are-rejected-independently', async () => {
  const h = harness({ '/v1/document-answer': payloads['answer-stale-source'] });
  const answer = await h.ask('mixed');
  assert.equal(answer.route, 'literature');
  assert.equal(answer.state, 'partial');
  assert.deepEqual(answer.branches[0].result, { kind: 'invalid' });
  assert.equal((await h.ask('document')).state, 'unavailable');
});

test('routing/out-of-scope-and-unknown-selections-make-no-calls', async () => {
  const h = harness();
  assert.deepEqual(await h.ask('out-of-scope'), { route: 'none', state: 'unsupported', branches: [] });
  assert.equal(selectedDemoQuestion(['mixed'], true), undefined);
  assert.equal(selectedDemoQuestion('constructor', true), undefined);
  assert.equal(selectedDemoQuestion('mixed', false), undefined);
  assert.deepEqual(demoQuestions(false).map(({ key }) => key), ['findings']);
  assert.equal(h.requests.length, 0);
});

test('input/both-fields-are-required-and-only-the-selected-questions-go-upstream', async () => {
  const payload = { document: document.doc_id, scope: 'both',
    documentQuestion: '  What does the document say about chest pain?  ',
    literatureQuestion: 'What is the synthetic demo topic?' };
  const result = questionPlan(payload, true);
  assert.ok('plan' in result);
  const h = harness();
  await routeQuestion(h.clients, result.plan, document);
  assert.deepEqual(h.requests.map(({ body }) => body), [
    { schema_version: '1.0.0', document, question: payload.documentQuestion.trim() },
    { schema_version: '1.0.0', question: payload.literatureQuestion },
  ]);
  for (const values of [
    { ...payload, literatureQuestion: '' }, { ...payload, literatureQuestion: undefined },
    { ...payload, history: ['unexpected'] }, { ...payload, scope: 'literature' },
  ]) {
    const rejected = questionPlan(values, true);
    assert.ok('status' in rejected && rejected.status === 422);
  }
});

test('input/combined-unicode-point-limit-and-english-validation', () => {
  const known = 'What is the synthetic demo topic?';
  const english = 'What does the original document say about the reason for this scheduled appointment?';
  const exact = english + ' '.repeat(1_000 - Array.from(english + known).length - 1) + '😀';
  const payload = { document: document.doc_id, scope: 'both', documentQuestion: exact, literatureQuestion: known };
  assert.ok('plan' in questionPlan(payload, true));
  const excess = questionPlan({ ...payload, documentQuestion: exact + '😀' }, true);
  assert.ok('status' in excess && excess.status === 413);
  for (const text of ['Age?', '   ', '\ud800', 'Pourquoi cette consultation a-t-elle été planifiée, et quel était le résultat du dernier examen ?']) {
    assert.ok('status' in questionPlan({ document: document.doc_id, scope: 'document', documentQuestion: text }, true));
  }
});

test('input/body-reader-enforces-cap-without-a-length-header', async () => {
  const request = new Request('http://localhost', {
    method: 'POST',
    body: new ReadableStream({ start(controller) {
      controller.enqueue(new Uint8Array(16 * 1024));
      controller.enqueue(new Uint8Array(1));
      controller.close();
    } }),
    duplex: 'half',
  } as RequestInit);
  assert.equal(await boundedBody(request, 16 * 1024), null);
});

async function historyHarness() {
  let now = 0;
  const store = new MemorySessions({ mode: 'mock', runtime: { now: () => now, schedule: () => () => {} } });
  const owner = store.createSession();
  const other = store.createSession();
  const second = { ...document, doc_id: randomUUID() };
  for (const doc of [document, second]) {
    const ticket = store.beginDocument(owner)!;
    assert.deepEqual(await store.storeDocument(owner, ticket, doc), { kind: 'stored' });
  }
  const plan = selectedDemoQuestion('mixed', true)!.plan;
  const answer = await harness().ask('mixed');
  const start = (docId = document.doc_id) => {
    const ongoing = store.beginQuestion(owner, docId);
    assert.equal(ongoing.kind, 'admitted');
    return ongoing.id;
  };
  const finish = (id: string, result: RoutedAnswer = answer) => store.finishQuestion(owner, id, plan, result);
  return { store, owner, other, second, start, finish, answer, advance: (time: number) => { now = time; } };
}

test('history/isolation-and-five-most-recent-completed-turns', async () => {
  const { store, owner, other, second, start, finish, answer } = await historyHarness();
  const ids = Array.from({ length: 6 }, () => {
    const id = start();
    assert.deepEqual(finish(id), { kind: 'saved', id });
    return id;
  });
  const history = store.questionHistory(owner, document.doc_id)!;
  assert.deepEqual(history.map(turn => turn.id), ids.slice(1));
  assert.deepEqual(history[0].answer, answer);
  assert.deepEqual(store.questionHistory(owner, second.doc_id), []);
  assert.equal(store.questionHistory(other, document.doc_id), null);
  assert.deepEqual(store.beginQuestion(other, document.doc_id), UNAVAILABLE);
});

test('history/utf8-budget-evicts-whole-turns-and-oversize-is-transient', async () => {
  const { store, owner, start, finish, answer } = await historyHarness();
  const padded = (count: number): RoutedAnswer => ({
    ...answer,
    branches: [{ origin: 'literature', result: {
      kind: 'accepted', record: { ...litAnswer, warnings: ['€'.repeat(count)] },
    } }],
  });
  const first = start();
  assert.equal(finish(first, padded(7_000)).kind, 'saved');
  const second = start();
  assert.equal(finish(second, padded(7_000)).kind, 'saved');
  const transient = finish(start(), padded(11_000));
  assert.equal(transient.kind, 'transient');
  assert.ok(transient.turn.answer.branches.length);
  assert.deepEqual(store.questionHistory(owner, document.doc_id)?.map(turn => turn.id), [second]);
});

test('history/rate-window-and-single-flight-are-per-session', async () => {
  const { store, owner, second, start, finish, advance } = await historyHarness();
  const first = start();
  assert.deepEqual(store.beginQuestion(owner, second.doc_id), { kind: 'busy' });
  finish(first);
  advance(30_000);
  for (let i = 0; i < 9; i++) finish(start());
  assert.deepEqual(store.beginQuestion(owner, second.doc_id), { kind: 'rate', retryAfter: 30 });
  advance(60_000);
  finish(start(second.doc_id));
  assert.deepEqual(store.beginQuestion(owner, second.doc_id), { kind: 'rate', retryAfter: 30 });
});

test('history/clear-delete-idle-expiry-and-session-close-discard-pending-results', async () => {
  for (const transition of ['clear', 'delete', 'expiry', 'close'] as const) {
    const { store, owner, start, finish, advance } = await historyHarness();
    finish(start());
    const pending = start();
    if (transition === 'clear') {
      assert.equal(store.clearQuestionHistory(owner, document.doc_id), true);
      assert.deepEqual(store.beginQuestion(owner, document.doc_id), { kind: 'busy' });
    } else if (transition === 'delete') {
      store.deleteDocument(owner, document.doc_id);
    } else if (transition === 'expiry') {
      advance(1_800_000);
    } else {
      store.endSession(owner);
    }
    assert.deepEqual(finish(pending), UNAVAILABLE);
    assert.deepEqual(store.questionHistory(owner, document.doc_id), transition === 'clear' ? [] : null);
  }
});
