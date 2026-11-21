import documents from '../../../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import { validateRecord } from '@notelens/contracts/v1';
import type { MemorySessions } from '../sessions/memory.ts';
import { UNAVAILABLE } from '../sessions/memory.ts';
import { sessionConfiguration } from '../config/session-policy.ts';
import { canonicalText, preparationRejected } from './canonical.ts';
import type { PreparationRejection } from './canonical.ts';
import { storePreparedDocument } from './prepared.ts';

// A fixed, repository-versioned synthetic catalog. No caller-supplied document,
// language declaration, source, ID, digest or fixture path is accepted here.
export const BUILTIN_IDS = Object.freeze(['offset', 'history', 'procedure', 'procedure-ordered',
  'procedure-performed', 'procedure-cancelled', 'procedure-hypothetical', 'procedure-unknown'] as const);
type BuiltinId = typeof BUILTIN_IDS[number];
export type PreparedBuiltin = { kind: 'prepared'; docId: string };

/** Server-side core only. Browser ownership transport remains a separate gate. */
export async function prepareBuiltin(store: MemorySessions, capability: string, id: unknown): Promise<PreparedBuiltin | PreparationRejection | typeof UNAVAILABLE> {
  if (typeof id !== 'string' || !BUILTIN_IDS.some(known => known === id)) return preparationRejected('unknown-builtin');
  try {
    sessionConfiguration();
    // The absolute deadline begins before text preparation and either validation.
    const ticket = store.beginDocument(capability);
    if (!ticket) return UNAVAILABLE;
    try {
      const example = await validateRecord('PreparedDocument', structuredClone(documents[id as BuiltinId]));
      const canonical = canonicalText(example.text);
      if (canonical.kind !== 'canonical') return canonical;
      return await storePreparedDocument(store, capability, ticket, canonical.text, example.source, example.language_validation);
    } finally {
      store.cancelPreparation(capability, ticket);
    }
  } catch {
    // Never echo document text, capability, exception or runtime issue paths.
    return preparationRejected('preparation-unavailable');
  }
}
