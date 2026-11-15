// Finite module HTTP checks only: no report routing, user input or shared dev stack.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { readFile, writeFile, realpath } from 'node:fs/promises';
import http from 'node:http';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import { isDeepStrictEqual } from 'node:util';
import { validateJson, validateExchange } from '@notelens/contracts/v1';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const cache = path.join(root, '.cache/scaffold');
const inputs = JSON.parse(await readFile(path.join(root, 'scripts/project/scaffold_inputs.json'), 'utf8'));
const documents = JSON.parse(await readFile(path.join(root, 'contracts/v1/fixtures/documents.json'), 'utf8'));
const payloads = JSON.parse(await readFile(path.join(root, 'contracts/v1/fixtures/payloads.json'), 'utf8'));
const demo = JSON.parse(await readFile(path.join(root, 'services/extraction/fixtures/demo-request.json'), 'utf8'));
assert.equal(await realpath(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))), await realpath(path.join(root, 'contracts/generated/typescript/v1.mjs')));
const report = { passed: false, cases: [], processes: [] };

async function reservePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

function reachable(port) {
  return new Promise(resolve => {
    const socket = net.createConnection({ host: '127.0.0.1', port });
    const finish = value => { socket.destroy(); resolve(value); };
    socket.once('connect', () => finish(true)); socket.once('error', () => finish(false));
    socket.setTimeout(300, () => finish(false));
  });
}

async function server(service, scenario, run) {
  const port = await reservePort();
  const python = path.join(root, `services/${service}/.venv/Scripts/python.exe`);
  const env = { ...process.env };
  for (const name of Object.keys(env)) if (/^(OPENAI|AZURE_OPENAI|ANTHROPIC|AWS_|NOTELENS_)/i.test(name) || name.toUpperCase().endsWith('_API_KEY')) delete env[name];
  Object.assign(env, { PYTHONPATH: path.join(root, 'scripts/project/scaffold_guard'), PYTHONDONTWRITEBYTECODE: '1',
    NOTELENS_REVIEW_NETWORK_LOG: path.join(cache, 'network-blocks.jsonl'),
    NOTELENS_MODE: 'mock', NOTELENS_RAG_MODE: 'mock', NOTELENS_CLASSIFIER_MODE: 'mock',
    NOTELENS_RAG_MOCK_SCENARIO: scenario, NOTELENS_CLASSIFIER_MOCK_SCENARIO: scenario,
    ANONYMIZED_TELEMETRY: 'False', OTEL_SDK_DISABLED: 'true' });
  const args = service === 'rag' ? ['-B', '-m', 'uvicorn', 'notelens_rag.main:app', '--host', '127.0.0.1', '--port', String(port), '--no-proxy-headers', '--no-access-log', '--log-level', 'warning']
    : service === 'classifier' ? ['-B', '-m', 'notelens_classifier', '--port', String(port)]
    : ['-B', '-m', 'notelens_extraction.cli', 'serve', '--port', String(port)];
  const child = spawn(python, args, { cwd: root, env, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  let exited = false, spawnFailed = false, logs = '';
  const closed = new Promise(resolve => child.once('close', () => { exited = true; resolve(); }));
  child.once('error', () => { spawnFailed = true; });
  child.stdout.on('data', data => { logs += data; }); child.stderr.on('data', data => { logs += data; });
  const record = { service, scenario, pid: child.pid, stopped: false, port_closed: false };
  report.processes.push(record);
  try {
    const deadline = Date.now() + 20_000;
    while (!await reachable(port)) {
      assert.ok(!exited && !spawnFailed && Date.now() < deadline, 'Owned module did not start');
      await delay(50);
    }
    await run(port);
  } finally {
    if (!exited) child.kill();
    await Promise.race([closed, delay(5000)]);
    if (!exited) { child.kill('SIGKILL'); await Promise.race([closed, delay(5000)]); }
    record.stopped = exited; record.port_closed = !await reachable(port);
    assert.ok(record.stopped && record.port_closed, 'Owned module cleanup failed');
    assert.ok(!logs.includes('Traceback'), 'Unexpected module traceback');
  }
}

function wire(port, route, body, headers) {
  const raw = JSON.stringify(body);
  return new Promise((resolve, reject) => {
    const request = http.request({ host: '127.0.0.1', port, path: route, method: 'POST',
      headers: ['Host', `127.0.0.1:${port}`, 'Connection', 'close', 'Content-Type', 'application/json', 'Content-Length', String(Buffer.byteLength(raw)), ...headers.flat()] }, response => {
      let text = ''; response.setEncoding('utf8'); response.on('data', chunk => { text += chunk; });
      response.on('error', reject); response.on('end', () => {
        const rawHeaders = [];
        for (let i = 0; i < response.rawHeaders.length; i += 2) rawHeaders.push([response.rawHeaders[i], response.rawHeaders[i + 1]]);
        resolve({ status: response.statusCode, headers: rawHeaders, text });
      });
    });
    request.on('error', () => reject(new Error('Module HTTP failed')));
    request.setTimeout(10_000, () => request.destroy(new Error('Review deadline exceeded')));
    request.end(raw);
  });
}

async function check(port, id, route, request, definition, status = 200, verify = () => {}, headers = [['X-Request-ID', randomUUID()]]) {
  report.in_progress = id;
  const response = await wire(port, route, request, headers);
  assert.equal(response.status, status, id + ': unexpected status');
  const body = await validateJson(status === 200 ? definition : 'ErrorEnvelope', response.text, status === 200 && request.document ? { document: request.document } : undefined);
  assert.deepEqual(await validateExchange({ path: route, request_headers: headers, response_headers: response.headers, status, body,
    disposition: status === 200 ? 'accepted_result' : 'failed_call' }), [], id + ': correlation');
  if (status === 200) assert.equal(body.mode, 'mock');
  verify(body);
  report.cases.push({ id, route, status, passed: true });
  console.log('PASS: ' + id);
}

const question = { schema_version: '1.0.0', question: 'What is the synthetic demo topic?' };
try {
  for (const scenario of ['sufficient', 'insufficient', 'clarification']) {
    await server('rag', scenario, async port => {
      if (scenario !== 'clarification') await check(port, `rag-retrieve-${scenario}`, '/v1/retrieve', question, 'RetrievalResult', 200, body => {
        assert.equal(body.state, scenario); assert.equal(Boolean(body.passages.length), scenario === 'sufficient');
      });
      await check(port, scenario === 'clarification' ? 'rag-clarification' : `rag-answer-${scenario}`, '/v1/literature-answer', question, 'AnswerResult', 200, body => {
        if (scenario === 'sufficient') {
          assert.equal(body.route, 'literature'); assert.ok(body.claims.length && body.components.length);
          for (const component of body.components) for (const key of ['corpus_version', 'index_version', 'retriever_version']) assert.equal(component[key], body.retrieval_provenance[key]);
        } else {
          assert.deepEqual([body.claims, body.sources, body.components], [[], [], []]); assert.equal(body.prompt_version, null);
          if (scenario === 'clarification') { assert.ok(body.clarification); assert.equal(body.retrieval_provenance, null); }
          else assert.equal(body.retrieval_provenance.state, 'insufficient');
        }
      });
      if (scenario === 'sufficient') await check(port, 'rag-invalid-id', '/v1/retrieve', question, 'ErrorEnvelope', 400, () => {}, []);
    });
  }
  for (const [scenario, status] of [['timeout', 504], ['rate_limit', 429], ['provider_unavailable', 503], ['internal_error', 500]]) {
    await server('rag', scenario, async port => {
      for (const [op, route] of [['retrieve', '/v1/retrieve'], ['answer', '/v1/literature-answer']])
        await check(port, `rag-${op}-${scenario}`, route, question, 'ErrorEnvelope', status, body => assert.equal(body.error.code, scenario));
    });
  }
  const scenarios = { supported: 'classification-supported', uncertain: 'classification-uncertain', unsupported_skipped: 'classification-unsupported', unsupported_performed: 'classification-unsupported-performed' };
  for (const [scenario, fixture] of Object.entries(scenarios)) {
    await server('classifier', scenario, async port => {
      for (const name of ['offset', 'history']) {
        const document = { ...structuredClone(documents[name]), doc_id: `candidate-${scenario}-${name}` };
        await check(port, `classifier-${scenario}-${name}`, '/v1/classify', { schema_version: '1.0.0', document }, 'ClassificationResult', 200, body => {
          const expected = { ...structuredClone(payloads[fixture]), doc_id: document.doc_id, text_sha256: document.text_sha256 };
          assert.ok(isDeepStrictEqual(body, expected), 'Frozen scenario/identity mismatch');
        });
      }
      if (scenario === 'supported') await check(port, 'classifier-invalid-id', '/v1/classify', { schema_version: '1.0.0', document: documents.offset }, 'ErrorEnvelope', 400, () => {}, []);
    });
  }
  await server('extraction', 'default', async port => {
    const procedure = { schema_version: '1.0.0', document: documents.procedure };
    await check(port, 'extraction-planned', '/v1/extract', procedure, 'ExtractionResult', 200, body => {
      assert.equal(body.doc_id, procedure.document.doc_id); assert.equal(body.text_sha256, procedure.document.text_sha256);
      const item = body.items.find(item => item.type === 'procedure'); assert.equal(item.procedure_status, 'planned');
      assert.equal(item.mention.quote, 'Colonoscopy'); assert.equal(item.evidence[0].quote, procedure.document.text);
    });
    await check(port, 'extraction-procedure-answer', '/v1/document-answer', { ...procedure, question: 'Which procedure is mentioned?' }, 'AnswerResult', 200, body => {
      assert.equal(body.route, 'document'); assert.equal(body.evidence_state, 'sufficient'); assert.equal(body.sources[0].evidence.quote, procedure.document.text);
    });
    await check(port, 'extraction-summary', '/v1/extract', demo, 'ExtractionResult', 200, body => {
      assert.equal(body.summary.status, 'completed'); assert.ok(body.summary.result.claims.length);
    });
    await check(port, 'extraction-partial-answer', '/v1/document-answer', { ...demo, question: "What does the document say about chest pain and the patient's age?" }, 'AnswerResult', 200, body => {
      assert.equal(body.evidence_state, 'partial'); assert.ok(body.claims.length && body.sources.length && body.warnings.length);
    });
    await check(port, 'extraction-no-answer', '/v1/document-answer', { ...demo, question: "What is the patient's age?" }, 'AnswerResult', 200, body => {
      assert.equal(body.route, 'none'); assert.deepEqual(body.claims, []);
    });
    await check(port, 'extraction-invalid-digest', '/v1/extract', { ...procedure, document: { ...procedure.document, text_sha256: '0'.repeat(64) } }, 'ErrorEnvelope', 422);
    await check(port, 'extraction-invalid-id', '/v1/extract', procedure, 'ErrorEnvelope', 400, () => {}, []);
  });
  assert.equal(report.cases.length, inputs.http_cases.length);
  assert.equal(new Set(report.cases.map(c => c.id)).size, report.cases.length);
  report.cases = inputs.http_cases.map(id => { const result = report.cases.find(c => c.id === id); assert.ok(result); return result; });
  report.passed = true; delete report.in_progress;
  console.log(`PASS: ${report.cases.length} module HTTP cases; all ${report.processes.length} owned processes stopped`);
} catch (error) {
  report.diagnostic = { name: error.name, message: String(error.message).split('\n')[0], issues: error.issues };
  console.error('FAIL: ' + report.in_progress + ': ' + report.diagnostic.message); process.exitCode = 1;
} finally {
  await writeFile(path.join(cache, 'http.json'), JSON.stringify(report, null, 2) + '\n');
}
