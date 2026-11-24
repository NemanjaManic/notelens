import { mockServiceClients } from '../../../../lib/clients/mock-services.ts';
import { DOCUMENT_ID } from '../../../../lib/routing/question-input.ts';
import { demoWorkspace } from '../../../../lib/scaffold/demo.ts';
import { readBrowserSession } from '../../../../lib/sessions/browser.ts';
import { getSessionStore, isSessionRequestFromOrigin, sessionErrorResponse } from '../../../../lib/sessions/route.ts';

export const runtime = 'nodejs';

export async function POST(request: Request): Promise<Response> {
  const headers = new Headers({ 'Cache-Control': 'no-store' });
  const reject = (status: number, notice: string) => Response.json({ notice }, { status, headers });
  try {
    if (!mockServiceClients()?.evaluation || request.headers.get('X-NoteLens-Evaluation-Output') !== '1') {
      return reject(404, 'Evaluation output is unavailable.');
    }
    if (!isSessionRequestFromOrigin(request.headers)) return reject(403, 'Use the configured evaluation origin.');
    const store = getSessionStore();
    const owner = readBrowserSession(store, request.headers);
    const id = new URL(request.url).searchParams.get('document');
    if (!owner || !id || !DOCUMENT_ID.test(id)) return reject(404, 'The document is unavailable.');
    const document = store.getDocument(owner, id);
    if ('kind' in document) return reject(404, document.notice);
    const view = await demoWorkspace({}, document, owner);
    if ('kind' in store.getDocument(owner, id)) return reject(404, 'The document is unavailable.');
    return Response.json({ document: id, canonical_sha256: document.text_sha256,
      classification: view.classification, extraction: view.extraction }, { headers });
  } catch (error) {
    return sessionErrorResponse(error, headers);
  }
}
