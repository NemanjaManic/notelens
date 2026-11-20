import { createHash, randomUUID } from 'node:crypto';
import documents from '../../../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import { validateRecord } from '@notelens/contracts/v1';
import type { PreparedDocument } from '@notelens/contracts/v1';
import type { MemorySessions } from '../sessions/memory.ts';
import { UNAVAILABLE } from '../sessions/memory.ts';
import { sessionConfiguration } from '../config/session-policy.ts';
import { canonicalText, preparationRejected } from './canonical.ts';
import type { PreparationRejection } from './canonical.ts';

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
      const record: PreparedDocument = {
        schema_version: '1.0.0', doc_id: randomUUID(),
        text: canonical.text, text_sha256: createHash('sha256').update(canonical.text, 'utf8').digest('hex'),
        canonicalization_version: 'nfc-lf-v1', source: structuredClone(example.source),
        language: 'en', language_validation: structuredClone(example.language_validation),
      };
      // The accepted English declaration is restricted to these known synthetic
      // fixtures. It is not an English detector or permission to accept user text.
      const validated = await validateRecord('PreparedDocument', record);
      const stored = await store.storeDocument(capability, ticket, validated);
      if (stored.kind !== 'stored') return UNAVAILABLE;
      const current = store.getDocument(capability, validated.doc_id);
      if ('kind' in current) return UNAVAILABLE;
      return { kind: 'prepared', docId: current.doc_id };
    } finally {
      store.cancelPreparation(capability, ticket);
    }
  } catch {
    // Never echo document text, capability, exception or runtime issue paths.
    return preparationRejected('preparation-unavailable');
  }
}
