import assert from 'node:assert/strict';
import { readFile, realpath } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validateRecord } from '@notelens/contracts/v1';

const expected = new URL('../../../contracts/generated/typescript/v1.mjs', import.meta.url);
assert.equal(await realpath(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))), await realpath(fileURLToPath(expected)));
const documents = JSON.parse(await readFile(new URL('../../../contracts/v1/fixtures/documents.json', import.meta.url), 'utf8'));
const document = await validateRecord('PreparedDocument', documents.offset);
assert.equal(document.schema_version, '1.0.0');
console.log('PASS: web resolves local frozen package and validates synthetic fixture');
