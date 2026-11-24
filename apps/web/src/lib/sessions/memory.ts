import { createHash, randomBytes, randomUUID } from 'node:crypto';
import { validateRecord } from '@notelens/contracts/v1';
import type { ExtractionResult, PreparedDocument } from '@notelens/contracts/v1';
import type { MockResult } from '../clients/mock-services.ts';
import type { RoutedAnswer } from '../routing/answer.ts';
import type { QuestionPlan } from '../routing/demo-questions.ts';
import {
  DOCUMENT_LIFETIME_MS, MAX_ACTIVE_DOCUMENTS, MAX_ACTIVE_SESSIONS, MAX_DOCUMENT_CODE_POINTS,
  MAX_HISTORY_BYTES, MAX_HISTORY_TURNS, MAX_NEW_SESSIONS, MAX_QUESTIONS_PER_WINDOW, MAX_QUESTIONS_PER_SESSION,
  QUESTION_RATE_WINDOW_MS, SESSION_IDLE_MS, SESSION_LIFETIME_MS, SESSION_RATE_WINDOW_MS, sessionConfiguration,
} from '../config/session-policy.ts';

export type QuestionTurn = { id: string; plan: QuestionPlan; answer: RoutedAnswer };
type StoredTurn = { turn: QuestionTurn; bytes: number };
type PendingQuestion = { id: string; docId: string; keep: boolean };
type Entry = { expiresAt: number; document: PreparedDocument | null; validating: boolean; history?: StoredTurn[];
  extraction?: Promise<MockResult<ExtractionResult>> };
type Session = {
  deadline: number;
  lastActivity: number;
  entries: Map<string, Entry>;
  cancel: () => void;
  questionAdmissions: number[];
  submittedQuestions: Set<string>;
  pendingQuestion?: PendingQuestion;
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

function activeDocument(session: Session, docId: string, now: number) {
  return [...session.entries.values()].find(entry => now < entry.expiresAt && entry.document?.doc_id === docId);
}

/** Server-only process memory core. Never serialize a store or expose session tokens in logs. */
export class MemorySessions {
  #sessions = new Map<string, Session>();
  #admissions: number[] = [];
  #closed = false;
  #lastTime = -Infinity;
  #runtime: SessionRuntime;
  #interactiveQuestions: boolean;

  constructor(options: { mode?: string; runtime?: SessionRuntime; interactiveQuestions?: boolean } = {}) {
    sessionConfiguration(options.mode);
    this.#runtime = options.runtime ?? runtime;
    this.#interactiveQuestions = options.interactiveQuestions ?? true;
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
      deadline: now + SESSION_LIFETIME_MS, lastActivity: now, entries: new Map(), cancel: () => {}, questionAdmissions: [], submittedQuestions: new Set(),
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
      const entry = activeDocument(session, docId, now);
      if (entry?.document) {
        session.lastActivity = now;
        return structuredClone(entry.document);
      }
    } catch {
      return UNAVAILABLE;
    }
    return UNAVAILABLE;
  }

  extractionOnce(capability: string, docId: string, dispatch: () => Promise<MockResult<ExtractionResult>>) {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    const entry = session && activeDocument(session, docId, now);
    if (!entry) return Promise.resolve({ kind: 'unavailable' } as const);
    return entry.extraction ??= dispatch();
  }

  beginQuestion(capability: string, docId: string, plan?: QuestionPlan) {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    if (!session || !activeDocument(session, docId, now)) return UNAVAILABLE;
    if (session.pendingQuestion) return { kind: 'busy' } as const;
    let questionKey: string | undefined;
    if (this.#interactiveQuestions) {
      if (!plan) throw new Error('A question plan is required.');
      const normalize = (text = '') => text.trim().replace(/\s+/gu, ' ').toLowerCase();
      questionKey = createHash('sha256').update(JSON.stringify([docId,
        normalize(plan.document), normalize(plan.literature),
        plan.document || plan.literature ? '' : normalize(plan.label)])).digest('hex');
      if (session.submittedQuestions.has(questionKey)) return { kind: 'duplicate' } as const;
      if (session.submittedQuestions.size >= MAX_QUESTIONS_PER_SESSION) return { kind: 'quota' } as const;
    }
    session.questionAdmissions = session.questionAdmissions.filter(time => now - time < QUESTION_RATE_WINDOW_MS);
    if (session.questionAdmissions.length >= MAX_QUESTIONS_PER_WINDOW) {
      const retryAfter = Math.ceil((session.questionAdmissions[0] + QUESTION_RATE_WINDOW_MS - now) / 1000);
      return { kind: 'rate', retryAfter } as const;
    }
    const id = randomUUID();
    session.pendingQuestion = { id, docId, keep: true };
    // Reserve before dispatch; failures, history clearing and document removal do not refund a slot.
    if (questionKey !== undefined) session.submittedQuestions.add(questionKey);
    session.questionAdmissions.push(now);
    session.lastActivity = now;
    return { kind: 'admitted', id } as const;
  }

  finishQuestion(capability: string, id: string, plan: QuestionPlan, answer: RoutedAnswer) {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    const pending = session?.pendingQuestion;
    if (!session || pending?.id !== id) return UNAVAILABLE;
    delete session.pendingQuestion;
    const entry = activeDocument(session, pending.docId, now);
    if (!entry || !pending.keep) return UNAVAILABLE;

    const turn = { id, plan, answer };
    const bytes = Buffer.byteLength(JSON.stringify(turn), 'utf8');
    if (bytes + 2 > MAX_HISTORY_BYTES) return { kind: 'transient', turn } as const;
    const history = entry.history ??= [];
    history.push({ turn: structuredClone(turn), bytes });
    // Count the enclosing array and delimiters along with all serialized turns.
    while (history.length > MAX_HISTORY_TURNS ||
        history.reduce((total, stored) => total + stored.bytes + 1, 1) > MAX_HISTORY_BYTES) {
      history.shift();
    }
    return { kind: 'saved', id } as const;
  }

  cancelQuestion(capability: string, id: string): void {
    const session = this.#sessions.get(capability);
    if (session?.pendingQuestion?.id === id) delete session.pendingQuestion;
  }

  questionHistory(capability: string, docId: string): QuestionTurn[] | null {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    const entry = session && activeDocument(session, docId, now);
    return entry ? structuredClone(entry.history?.map(({ turn }) => turn) ?? []) : null;
  }

  clearQuestionHistory(capability: string, docId: string): boolean {
    const now = this.#now();
    const session = this.#activeSession(capability, now);
    const entry = session && activeDocument(session, docId, now);
    if (!session || !entry) return false;
    delete entry.history;
    if (session.pendingQuestion?.docId === docId) session.pendingQuestion.keep = false;
    session.lastActivity = now;
    return true;
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
