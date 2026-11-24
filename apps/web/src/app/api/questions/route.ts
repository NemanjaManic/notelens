import { mockServiceClients } from '../../../lib/clients/mock-services.ts';
import { boundedBody } from '../../../lib/http/bounded-body.ts';
import { routeQuestion } from '../../../lib/routing/answer.ts';
import { DOCUMENT_ID, MAX_QUESTION_BODY_BYTES, questionDocument, questionPlan } from '../../../lib/routing/question-input.ts';
import { isBuiltinDemoDocument } from '../../../lib/scaffold/demo.ts';
import { readBrowserSession } from '../../../lib/sessions/browser.ts';
import { UNAVAILABLE } from '../../../lib/sessions/memory.ts';
import { getSessionStore, isSessionRequestFromOrigin, sessionErrorResponse } from '../../../lib/sessions/route.ts';

export const runtime = 'nodejs';

async function handle(request: Request): Promise<Response> {
  const headers = new Headers({ 'Cache-Control': 'no-store' });
  const reject = (status: number, notice: string) => Response.json({ notice }, { status, headers });
  try {
    const clients = mockServiceClients();
    if (!clients) return reject(503, 'The local mock demo is unavailable.');
    if (!isSessionRequestFromOrigin(request.headers)) return reject(403, 'The question request must come from this site.');
    const store = getSessionStore();
    const owner = readBrowserSession(store, request.headers);
    if (!owner) return reject(404, UNAVAILABLE.notice);

    if (request.method === 'DELETE') {
      const id = new URL(request.url).searchParams.get('document');
      return id && DOCUMENT_ID.test(id) && store.clearQuestionHistory(owner, id)
        ? new Response(null, { status: 204, headers }) : reject(404, UNAVAILABLE.notice);
    }

    if (request.headers.get('Content-Type')?.split(';', 1)[0].trim().toLowerCase() !== 'application/json') {
      return reject(415, 'Submit a JSON question request.');
    }
    const bytes = await boundedBody(request, MAX_QUESTION_BODY_BYTES);
    if (!bytes) return reject(413, 'The question request exceeds 16 KiB.');
    let input: unknown;
    try {
      input = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    } catch {
      return reject(400, 'The question request contains invalid JSON or UTF-8.');
    }
    const id = questionDocument(input);
    if (!id) return reject(400, 'Select a document before asking a question.');
    const document = store.getDocument(owner, id);
    if ('kind' in document) return reject(404, document.notice);
    const evaluationCapture = Boolean(clients.evaluation && request.headers.get('X-NoteLens-Evaluation-Output') === '1');
    const result = questionPlan(input as Record<string, unknown>, isBuiltinDemoDocument(document), evaluationCapture,
      clients.reviewedQuestionHashes);
    if ('notice' in result) return reject(result.status, result.notice);

    const pending = store.beginQuestion(owner, id, result.plan);
    if (pending.kind === 'unavailable') return reject(404, pending.notice);
    if (pending.kind === 'duplicate') return reject(409, 'This question has already been submitted for this document in this session.');
    if (pending.kind === 'quota') return reject(429, 'This demo session has reached its limit of 5 questions.');
    if (pending.kind === 'busy') return reject(409, 'Another question is still running in this session.');
    if (pending.kind === 'rate') {
      headers.set('Retry-After', String(pending.retryAfter));
      return reject(429, 'This session has reached 10 questions per minute. Try again shortly.');
    }
    try {
      const answer = await routeQuestion(clients, result.plan, document);
      const completed = store.finishQuestion(owner, pending.id, result.plan, answer);
      if (completed.kind === 'unavailable') return reject(409, 'The answer is no longer available. Reopen the report before asking again.');
      return Response.json(evaluationCapture && completed.kind === 'saved' ? { ...completed, answer } : completed,
        { status: 200, headers });
    } finally {
      store.cancelQuestion(owner, pending.id);
    }
  } catch (error) {
    return sessionErrorResponse(error, headers);
  }
}

export { handle as POST, handle as DELETE };
