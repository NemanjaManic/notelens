import type { MemorySessions } from './memory.ts';

const cookieName = '__Host-notelens-session';
const cookieScope = 'Path=/; Secure; HttpOnly; SameSite=Strict';
const capabilityPattern = /^[A-Za-z0-9_-]{43}$/;

function cookieCapability(requestHeaders: Pick<Headers, 'get'>): string | null {
  let capability: string | null = null;
  for (const field of (requestHeaders.get('Cookie') ?? '').split(';')) {
    const separator = field.indexOf('=');
    const name = separator < 0 ? field : field.slice(0, separator);
    if (name.trim() !== cookieName) continue;
    if (separator < 0 || capability !== null) return null;
    const value = field.slice(separator + 1).trim();
    if (!capabilityPattern.test(value)) return null;
    capability = value;
  }
  return capability;
}

/** Resolve a server-issued browser capability. A lookup never creates a session. */
export function readBrowserSession(store: MemorySessions, requestHeaders: Pick<Headers, 'get'>): string | null {
  const capability = cookieCapability(requestHeaders);
  return capability !== null && store.hasSession(capability) ? capability : null;
}

/** Call from a trusted server handler after its session admission checks. */
export function openBrowserSession(store: MemorySessions, requestHeaders: Headers, responseHeaders: Headers): string {
  responseHeaders.set('Cache-Control', 'no-store');
  const existing = cookieCapability(requestHeaders);
  if (existing !== null && store.recordActivity(existing)) return existing;

  const capability = store.createSession();
  try {
    responseHeaders.append('Set-Cookie', `${cookieName}=${capability}; ${cookieScope}`);
  } catch (error) {
    store.endSession(capability);
    throw error;
  }
  return capability;
}

/** Revoke the resolved session and expire its browser cookie. */
export function closeBrowserSession(store: MemorySessions, requestHeaders: Headers, responseHeaders: Headers): void {
  const capability = readBrowserSession(store, requestHeaders);
  if (capability !== null) store.endSession(capability);
  responseHeaders.set('Cache-Control', 'no-store');
  responseHeaders.append('Set-Cookie', `${cookieName}=; ${cookieScope}; Max-Age=0`);
}
