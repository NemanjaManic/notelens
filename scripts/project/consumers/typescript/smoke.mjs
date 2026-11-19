import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateRecord} from '@notelens/contracts/v1';
const payloads=JSON.parse(readFileSync(new URL('../../../../contracts/v1/fixtures/payloads.json',import.meta.url),'utf8'));
assert.equal((await validateRecord('ClassificationResult',payloads['classification-supported'])).status,'supported');
assert.equal((await validateRecord('LivenessResult',payloads['liveness-valid'])).status,'alive');
console.log('PASS: installed @notelens/contracts/v1 package resolves and validates consumer payloads');
