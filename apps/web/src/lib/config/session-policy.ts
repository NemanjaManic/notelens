export const DOCUMENT_LIFETIME_MS = 60 * 60 * 1000;
export const MAX_PDF_BYTES = 2_097_152;
export const MAX_DOCUMENT_CODE_POINTS = 100_000;
export const SESSION_LIFETIME_MS = 60 * 60 * 1000;
export const SESSION_IDLE_MS = 30 * 60 * 1000;
export const MAX_ACTIVE_SESSIONS = 32;
export const MAX_NEW_SESSIONS = 10;
export const SESSION_RATE_WINDOW_MS = 60_000;
export const MAX_ACTIVE_DOCUMENTS = 3;
export const QUESTION_RATE_WINDOW_MS = 60_000;
export const MAX_QUESTIONS_PER_WINDOW = 10;
export const MAX_QUESTIONS_PER_SESSION = 5;

export function interactiveQuestionsEnabled(env: NodeJS.ProcessEnv = process.env): boolean {
  if (env.NOTELENS_QUESTION_PROFILE === undefined) return true;
  if (env.NOTELENS_QUESTION_PROFILE === 'final-evaluation' &&
      (env.NOTELENS_BOUNDED_EVALUATION === 'offline' || env.NOTELENS_BOUNDED_EVALUATION === 'provider-backed')) return false;
  throw new Error('The question profile configuration is unavailable.');
}
export const MAX_HISTORY_TURNS = 5;
export const MAX_HISTORY_BYTES = 32 * 1024;

export function sessionConfiguration(mode: string | undefined = process.env.NOTELENS_MODE) {
  if (mode !== undefined && mode !== 'mock') {
    throw new Error('Live execution is unavailable. Operational approval and configuration are required.');
  }
  return Object.freeze({
    mode: 'mock' as const,
    documentLifetimeMs: DOCUMENT_LIFETIME_MS,
    maxPdfBytes: MAX_PDF_BYTES,
    maxDocumentCodePoints: MAX_DOCUMENT_CODE_POINTS,
    sessionLifetimeMs: SESSION_LIFETIME_MS,
    sessionIdleMs: SESSION_IDLE_MS,
    maxActiveSessions: MAX_ACTIVE_SESSIONS,
    maxNewSessions: MAX_NEW_SESSIONS,
    sessionRateWindowMs: SESSION_RATE_WINDOW_MS,
    maxActiveDocuments: MAX_ACTIVE_DOCUMENTS,
    maxPendingPreparations: 1,
    storedChatTurns: MAX_HISTORY_TURNS,
    automaticRetries: 0,
  });
}

export function sessionOrigin(value: string | undefined): string {
  const url = new URL(value ?? '');
  const loopback = url.protocol === 'http:' && url.hostname === 'localhost';
  if (value !== url.origin || (url.protocol !== 'https:' && !loopback)) {
    throw new Error('A trusted browser origin is required.');
  }
  return url.origin;
}
