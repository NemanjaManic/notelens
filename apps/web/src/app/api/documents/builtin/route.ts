import { prepareBuiltin } from '../../../../lib/documents/builtin.ts';
import { isDemoConfigured } from '../../../../lib/scaffold/demo.ts';
import { openBrowserSession } from '../../../../lib/sessions/browser.ts';
import { getSessionStore, isSessionRequestFromOrigin, sessionErrorResponse } from '../../../../lib/sessions/route.ts';

export const runtime = 'nodejs';

export async function POST(request: Request): Promise<Response> {
  const headers = new Headers({ 'Cache-Control': 'no-store' });
  try {
    if (!isDemoConfigured()) {
      return Response.json({ notice: 'The local mock demo is unavailable.' }, { status: 503, headers });
    }
    if (!isSessionRequestFromOrigin(request.headers)) {
      return Response.json({ notice: 'The example request must come from this site.' }, { status: 403, headers });
    }

    const store = getSessionStore();
    const owner = openBrowserSession(store, request.headers, headers);
    const result = await prepareBuiltin(store, owner, 'offset');
    headers.set('Location', result.kind === 'prepared' ? `/demo?document=${result.docId}` : '/demo?prepare=unavailable');
    return new Response(null, { status: 303, headers });
  } catch (error) {
    return sessionErrorResponse(error, headers);
  }
}
