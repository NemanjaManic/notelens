import { randomUUID } from 'node:crypto';
import type {
  ClassificationRequest, DocumentQuestionRequest, ExtractionRequest, LiteratureAnswerRequest, Records,
} from '@notelens/contracts/v1';
import { consumeExchange, OPERATIONS } from '../contracts/consumer.ts';
import { boundedEvaluation } from './bounded-evaluation.ts';

type Requests = {
  classify: ClassificationRequest;
  extract: ExtractionRequest;
  'document-answer': DocumentQuestionRequest;
  'literature-answer': LiteratureAnswerRequest;
};
type Operation = keyof Requests;
type Result<K extends Operation> = Records[(typeof OPERATIONS)[K]['definition']];
export type MockResult<T> = { kind: 'accepted'; record: T } | { kind: 'unavailable' } | { kind: 'invalid' } | { kind: 'unsupported' };
type DemoService = 'RAG' | 'CLASSIFIER' | 'EXTRACTION';

const services: Record<Operation, DemoService> = {
  classify: 'CLASSIFIER', extract: 'EXTRACTION', 'document-answer': 'EXTRACTION', 'literature-answer': 'RAG',
};
const demoTimeoutMs = 5_000;

function loopbackPort(value: string | undefined) {
  return value && /^[1-9][0-9]{0,4}$/.test(value) && Number(value) <= 65535 ? value : null;
}

export function mockServiceClients(env: NodeJS.ProcessEnv = process.env, transport: typeof fetch = fetch) {
  const token = env.NOTELENS_DEMO_TOKEN;
  const replayProfile = env.NOTELENS_LOCAL_D005_PROFILE;
  const d005Replay = replayProfile === 'saved-replay';
  const evaluation = boundedEvaluation(env);
  if (env.NOTELENS_BOUNDED_EVALUATION !== undefined && (!evaluation || replayProfile !== undefined)) return null;
  if (replayProfile !== undefined && (!d005Replay ||
      !loopbackPort(/^http:\/\/localhost:([0-9]+)$/.exec(env.NOTELENS_SESSION_ORIGIN ?? '')?.[1]) ||
      !token || !/^\S+$/.test(token))) return null;
  const ports = {
    RAG: loopbackPort(env.NOTELENS_DEMO_RAG_PORT),
    CLASSIFIER: loopbackPort(env.NOTELENS_DEMO_CLASSIFIER_PORT),
    EXTRACTION: loopbackPort(env.NOTELENS_DEMO_EXTRACTION_PORT),
  };
  if (env.NOTELENS_MODE !== 'mock' || !env.NOTELENS_DEMO_RUN || !token || Object.values(ports).some(port => !port)) return null;

  async function exchange<K extends Operation>(operation: K, body: Requests[K]): Promise<MockResult<Result<K>>> {
    const requestHeaders: [string, string][] = [['Content-Type', 'application/json'], ['X-Request-ID', randomUUID()]];
    try {
      const headers = new Headers(requestHeaders);
      const serviceToken = !evaluation || operation === 'classify' ? token
        : operation === 'literature-answer' ? evaluation.ragToken : evaluation.extractionToken;
      headers.set('Authorization', `Bearer ${serviceToken}`);
      const response = await transport(`http://127.0.0.1:${ports[services[operation]]}${OPERATIONS[operation].path}`, {
        method: 'POST', headers, body: JSON.stringify(body), cache: 'no-store', redirect: 'error',
        signal: AbortSignal.timeout(evaluation?.timeoutMs ?? demoTimeoutMs),
      });
      if (response.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
        return { kind: response.ok ? 'invalid' : 'unavailable' };
      }
      const result = await consumeExchange(operation, {
        status: response.status, requestHeaders, responseHeaders: [...response.headers],
        json: await response.text(), disposition: response.ok ? 'accepted_result' : 'failed_call',
        document: 'document' in body ? body.document : undefined,
      }, d005Replay, Boolean(evaluation && operation !== 'classify'));
      // consumeExchange validates the response with the definition for this operation.
      if (result.kind === 'accepted') return { kind: 'accepted', record: result.record as Result<K> };
      if (operation === 'literature-answer' && response.status === 422 &&
          result.kind === 'service-error' && result.code === 'validation_failure') return { kind: 'unsupported' };
      return { kind: result.kind === 'rejected' ? 'invalid' : 'unavailable' };
    } catch {
      return { kind: 'unavailable' };
    }
  }

  function post<K extends Operation>(operation: K, body: Requests[K]): Promise<MockResult<Result<K>>> {
    if (!evaluation || operation === 'classify') return exchange(operation, body);
    const source = operation === 'extract' && 'document' in body ? body.document.text_sha256 : undefined;
    return evaluation.budget.dispatch(operation, source, () => exchange(operation, body));
  }

  return {
    d005Replay,
    evaluation: evaluation?.profile,
    classify: (document: ClassificationRequest['document']) => post('classify', { schema_version: '1.0.0', document }),
    extract: (document: ExtractionRequest['document']) => post('extract', { schema_version: '1.0.0', document }),
    documentAnswer: (document: DocumentQuestionRequest['document'], question: string) =>
      post('document-answer', { schema_version: '1.0.0', document, question }),
    literatureAnswer: (question: string) => post('literature-answer', { schema_version: '1.0.0', question }),
  };
}

export type MockServiceClients = NonNullable<ReturnType<typeof mockServiceClients>>;
