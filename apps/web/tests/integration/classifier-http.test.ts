import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import type { ServerResponse } from 'node:http';
import { test } from 'node:test';
import type { TestContext } from 'node:test';
import { validateJson } from '@notelens/contracts/v1';
import type { ClassificationResult, HealthResult, PreparedDocument } from '@notelens/contracts/v1';
import documents from '../../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import payloads from '../../../../contracts/v1/fixtures/payloads.json' with { type: 'json' };
import { classifierTestClient } from '../../src/lib/clients/classifier-test-client.ts';
import { canonicalText } from '../../src/lib/documents/canonical.ts';

type Example = { document: PreparedDocument; status: 'supported' | 'uncertain'; category: ClassificationResult['category'] };
type Target = Parameters<typeof classifierTestClient>[0];
type Fault = 'none' | 'not-ready' | 'request-id' | 'document-id' | 'digest' | 'error-id';

const categories = ['Cardiovascular / Pulmonary', 'Orthopedic', 'Gastroenterology', 'Neurology', 'Urology'];
const fixtureExamples: Example[] = [
  { document: documents.offset as PreparedDocument, status: 'supported', category: 'Cardiovascular / Pulmonary' },
  { document: documents.history as PreparedDocument, status: 'uncertain', category: null },
];

function reply(response: ServerResponse, status: number, payload: unknown, headers: Record<string, string> = {}) {
  response.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers });
  response.end(JSON.stringify(payload));
}

async function startFixture(t: TestContext) {
  const token = randomUUID();
  const requestIds = new Set<string>();
  let fault: Fault = 'none';
  const server = createServer(async (request, response) => {
    try {
      const ready = request.method === 'GET' && request.url === '/health/ready';
      if (!ready && (request.method !== 'POST' || request.url !== '/v1/classify')) {
        response.writeHead(404).end();
        return;
      }
      const requestId = ready ? randomUUID() : request.headers['x-request-id'];
      if (typeof requestId !== 'string' ||
          (await validateJson('RequestId', JSON.stringify(requestId))) !== requestId || requestIds.has(requestId)) {
        response.writeHead(400).end();
        return;
      }
      if (!ready) requestIds.add(requestId);
      if (request.headers.authorization !== `Bearer ${token}`) {
        reply(response, 401, {
          schema_version: '1.0.0', request_id: fault === 'error-id' ? randomUUID() : requestId,
          error: { code: 'unauthorized', message: 'Private fixture diagnostic.', retryable: false },
        }, { 'X-Request-ID': requestId, 'WWW-Authenticate': 'Bearer' });
        return;
      }
      if (ready) {
        const record: HealthResult = {
          schema_version: '1.0.0', service: 'classifier', mode: 'mock', version: 'loopback-fixture-v1',
          status: fault === 'not-ready' ? 'not_ready' : 'ok', model_version: null,
          reason: fault === 'not-ready' ? 'The fixture is not ready.' : null,
        };
        reply(response, fault === 'not-ready' ? 503 : 200, record);
        return;
      }
      const chunks: Buffer[] = [];
      for await (const chunk of request) chunks.push(chunk as Buffer);
      const { document } = await validateJson('ClassificationRequest', Buffer.concat(chunks).toString('utf8'));
      const example = fixtureExamples.find(item => item.document.doc_id === document.doc_id);
      if (!example || example.document.text !== document.text || example.document.text_sha256 !== document.text_sha256) {
        response.writeHead(422).end();
        return;
      }
      const record = {
        ...payloads[`classification-${example.status}`],
        doc_id: fault === 'document-id' ? 'unrelated-synthetic-document' : document.doc_id,
        text_sha256: fault === 'digest' ? '0'.repeat(64) : document.text_sha256,
      };
      reply(response, 200, record, { 'X-Request-ID': fault === 'request-id' ? randomUUID() : requestId });
    } catch {
      response.writeHead(500).end();
    }
  });
  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  t.after(() => new Promise<void>((resolve, reject) => {
    server.close(error => error ? reject(error) : resolve());
    server.closeAllConnections();
  }));
  const address = server.address();
  assert.ok(address && typeof address === 'object');
  const target: Target = { profile: 'fixture', port: address.port, token };
  return { target, setFault(value: Fault) { fault = value; } };
}

async function smoke(t: TestContext, target: Target, examples: Example[]) {
  const client = classifierTestClient(target);
  await t.test('accepts authenticated readiness for the selected mode and model', async () => {
    const result = await client.readiness();
    assert.ok(result.kind === 'accepted', 'Classifier readiness failed.');
    assert.equal(result.record.mode, target.profile === 'fitted' ? 'live' : 'mock');
    assert.equal(result.record.model_version, target.profile === 'fitted' ? target.modelVersion : null);
  });

  for (const { document, status, category } of examples) {
    await t.test(`binds a repeatable ${status} classification to the request and canonical document`, async () => {
      const first = await client.classify(document);
      const second = await client.classify(document);
      assert.ok(first.kind === 'accepted' && second.kind === 'accepted', 'Classifier response failed validation.');
      assert.equal(first.record.doc_id, document.doc_id);
      assert.equal(first.record.text_sha256, createHash('sha256').update(document.text, 'utf8').digest('hex'));
      assert.equal(first.record.status, status);
      assert.equal(first.record.category, category);
      assert.equal(first.record.classification_execution, 'performed');
      assert.deepEqual(first.record.scores.map(score => score.category), categories);
      assert.ok(JSON.stringify(first.record) === JSON.stringify(second.record), 'Classification changed on repetition.');
    });
  }

  await t.test('rejects a wrong bearer token for readiness and classification without exposing its response', async () => {
    const denied = classifierTestClient({ ...target, token: randomUUID() });
    for (const outcome of [await denied.readiness(), await denied.classify(examples[0].document)]) {
      assert.ok(outcome.kind === 'unauthorized' && Object.keys(outcome).length === 1, 'Expected a redacted authorization failure.');
    }
  });
}

function fittedExamples(path: string): Example[] {
  try {
    const samples = JSON.parse(readFileSync(path, 'utf8'));
    return (['supported', 'uncertain'] as const).map(status => {
      const sample = samples[status];
      const canonical = canonicalText(sample.text);
      const category = status === 'supported' ? sample.category : null;
      if (canonical.kind !== 'canonical' || !['public_text', 'synthetic_text'].includes(sample.source_kind) ||
          (status === 'supported' && !categories.includes(category))) throw new Error();
      return {
        status, category,
        document: {
          schema_version: '1.0.0', doc_id: randomUUID(), text: canonical.text,
          text_sha256: createHash('sha256').update(canonical.text, 'utf8').digest('hex'),
          canonicalization_version: 'nfc-lf-v1', source: { kind: sample.source_kind },
          language: 'en', language_validation: {
            outcome: 'accepted', language: 'en', policy_version: 'classifier-smoke-approved-english-v1', reason: null,
          },
        },
      };
    });
  } catch {
    throw new Error('Provide the approved English classifier examples in the documented JSON format.');
  }
}

const profile = process.env.NOTELENS_CLASSIFIER_TEST_PROFILE ?? 'fixture';
if (profile === 'fitted') {
  test('fitted classifier loopback HTTP', async t => {
    const port = process.env.NOTELENS_CLASSIFIER_TEST_PORT;
    const modelVersion = process.env.NOTELENS_CLASSIFIER_TEST_MODEL_VERSION;
    const token = process.env.NOTELENS_CLASSIFIER_SERVICE_TOKEN;
    const samples = process.env.NOTELENS_CLASSIFIER_TEST_EXAMPLES;
    assert.ok(port && /^[1-9][0-9]{0,4}$/.test(port) && token && modelVersion && samples,
      'Set the fitted classifier test port, service token, reviewed model version and approved examples file.');
    const examples = fittedExamples(samples);
    const target = { profile, port: Number(port), token, modelVersion } as const;
    await smoke(t, target, examples);
    await t.test('rejects readiness and classification for an unexpected fitted model version', async () => {
      const wrongVersion = classifierTestClient({ ...target, modelVersion: `${modelVersion}-unexpected` });
      assert.ok((await wrongVersion.readiness()).kind === 'invalid');
      assert.ok((await wrongVersion.classify(examples[0].document)).kind === 'invalid');
    });
  });
} else {
  test('classifier loopback HTTP fixture', async t => {
    assert.equal(profile, 'fixture', 'Select either the fixture or fitted classifier test profile.');
    const { target, setFault } = await startFixture(t);
    await smoke(t, target, fixtureExamples);
    const client = classifierTestClient(target);
    const { document } = fixtureExamples[0];

    await t.test('distinguishes an authenticated not-ready health response', async () => {
      setFault('not-ready');
      assert.ok((await client.readiness()).kind === 'not-ready');
      setFault('none');
    });

    for (const fault of ['request-id', 'document-id', 'digest', 'error-id'] as const) {
      await t.test(`rejects a mismatched ${fault} over HTTP`, async () => {
        setFault(fault);
        const caller = fault === 'error-id' ? classifierTestClient({ ...target, token: randomUUID() }) : client;
        const outcome = await caller.classify(document);
        assert.ok(outcome.kind === 'invalid' && Object.keys(outcome).length === 1, 'Expected a redacted response rejection.');
        setFault('none');
      });
    }

    await t.test('the fitted profile rejects mock readiness and classification', async () => {
      const fitted = classifierTestClient({ ...target, profile: 'fitted', modelVersion: 'expected-fitted-model' });
      assert.ok((await fitted.readiness()).kind === 'invalid');
      assert.ok((await fitted.classify(document)).kind === 'invalid');
    });
  });
}
