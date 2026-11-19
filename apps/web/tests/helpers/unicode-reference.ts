// Test-local demonstrations only; production preparation/highlighting has separate gates.
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { validateRecord, ContractValidationError } from '@notelens/contracts/v1';
import type { Issue, PreparedDocument, Records } from '@notelens/contracts/v1';

export const root = fileURLToPath(new URL('../../../../', import.meta.url));
const read = (name: string): any => JSON.parse(readFileSync(new URL(name, new URL('../../../../', import.meta.url)), 'utf8'));
export const vectors = read('apps/web/tests/fixtures/unicode-vectors.json');
const documents = read('contracts/v1/fixtures/documents.json');
const payloads = read('contracts/v1/fixtures/payloads.json');
const manifest = read('contracts/v1/fixtures/manifest.json');
const references = read('contracts/v1/fixtures/references.json');
export const digest = (text: string): string => createHash('sha256').update(text, 'utf8').digest('hex');

function scalars(text: string): string[] {
  const chars = Array.from(text);
  if (chars.some(c => c.length === 1 && c.charCodeAt(0) >= 0xd800 && c.charCodeAt(0) <= 0xdfff)) throw new RangeError('Invalid scalar text');
  return chars;
}

export function prepareExample(text: string): string {
  scalars(text);
  return text.replace(/\r\n?/g, '\n').normalize('NFC');
}

function index(value: unknown, maximum: number): asserts value is number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0 || value > maximum) throw new RangeError('Invalid boundary');
}

export function toUtf16(text: string, codepoint: unknown): number {
  const chars = scalars(text);
  index(codepoint, chars.length);
  return chars.slice(0, codepoint).join('').length;
}

export function toCodepoint(text: string, utf16: unknown): number {
  const chars = scalars(text);
  index(utf16, text.length);
  let units = 0, count = 0;
  for (const char of chars) {
    if (units === utf16) return count;
    units += char.length; count++;
    if (units > utf16) throw new RangeError('Boundary splits surrogate pair');
  }
  return count;
}

export type Result = { id: string; passed: true; [key: string]: unknown };
export type Case = { id: string; run: () => Promise<Omit<Result, 'id' | 'passed'>> };
const equal = (actual: unknown, expected: unknown, id: string) =>
  assert.ok(JSON.stringify(actual) === JSON.stringify(expected), id + ': literal expectation mismatch');
async function issues(definition: keyof Records, value: unknown, context: any = {}): Promise<Issue[]> {
  try { await validateRecord(definition, value, context); return []; }
  catch (error) { if (error instanceof ContractValidationError) return error.issues; throw error; }
}

export function cases(): Case[] {
  assert.equal(vectors.format, 'notelens-f012-vectors-v1');
  assert.equal(realpathSync(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))),
    realpathSync(new URL('contracts/generated/typescript/v1.mjs', new URL('../../../../', import.meta.url))));
  const result: Case[] = [];
  const add = (id: string, run: Case['run']) => result.push({ id, run });
  for (const v of vectors.preparation) add('prepare-' + v.id, async () => {
    const text = prepareExample(v.raw);
    equal(text, v.canonical, v.id); equal(prepareExample(text), text, v.id);
    equal(digest(text), v.sha256, v.id); equal(scalars(text).length, v.code_points, v.id);
    equal(text.length, v.utf16_units, v.id);
    const document = { ...structuredClone(documents.offset), doc_id: 'unicode-' + v.id, text, text_sha256: v.sha256 };
    equal(await issues('PreparedDocument', document), [], v.id);
    return { sha256: v.sha256, code_points: v.code_points, utf16_units: v.utf16_units };
  });
  for (const name of vectors.canonical_documents) add('document-' + name, async () => {
    const document = documents[name]; const original = JSON.stringify(document);
    equal(digest(document.text), document.text_sha256, name);
    equal(await issues('PreparedDocument', document), [], name);
    equal(JSON.stringify(document), original, name);
    return { sha256: document.text_sha256, code_points: scalars(document.text).length, utf16_units: document.text.length };
  });
  for (const name of vectors.metadata_payloads) add('metadata-' + name, async () => {
    const record = payloads[name]; const original = JSON.stringify(record);
    const c = manifest.cases.find((c: any) => c.id === name);
    equal(await issues(c.definition, record, { document: documents[c.document], reference: references[c.reference] }), [], name);
    equal(JSON.stringify(record), original, name);
    return { issues: [] };
  });
  const document: PreparedDocument = documents.offset;
  for (const v of vectors.spans) add('span-' + v.id, async () => {
    const start = toUtf16(document.text, v.start), end = toUtf16(document.text, v.end);
    equal([start, end], v.utf16, v.id);
    equal(document.text.slice(start, end), v.quote, v.id);
    equal([toCodepoint(document.text, start), toCodepoint(document.text, end)], [v.start, v.end], v.id);
    equal(await issues('EvidenceSpan', { start: v.start, end: v.end, quote: v.quote }, { document }), [], v.id);
    if (v.id === 'second-occurrence') {
      // The first matching quote is valid evidence but is the wrong requested occurrence.
      assert.ok(document.text.indexOf(v.quote) !== start, 'Second occurrence must not use first-match search');
      assert.ok(document.text.slice(v.start, v.end) !== v.quote, 'Raw code points are not native indices');
    }
    return { codepoints: [v.start, v.end], utf16: v.utf16 };
  });
  for (const v of vectors.boundaries) add('boundary-' + v.codepoint, async () => {
    equal(toUtf16(document.text, v.codepoint), v.utf16, 'boundary');
    equal(toCodepoint(document.text, v.utf16), v.codepoint, 'boundary');
    return { codepoint: v.codepoint, utf16: v.utf16 };
  });
  for (const kind of ['codepoint', 'utf16']) vectors.invalid_indices[kind].forEach((value: unknown, i: number) => {
    add(`invalid-${kind}-${i}`, async () => {
      assert.throws(() => (kind === 'codepoint' ? toUtf16 : toCodepoint)(document.text, value), RangeError);
      return { rejected: true };
    });
  });
  for (const [id, text] of [['high', '\ud800'], ['low', '\udc00']]) add('helper-surrogate-' + id, async () => {
    assert.throws(() => prepareExample(text), RangeError);
    assert.throws(() => toUtf16(text, 0), RangeError);
    assert.throws(() => toCodepoint(text, 0), RangeError);
    return { rejected: true };
  });
  for (const v of vectors.negatives) add('negative-' + v.id, async () => {
    const definition = v.kind === 'span' ? 'EvidenceSpan' : v.kind === 'identity' ? 'ClassificationResult' : 'PreparedDocument';
    const base = v.kind === 'span' ? { start: 47, end: 61, quote: 'No chest pain.' }
      : v.kind === 'identity' ? payloads['classification-supported'] : document;
    const value = { ...structuredClone(base), ...v.patch };
    const actual = await issues(definition, value, v.kind === 'document' ? {} : { document });
    equal(actual, v.expected, v.id);
    return { issues: actual };
  });
  assert.ok(result.length > 0 && new Set(result.map(c => c.id)).size === result.length, 'Case IDs must be nonempty and unique');
  return result;
}
