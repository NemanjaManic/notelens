import { MAX_DOCUMENT_CODE_POINTS } from '../config/session-policy.ts';

export type PreparationRejection = { kind: 'rejected'; code: 'invalid-text' | 'invalid-unicode' | 'text-too-large' | 'empty-text' | 'unknown-builtin' | 'preparation-unavailable'; notice: string };
export function preparationRejected(code: PreparationRejection['code']): PreparationRejection {
  return { kind: 'rejected', code, notice: 'The example could not be prepared. Choose an available built-in example.' };
}

/** String preparation only; this does not admit arbitrary input or establish language. */
export function canonicalText(input: unknown): { kind: 'canonical'; text: string } | PreparationRejection {
  if (typeof input !== 'string') return preparationRejected('invalid-text');
  let count = 0;
  for (const point of input) {
    const unit = point.charCodeAt(0);
    if (point.length === 1 && unit >= 0xd800 && unit <= 0xdfff) return preparationRejected('invalid-unicode');
    if (++count > MAX_DOCUMENT_CODE_POINTS) return preparationRejected('text-too-large');
  }
  const text = input.replace(/\r\n?/g, '\n').normalize('NFC');
  if (Array.from(text).length > MAX_DOCUMENT_CODE_POINTS) return preparationRejected('text-too-large');
  if (!text.trim()) return preparationRejected('empty-text');
  return { kind: 'canonical', text };
}
