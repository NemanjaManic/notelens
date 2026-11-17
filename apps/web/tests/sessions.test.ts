import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';
import type { SessionRuntime } from '../src/lib/sessions/memory.ts';
import { DOCUMENT_LIFETIME_MS as TTL, sessionConfiguration } from '../src/lib/config/session-policy.ts';

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
test('config/approved-limits-only', () => same(sessionConfiguration('mock'), {
  mode: 'mock', documentLifetimeMs: 3_600_000, maxPdfBytes: 2_097_152, maxDocumentCodePoints: 100_000,
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
  const s = setup(); await add(s); s.advance(TTL - 1); same(s.store.getDocument(s.session, fixture.doc_id), fixture);
  s.advance(TTL); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
test('retention/delayed-timer-access-denied', async () => {
  const s = setup(); await add(s); s.advance(TTL + 1, false);
  same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
test('retention/timer-removes-idle-document', async () => {
  const s = setup(); await add(s); s.advance(TTL);
  same(s.timers.size, 0);
  // No get/store call may lazily remove the expired entry before this observation.
  // If the fired callback left it behind, endSession would cancel that stale entry.
  s.store.endSession(s.session);
  same(s.cancellations, 0); s.store.dispose();
});
test('retention/preparation-counts-toward-deadline', async () => {
  const s = setup(); const ticket = s.store.beginDocument(s.session)!; s.advance(TTL - 1);
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
  s.advance(TTL, false); // Cross the deadline while validation awaits; timers stay unfired.
  same(await pending, UNAVAILABLE);
  s.store.dispose(); same(s.timers.size, 0);
});
test('retention/replace-cannot-renew', async () => {
  const s = setup(); const ticket = await add(s); s.advance(TTL - 1);
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
  s.store.deleteDocument(s.session, fixture.doc_id); same(s.store.getDocument(s.session, fixture.doc_id), UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
