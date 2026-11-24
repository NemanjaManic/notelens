import { mockServiceClients } from '../../../../lib/clients/mock-services.ts';
import { inputErrors, prepareSubmitted, submissionByteLimit } from '../../../../lib/documents/submitted.ts';
import { exceedsDeclaredBodyLimit } from '../../../../lib/http/bounded-body.ts';
import { openBrowserSession } from '../../../../lib/sessions/browser.ts';
import { getSessionStore, isSessionRequestFromOrigin, sessionErrorResponse } from '../../../../lib/sessions/route.ts';

export const runtime = 'nodejs';

export async function POST(request: Request): Promise<Response> {
  const headers = new Headers({ 'Cache-Control': 'no-store' });
  const reject = (status: number, notice: string) => Response.json({ notice }, { status, headers });
  try {
    const clients = mockServiceClients();
    if (!clients) return reject(503, 'The local mock demo is unavailable.');
    if (!isSessionRequestFromOrigin(request.headers)) return reject(403, 'The submission must come from this site.');
    const mime = request.headers.get('Content-Type')?.split(';', 1)[0].trim().toLowerCase();
    const input = mime === 'text/plain' ? 'text' : mime === 'application/pdf' ? 'pdf' : null;
    if (input === null) return reject(415, 'Submit pasted English text or a text-based PDF.');
    const scope = request.headers.get('X-NoteLens-Input-Scope');
    if (scope !== 'public' && scope !== 'synthetic') return reject(400, 'Confirm that the input is public or synthetic.');
    const encoding = request.headers.get('Content-Encoding');
    if (encoding !== null && encoding.trim().toLowerCase() !== 'identity') {
      return reject(415, 'Submit an uncompressed text or PDF request.');
    }
    if (exceedsDeclaredBodyLimit(request, submissionByteLimit(input))) {
      return reject(413, inputErrors[input === 'pdf' ? 'pdf-too-large' : 'text-too-large']);
    }

    const store = getSessionStore();
    const owner = openBrowserSession(store, request.headers, headers);
    const reviewedReplayHashes = clients.d005Replay
      ? process.env.NOTELENS_LOCAL_D005_REVIEWED_TEXT_SHA256?.split(',')
      : undefined;
    const result = await prepareSubmitted(store, owner, request, input, scope, reviewedReplayHashes);
    if (result.kind === 'prepared') {
      if (clients.evaluation && clients.evaluation !== 'public-live' && request.headers.get('X-NoteLens-Evaluation-Output') === '1') {
        const prepared = store.getDocument(owner, result.docId);
        if ('kind' in prepared) return reject(409, prepared.notice);
        return Response.json({ document: result.docId, canonical_sha256: prepared.text_sha256 }, { status: 201, headers });
      }
      return Response.json({ document: result.docId }, { status: 201, headers });
    }
    if (result.kind === 'unavailable') return reject(409, result.notice);
    return reject(result.code.endsWith('too-large') ? 413 : 422, inputErrors[result.code]);
  } catch (error) {
    return sessionErrorResponse(error, headers);
  }
}
