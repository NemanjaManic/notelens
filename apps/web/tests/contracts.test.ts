import { after, test } from 'node:test';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, realpathSync } from 'node:fs';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Context, PreparedDocument } from '@notelens/contracts/v1';
import { consumeRecord, consumeExchange, OPERATIONS } from '../src/lib/contracts/consumer.ts';
import type { ResultDefinition, ConsumerOutcome, BusinessOperation, BusinessExchange } from '../src/lib/contracts/consumer.ts';

// Resolve from the installed binding, including when a fault probe copies this test.
const ROOT = resolve(dirname(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))), '../../..');
const read = (path: string) => JSON.parse(readFileSync(resolve(ROOT, path), 'utf8'));
const documents: Record<string, PreparedDocument> = read('contracts/v1/fixtures/documents.json');
const payloads: Record<string, unknown> = read('contracts/v1/fixtures/payloads.json');
const references: Record<string, NonNullable<Context['reference']>> = read('contracts/v1/fixtures/references.json');
const manifest: { cases: { id: string; definition?: string; document?: string; reference?: string; expected: unknown[] }[] } = read('contracts/v1/fixtures/manifest.json');
const openapi = read('contracts/v1/openapi.json');
const digest = (value: unknown) => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const same = (actual: unknown, expected: unknown) => {
  if (digest(actual) !== digest(expected)) throw new Error('CHECK_FAILED');
};
const freeze = (value: unknown): void => {
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) freeze(item);
    Object.freeze(value);
  }
};
freeze(documents); freeze(payloads); freeze(references);
const context = (id = 'offset'): Context => ({ document: documents[id] });
const clone = (id: string): any => structuredClone(payloads[id]);
const marker = 'PRIVATE_BODY_OR_TOKEN_MARKER';
const reject = (result: ConsumerOutcome, code?: string) => {
  same(result.kind, 'rejected');
  if (result.kind !== 'rejected') throw new Error('CHECK_FAILED');
  if (code) same(result.code, code);
  same(Object.hasOwn(result, 'record'), false);
  same(JSON.stringify(result).includes(marker), false);
  same(result.notice, 'The response could not be verified. No result was accepted.');
  if (!result.notice || !result.rules.length) throw new Error('CHECK_FAILED');
};
const accept = (result: ConsumerOutcome, expected: unknown) => {
  same(result.kind, 'accepted');
  if (result.kind !== 'accepted') throw new Error('CHECK_FAILED');
  same(result.record, expected);
};
const input = (value: unknown) => ({ kind: 'native' as const, value });
const json = (value: unknown) => ({ kind: 'json' as const, value: JSON.stringify(value) });
const ID = '11111111-1111-4111-8111-111111111111';
const OTHER = '22222222-2222-4222-8222-222222222222';
const headers = (id = ID): [string, string][] => [['X-Request-ID', id]];
const exchange = (fixture = 'classification-supported'): BusinessExchange => ({
  status: 200, requestHeaders: headers(), responseHeaders: headers(),
  json: JSON.stringify(payloads[fixture]), disposition: 'accepted_result', document: documents.offset,
});
const errorExchange = (status = 422, retryable = false): BusinessExchange => ({
  ...exchange(), status, disposition: 'failed_call',
  json: JSON.stringify({ schema_version: '1.0.0', request_id: ID,
    error: { code: 'validation_failure', message: marker, retryable } }),
});

type Scenario = { id: string; run: () => Promise<void> };
const scenarios: Scenario[] = [];
const add = (id: string, run: Scenario['run']) => scenarios.push({ id, run });
const definitions = new Set(['ClassificationResult', 'ExtractionResult', 'RetrievalResult', 'AnswerResult']);

// The frozen manifest declares expected validity; every check enters our consumer.
for (const fixture of manifest.cases.filter(c => definitions.has(c.definition ?? ''))) {
  for (const representation of ['native', 'json'] as const) {
    add(`record/${fixture.id}/${representation}`, async () => {
      const value = payloads[fixture.id];
      const ctx: Context = {};
      if (fixture.document) ctx.document = documents[fixture.document];
      if (fixture.reference) ctx.reference = references[fixture.reference];
      const before = digest([value, ctx]);
      const result = await consumeRecord(fixture.definition as ResultDefinition,
        representation === 'native' ? input(value) : json(value), ctx);
      // A valid mixed/live fixture is deliberately outside this mock consumer.
      const mode = (value as { mode?: string }).mode;
      if (!fixture.expected.length && mode === 'mock') accept(result, value);
      else reject(result);
      same(digest([value, ctx]), before);
    });
  }
}

for (const definition of ['ClassificationResult', 'ExtractionResult'] as const) {
  const fixture = definition === 'ClassificationResult' ? 'classification-supported' : 'extraction-valid';
  add(`context/${definition}/missing`, async () => reject(await consumeRecord(definition, input(payloads[fixture])), 'document-context'));
  for (const field of ['doc_id', 'text_sha256'] as const) {
    add(`context/${definition}/${field}`, async () => {
      const document = structuredClone(documents.offset);
      if (field === 'doc_id') document.doc_id = OTHER;
      else document.text_sha256 = '0'.repeat(64);
      reject(await consumeRecord(definition, input(payloads[fixture]), { document }));
    });
  }
}
add('context/answer/missing', async () => reject(await consumeRecord('AnswerResult', input(payloads['answer-document']))));
add('context/corrupt-canonical-text', async () => {
  const document = structuredClone(documents.offset); document.text += marker;
  reject(await consumeRecord('ExtractionResult', input(payloads['extraction-valid']), { document }));
});
add('context/answer/stale-document', async () => {
  const document = structuredClone(documents.offset); document.doc_id = OTHER;
  reject(await consumeRecord('AnswerResult', input(payloads['answer-document']), { document }));
});
add('definition/wrong-result', async () => reject(await consumeRecord('RetrievalResult', input(payloads['classification-supported']))));
add('definition/unsupported-runtime-name', async () => reject(await consumeRecord('ErrorEnvelope' as ResultDefinition, input(payloads['error-envelope-valid']))));

for (const [id, mutate] of [
  ['non-bmp-offset', (v: any) => { v.items[0].evidence[0].start += 1; }],
  ['quote', (v: any) => { v.items[0].evidence[0].quote = marker; }],
  ['mention-outside', (v: any) => { v.items[0].mention.start = 0; }],
  ['repeated-reference', (v: any) => { v.items[0].evidence[0] = structuredClone(payloads['span-first-valid']); }],
] as const) {
  add(`evidence/${id}`, async () => {
    const value = clone('extraction-valid'); mutate(value);
    reject(await consumeRecord('ExtractionResult', input(value), {
      ...context(), reference: { spans: { '/items/0/evidence/0': clone('span-second-valid') } },
    }));
  });
}
add('evidence/second-occurrence-preserved', async () => {
  const value = payloads['extraction-valid'];
  accept(await consumeRecord('ExtractionResult', input(value), {
    ...context(), reference: { spans: { '/items/0/evidence/0': clone('span-second-valid') } },
  }), value);
});
for (const state of ['planned', 'ordered', 'performed', 'cancelled', 'hypothetical', 'unknown']) {
  add(`preserve/procedure-${state}`, async () => {
    const value = clone('extraction-empty');
    value.items = [clone(`procedure-${state}`)];
    // These items belong to their matching frozen canonical document.
    const document = state === 'planned' ? documents.procedure : documents[`procedure-${state}`];
    value.doc_id = document.doc_id; value.text_sha256 = document.text_sha256;
    accept(await consumeRecord('ExtractionResult', input(value), { document }), value);
  });
}
add('preserve/unknown-assertion', async () => {
  const value = clone('extraction-valid'); value.items = [clone('extraction-unknown-assertion')];
  accept(await consumeRecord('ExtractionResult', input(value), context()), value);
});
for (const fact of ['historical', 'family']) {
  add(`preserve/${fact}`, async () => {
    const value = clone('extraction-empty'); value.items = [clone(`extraction-${fact}`)];
    value.doc_id = documents.history.doc_id; value.text_sha256 = documents.history.text_sha256;
    const ref = references[`${fact}-facts`];
    const prefix = (entries: Record<string, unknown> = {}) => Object.fromEntries(Object.entries(entries).map(([key, item]) => [`/items/0${key}`, item]));
    const ctx = { document: documents.history, reference: { attributes: prefix(ref.attributes), spans: prefix(ref.spans) } };
    accept(await consumeRecord('ExtractionResult', input(value), ctx), value);
    value.items[0].subject = fact === 'family' ? 'patient' : 'family';
    reject(await consumeRecord('ExtractionResult', input(value), ctx));
  });
}
for (const id of ['answer-literature-insufficient-no-generation', 'answer-document-supported-literature-insufficient']) {
  add(`preserve/mock-${id}`, async () => {
    const value = clone(id);
    // Explicit synthetic mock variant; original frozen live/mixed fixture stays untouched.
    value.mode = 'mock'; value.retrieval_provenance.mode = 'mock';
    accept(await consumeRecord('AnswerResult', input(value), context()), value);
    const stale = structuredClone(value); stale.retrieval_provenance = null;
    if (id === 'answer-document-supported-literature-insufficient') {
      // Null is a valid unavailable-retrieval outcome. Preserve that distinction too.
      accept(await consumeRecord('AnswerResult', input(stale), context()), stale);
    }
  });
}

for (const [id, raw] of [
  ['malformed', '{'], ['duplicate', '{"mode":"mock","mode":"live"}'],
  ['overflow', JSON.stringify(payloads['retrieval-sufficient']).replace('"score":0.82', '"score":1e999')],
] as const) {
  add(`strict/json-${id}`, async () => {
    const value = id === 'overflow' ? JSON.stringify(payloads['retrieval-sufficient']).replace(/"score":\s*-?[\d.]+/, '"score":1e999') : raw;
    reject(await consumeRecord('RetrievalResult', { kind: 'json', value }));
  });
}
for (const value of [NaN, Infinity, -Infinity]) {
  add(`strict/native-${String(value)}`, async () => {
    const record = clone('retrieval-sufficient'); record.passages[0].score = value;
    reject(await consumeRecord('RetrievalResult', input(record)));
  });
}
for (const [id, mutate] of [
  ['version', (v: any) => { v.schema_version = '2.0.0'; }],
  ['extra', (v: any) => { v.secret = marker; }],
  ['missing', (v: any) => { delete v.state; }],
  ['enum', (v: any) => { v.state = marker; }],
  ['live', (v: any) => { v.mode = 'live'; }],
] as const) {
  add(`strict/${id}`, async () => {
    const value = clone('retrieval-sufficient'); mutate(value);
    reject(await consumeRecord('RetrievalResult', input(value)));
  });
}
add('diagnostic/throwing-native-getter', async () => {
  const value = { get schema_version(): string { throw new Error(marker); } };
  reject(await consumeRecord('RetrievalResult', input(value)));
});
add('diagnostic/accepted-native-identity', async () => {
  const value = clone('answer-mixed-partial'); freeze(value);
  const result = await consumeRecord('AnswerResult', input(value), context());
  accept(result, value);
  same(result.kind === 'accepted' && result.record === value, true);
});

const operations = Object.keys(OPERATIONS) as BusinessOperation[];
const fixtures: Record<BusinessOperation, string> = {
  classify: 'classification-supported', extract: 'analysis-extraction-failed-summary-kept',
  'document-answer': 'answer-document', retrieve: 'retrieval-insufficient',
  'literature-answer': 'answer-literature',
};
for (const operation of operations) {
  add(`exchange/${operation}/openapi-metadata`, async () => {
    const metadata = OPERATIONS[operation];
    const responses = openapi.paths[metadata.path].post.responses;
    same(metadata.statuses, Object.keys(responses).map(Number));
    same(responses['200'].content['application/json'].schema.$ref, `./schema.json#/$defs/${metadata.definition}`);
  });
  add(`exchange/${operation}/success`, async () => {
    const value = exchange(fixtures[operation]);
    const before = digest(value); freeze(value);
    accept(await consumeExchange(operation, value), payloads[fixtures[operation]]);
    same(digest(value), before);
  });
}
add('exchange/d005-replay-requires-live-mode-only-for-d005', async () => {
  for (const operation of ['extract', 'document-answer'] as const) {
    const result = await consumeExchange(operation, exchange(fixtures[operation]), true);
    reject(result, 'invalid-result');
    same(result.kind === 'rejected' && result.rules, ['D005_REPLAY_MODE_REQUIRED']);
  }
  for (const operation of ['classify', 'literature-answer'] as const) {
    accept(await consumeExchange(operation, exchange(fixtures[operation]), true), payloads[fixtures[operation]]);
  }
});
for (const status of OPERATIONS.classify.statuses.filter(s => s !== 200)) {
  add(`exchange/error-status-${status}`, async () => {
    const result = await consumeExchange('classify', errorExchange(status));
    same(result.kind, 'service-error');
    if (result.kind !== 'service-error') throw new Error('CHECK_FAILED');
    same(result.code, 'validation_failure'); same(result.retryable, false); same(result.requestId, ID);
    same(JSON.stringify(result).includes(marker), false);
  });
}
add('exchange/error-retryable-preserved', async () => {
  const result = await consumeExchange('extract', errorExchange(503, true));
  same(result.kind === 'service-error' && result.retryable, true);
});
add('exchange/error-invalid-document-allowed', async () => {
  const value = errorExchange(); value.document = { ...documents.offset, text_sha256: '0'.repeat(64) };
  same((await consumeExchange('extract', value)).kind, 'service-error');
});
for (const [id, mutate] of [
  ['response-missing', (v: BusinessExchange) => { v.responseHeaders = []; }],
  ['response-duplicate', (v: BusinessExchange) => { v.responseHeaders.push(['x-request-id', ID]); }],
  ['response-mismatch', (v: BusinessExchange) => { v.responseHeaders = headers(OTHER); }],
  ['request-missing-success', (v: BusinessExchange) => { v.requestHeaders = []; }],
  ['request-duplicate-success', (v: BusinessExchange) => { v.requestHeaders.push(['x-request-id', ID]); }],
  ['disposition', (v: BusinessExchange) => { v.disposition = 'failed_call'; }],
  ['undocumented-status', (v: BusinessExchange) => { v.status = 201; }],
  ['error-body-success', (v: BusinessExchange) => { v.json = errorExchange().json; }],
  ['success-body-error', (v: BusinessExchange) => { v.status = 422; v.disposition = 'failed_call'; }],
  ['wrong-definition', (v: BusinessExchange) => { v.json = JSON.stringify(payloads['retrieval-sufficient']); }],
  ['no-document', (v: BusinessExchange) => { delete v.document; }],
  ['duplicate-json', (v: BusinessExchange) => { v.json = v.json.replace('"mode":"mock"', '"mode":"mock","mode":"mock"'); }],
] as const) {
  add(`exchange/reject-${id}`, async () => {
    const value = exchange(); mutate(value); reject(await consumeExchange('classify', value));
  });
}
for (const kind of ['missing', 'malformed', 'duplicate'] as const) {
  add(`exchange/admission-${kind}`, async () => {
    const value = errorExchange(400);
    value.requestHeaders = kind === 'missing' ? [] : kind === 'malformed' ? headers(marker) : [...headers(), ...headers()];
    value.responseHeaders = headers(OTHER);
    value.json = value.json.replace(ID, OTHER);
    same((await consumeExchange('classify', value)).kind, 'service-error');
  });
}
add('exchange/error-envelope-correlation', async () => {
  const value = errorExchange(); value.json = value.json.replace(ID, OTHER);
  reject(await consumeExchange('retrieve', value));
});
add('exchange/error-admission-id-reused', async () => {
  const value = errorExchange(400); value.requestHeaders.push(['x-request-id', ID]);
  reject(await consumeExchange('retrieve', value));
});
add('exchange/error-duplicate-json', async () => {
  const value = errorExchange(); value.json = value.json.replace('"retryable":false', '"retryable":false,"retryable":false');
  reject(await consumeExchange('retrieve', value));
});
add('exchange/error-invalid-admission-status', async () => {
  const value = errorExchange(401); value.requestHeaders = [];
  reject(await consumeExchange('retrieve', value));
});
add('exchange/error-invalid-admission-code', async () => {
  const value = errorExchange(400); value.requestHeaders = []; value.json = value.json.replace('validation_failure', 'internal_error');
  reject(await consumeExchange('retrieve', value));
});
add('exchange/document-none-still-needs-selected-context', async () => {
  const value = exchange('answer-none'); delete value.document;
  reject(await consumeExchange('document-answer', value));
});
add('exchange/unknown-operation', async () => reject(await consumeExchange('health' as BusinessOperation, exchange())));

const ids = scenarios.map(s => s.id);
if (new Set(ids).size !== ids.length) throw new Error('DUPLICATE_CASE');
if (process.argv.includes('--list-cases')) {
  process.stdout.write(JSON.stringify(ids));
} else {
  const results: { id: string; passed: boolean; boundary: 'web-consumer' }[] = [];
  for (const scenario of scenarios) {
    test(scenario.id, async () => {
      let passed = false;
      try { await scenario.run(); passed = true; }
      catch { throw new Error(`CONSUMER_CASE_FAILED: ${scenario.id}`); }
      finally { results.push({ id: scenario.id, passed, boundary: 'web-consumer' }); }
    });
  }
  after(() => {
    const target = process.env.NOTELENS_B010_REPORT;
    if (!target) return; // Direct node:test diagnostics do not claim coordinator evidence.
    const base = realpathSync(resolve(ROOT, '.cache/review/b010-contracts'));
    const parent = realpathSync(dirname(target));
    if (!parent.startsWith(base + sep) || !/^run-[a-f0-9-]+$/.test(parent.slice(base.length + 1)) || resolve(parent, 'cases.json') !== resolve(target)) {
      throw new Error('UNSAFE_REPORT_PATH');
    }
    writeFileSync(target, JSON.stringify({ nonce: process.env.NOTELENS_B010_NONCE, results }), { flag: 'wx' });
  });
}
