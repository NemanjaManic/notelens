import { spawnSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const sources = ['apps/web/src/components/report-workspace.tsx', 'apps/web/src/lib/report/model.ts',
  'apps/web/src/lib/report/evidence.ts', 'apps/web/tests/report-view.test.tsx', 'apps/web/tests/tsconfig.report.json',
  'apps/web/scripts/check-report.mjs', 'apps/web/src/app/page.tsx', 'apps/web/src/app/globals.css'];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const hashes = paths => Object.fromEntries([...paths].sort().map(p => [p, hash(readFileSync(resolve(root, p)))]));
const cache = resolve(root, '.cache/review/b002-report');
mkdirSync(cache, { recursive: true });
if (realpathSync(cache) !== cache) throw new Error('CACHE_ORIGIN');
const nonce = randomUUID();
const directory = resolve(cache, `run-${nonce}`);
mkdirSync(directory);
writeFileSync(resolve(directory, 'package.json'), '{"type":"module"}\n', { flag: 'wx' });
const report = { passed: false, nonce, node: process.version, compile: null, test: null };
const save = () => writeFileSync(resolve(cache, 'latest.json'), JSON.stringify(report, null, 2) + '\n');
save();
try {
  if (realpathSync(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))) !== realpathSync(resolve(root, 'contracts/generated/typescript/v1.mjs'))) throw new Error('BINDING_ORIGIN');
  const inventory = JSON.parse(readFileSync(resolve(root, 'scripts/project/scaffold_inputs.json'), 'utf8'));
  const frozen = hashes(Object.keys(inventory.frozen_files));
  if (Object.entries(inventory.frozen_files).some(([p, h]) => frozen[p] !== h)) throw new Error('FROZEN_INPUT');
  report.inputs = { sources: hashes(sources), frozen };
  const env = { ...process.env, NOTELENS_MODE: 'mock', NO_COLOR: '1' };
  for (const key of Object.keys(env)) if (key !== 'NOTELENS_MODE' && (/^(NOTELENS|OPENAI|ANTHROPIC|AZURE|AWS|RAG|CLASSIFIER|EXTRACTION)(_|$)/i.test(key) || /API_KEY|TOKEN|SECRET|PASSWORD/.test(key) || key === 'NODE_OPTIONS' || key === 'NODE_PATH')) delete env[key];
  const run = args => spawnSync(process.execPath, args, { cwd: root, env, encoding: 'utf8', windowsHide: true, timeout: 120000, maxBuffer: 4 * 1024 * 1024 });
  // Emit JSX and rewritten .ts/.tsx imports into this fresh ignored run directory.
  // Only versioned synthetic fixture JSON may be copied by TypeScript; never submissions.
  const compile = run(['node_modules/typescript/bin/tsc', '--project', sources[4], '--outDir', directory]);
  report.compile = compile.status;
  if (compile.status !== 0) throw new Error('TYPECHECK_EMIT_FAILED');
  const tests = run(['--test', '--test-reporter=tap', '--test-isolation=none', resolve(directory, 'apps/web/tests/report-view.test.js')]);
  report.test = tests.status;
  const tap = tests.stdout ?? '';
  report.counts = Object.fromEntries([...tap.matchAll(/^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$/gm)].map(m => [m[1], Number(m[2])]));
  report.cases = [...tap.matchAll(/^ok \d+ - ([a-zA-Z0-9/-]+)\r?$/gm)].map(m => m[1]);
  if (tests.status !== 0 || report.counts.tests !== 37 || report.counts.pass !== 37 ||
    ['fail', 'cancelled', 'skipped', 'todo'].some(k => report.counts[k] !== 0) || report.cases.length !== 37 || new Set(report.cases).size !== 37 ||
    ['evidence/repeated-codepoint-occurrence', 'render/independent-summary-failure', 'render/independent-findings-failure', 'render/invalid-entire-extraction-withheld', 'security/react-escapes-source-text'].some(id => !report.cases.includes(id))) throw new Error('REPORT_CASES_FAILED');
  if (JSON.stringify(report.inputs) !== JSON.stringify({ sources: hashes(sources), frozen: hashes(Object.keys(inventory.frozen_files)) })) throw new Error('INPUT_CHANGED');
  report.passed = true;
} catch (error) {
  report.rule = error instanceof Error && /^[A-Z_]+$/.test(error.message) ? error.message : 'VERIFICATION_FAILED';
}
writeFileSync(resolve(directory, 'result.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
save();
console.log(JSON.stringify({ passed: report.passed, cases: report.counts?.pass ?? 0, rule: report.rule, report: '.cache/review/b002-report/latest.json' }));
if (!report.passed) process.exitCode = 1;
