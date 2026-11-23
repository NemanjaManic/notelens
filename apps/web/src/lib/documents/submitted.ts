import { createHash } from 'node:crypto';
import { MAX_DOCUMENT_CODE_POINTS, MAX_PDF_BYTES } from '../config/session-policy.ts';
import { boundedBody } from '../http/bounded-body.ts';
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

export function submissionByteLimit(input: Input): number {
  return input === 'pdf' ? MAX_PDF_BYTES : MAX_DOCUMENT_CODE_POINTS * 4;
}

async function readText(request: Request, input: Input): Promise<{ kind: 'text'; text: string } | Rejection> {
  const bytes = await boundedBody(request, submissionByteLimit(input));
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

export async function prepareSubmitted(
  store: MemorySessions, owner: string, request: Request, input: Input, scope: 'public' | 'synthetic',
  reviewedReplayHashes?: readonly string[],
) {
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
    const reviewedReplay = input === 'text' && scope === 'synthetic' && reviewedReplayHashes?.includes(
      createHash('sha256').update(canonical.text, 'utf8').digest('hex'),
    );
    if (!reviewedReplay) {
      const english = englishLanguage(canonical.text);
      if (english !== 'accepted') return { kind: 'rejected', code: english } satisfies Rejection;
    }
    const source = input === 'pdf' ? 'text_pdf' : scope === 'public' ? 'public_text' : 'synthetic_text';
    return await storePreparedDocument(store, owner, ticket, canonical.text, { kind: source }, {
      outcome: 'accepted', language: 'en',
      policy_version: reviewedReplay ? 'saved-replay-english-v1' : SUBMITTED_LANGUAGE_POLICY, reason: null,
    });
  } finally {
    store.cancelPreparation(owner, ticket);
  }
}
