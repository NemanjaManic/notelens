import fixtures from '../../../../../contracts/v1/fixtures/documents.json';
import type { PreparedDocument } from '@notelens/contracts/v1';
import { requireMockMode } from './config';

export async function scaffoldStatus(): Promise<{ mode: 'mock'; schemaVersion: PreparedDocument['schema_version'] }> {
  const mode = requireMockMode();
  const { validateRecord } = await import('@notelens/contracts/v1');
  // Only the versioned synthetic fixture enters this scaffold. No input is accepted.
  const document = await validateRecord('PreparedDocument', fixtures.offset);
  return { mode, schemaVersion: document.schema_version };
}
