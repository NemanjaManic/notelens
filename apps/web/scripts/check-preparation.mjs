import { spawnSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const sources = ['apps/web/src/lib/documents/canonical.ts', 'apps/web/src/lib/documents/builtin.ts',
  'apps/web/tests/preparation.test.ts', 'apps/web/tests/tsconfig.preparation.json', 'apps/web/scripts/check-preparation.mjs',
  'apps/web/src/lib/sessions/memory.ts', 'apps/web/src/lib/config/session-policy.ts', 'apps/web/tsconfig.json',
  'apps/web/tests/tsconfig.contracts.json', 'apps/web/src/lib/documents/prepared.ts',
  'apps/web/src/lib/documents/submitted.ts', 'apps/web/src/lib/documents/language.ts',
  'apps/web/src/lib/documents/pdf.ts', 'apps/web/src/lib/documents/pdf-worker.mjs', 'apps/web/package.json', 'package-lock.json'];
const expectedCases = 51;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const hashes = paths => Object.fromEntries([...paths].sort().map(p => [p, hash(readFileSync(resolve(root, p)))]));
const cache = resolve(root, '.cache/review/b001-preparation');
mkdirSync(cache, { recursive: true });
if (realpathSync(cache) !== cache) throw new Error('CACHE_ORIGIN');
const nonce = randomUUID();
const report = { passed: false, nonce, node: process.version, typecheck: null, test: null };
const save = () => writeFileSync(resolve(cache, 'latest.json'), JSON.stringify(report, null, 2) + '\n');
save();
try {
  if (realpathSync(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))) !== realpathSync(resolve(root, 'contracts/generated/typescript/v1.mjs'))) throw new Error('BINDING_ORIGIN');
  const inventory = JSON.parse(readFileSync(resolve(root, 'scripts/project/scaffold_inputs.json'), 'utf8'));
  const frozen = hashes(Object.keys(inventory.frozen_files));
  if (Object.entries(inventory.frozen_files).some(([p, h]) => frozen[p] !== h)) throw new Error('FROZEN_INPUT');
  report.inputs = { sources: hashes(sources), frozen };
  const env = { ...process.env, NOTELENS_MODE: 'mock', NO_COLOR: '1' };
  for (const key of Object.keys(env)) if (key !== 'NOTELENS_MODE' && (/^(NOTELENS|OPENAI|ANTHROPIC|AZURE|AWS|COHERE|GEMINI|GOOGLE|RAG|CLASSIFIER|EXTRACTION)(_|$)/i.test(key) || /API_KEY|TOKEN|SECRET|PASSWORD/.test(key) || key === 'NODE_OPTIONS' || key === 'NODE_PATH')) delete env[key];
  const run = args => spawnSync(process.execPath, args, { cwd: root, env, encoding: 'utf8', windowsHide: true, timeout: 120000, maxBuffer: 4 * 1024 * 1024 });
  const compiler = run(['node_modules/typescript/bin/tsc', '--noEmit', '--project', sources[3]]);
  report.typecheck = compiler.status;
  if (compiler.status !== 0) throw new Error('TYPECHECK_FAILED');
  const tests = run(['--experimental-strip-types', '--test', '--test-reporter=tap', '--test-isolation=none', sources[2]]);
  report.test = tests.status;
  const tap = tests.stdout ?? '';
  report.counts = Object.fromEntries([...tap.matchAll(/^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$/gm)].map(m => [m[1], Number(m[2])]));
  report.cases = [...tap.matchAll(/^ok \d+ - ([a-zA-Z0-9/_-]+)\r?$/gm)].map(m => m[1]);
  if (tests.status !== 0 || report.counts.tests !== expectedCases || report.counts.pass !== expectedCases ||
    ['fail', 'cancelled', 'skipped', 'todo'].some(k => report.counts[k] !== 0) ||
    report.cases.length !== expectedCases || new Set(report.cases).size !== expectedCases ||
    ['canonical/non-bmp-limit-is-not-utf16', 'canonical/reject-nfc-expansion-excess', 'handoff/deadline-starts-before-validation',
      'handoff/expiry-after-store-before-receipt', 'submission/canonical-pasted-text-and-provenance',
      'submission/streamed-pdf-byte-limit', 'submission/accepts-exact-codepoint-limit'].some(id => !report.cases.includes(id))) {
    throw new Error('PREPARATION_CASES_FAILED');
  }
  if (JSON.stringify(report.inputs) !== JSON.stringify({ sources: hashes(sources), frozen: hashes(Object.keys(inventory.frozen_files)) })) throw new Error('INPUT_CHANGED');
  report.passed = true;
} catch (error) {
  report.rule = error instanceof Error && /^[A-Z_]+$/.test(error.message) ? error.message : 'VERIFICATION_FAILED';
}
writeFileSync(resolve(cache, `run-${nonce}.json`), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
save();
console.log(JSON.stringify({ passed: report.passed, cases: report.counts?.pass ?? 0, rule: report.rule, report: '.cache/review/b001-preparation/latest.json' }));
if (!report.passed) process.exitCode = 1;
