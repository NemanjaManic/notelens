import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { validateRecord } from '@notelens/contracts/v1';
import documents from '../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import { canonicalText } from '../src/lib/documents/canonical.ts';
import { BUILTIN_IDS, prepareBuiltin } from '../src/lib/documents/builtin.ts';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';
import { DOCUMENT_LIFETIME_MS as TTL, SESSION_IDLE_MS as IDLE } from '../src/lib/config/session-policy.ts';
const same = (a: unknown, b: unknown) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error('PREPARATION_CHECK_FAILED'); };
const sha = (text: string) => createHash('sha256').update(text, 'utf8').digest('hex');
function setup(Store: typeof MemorySessions = MemorySessions) {
  let time = 0;
  let cancellations = 0;
  const timers = new Set<{ callback: () => void; at: number }>();
  const store = new Store({ mode: 'mock', runtime: { now: () => time, schedule: (callback, delay) => {
    const timer = { callback, at: time + delay }; timers.add(timer);
    return () => { cancellations++; timers.delete(timer); };
  } } });
  const session = store.createSession();
  return { store, session, timers, get cancellations() { return cancellations; }, advance(to: number, fire = true) {
    time = to;
    if (fire) for (const timer of [...timers]) if (timer.at <= time) { timers.delete(timer); timer.callback(); }
  } };
}
for (const [id, raw, expected] of [
  ['lf', 'A\nB', 'A\nB'], ['crlf', 'A\r\nB\r\n', 'A\nB\n'], ['cr', 'A\rB', 'A\nB'],
  ['mixed', 'A\r\nB\rC\nD', 'A\nB\nC\nD'], ['nfc', 'Cafe\u0301', 'Caf\u00e9'],
  ['spaces', '  A\n\nB  ', '  A\n\nB  '], ['bom', '\ufeffA', '\ufeffA'],
  ['non-bmp', 'Demo 🩺\r\nA', 'Demo 🩺\nA'], ['repeated', 'same same', 'same same'],
] as const) test(`canonical/${id}`, () => same(canonicalText(raw), { kind: 'canonical', text: expected }));
for (const [id, raw, code] of [
  ['high-surrogate', '\ud800', 'invalid-unicode'], ['low-surrogate', '\udfff', 'invalid-unicode'],
  ['trailing-surrogate', 'A\ud800', 'invalid-unicode'], ['empty', '', 'empty-text'],
  ['whitespace', ' \r\n\t ', 'empty-text'], ['non-string', { text: 'PRIVATE_MARKER' }, 'invalid-text'],
  ['null', null, 'invalid-text'], ['undefined', undefined, 'invalid-text'],
] as const) test(`canonical/reject-${id}`, () => {
  const result = canonicalText(raw); same(result.kind, 'rejected');
  if (result.kind === 'rejected') { same(result.code, code); same(JSON.stringify(result).includes('PRIVATE_MARKER'), false); }
});
test('canonical/exact-codepoint-limit', () => {
  const text = 'a'.repeat(100_000); same(canonicalText(text), { kind: 'canonical', text });
});
test('canonical/non-bmp-limit-is-not-utf16', () => {
  const text = '🩺'.repeat(100_000); same(canonicalText(text), { kind: 'canonical', text });
});
test('canonical/reject-raw-excess-before-nfc', () => {
  const result = canonicalText('e\u0301'.repeat(50_001)); same(result.kind === 'rejected' && result.code, 'text-too-large');
});
test('canonical/reject-nfc-expansion-excess', () => {
  const result = canonicalText('\u0344'.repeat(50_001)); same(result.kind === 'rejected' && result.code, 'text-too-large');
});
test('canonical/reject-codepoint-excess-without-truncation', () => {
  const result = canonicalText('a'.repeat(100_001)); same(result.kind === 'rejected' && result.code, 'text-too-large');
});
for (const id of BUILTIN_IDS) test(`builtin/${id}`, async () => {
  const s = setup();
  try {
    const outcome = await prepareBuiltin(s.store, s.session, id); same(outcome.kind, 'prepared');
    if (outcome.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    const doc = s.store.getDocument(s.session, outcome.docId);
    if ('kind' in doc) throw new Error('PREPARATION_CHECK_FAILED');
    await validateRecord('PreparedDocument', doc);
    same(doc.text, documents[id].text); same(doc.text_sha256, sha(doc.text));
    same(doc.text_sha256, documents[id].text_sha256); same(doc.source, documents[id].source);
    same(doc.language_validation, documents[id].language_validation);
    same(doc.doc_id === documents[id].doc_id, false);
    same(/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/.test(doc.doc_id), true);
  } finally { s.store.dispose(); }
});
test('builtin/fresh-identities-same-canonical-digest', async () => {
  const s = setup();
  try {
    const a = await prepareBuiltin(s.store, s.session, 'offset'); const b = await prepareBuiltin(s.store, s.session, 'offset');
    if (a.kind !== 'prepared' || b.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    same(a.docId === b.docId, false);
    same(Object.keys(a).sort(), ['docId', 'kind']);
  } finally { s.store.dispose(); }
});
for (const id of ['__proto__', 'constructor', '../../secrets', 'PRIVATE_MARKER', { text: 'PRIVATE_MARKER' }]) test(`builtin/reject-${typeof id === 'string' && !id.includes('/') ? id : typeof id}`, async () => {
  const s = setup();
  try {
    const result = await prepareBuiltin(s.store, s.session, id);
    same(result.kind, 'rejected'); same(JSON.stringify(result).includes('PRIVATE_MARKER'), false); same(s.timers.size, 1);
  } finally { s.store.dispose(); }
});
test('handoff/unknown-capability-unavailable', async () => {
  const s = setup(); try { same(await prepareBuiltin(s.store, 'PRIVATE_MARKER', 'offset'), UNAVAILABLE); same(s.timers.size, 1); } finally { s.store.dispose(); }
});
test('handoff/cross-session-document-denied', async () => {
  const s = setup(); try {
    const result = await prepareBuiltin(s.store, s.session, 'offset');
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    same(s.store.getDocument(s.store.createSession(), result.docId), UNAVAILABLE);
  } finally { s.store.dispose(); }
});
test('handoff/deadline-starts-before-validation', async () => {
  const s = setup(); try {
    const pending = prepareBuiltin(s.store, s.session, 'offset'); s.advance(TTL, false);
    same(await pending, UNAVAILABLE);
  } finally { s.store.dispose(); }
});
test('handoff/preparation-time-is-not-renewed', async () => {
  const s = setup(); try {
    const pending = prepareBuiltin(s.store, s.session, 'offset');
    s.advance(IDLE - 1);
    same(s.store.recordActivity(s.session), true);
    s.advance(TTL - 2);
    same(s.store.recordActivity(s.session), true);
    s.advance(TTL - 1);
    const result = await pending;
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    s.advance(TTL); same(s.store.getDocument(s.session, result.docId), UNAVAILABLE);
  } finally { s.store.dispose(); }
});
test('handoff/idle-expiry-precedes-teardown', async () => {
  const s = setup(); await prepareBuiltin(s.store, s.session, 'offset'); s.advance(TTL);
  s.store.endSession(s.session); same(s.cancellations, 0); s.store.dispose();
});
test('handoff/session-ended-during-preparation', async () => {
  const s = setup(); const pending = prepareBuiltin(s.store, s.session, 'offset'); s.store.endSession(s.session);
  same(await pending, UNAVAILABLE); same(s.timers.size, 0); s.store.dispose();
});
test('handoff/expiry-after-store-before-receipt', async () => {
  let expire = () => {};
  class ExpiringStore extends MemorySessions {
    override async storeDocument(...args: Parameters<MemorySessions['storeDocument']>) {
      const result = await super.storeDocument(...args); expire(); return result;
    }
  }
  const s = setup(ExpiringStore); expire = () => s.advance(TTL, false);
  try { same(await prepareBuiltin(s.store, s.session, 'offset'), UNAVAILABLE); } finally { s.store.dispose(); }
});
test('handoff/storage-rejection-does-not-return-prepared', async () => {
  class RejectingStore extends MemorySessions {
    override async storeDocument() { return UNAVAILABLE; }
  }
  const s = setup(RejectingStore);
  try { same(await prepareBuiltin(s.store, s.session, 'offset'), UNAVAILABLE); } finally { s.store.dispose(); }
});
test('handoff/restart-loses-prepared-document', async () => {
  const s = setup(); const result = await prepareBuiltin(s.store, s.session, 'offset'); s.store.dispose();
  if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
  const replacement = setup(); same(replacement.store.getDocument(s.session, result.docId), UNAVAILABLE); replacement.store.dispose();
});
test('builtin/fixture-and-return-mutations-isolated', async () => {
  const before = JSON.stringify(documents); const s = setup();
  try {
    const result = await prepareBuiltin(s.store, s.session, 'offset');
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    const value = s.store.getDocument(s.session, result.docId);
    if ('kind' in value) throw new Error('PREPARATION_CHECK_FAILED');
    value.text = 'PRIVATE_MARKER'; same(JSON.stringify(documents), before);
    const again = s.store.getDocument(s.session, result.docId); same('text' in again && again.text, documents.offset.text);
  } finally { s.store.dispose(); }
});
test('mode/live-rejected-without-provider-or-session-work', async () => {
  const s = setup(); const prior = process.env.NOTELENS_MODE;
  try { process.env.NOTELENS_MODE = 'live'; const result = await prepareBuiltin(s.store, s.session, 'offset');
    same(result.kind, 'rejected'); same(s.timers.size, 1);
  } finally { if (prior === undefined) delete process.env.NOTELENS_MODE; else process.env.NOTELENS_MODE = prior; s.store.dispose(); }
});
