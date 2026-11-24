import { DOCUMENT_LIFETIME_MS } from '../config/session-policy.ts';

export type EvaluationProfile = 'offline' | 'provider-backed';
export const boundedOperations = ['extract', 'document-answer', 'literature-answer'] as const;
export type BoundedOperation = typeof boundedOperations[number];
type Limits = Record<BoundedOperation, number>;

class RunBudget {
  #attempts: Limits = { extract: 0, 'document-answer': 0, 'literature-answer': 0 };
  #sources = new Set<string>();
  #tail = Promise.resolve();
  #stopped = false;
  #deadline = performance.now() + DOCUMENT_LIFETIME_MS;
  #limits: Limits;

  constructor(limits: Limits) {
    this.#limits = limits;
  }

  dispatch<T extends { kind: string }>(
    operation: BoundedOperation, source: string | undefined, send: () => Promise<T>,
  ): Promise<T | { kind: 'unavailable' }> {
    const unavailable = { kind: 'unavailable' as const };
    const work = this.#tail.then(async () => {
      if (this.#stopped || performance.now() >= this.#deadline) return unavailable;
      if (source !== undefined && this.#sources.has(source)) return unavailable;
      if (this.#attempts[operation] >= this.#limits[operation]) {
        this.#stopped = true;
        return unavailable;
      }
      this.#attempts[operation]++;
      if (source !== undefined) this.#sources.add(source);
      try {
        const result = await send();
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
} | null {
  const profile = env.NOTELENS_BOUNDED_EVALUATION;
  if (profile !== 'offline' && profile !== 'provider-backed') return null;
  const ragToken = env.NOTELENS_BOUNDED_RAG_TOKEN;
  const extractionToken = env.NOTELENS_BOUNDED_EXTRACTION_TOKEN;
  const timeoutMs = Number(env.NOTELENS_BOUNDED_HTTP_TIMEOUT_MS);
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > DOCUMENT_LIFETIME_MS) return null;
  if (!env.NOTELENS_DEMO_RUN || !ragToken || !extractionToken ||
      !/^\S+$/.test(ragToken) || !/^\S+$/.test(extractionToken) ||
      !/^http:\/\/localhost:[1-9][0-9]{0,4}$/.test(env.NOTELENS_SESSION_ORIGIN ?? '')) return null;
  try {
    const limits = JSON.parse(env.NOTELENS_BOUNDED_LIMITS ?? '') as Limits;
    if (Object.keys(limits).length !== boundedOperations.length ||
        boundedOperations.some(op => !Number.isSafeInteger(limits[op]) || limits[op] < 0)) return null;
    const configuration = JSON.stringify([profile, env.NOTELENS_DEMO_RUN, env.NOTELENS_SESSION_ORIGIN,
      env.NOTELENS_DEMO_RAG_PORT, env.NOTELENS_DEMO_EXTRACTION_PORT, ragToken, extractionToken, timeoutMs, limits]);
    const state = processState.notelensBoundedEvaluation ??= { configuration, budget: new RunBudget(limits) };
    if (state.configuration !== configuration) return null;
    return { profile, ragToken, extractionToken, timeoutMs, budget: state.budget };
  } catch {
    return null;
  }
}
