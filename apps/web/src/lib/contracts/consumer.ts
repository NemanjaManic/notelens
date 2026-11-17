import { ContractValidationError, validateExchange, validateJson, validateRecord } from '@notelens/contracts/v1';
import type { Context, ErrorDetail, PreparedDocument, Records } from '@notelens/contracts/v1';

export type ResultDefinition = 'ClassificationResult' | 'ExtractionResult' | 'RetrievalResult' | 'AnswerResult';
export type RecordInput = { kind: 'native'; value: unknown } | { kind: 'json'; value: string };
export type Rejected = {
  kind: 'rejected';
  code: 'invalid-result' | 'document-context' | 'mock-mode' | 'invalid-exchange';
  notice: string;
  rules: string[];
};
export type Accepted<K extends ResultDefinition = ResultDefinition> = { kind: 'accepted'; record: Records[K] };
export type ServiceError = {
  kind: 'service-error'; code: ErrorDetail['code']; retryable: boolean; requestId: string; notice: string;
};
export type ConsumerOutcome<K extends ResultDefinition = ResultDefinition> = Accepted<K> | Rejected | ServiceError;

// Frozen contracts/v1/openapi.json business POST metadata. Tests compare every entry.
// Keeping this bounded lookup avoids shipping an OpenAPI parser in the application.
const statuses = Object.freeze([200, 400, 401, 404, 413, 415, 422, 429, 500, 502, 503, 504]);
export const OPERATIONS = Object.freeze({
  classify: Object.freeze({ path: '/v1/classify', definition: 'ClassificationResult', document: true, statuses } as const),
  extract: Object.freeze({ path: '/v1/extract', definition: 'ExtractionResult', document: true, statuses } as const),
  'document-answer': Object.freeze({ path: '/v1/document-answer', definition: 'AnswerResult', document: true, statuses } as const),
  retrieve: Object.freeze({ path: '/v1/retrieve', definition: 'RetrievalResult', document: false, statuses } as const),
  'literature-answer': Object.freeze({ path: '/v1/literature-answer', definition: 'AnswerResult', document: false, statuses } as const),
});
export type BusinessOperation = keyof typeof OPERATIONS;
export interface BusinessExchange {
  status: number;
  requestHeaders: [string, string][];
  responseHeaders: [string, string][];
  json: string;
  disposition: string;
  document?: PreparedDocument;
}

function rejected(code: Rejected['code'], rules: string[] = ['CONSUMER_REJECTED']): Rejected {
  // Only contract rule identifiers may leave the boundary, never paths or messages.
  const safe = [...new Set(rules.filter(rule => /^[A-Z][A-Z0-9_]{0,63}$/.test(rule)))];
  return { kind: 'rejected', code, notice: 'The response could not be verified. No result was accepted.',
    rules: safe.length ? safe : ['CONSUMER_REJECTED'] };
}

function invalid(error: unknown, code: Rejected['code'] = 'invalid-result'): Rejected {
  return rejected(code, error instanceof ContractValidationError ? error.issues.map(issue => issue.rule) : ['VALIDATION_FAILED']);
}

/** Consume a generated result without coercion, text repair, composition or I/O. */
export async function consumeRecord<K extends ResultDefinition>(
  definition: K, input: RecordInput, context: Context = {},
): Promise<Accepted<K> | Rejected> {
  try {
    if (!['ClassificationResult', 'ExtractionResult', 'RetrievalResult', 'AnswerResult'].includes(definition)) {
      return rejected('invalid-result', ['RESULT_DEFINITION']);
    }
    if (context.document) await validateRecord('PreparedDocument', context.document);
    if ((definition === 'ClassificationResult' || definition === 'ExtractionResult') && !context.document) {
      return rejected('document-context', ['DOCUMENT_CONTEXT']);
    }
    // Native values must reach validation before serialization can hide NaN/Infinity.
    // Raw JSON must reach the strict validator before duplicate keys can be lost.
    const record = input.kind === 'native' ? await validateRecord(definition, input.value, context)
      : input.kind === 'json' ? await validateJson(definition, input.value, context) : null;
    if (!record) return rejected('invalid-result', ['INPUT_REPRESENTATION']);
    if (definition === 'AnswerResult') {
      const answer = record as Records['AnswerResult'];
      if ((answer.route === 'document' || answer.route === 'mixed' || answer.sources.some(s => s.kind === 'document')) && !context.document) {
        return rejected('document-context', ['DOCUMENT_CONTEXT']);
      }
    }
    if (record.mode !== 'mock') return rejected('mock-mode', ['MOCK_MODE_REQUIRED']);
    return { kind: 'accepted', record };
  } catch (error) {
    return invalid(error);
  }
}

/** Check a synthetic business exchange, preserving raw duplicate header admission. */
export async function consumeExchange(operation: BusinessOperation, exchange: BusinessExchange): Promise<ConsumerOutcome> {
  try {
    if (!Object.hasOwn(OPERATIONS, operation)) return rejected('invalid-exchange', ['BUSINESS_OPERATION']);
    const metadata = OPERATIONS[operation];
    if (!metadata.statuses.includes(exchange.status)) return rejected('invalid-exchange', ['HTTP_STATUS']);
    const transport = (body: unknown) => validateExchange({
      path: metadata.path, status: exchange.status, body,
      request_headers: exchange.requestHeaders, response_headers: exchange.responseHeaders,
      disposition: exchange.disposition,
    });
    if (exchange.status !== 200) {
      // An invalid submitted document must not hide a valid 422/admission envelope.
      // ErrorEnvelope deliberately has no mode and its upstream message is private.
      const envelope = await validateJson('ErrorEnvelope', exchange.json);
      const rules = await transport(envelope);
      if (rules.length) return rejected('invalid-exchange', rules);
      if (exchange.status === 400) {
        const incoming = exchange.requestHeaders.filter(([name]) => name.toLowerCase() === 'x-request-id').map(([, value]) => value);
        let canonical = false;
        if (incoming.length === 1) {
          try { await validateRecord('RequestId', incoming[0]); canonical = true; } catch { /* Admission rejected this ID. */ }
        }
        // The frozen business validator checks admission/correlation, but freshness
        // also requires that a diagnostic ID not reuse any rejected incoming value.
        if (!canonical && incoming.includes(envelope.request_id)) return rejected('invalid-exchange', ['ADMISSION_ID_REUSED']);
      }
      return { kind: 'service-error', code: envelope.error.code, retryable: envelope.error.retryable,
        requestId: envelope.request_id, notice: 'The service could not complete this request.' };
    }
    if (metadata.document && !exchange.document) return rejected('document-context', ['DOCUMENT_CONTEXT']);
    const result = await consumeRecord(metadata.definition, { kind: 'json', value: exchange.json },
      exchange.document ? { document: exchange.document } : {});
    if (result.kind !== 'accepted') return result;
    const rules = await transport(result.record);
    if (rules.length) return rejected('invalid-exchange', rules);
    return result;
  } catch (error) {
    return invalid(error, 'invalid-exchange');
  }
}
