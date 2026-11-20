import { randomUUID } from 'node:crypto';
import { validateExchange, validateJson } from '@notelens/contracts/v1';
import type { ClassificationResult, HealthResult, PreparedDocument } from '@notelens/contracts/v1';
import { OPERATIONS } from '../contracts/consumer.ts';

type Target = { port: number; token: string } & (
  { profile: 'fixture' } | { profile: 'fitted'; modelVersion: string }
);
type Failure = { kind: 'unavailable' | 'invalid' | 'unauthorized' | 'not-ready' };
type Outcome<T> = { kind: 'accepted'; record: T } | Failure;
type Reply = { status: number; headers: [string, string][]; json: string };

const readyPath = '/health/ready';
const classify = OPERATIONS.classify;

/** Server-side loopback client for the explicit classifier integration test profiles. */
export function classifierTestClient(target: Target) {
  const { port, token } = target;
  if (!Number.isInteger(port) || port < 1 || port > 65535 || !/^\S+$/.test(token) ||
      (target.profile === 'fitted' && !target.modelVersion.trim())) {
    throw new Error('Invalid classifier test configuration.');
  }
  const mode = target.profile === 'fitted' ? 'live' : 'mock';
  const modelVersion = target.profile === 'fitted' ? target.modelVersion : null;

  async function send(path: string, requestHeaders: [string, string][], body?: string): Promise<Reply | Failure> {
    try {
      const headers = new Headers(requestHeaders);
      headers.set('Authorization', `Bearer ${token}`);
      const response = await fetch(`http://127.0.0.1:${port}${path}`, {
        method: body === undefined ? 'GET' : 'POST',
        headers, body, redirect: 'error', cache: 'no-store', signal: AbortSignal.timeout(5_000),
      });
      if (response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
        await response.body?.cancel();
        return { kind: 'invalid' };
      }
      return { status: response.status, headers: [...response.headers], json: await response.text() };
    } catch {
      return { kind: 'unavailable' };
    }
  }

  async function checkError(path: string, requestHeaders: [string, string][], reply: Reply): Promise<Failure> {
    const body = await validateJson('ErrorEnvelope', reply.json);
    const rules = await validateExchange({
      path, status: reply.status, body, request_headers: requestHeaders, response_headers: reply.headers,
      disposition: 'failed_call',
    });
    if (rules.length) return { kind: 'invalid' };
    if (reply.status !== 401) return { kind: 'unavailable' };
    return { kind: body.error.code === 'unauthorized' && !body.error.retryable ? 'unauthorized' : 'invalid' };
  }

  return {
    async readiness(): Promise<Outcome<HealthResult>> {
      const requestHeaders: [string, string][] = [['X-Request-ID', randomUUID()]];
      const reply = await send(readyPath, requestHeaders);
      if ('kind' in reply) return reply;
      try {
        if (reply.status === 401) return await checkError(readyPath, requestHeaders, reply);
        const record = await validateJson('HealthResult', reply.json);
        if (record.service !== 'classifier' || record.mode !== mode) return { kind: 'invalid' };
        if (reply.status === 503 && record.status === 'not_ready') return { kind: 'not-ready' };
        if (reply.status !== 200 || record.status !== 'ok' || record.model_version !== modelVersion) {
          return { kind: 'invalid' };
        }
        return { kind: 'accepted', record };
      } catch {
        return { kind: 'invalid' };
      }
    },

    async classify(document: PreparedDocument): Promise<Outcome<ClassificationResult>> {
      const requestHeaders: [string, string][] = [['Content-Type', 'application/json'], ['X-Request-ID', randomUUID()]];
      try {
        const json = JSON.stringify({ schema_version: '1.0.0', document });
        const request = await validateJson('ClassificationRequest', json);
        const reply = await send(classify.path, requestHeaders, json);
        if ('kind' in reply) return reply;
        if (!classify.statuses.includes(reply.status)) return { kind: 'invalid' };
        if (reply.status !== 200) return await checkError(classify.path, requestHeaders, reply);
        const record = await validateJson(classify.definition, reply.json, { document: request.document });
        const rules = await validateExchange({
          path: classify.path, status: reply.status, body: record, request_headers: requestHeaders,
          response_headers: reply.headers, disposition: 'accepted_result',
        });
        if (rules.length || record.mode !== mode ||
            (modelVersion !== null && record.classification_execution === 'performed' && record.model_version !== modelVersion)) {
          return { kind: 'invalid' };
        }
        return { kind: 'accepted', record };
      } catch {
        return { kind: 'invalid' };
      }
    },
  };
}
