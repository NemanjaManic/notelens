import assert from 'node:assert/strict';
import { requireMockMode } from '../src/lib/scaffold/config.ts';

assert.equal(requireMockMode(), 'mock');
assert.equal(requireMockMode('mock'), 'mock');
for (const mode of ['live', '', 'MOCK', 'unknown']) {
  assert.throws(() => requireMockMode(mode), /mock mode only/);
}
console.log('PASS: mock configuration rejects unavailable modes');
