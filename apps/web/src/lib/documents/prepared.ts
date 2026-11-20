import { createHash, randomUUID } from 'node:crypto';
import type { PreparedDocument } from '@notelens/contracts/v1';
import { MemorySessions, UNAVAILABLE } from '../sessions/memory.ts';

export async function storePreparedDocument(
  store: MemorySessions, owner: string, ticket: string, text: string,
  source: PreparedDocument['source'], languageValidation: PreparedDocument['language_validation'],
) {
  const record: PreparedDocument = {
    schema_version: '1.0.0',
    doc_id: randomUUID(),
    text,
    text_sha256: createHash('sha256').update(text, 'utf8').digest('hex'),
    canonicalization_version: 'nfc-lf-v1',
    source,
    language: 'en',
    language_validation: languageValidation,
  };
  const stored = await store.storeDocument(owner, ticket, record);
  if (stored.kind !== 'stored') return UNAVAILABLE;
  const current = store.getDocument(owner, record.doc_id);
  if ('kind' in current) return UNAVAILABLE;
  return { kind: 'prepared' as const, docId: current.doc_id };
}
