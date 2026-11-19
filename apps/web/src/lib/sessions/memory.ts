import { randomBytes } from 'node:crypto';
import { validateRecord } from '@notelens/contracts/v1';
import type { PreparedDocument } from '@notelens/contracts/v1';
import { DOCUMENT_LIFETIME_MS, MAX_DOCUMENT_CODE_POINTS, sessionConfiguration } from '../config/session-policy.ts';

type Entry = { expiresAt: number; document: PreparedDocument | null; cancel: () => void };
type Session = Map<string, Entry>;
export type SessionRuntime = {
  now: () => number;
  schedule: (callback: () => void, delayMs: number) => () => void;
};
const runtime: SessionRuntime = {
  now: () => performance.now(),
  schedule: (callback, delay) => {
    const timer = setTimeout(callback, delay); timer.unref();
    return () => clearTimeout(timer);
  },
};
export const UNAVAILABLE = Object.freeze({ kind: 'unavailable' as const,
  notice: 'The document is unavailable. Start a new submission.' });

/** Server-only process memory core. Never serialize a store or expose session tokens in logs. */
export class MemorySessions {
  #sessions = new Map<string, Session>();
  #closed = false;
  #lastTime = -Infinity;
  #runtime: SessionRuntime;

  constructor(options: { mode?: string; runtime?: SessionRuntime } = {}) {
    sessionConfiguration(options.mode);
    this.#runtime = options.runtime ?? runtime;
  }

  #now(): number {
    const now = this.#runtime.now();
    if (!Number.isFinite(now) || now < this.#lastTime) {
      this.dispose(); throw new Error('The session clock is unavailable.');
    }
    this.#lastTime = now;
    return now;
  }

  createSession(): string {
    if (this.#closed) throw new Error('The session store is unavailable.');
    const capability = randomBytes(32).toString('base64url');
    this.#sessions.set(capability, new Map());
    return capability;
  }

  // Called before preparation starts: validation/preparation time cannot renew retention.
  beginDocument(capability: string): string | null {
    const session = this.#sessions.get(capability);
    if (!session || this.#closed) return null;
    const now = this.#now();
    const ticket = randomBytes(32).toString('base64url');
    const entry: Entry = { expiresAt: now + DOCUMENT_LIFETIME_MS, document: null, cancel: () => {} };
    session.set(ticket, entry);
    const expire = () => {
      if (session.get(ticket) !== entry) return;
      try {
        const remaining = entry.expiresAt - this.#now();
        if (remaining > 0) { entry.cancel = this.#runtime.schedule(expire, remaining); return; }
      } catch { /* Clock failure disposes all entries. */ }
      entry.document = null; session.delete(ticket);
    };
    entry.cancel = this.#runtime.schedule(expire, DOCUMENT_LIFETIME_MS);
    return ticket;
  }

  async storeDocument(capability: string, ticket: string, value: unknown): Promise<{ kind: 'stored' } | typeof UNAVAILABLE> {
    const session = this.#sessions.get(capability);
    const entry = session?.get(ticket);
    if (!session || !entry || entry.document) return UNAVAILABLE;
    try {
      if (this.#now() >= entry.expiresAt) { this.#remove(session, ticket); return UNAVAILABLE; }
      // Validate a private snapshot so callers cannot alter content during an await.
      const snapshot: unknown = structuredClone(value);
      const document = await validateRecord('PreparedDocument', snapshot);
      if (Array.from(document.text).length > MAX_DOCUMENT_CODE_POINTS) return UNAVAILABLE;
      if (this.#closed || this.#sessions.get(capability) !== session || session.get(ticket) !== entry ||
        this.#now() >= entry.expiresAt || entry.document) return UNAVAILABLE;
      if ([...session.values()].some(other => other.document?.doc_id === document.doc_id)) return UNAVAILABLE;
      entry.document = document;
      return { kind: 'stored' };
    } catch { return UNAVAILABLE; }
  }

  getDocument(capability: string, docId: string): PreparedDocument | typeof UNAVAILABLE {
    const session = this.#sessions.get(capability);
    if (!session) return UNAVAILABLE;
    try {
      const now = this.#now();
      for (const [ticket, entry] of session) {
        if (now >= entry.expiresAt) { this.#remove(session, ticket); continue; }
        if (entry.document?.doc_id === docId) return structuredClone(entry.document);
      }
    } catch { return UNAVAILABLE; }
    return UNAVAILABLE;
  }

  deleteDocument(capability: string, docId: string): void {
    const session = this.#sessions.get(capability);
    if (session) for (const [ticket, entry] of session) if (entry.document?.doc_id === docId) this.#remove(session, ticket);
  }

  #remove(session: Session, ticket: string): void {
    const entry = session.get(ticket);
    if (entry) { entry.cancel(); entry.document = null; session.delete(ticket); }
  }

  endSession(capability: string): void {
    const session = this.#sessions.get(capability);
    if (session) for (const ticket of session.keys()) this.#remove(session, ticket);
    this.#sessions.delete(capability);
  }

  dispose(): void {
    for (const capability of this.#sessions.keys()) this.endSession(capability);
    this.#closed = true;
  }
}
