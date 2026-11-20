import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { createHash, randomUUID } from 'node:crypto';
import { closeBrowserSession, openBrowserSession, readBrowserSession } from '../src/lib/sessions/browser.ts';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';
import type { SessionRuntime } from '../src/lib/sessions/memory.ts';
import { handleSessionRequest } from '../src/lib/sessions/route.ts';
import { DOCUMENT_LIFETIME_MS as TTL, SESSION_IDLE_MS as IDLE, sessionConfiguration } from '../src/lib/config/session-policy.ts';

const fixture = JSON.parse(readFileSync(new URL('../../../contracts/v1/fixtures/documents.json', import.meta.url), 'utf8')).offset;
const same = (a: unknown, b: unknown) => {
  if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error('SESSION_CHECK_FAILED');
};
function setup() {
  let time = 0;
  let cancellations = 0;
  const timers = new Set<{ callback: () => void; at: number }>();
  const runtime: SessionRuntime = { now: () => time, schedule: (callback, delay) => {
    const timer = { callback, at: time + delay }; timers.add(timer); return () => { cancellations++; timers.delete(timer); };
  } };
  const store = new MemorySessions({ mode: 'mock', runtime });
  const session = store.createSession();
  const advance = (to: number, fire = true) => {
    time = to;
    if (fire) for (const t of [...timers]) if (t.at <= time) { timers.delete(t); t.callback(); }
  };
  return { store, session, advance, timers, get cancellations() { return cancellations; } };
}
const add = async (s: ReturnType<typeof setup>, value: unknown = fixture) => {
  const ticket = s.store.beginDocument(s.session)!;
  same(await s.store.storeDocument(s.session, ticket, value), { kind: 'stored' });
  return ticket;
};
function stayActive(s: ReturnType<typeof setup>) {
  s.advance(IDLE - 1);
  same(s.store.recordActivity(s.session), true);
  s.advance(TTL - 2);
  same(s.store.recordActivity(s.session), true);
}

test('config/approved-limits-only', () => same(sessionConfiguration('mock'), {
  mode: 'mock', documentLifetimeMs: 3_600_000, maxPdfBytes: 2_097_152, maxDocumentCodePoints: 100_000,
  sessionLifetimeMs: 3_600_000, sessionIdleMs: 1_800_000, maxActiveSessions: 32, maxNewSessions: 10,
  sessionRateWindowMs: 60_000, maxActiveDocuments: 3, maxPendingPreparations: 1, storedChatTurns: 0, automaticRetries: 0,
}));
for (const mode of ['live', 'mixed', '', 'MOCK', 'unknown']) test(`config/reject-${mode || 'empty'}`, () => {
  let rejected = false; try { new MemorySessions({ mode }); } catch { rejected = true; }
  same(rejected, true);
});
test('sessions/opaque-unique-capabilities', () => {
  const s = setup(); const other = s.store.createSession();
  same(s.session.length, 43); same(other === s.session, false); same(s.session.includes(fixture.doc_id), false); s.store.dispose();
});
test('sessions/two-session-isolation', async () => {
  const s = setup(); await add(s); const other = s.store.createSession();
  same(s.store.getDocument(other, fixture.doc_id), UNAVAILABLE);
  same(s.store.getDocument(s.session, fixture.doc_id), fixture); s.store.dispose();
});
test('sessions/invalid-expired-unknown-uniform', async () => {
  const s = setup(); await add(s);
  const invalid = s.store.getDocument('invalid', fixture.doc_id);
  same(s.store.getDocument(s.session, 'unknown'), invalid);
  s.advance(TTL); same(s.store.getDocument(s.session, fixture.doc_id), invalid); s.store.dispose();
});
test('sessions/copy-in-and-out', async () => {
  const s = setup(); const value = structuredClone(fixture); await add(s, value);
  value.text = 'PRIVATE_MARKER'; const output = s.store.getDocument(s.session, fixture.doc_id);
  same(output, fixture);
  if ('text' in output) output.text = 'PRIVATE_MARKER';
  same(s.store.getDocument(s.session, fixture.doc_id), fixture); s.store.dispose();
});
test('sessions/end-session-clears-only-owner', async () => {
  const s = setup(); await add(s); const other = s.store.createSession();
  const ticket = s.store.beginDocument(other)!; same(await s.store.storeDocument(other, ticket, fixture), { kind: 'stored' });
  s.store.endSession(s.session); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE);
  same(s.store.getDocument(other, fixture.doc_id), fixture); same(s.timers.size, 1); s.store.dispose();
});
test('sessions/cross-session-ticket-rejected', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!;
  same(await s.store.storeDocument(s.store.createSession(), ticket, fixture), UNAVAILABLE); s.store.dispose();
});
test('retention/absolute-boundary-and-no-read-renewal', async () => {
  const s = setup(); await add(s); stayActive(s); s.advance(TTL - 1); same(s.store.getDocument(s.session, fixture.doc_id), fixture);
  s.advance(TTL); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
test('retention/delayed-timer-access-denied', async () => {
  const s = setup(); await add(s); s.advance(TTL + 1, false);
  same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
test('retention/timer-removes-idle-document', async () => {
  const s = setup(); await add(s); s.advance(IDLE);
  same(s.timers.size, 0);
  // No get/store call may lazily remove the expired entry before this observation.
  // If the fired callback left it behind, endSession would cancel that stale entry.
  s.store.endSession(s.session);
  same(s.cancellations, 0); s.store.dispose();
});
test('retention/preparation-counts-toward-deadline', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!; stayActive(s); s.advance(TTL - 1);
  same(await s.store.storeDocument(s.session, ticket, fixture), { kind: 'stored' });
  s.advance(TTL); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); s.store.dispose();
});
test('retention/expired-preparation-rejected', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!; s.advance(TTL, false);
  same(await s.store.storeDocument(s.session, ticket, fixture), UNAVAILABLE); s.store.dispose();
});
test('retention/expires-during-validation', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!;
  const pending = s.store.storeDocument(s.session, ticket, fixture);
  s.advance(IDLE, false); // Cross the deadline while validation awaits; timers stay unfired.
  same(await pending, UNAVAILABLE);
  s.store.dispose(); same(s.timers.size, 0);
});
test('retention/replace-cannot-renew', async () => {
  const s = setup(); const ticket = await add(s); stayActive(s); s.advance(TTL - 1);
  same(await s.store.storeDocument(s.session, ticket, fixture), UNAVAILABLE);
  s.advance(TTL); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); s.store.dispose();
});
test('retention/duplicate-active-document-rejected', async () => {
  const s = setup(); await add(s); const ticket = s.store.beginDocument(s.session)!;
  same(await s.store.storeDocument(s.session, ticket, fixture), UNAVAILABLE); s.store.dispose();
});
test('retention/clock-rollback-disposes', async () => {
  const s = setup(); await add(s); s.advance(5, false); s.store.getDocument(s.session, fixture.doc_id);
  s.advance(4, false); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0);
});
test('retention/restart-loses-sessions', async () => {
  const s = setup(); await add(s); s.store.dispose(); const replacement = setup();
  same(replacement.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); replacement.store.dispose();
});
test('sessions/dispose-during-validation', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!;
  const pending = s.store.storeDocument(s.session, ticket, fixture); s.store.dispose();
  same(await pending, UNAVAILABLE); same(s.timers.size, 0);
});
test('sessions/concurrent-write-one-winner', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!;
  const results = await Promise.all([s.store.storeDocument(s.session, ticket, fixture), s.store.storeDocument(s.session, ticket, fixture)]);
  same(results.filter(r => r.kind === 'stored').length, 1); s.store.dispose();
});
test('sessions/invalid-native-input-safe', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!;
  same(await s.store.storeDocument(s.session, ticket, { ...fixture, text_sha256: '0'.repeat(64) }), UNAVAILABLE);
  same(await s.store.storeDocument(s.session, ticket, { get text() { throw new Error('PRIVATE_MARKER'); } }), UNAVAILABLE); s.store.dispose();
});
test('sessions/excess-codepoints-rejected', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!; const text = 'a'.repeat(100_001);
  const value = { ...fixture, text, text_sha256: createHash('sha256').update(text).digest('hex') };
  same(await s.store.storeDocument(s.session, ticket, value), UNAVAILABLE); s.store.dispose();
});
test('sessions/unknown-capability-no-ticket', () => { const s = setup(); same(s.store.beginDocument('unknown'), null); s.store.dispose(); });
test('sessions/explicit-delete', async () => {
  const s = setup(); await add(s); s.store.deleteDocument('unknown', fixture.doc_id);
  same(s.store.getDocument(s.session, fixture.doc_id), fixture);
  s.store.deleteDocument(s.session, fixture.doc_id); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); s.store.dispose();
});

function browser(store: MemorySessions) {
  const response = new Response();
  const capability = openBrowserSession(store, new Headers(), response.headers);
  const cookie = response.headers.getSetCookie()[0];
  const request = new Request('https://notelens.test/', { headers: { Cookie: cookie.split(';', 1)[0] } });
  return { capability, cookie, request, response };
}

test('browser/secure-cookie-and-existing-session', () => {
  const { store } = setup();
  const owner = browser(store);
  same(owner.cookie.split('; ').slice(1), ['Path=/', 'Secure', 'HttpOnly', 'SameSite=Strict']);
  same(owner.cookie.startsWith('__Host-notelens-session='), true);
  same(owner.response.headers.get('Cache-Control'), 'no-store');
  same(readBrowserSession(store, owner.request.headers), owner.capability);

  const response = new Response();
  same(openBrowserSession(store, owner.request.headers, response.headers), owner.capability);
  same(response.headers.getSetCookie(), []);
  store.dispose();
});

test('browser/rejects-invalid-ambiguous-and-unknown-cookies', () => {
  const { store } = setup();
  const owner = browser(store);
  const cookie = owner.request.headers.get('Cookie');
  for (const value of ['', '__Host-notelens-session=bad', '__Host-notelens-session=' + 'a'.repeat(43),
    `${cookie}; ${cookie}`, `__Host-notelens-session; ${cookie}`, `other=${owner.capability}`]) {
    same(readBrowserSession(store, new Headers({ Cookie: value })), null);
  }
  same(readBrowserSession(store, new Headers({ Cookie: `other=one; ${cookie}; third=two` })), owner.capability);
  store.dispose();
});

test('browser/distinct-cookies-isolate-documents', async () => {
  const s = setup();
  const owner = browser(s.store);
  const other = browser(s.store);
  await add({ ...s, session: owner.capability });
  same(s.store.getDocument(readBrowserSession(s.store, owner.request.headers)!, fixture.doc_id), fixture);
  same(s.store.getDocument(readBrowserSession(s.store, other.request.headers)!, fixture.doc_id), UNAVAILABLE);
  s.store.dispose();
});

test('browser/session-and-document-expire-with-cookie-still-present', async () => {
  const s = setup();
  const owner = browser(s.store);
  await add({ ...s, session: owner.capability });
  s.advance(IDLE);
  same(readBrowserSession(s.store, owner.request.headers), null);
  same(s.store.getDocument(owner.capability, fixture.doc_id), UNAVAILABLE);
  s.store.dispose();
});

test('browser/close-revokes-documents-and-cookie', async () => {
  const s = setup();
  const owner = browser(s.store);
  await add({ ...s, session: owner.capability });
  const response = new Response();
  closeBrowserSession(s.store, owner.request.headers, response.headers);
  same(response.headers.getSetCookie(), ['__Host-notelens-session=; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=0']);
  same(response.headers.get('Cache-Control'), 'no-store');
  same(readBrowserSession(s.store, owner.request.headers), null);
  same(s.store.getDocument(owner.capability, fixture.doc_id), UNAVAILABLE);
  same(s.timers.size, 1);
  s.store.dispose();
});

test('browser/process-replacement-rejects-stale-cookie', () => {
  const { store } = setup();
  const owner = browser(store);
  store.dispose();
  const fresh = setup();
  same(readBrowserSession(fresh.store, owner.request.headers), null);
  const response = new Response();
  const capability = openBrowserSession(fresh.store, owner.request.headers, response.headers);
  same(capability === owner.capability, false);
  same(response.headers.getSetCookie().length, 1);
  fresh.store.dispose();
});

test('retention/failed-access-and-cookie-lookup-do-not-reset-idle', async () => {
  const s = setup();
  const owner = browser(s.store);
  await add({ ...s, session: owner.capability });
  s.advance(IDLE - 1);
  same(readBrowserSession(s.store, owner.request.headers), owner.capability);
  same(s.store.getDocument(owner.capability, 'unknown'), UNAVAILABLE);
  s.advance(IDLE, false);
  same(readBrowserSession(s.store, owner.request.headers), null);
  same(s.store.getDocument(owner.capability, fixture.doc_id), UNAVAILABLE);
  s.store.dispose();
});

test('sessions/pending-reserves-slot-and-failure-releases-it', async () => {
  const s = setup();
  for (let i = 0; i < 2; i++) await add(s, { ...fixture, doc_id: randomUUID() });
  const ticket = s.store.beginDocument(s.session)!;
  same(s.store.beginDocument(s.session), null);
  const pending = s.store.storeDocument(s.session, ticket, {});
  s.store.cancelPreparation(s.session, ticket);
  same(s.store.beginDocument(s.session), null);
  same(await pending, UNAVAILABLE);
  await add(s);
  same(s.store.beginDocument(s.session), null);
  s.store.deleteDocument(s.session, fixture.doc_id);
  const next = s.store.beginDocument(s.session)!;
  s.store.cancelPreparation(s.session, next);
  same(typeof s.store.beginDocument(s.session), 'string');
  s.store.dispose();
});

const origin = 'https://notelens.test';
function callSession(store: MemorySessions, method = 'POST', headers: HeadersInit = { Origin: origin }, config = origin) {
  return handleSessionRequest(new Request(origin + '/api/session', { method, headers }), () => store, config);
}

test('routes/exact-origin-and-configuration-required', () => {
  const { store } = setup();
  for (const value of ['null', 'https://sub.notelens.test', 'http://notelens.test', 'https://notelens.test:444']) {
    for (const method of ['POST', 'DELETE']) {
      const response = callSession(store, method, { Origin: value });
      same(response.status, 403);
      same(response.headers.getSetCookie(), []);
      same(response.headers.get('Cache-Control'), 'no-store');
    }
  }
  same(callSession(store, 'POST', {}).status, 403);
  same(callSession(store, 'POST', { Origin: origin }, '').status, 503);
  same(callSession(store, 'POST', { Origin: origin }, 'http://notelens.test').status, 503);
  same(callSession(store, 'POST', { Origin: origin }, origin + '/path').status, 503);
  same(callSession(store, 'GET').status, 405);
  const previous = process.env.NOTELENS_MODE;
  try {
    process.env.NOTELENS_MODE = 'live';
    same(callSession(store).status, 503);
  } finally {
    if (previous === undefined) delete process.env.NOTELENS_MODE;
    else process.env.NOTELENS_MODE = previous;
    store.dispose();
  }
});

test('routes/rolling-rate-and-reuse-at-limit', () => {
  const s = setup();
  const first = callSession(s.store);
  const cookie = first.headers.getSetCookie()[0].split(';', 1)[0];
  same(first.status, 204);
  s.advance(5_000);
  for (let i = 0; i < 8; i++) same(callSession(s.store).status, 204);
  const limited = callSession(s.store);
  same(limited.status, 429);
  same(limited.headers.get('Retry-After'), '55');
  const reused = callSession(s.store, 'POST', { Origin: origin, Cookie: cookie });
  same(reused.status, 204);
  same(reused.headers.getSetCookie(), []);
  same(callSession(s.store, 'DELETE', { Origin: origin, Cookie: cookie }).status, 204);
  same(callSession(s.store).status, 429);
  s.advance(60_000);
  same(callSession(s.store).status, 204);
  same(callSession(s.store).status, 204);
  same(callSession(s.store).status, 429);
  s.store.dispose();
});

test('routes/capacity-preserves-existing-sessions', () => {
  const s = setup();
  for (let i = 1; i < 32; i++) {
    s.advance(Math.floor(i / 10) * 60_000);
    same(callSession(s.store).status, 204);
  }
  same(callSession(s.store).status, 503);
  same(s.store.hasSession(s.session), true);
  s.store.endSession(s.session);
  same(callSession(s.store).status, 204);
  s.store.dispose();
});
