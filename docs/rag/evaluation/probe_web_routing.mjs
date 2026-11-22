/** Exercise B's unchanged client/router against the local synthetic RAG server. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [rootArg, port, phase] = process.argv.slice(2);
let activeCase = 'setup';

async function main() {
  assert.ok(Number(process.versions.node.split('.')[0]) >= 24);
  assert.ok(rootArg && /^[1-9][0-9]{0,4}$/.test(port) && Number(port) <= 65535);
  assert.ok(phase === 'healthy' || phase === 'stopped');
  const token = process.env.NOTELENS_WEB_RAG_PROBE_TOKEN;
  assert.ok(token);
  const root = resolve(rootArg);
  const file = path => pathToFileURL(resolve(root, path)).href;
  const { mockServiceClients } = await import(file('apps/web/src/lib/clients/mock-services.ts'));
  const { routeQuestion } = await import(file('apps/web/src/lib/routing/answer.ts'));
  const { validateRecord } = await import(file('contracts/generated/typescript/v1.mjs'));
  const documents = JSON.parse(await readFile(resolve(root, 'contracts/v1/fixtures/documents.json'), 'utf8'));
  const payloads = JSON.parse(await readFile(resolve(root, 'contracts/v1/fixtures/payloads.json'), 'utf8'));
  const document = documents.offset;
  const documentAnswer = payloads['answer-document'];
  await validateRecord('PreparedDocument', document);
  await validateRecord('AnswerResult', documentAnswer, { document });
  const question = 'What is the synthetic demo topic?';
  const partial = 'What is the synthetic demo topic, and when did it begin?';
  const missing = 'When did the synthetic demo topic begin?';
  const unknown = 'An unregistered synthetic question?';
  const requests = [];
  const responses = [];
  let documentFixtureCalls = 0;
  const results = [];

  const transport = async (input, init) => {
    const url = new URL(String(input));
    assert.equal(url.origin, `http://127.0.0.1:${port}`);
    assert.equal(url.pathname, '/v1/literature-answer');
    assert.equal(init.method, 'POST');
    const body = JSON.parse(init.body);
    assert.deepEqual(Object.keys(body).sort(), ['question', 'schema_version']);
    assert.equal(body.schema_version, '1.0.0');
    const requestId = new Headers(init.headers).get('x-request-id');
    assert.match(requestId, /^[a-f0-9-]{36}$/);
    requests.push(activeCase);
    const response = await fetch(input, init);
    assert.equal(response.headers.get('x-request-id'), requestId);
    responses.push(response.status);
    return response;
  };

  function clients(authToken = token) {
    // The unused service ports satisfy B's existing configuration gate. Only
    // literatureAnswer uses HTTP; documentAnswer is the frozen synthetic fixture.
    const connected = mockServiceClients({
      NOTELENS_MODE: 'mock', NOTELENS_DEMO_RUN: 'A-owned-web-rag-probe', NOTELENS_DEMO_TOKEN: authToken,
      NOTELENS_DEMO_RAG_PORT: port, NOTELENS_DEMO_CLASSIFIER_PORT: port, NOTELENS_DEMO_EXTRACTION_PORT: port,
    }, transport);
    assert.ok(connected);
    return { literatureAnswer: connected.literatureAnswer,
      documentAnswer: async () => {
        documentFixtureCalls++;
        return { kind: 'accepted', record: structuredClone(documentAnswer) };
      } };
  }

  async function check(id, text, mixed, expectedRoute, expectedState, expectedKind, authToken = token) {
    activeCase = id;
    const before = requests.length;
    const plan = mixed ? { label: id, document: 'What does the document say about chest pain?', literature: text }
      : { label: id, literature: text };
    const answer = await routeQuestion(clients(authToken), plan, document);
    assert.equal(requests.length - before, 1, 'Each case must make one literature HTTP attempt without retries.');
    assert.equal(answer.route, expectedRoute);
    assert.equal(answer.state, expectedState);
    const literature = answer.branches.find(branch => branch.origin === 'literature');
    assert.equal(literature.result.kind, expectedKind);
    const doc = answer.branches.find(branch => branch.origin === 'document');
    if (mixed) {
      assert.equal(doc.result.kind, 'accepted');
      assert.deepEqual(doc.result.record.claims.map(claim => claim.text), documentAnswer.claims.map(claim => claim.text));
      assert.deepEqual(doc.result.record.sources.map(source => source.text), documentAnswer.sources.map(source => source.text));
    } else assert.equal(doc, undefined);
    for (const branch of answer.branches) {
      if (branch.result.kind !== 'accepted') continue;
      const record = branch.result.record;
      assert.equal(record.mode, 'mock');
      assert.ok(record.sources.every(source => source.kind === branch.origin));
      const sources = new Set(record.sources.map(source => source.source_id));
      const components = new Set(record.components.map(component => component.component_id));
      for (const claim of record.claims) {
        assert.ok(components.has(claim.component_id));
        assert.ok(claim.source_ids.every(source => sources.has(source)));
      }
    }
    if (expectedKind === 'accepted' && text === missing) {
      assert.equal(literature.result.record.evidence_state, 'insufficient');
      assert.equal(literature.result.record.retrieval_provenance.state, 'insufficient');
      assert.equal(literature.result.record.claims.length, 0);
    }
    if (expectedKind === 'accepted' && text === partial) {
      assert.ok(literature.result.record.warnings.some(warning => warning.includes('Start date')));
    }
    results.push({ case_id: id, route: answer.route, state: answer.state,
      document_claims_preserved: mixed ? doc.result.record.claims.length === documentAnswer.claims.length : null,
      literature_result_kind: literature.result.kind,
      literature_evidence_state: literature.result.kind === 'accepted' ? literature.result.record.evidence_state : null });
  }

  if (phase === 'healthy') {
    await check('literature-full', question, false, 'literature', 'sufficient', 'accepted');
    await check('literature-partial', partial, false, 'literature', 'partial', 'accepted');
    await check('literature-insufficient', missing, false, 'none', 'insufficient', 'accepted');
    await check('mixed-full', question, true, 'mixed', 'sufficient', 'accepted');
    await check('mixed-partial', partial, true, 'mixed', 'partial', 'accepted');
    await check('mixed-insufficient-literature', missing, true, 'document', 'partial', 'accepted');
    await check('literature-unregistered', unknown, false, 'none', 'unsupported', 'unsupported');
    await check('mixed-unregistered', unknown, true, 'document', 'partial', 'unsupported');
    await check('literature-auth-denied', question, false, 'none', 'unavailable', 'unavailable', 'different-synthetic-token');
    await check('mixed-auth-denied', question, true, 'document', 'partial', 'unavailable', 'different-synthetic-token');
    assert.deepEqual(responses, [200, 200, 200, 200, 200, 200, 422, 422, 401, 401]);
  } else {
    await check('literature-service-stopped', question, false, 'none', 'unavailable', 'unavailable');
    await check('mixed-service-stopped', question, true, 'document', 'partial', 'unavailable');
    assert.equal(responses.length, 0);
  }
  return { phase, cases: results, literature_attempts: requests.length, http_statuses: responses,
    document_fixture_calls: documentFixtureCalls, real_document_service_calls: 0,
    document_text_sent_to_RAG: false, provider_calls: 0 };
}

try {
  console.log(JSON.stringify(await main()));
} catch {
  console.error(`The key-free web/RAG probe failed at case ${activeCase}.`);
  process.exitCode = 1;
}
