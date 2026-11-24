import { DOCUMENT_LIFETIME_MS } from '../config/session-policy.ts';

export type EvaluationProfile = 'offline' | 'provider-backed';
const reviewedScopes = ['document', 'literature', 'both', 'out-of-scope'] as const;
export type ReviewedQuestionHashes = Readonly<Record<typeof reviewedScopes[number], readonly string[]>>;
export const boundedOperations = ['extract', 'document-answer', 'literature-answer'] as const;
export type BoundedOperation = typeof boundedOperations[number];
type Limits = Record<BoundedOperation, number>;

class RunBudget {
  #attempts: Limits = { extract: 0, 'document-answer': 0, 'literature-answer': 0 };
  #sources = new Set<string>();
  #tail = Promise.resolve();
  #stopped = false;
  #deadline: number;
  #limits: Limits;

  constructor(limits: Limits, deadlineUnixMs: number | null) {
    this.#limits = limits;
    this.#deadline = performance.now() + Math.min(DOCUMENT_LIFETIME_MS,
      deadlineUnixMs === null ? DOCUMENT_LIFETIME_MS : deadlineUnixMs - Date.now());
  }

  dispatch<T extends { kind: string }>(
    operation: BoundedOperation, source: string | undefined, send: (remainingMs: number) => Promise<T>,
  ): Promise<T | { kind: 'unavailable' }> {
    const unavailable = { kind: 'unavailable' as const };
    const work = this.#tail.then(async () => {
      const remainingMs = Math.floor(this.#deadline - performance.now());
      if (this.#stopped || remainingMs < 1) return unavailable;
      if (source !== undefined && this.#sources.has(source)) return unavailable;
      if (this.#attempts[operation] >= this.#limits[operation]) {
        this.#stopped = true;
        return unavailable;
      }
      this.#attempts[operation]++;
      if (source !== undefined) this.#sources.add(source);
      try {
        const result = await send(remainingMs);
        if (result.kind !== 'accepted') this.#stopped = true;
        return result;
      } catch {
        this.#stopped = true;
        return unavailable;
      }
    });
    this.#tail = work.then(() => undefined);
    return work;
  }
}

// The launcher owns one Next process per run. Route bundles share its ledger.
const processState = globalThis as typeof globalThis & {
  notelensBoundedEvaluation?: { configuration: string; budget: RunBudget };
};

export function boundedEvaluation(env: NodeJS.ProcessEnv): {
  profile: EvaluationProfile; ragToken: string; extractionToken: string; timeoutMs: number; budget: RunBudget;
  reviewedQuestionHashes?: ReviewedQuestionHashes;
} | null {
  const profile = env.NOTELENS_BOUNDED_EVALUATION;
  if (profile !== 'offline' && profile !== 'provider-backed') return null;
  const ragToken = env.NOTELENS_BOUNDED_RAG_TOKEN;
  const extractionToken = env.NOTELENS_BOUNDED_EXTRACTION_TOKEN;
  const timeoutMs = Number(env.NOTELENS_BOUNDED_HTTP_TIMEOUT_MS);
  const deadlineUnixMs = env.NOTELENS_BOUNDED_DEADLINE_UNIX_MS === undefined
    ? null : Number(env.NOTELENS_BOUNDED_DEADLINE_UNIX_MS);
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > DOCUMENT_LIFETIME_MS) return null;
  if (deadlineUnixMs !== null && (!Number.isSafeInteger(deadlineUnixMs) || deadlineUnixMs < 1 ||
      deadlineUnixMs > Date.now() + DOCUMENT_LIFETIME_MS)) return null;
  if (!env.NOTELENS_DEMO_RUN || !ragToken || !extractionToken ||
      !/^\S+$/.test(ragToken) || !/^\S+$/.test(extractionToken) ||
      !/^http:\/\/localhost:[1-9][0-9]{0,4}$/.test(env.NOTELENS_SESSION_ORIGIN ?? '')) return null;
  try {
    const limits = JSON.parse(env.NOTELENS_BOUNDED_LIMITS ?? '') as Limits;
    if (Object.keys(limits).length !== boundedOperations.length ||
        boundedOperations.some(op => !Number.isSafeInteger(limits[op]) || limits[op] < 0)) return null;
    const rawHashes = env.NOTELENS_BOUNDED_REVIEWED_QUESTION_HASHES;
    let reviewedQuestionHashes: ReviewedQuestionHashes | undefined;
    if (rawHashes !== undefined) {
      const hashes = JSON.parse(rawHashes) as ReviewedQuestionHashes;
      if (!hashes || Object.keys(hashes).length !== reviewedScopes.length ||
          !reviewedScopes.every(scope => Array.isArray(hashes[scope]) &&
            hashes[scope].every(value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value))) ||
          hashes.literature.length + hashes.both.length !== limits['literature-answer'] ||
          hashes.document.length + hashes.both.length !== limits['document-answer']) return null;
      reviewedQuestionHashes = hashes;
    }
    const configuration = JSON.stringify([profile, env.NOTELENS_DEMO_RUN, env.NOTELENS_SESSION_ORIGIN,
      env.NOTELENS_DEMO_RAG_PORT, env.NOTELENS_DEMO_EXTRACTION_PORT, ragToken, extractionToken, timeoutMs, deadlineUnixMs,
      limits, reviewedQuestionHashes]);
    const state = processState.notelensBoundedEvaluation ??= { configuration, budget: new RunBudget(limits, deadlineUnixMs) };
    if (state.configuration !== configuration) return null;
    return { profile, ragToken, extractionToken, timeoutMs, budget: state.budget, reviewedQuestionHashes };
  } catch {
    return null;
  }
}
