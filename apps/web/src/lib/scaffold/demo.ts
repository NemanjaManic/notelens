import { randomUUID } from 'node:crypto';
import type { AnswerResult, PreparedDocument } from '@notelens/contracts/v1';
import { consumeExchange, OPERATIONS } from '../contracts/consumer.ts';
import type { BusinessOperation } from '../contracts/consumer.ts';
import { buildReport, fixtureWorkspace } from '../report/model.ts';
import type { Workspace } from '../report/model.ts';

const questionKeys = ['document', 'literature', 'mixed', 'insufficient'] as const;
type Question = typeof questionKeys[number];
const documentQuestion = 'What does the document say about chest pain?';
const literatureQuestion = 'What is the synthetic demo topic?';
const presets: Record<Question, { label: string; document?: string; literature?: string }> = {
  document: { label: documentQuestion, document: documentQuestion },
  literature: { label: literatureQuestion, literature: literatureQuestion },
  mixed: { label: 'What does the report say about chest pain, and what is the synthetic demo topic?',
    document: documentQuestion, literature: literatureQuestion },
  insufficient: { label: "What is the patient's age?", document: "What is the patient's age?" },
};
export const demoQuestions = questionKeys.map(key => ({ key, label: presets[key].label }));

export type DemoAnswer = {
  route: 'document' | 'literature' | 'mixed' | 'none';
  state: 'sufficient' | 'partial' | 'insufficient' | 'unavailable';
  branches: { origin: 'document' | 'literature'; answer: AnswerResult | null }[];
};

function loopbackPort(service: 'RAG' | 'CLASSIFIER' | 'EXTRACTION') {
  const value = process.env[`NOTELENS_DEMO_${service}_PORT`];
  return value && /^[1-9][0-9]{0,4}$/.test(value) && Number(value) <= 65535 ? value : null;
}

export function isDemoConfigured() {
  return process.env.NOTELENS_MODE === 'mock' && !!process.env.NOTELENS_DEMO_RUN
    && !!process.env.NOTELENS_DEMO_TOKEN && !!loopbackPort('RAG')
    && !!loopbackPort('CLASSIFIER') && !!loopbackPort('EXTRACTION');
}

export function isBuiltinDemoDocument(document: PreparedDocument | null): boolean {
  return document?.language_validation.policy_version === 'fixture-language-policy-v0';
}

async function call(operation: BusinessOperation, document?: PreparedDocument, question?: string) {
  const service = operation === 'classify' ? 'CLASSIFIER' : operation === 'literature-answer' ? 'RAG' : 'EXTRACTION';
  const port = loopbackPort(service);
  if (!port) return null;
  const requestHeaders: [string, string][] = [
    ['Content-Type', 'application/json'], ['X-Request-ID', randomUUID()],
  ];
  try {
    const headers = new Headers(requestHeaders);
    headers.set('Authorization', `Bearer ${process.env.NOTELENS_DEMO_TOKEN}`);
    const response = await fetch(`http://127.0.0.1:${port}${OPERATIONS[operation].path}`, {
      method: 'POST', headers, body: JSON.stringify({ schema_version: '1.0.0', document, question }),
      cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(5000),
    });
    if (response.headers.get('content-type')?.split(';')[0].toLowerCase() !== 'application/json') return null;
    const result = await consumeExchange(operation, {
      status: response.status, requestHeaders, responseHeaders: [...response.headers],
      json: await response.text(), disposition: response.ok ? 'accepted_result' : 'failed_call', document,
    });
    return result.kind === 'accepted' ? result.record : null;
  } catch {
    return null;
  }
}

function selectedQuestion(value: string | string[] | undefined) {
  return questionKeys.find(key => key === value);
}

async function answerDemo(key: Question, document: PreparedDocument): Promise<DemoAnswer> {
  const preset = presets[key];
  const origins = (['document', 'literature'] as const).filter(origin => preset[origin]);
  const branches = await Promise.all(origins.map(async origin => {
    const answer = await call(origin === 'document' ? 'document-answer' : 'literature-answer',
      origin === 'document' ? document : undefined, preset[origin]);
    return { origin, answer: answer && 'route' in answer && (answer.route === origin || answer.route === 'none') ? answer : null };
  }));
  const supported = branches.filter(({ answer }) => answer && answer.claims.length > 0);
  const route = supported.length === 2 ? 'mixed' : supported[0]?.origin ?? 'none';
  const state = supported.length === 0
    ? branches.some(({ answer }) => !answer) ? 'unavailable' : 'insufficient'
    : supported.length < branches.length || supported.some(({ answer }) => answer?.evidence_state === 'partial')
      ? 'partial' : 'sufficient';
  return { route, state, branches };
}

export async function demoWorkspace(query: Record<string, string | string[] | undefined>, document: PreparedDocument | null):
    Promise<{ view: Workspace; question?: Question; answer?: DemoAnswer }> {
  if (!document) return { view: await fixtureWorkspace(query.document === undefined ? 'no-document' : 'unavailable') };
  const builtin = isBuiltinDemoDocument(document);
  const question = builtin ? selectedQuestion(query.question) : undefined;
  const [classification, extraction, answer] = await Promise.all([
    builtin ? call('classify', document) : undefined,
    call('extract', document),
    question ? answerDemo(question, document) : undefined,
  ]);
  const report = await buildReport(document, classification, extraction);
  if (!builtin) {
    report.classification = { state: 'empty', notice: 'Mock specialty classification is available for the built-in example.' };
  } else if (!classification) {
    report.classification = { state: 'unavailable', notice: 'The specialty result is unavailable.' };
  }
  if (!extraction) {
    report.extraction = { state: 'unavailable', notice: 'The findings and summary are unavailable.' };
  }
  for (const branch of answer?.branches ?? []) {
    branch.answer?.sources.forEach((source, index) => {
      if ('evidence' in source) report.passages.push({
        key: `answer-${branch.origin}-${index}`, label: `Answer source ${index + 1}`, span: source.evidence,
      });
    });
  }
  const selected = report.passages.find(passage => passage.key === query.evidence) ?? null;
  return { view: { ...report, scenario: 'ready', heading: builtin ? 'Report overview' : 'Prepared document', selected }, question, answer };
}
