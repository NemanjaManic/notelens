import { randomBytes } from 'node:crypto';
import { validateRecord } from '@notelens/contracts/v1';
import type { PreparedDocument } from '@notelens/contracts/v1';
import {
  DOCUMENT_LIFETIME_MS, MAX_ACTIVE_DOCUMENTS, MAX_ACTIVE_SESSIONS, MAX_DOCUMENT_CODE_POINTS,
  MAX_NEW_SESSIONS, SESSION_IDLE_MS, SESSION_LIFETIME_MS, SESSION_RATE_WINDOW_MS, sessionConfiguration,
} from '../config/session-policy.ts';

type Entry = { expiresAt: number; document: PreparedDocument | null; validating: boolean };
type Session = {
  deadline: number;
  lastActivity: number;
  entries: Map<string, Entry>;
  cancel: () => void;
};
export type SessionRuntime = {
  now: () => number;
  schedule: (callback: () => void, delayMs: number) => () => void;
};
const runtime: SessionRuntime = {
  now: () => performance.now(),
  schedule: (callback, delay) => {
    const timer = setTimeout(callback, delay);
    timer.unref();
    return () => clearTimeout(timer);
  },
};
export const UNAVAILABLE = Object.freeze({ kind: 'unavailable' as const,
  notice: 'The document is unavailable. Start a new submission.' });

export class SessionAdmissionError extends Error {
  readonly kind: 'rate' | 'capacity';
  readonly retryAfter?: number;

  constructor(kind: 'rate' | 'capacity', retryAfter?: number) {
    super(kind === 'rate' ? 'Too many new sessions. Try again shortly.' : 'All session slots are in use.');
    this.kind = kind;
    this.retryAfter = retryAfter;
  }
}

function sessionDeadline(session: Session): number {
  return Math.min(session.deadline, session.lastActivity + SESSION_IDLE_MS);
}

/** Server-only process memory core. Never serialize a store or expose session tokens in logs. */
export class MemorySessions {
  #sessions = new Map<string, Session>();
  #admissions: number[] = [];
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
      this.dispose();
      throw new Error('The session clock is unavailable.');
    }
    this.#lastTime = now;
    return now;
  }

  #activeSession(capability: string, now: number): Session | undefined {
    const session = this.#sessions.get(capability);
    if (!session || now < sessionDeadline(session)) return session;
    this.endSession(capability);
  }

  #scheduleExpiry(capability: string, session: Session, delay: number): void {
    session.cancel = this.#runtime.schedule(() => {
      if (this.#sessions.get(capability) !== session) return;
      let remaining: number;
      try {
        remaining = sessionDeadline(session) - this.#now();
      } catch {
        return; // Clock failure already disposed the store.
      }
      if (remaining <= 0) {
        session.cancel = () => {};
        this.endSession(capability);
      } else {
        this.#scheduleExpiry(capability, session, remaining);
      }
    }, delay);
  }

  createSession(): string {
    if (this.#closed) throw new Error('The session store is unavailable.');
    const now = this.#now();
    for (const capability of this.#sessions.keys()) this.#activeSession(capability, now);
    if (this.#sessions.size >= MAX_ACTIVE_SESSIONS) throw new SessionAdmissionError('capacity');
    this.#admissions = this.#admissions.filter(time => now - time < SESSION_RATE_WINDOW_MS);
    if (this.#admissions.length >= MAX_NEW_SESSIONS) {
      const retryAfter = Math.ceil((this.#admissions[0] + SESSION_RATE_WINDOW_MS - now) / 1000);
      throw new SessionAdmissionError('rate', retryAfter);
    }

    const capability = randomBytes(32).toString('base64url');
    const session: Session = {
      deadline: now + SESSION_LIFETIME_MS, lastActivity: now, entries: new Map(), cancel: () => {},
    };
    this.#scheduleExpiry(capability, session, SESSION_IDLE_MS);
    this.#sessions.set(capability, session);
    this.#admissions.push(now);
    return capability;
  }

  hasSession(capability: string): boolean {
    return this.#activeSession(capability, this.#now()) !== undefined;
  }

  recordActivity(capability: string): boolean {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    if (!session) return false;
    session.lastActivity = now;
    return true;
  }

  // The live session deadline always precedes or equals every document deadline.
  // A single session timer cleans up all of its documents and pending reservations.
  beginDocument(capability: string): string | null {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    if (!session || session.entries.size >= MAX_ACTIVE_DOCUMENTS) return null;
    if ([...session.entries.values()].some(entry => entry.document === null)) return null;
    const ticket = randomBytes(32).toString('base64url');
    session.entries.set(ticket, { expiresAt: now + DOCUMENT_LIFETIME_MS, document: null, validating: false });
    return ticket;
  }

  cancelPreparation(capability: string, ticket: string): void {
    const session = this.#sessions.get(capability);
    const entry = session?.entries.get(ticket);
    if (entry && !entry.document && !entry.validating) session?.entries.delete(ticket);
  }

  async storeDocument(capability: string, ticket: string, value: unknown): Promise<{ kind: 'stored' } | typeof UNAVAILABLE> {
    try {
      const now = this.#now();
      const session = this.#activeSession(capability, now);
      const entry = session?.entries.get(ticket);
      if (!session || !entry || entry.document || entry.validating || now >= entry.expiresAt) return UNAVAILABLE;

      entry.validating = true;
      try {
        const snapshot: unknown = structuredClone(value);
        const document = await validateRecord('PreparedDocument', snapshot);
        if (Array.from(document.text).length > MAX_DOCUMENT_CODE_POINTS) return UNAVAILABLE;
        const completedAt = this.#now();
        if (this.#activeSession(capability, completedAt) !== session || completedAt >= entry.expiresAt) return UNAVAILABLE;
        if ([...session.entries.values()].some(other => other.document?.doc_id === document.doc_id)) return UNAVAILABLE;
        entry.document = document;
        session.lastActivity = completedAt;
        return { kind: 'stored' };
      } finally {
        entry.validating = false;
        if (!entry.document) session.entries.delete(ticket);
      }
    } catch {
      return UNAVAILABLE;
    }
  }

  getDocument(capability: string, docId: string): PreparedDocument | typeof UNAVAILABLE {
    try {
      const now = this.#now();
      const session = this.#activeSession(capability, now);
      if (!session) return UNAVAILABLE;
      for (const entry of session.entries.values()) {
        if (now < entry.expiresAt && entry.document?.doc_id === docId) {
          const document = structuredClone(entry.document);
          session.lastActivity = now;
          return document;
        }
      }
    } catch {
      return UNAVAILABLE;
    }
    return UNAVAILABLE;
  }

  deleteDocument(capability: string, docId: string): void {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    if (!session) return;
    for (const [ticket, entry] of session.entries) {
      if (now < entry.expiresAt && entry.document?.doc_id === docId) {
        session.entries.delete(ticket);
        session.lastActivity = now;
        return;
      }
    }
  }

  endSession(capability: string): void {
    const session = this.#sessions.get(capability);
    if (!session) return;
    this.#sessions.delete(capability);
    session.cancel();
    session.entries.clear();
  }

  dispose(): void {
    this.#closed = true;
    for (const capability of this.#sessions.keys()) this.endSession(capability);
    this.#admissions = [];
  }
}
