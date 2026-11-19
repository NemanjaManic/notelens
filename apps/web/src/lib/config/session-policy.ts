// Approved limits only. No timeout, retry, history, rate or spending defaults.
export const DOCUMENT_LIFETIME_MS = 60 * 60 * 1000;
export const MAX_PDF_BYTES = 2_097_152;
export const MAX_DOCUMENT_CODE_POINTS = 100_000;

export function sessionConfiguration(mode: string | undefined = process.env.NOTELENS_MODE) {
  if (mode !== undefined && mode !== 'mock') {
    throw new Error('Live execution is unavailable. Operational approval and configuration are required.');
  }
  return Object.freeze({ mode: 'mock' as const, documentLifetimeMs: DOCUMENT_LIFETIME_MS,
    maxPdfBytes: MAX_PDF_BYTES, maxDocumentCodePoints: MAX_DOCUMENT_CODE_POINTS });
}
