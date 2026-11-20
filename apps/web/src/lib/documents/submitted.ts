import { MAX_DOCUMENT_CODE_POINTS, MAX_PDF_BYTES } from '../config/session-policy.ts';
import type { MemorySessions } from '../sessions/memory.ts';
import { UNAVAILABLE } from '../sessions/memory.ts';
import { canonicalText } from './canonical.ts';
import { englishLanguage, SUBMITTED_LANGUAGE_POLICY } from './language.ts';
import { pdfText } from './pdf.ts';
import { storePreparedDocument } from './prepared.ts';

export const inputErrors = {
  'invalid-text': 'Paste valid English text.',
  'invalid-unicode': 'The text contains invalid Unicode.',
  'empty-text': 'Paste text before opening a document.',
  'text-too-large': 'The document exceeds 100,000 Unicode code points.',
  'pdf-too-large': 'The PDF exceeds 2 MiB.',
  'no-text': 'This PDF has no selectable text. Use a text-based PDF or paste the text.',
  'invalid-pdf': 'The PDF could not be read. Choose a valid, unlocked text-based PDF.',
  'unsupported': 'Only English documents are supported.',
  'inconclusive': 'English could not be verified. Try a longer passage of English text.',
} as const;
type InputError = keyof typeof inputErrors;
type Rejection = { kind: 'rejected'; code: InputError };
type Input = 'text' | 'pdf';

async function boundedBody(request: Request, limit: number): Promise<Uint8Array<ArrayBuffer> | null> {
  if (Number(request.headers.get('Content-Length')) > limit) return null;
  if (!request.body) return new Uint8Array(0);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > limit) {
        void reader.cancel().catch(() => {});
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return bytes;
}

async function readText(request: Request, input: Input): Promise<{ kind: 'text'; text: string } | Rejection> {
  const bytes = await boundedBody(request, input === 'pdf' ? MAX_PDF_BYTES : MAX_DOCUMENT_CODE_POINTS * 4);
  if (!bytes) return { kind: 'rejected', code: input === 'pdf' ? 'pdf-too-large' : 'text-too-large' };
  if (input === 'pdf') {
    const result = await pdfText(bytes);
    if (result.kind === 'text') return result;
    return { kind: 'rejected', code: result.kind === 'too-large' ? 'text-too-large' : result.kind };
  }
  try {
    return { kind: 'text', text: new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes) };
  } catch {
    return { kind: 'rejected', code: 'invalid-unicode' };
  }
}

export async function prepareSubmitted(store: MemorySessions, owner: string, request: Request, input: Input, scope: 'public' | 'synthetic') {
  const ticket = store.beginDocument(owner);
  if (!ticket) return UNAVAILABLE;
  try {
    const raw = await readText(request, input);
    if (raw.kind === 'rejected') return raw;
    const canonical = canonicalText(raw.text);
    if (canonical.kind === 'rejected') {
      const code = canonical.code === 'unknown-builtin' || canonical.code === 'preparation-unavailable' ? 'invalid-text' : canonical.code;
      return { kind: 'rejected', code } satisfies Rejection;
    }
    const english = englishLanguage(canonical.text);
    if (english !== 'accepted') return { kind: 'rejected', code: english } satisfies Rejection;
    const source = input === 'pdf' ? 'text_pdf' : scope === 'public' ? 'public_text' : 'synthetic_text';
    return await storePreparedDocument(store, owner, ticket, canonical.text, { kind: source }, {
      outcome: 'accepted', language: 'en', policy_version: SUBMITTED_LANGUAGE_POLICY, reason: null,
    });
  } finally {
    store.cancelPreparation(owner, ticket);
  }
}
