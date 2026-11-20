import { sessionConfiguration, sessionOrigin } from '../config/session-policy.ts';
import { closeBrowserSession, openBrowserSession } from './browser.ts';
import { MemorySessions, SessionAdmissionError } from './memory.ts';

// Next route modules can be bundled separately while sharing one Node process.
const processState = globalThis as typeof globalThis & { notelensSessions?: MemorySessions };

export function getSessionStore(): MemorySessions {
  return processState.notelensSessions ??= new MemorySessions();
}

export function handleSessionRequest(
  request: Request,
  getStore = getSessionStore,
  configuredOrigin = process.env.NOTELENS_SESSION_ORIGIN,
): Response {
  const headers = new Headers({ 'Cache-Control': 'no-store' });
  try {
    sessionConfiguration();
    const origin = sessionOrigin(configuredOrigin);
    if (request.headers.get('Origin') !== origin) {
      return Response.json({ notice: 'The session request must come from this site.' }, { status: 403, headers });
    }

    if (request.method === 'POST') {
      openBrowserSession(getStore(), request.headers, headers);
    } else if (request.method === 'DELETE') {
      closeBrowserSession(getStore(), request.headers, headers);
    } else {
      headers.set('Allow', 'POST, DELETE');
      return new Response(null, { status: 405, headers });
    }
    return new Response(null, { status: 204, headers });
  } catch (error) {
    if (error instanceof SessionAdmissionError && error.kind === 'rate') {
      headers.set('Retry-After', String(error.retryAfter));
      return Response.json({ notice: error.message }, { status: 429, headers });
    }
    const notice = error instanceof SessionAdmissionError ? error.message : 'The session service is unavailable.';
    return Response.json({ notice }, { status: 503, headers });
  }
}
