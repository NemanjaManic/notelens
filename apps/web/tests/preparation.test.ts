import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { validateRecord } from '@notelens/contracts/v1';
import documents from '../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import { canonicalText } from '../src/lib/documents/canonical.ts';
import { BUILTIN_IDS, prepareBuiltin } from '../src/lib/documents/builtin.ts';
import { prepareSubmitted } from '../src/lib/documents/submitted.ts';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';
import { DOCUMENT_LIFETIME_MS as TTL, SESSION_IDLE_MS as IDLE } from '../src/lib/config/session-policy.ts';
const same = (a: unknown, b: unknown) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error('PREPARATION_CHECK_FAILED'); };
const sha = (text: string) => createHash('sha256').update(text, 'utf8').digest('hex');
const english = 'This synthetic medical report describes a scheduled follow-up. The patient reports no new symptoms today.';
function submission(body: string | Uint8Array<ArrayBuffer>) {
  return new Request('https://notelens.test/api/documents/submit', { method: 'POST', body });
}
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

test('submission/canonical-pasted-text-and-provenance', async () => {
  const s = setup();
  try {
    const raw = english + '\r\nThe patient met the care team at the Cafe\u0301.';
    const expected = english + '\nThe patient met the care team at the Caf\u00e9.';
    const result = await prepareSubmitted(s.store, s.session, submission(raw), 'text', 'public');
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    const stored = s.store.getDocument(s.session, result.docId);
    if ('kind' in stored) throw new Error('PREPARATION_CHECK_FAILED');
    same(stored.text, expected);
    same(stored.text_sha256, sha(expected));
    same(stored.source, { kind: 'public_text' });
    same(stored.language_validation, { outcome: 'accepted', language: 'en', policy_version: 'franc-6.2.0-en-v1', reason: null });
  } finally { s.store.dispose(); }
});

test('submission/reviewed-replay-requires-exact-synthetic-text', async () => {
  const s = setup();
  const text = 'No fever today.';
  const reviewed = [sha(text)];
  try {
    same(await prepareSubmitted(s.store, s.session, submission(text), 'text', 'synthetic'),
      { kind: 'rejected', code: 'inconclusive' });
    same(await prepareSubmitted(s.store, s.session, submission(text + '!'), 'text', 'synthetic', reviewed),
      { kind: 'rejected', code: 'inconclusive' });
    same(await prepareSubmitted(s.store, s.session, submission(text), 'text', 'public', reviewed),
      { kind: 'rejected', code: 'inconclusive' });
    const result = await prepareSubmitted(s.store, s.session, submission(text), 'text', 'synthetic', reviewed);
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    const stored = s.store.getDocument(s.session, result.docId);
    if ('kind' in stored) throw new Error('PREPARATION_CHECK_FAILED');
    same(stored.text, text);
    same(stored.text_sha256, reviewed[0]);
    same(stored.language_validation.policy_version, 'saved-replay-english-v1');
  } finally { s.store.dispose(); }
});

test('submission/failure-releases-session-reservation', async () => {
  const s = setup();
  try {
    same(await prepareSubmitted(s.store, s.session, submission(new Uint8Array([0xc3, 0x28])), 'text', 'synthetic'),
      { kind: 'rejected', code: 'invalid-unicode' });
    same(await prepareSubmitted(s.store, s.session, submission('Report.'), 'text', 'synthetic'),
      { kind: 'rejected', code: 'inconclusive' });
    same((await prepareSubmitted(s.store, s.session, submission(english), 'text', 'synthetic')).kind, 'prepared');
  } finally { s.store.dispose(); }
});

test('submission/streamed-pdf-byte-limit', async () => {
  const s = setup();
  try {
    const request = submission(new Uint8Array(2_097_153));
    same(request.headers.get('Content-Length'), null);
    same(await prepareSubmitted(s.store, s.session, request, 'pdf', 'synthetic'), { kind: 'rejected', code: 'pdf-too-large' });
  } finally { s.store.dispose(); }
});

test('submission/accepts-exact-codepoint-limit', async () => {
  const s = setup();
  try {
    const text = (english + ' ').repeat(1_000).slice(0, 100_000);
    same(Array.from(text).length, 100_000);
    const result = await prepareSubmitted(s.store, s.session, submission(text), 'text', 'synthetic');
    if (result.kind !== 'prepared') throw new Error('PREPARATION_CHECK_FAILED');
    const stored = s.store.getDocument(s.session, result.docId);
    if ('kind' in stored) throw new Error('PREPARATION_CHECK_FAILED');
    same(stored.text.length, 100_000);
    same(stored.text_sha256, sha(text));
  } finally { s.store.dispose(); }
});
