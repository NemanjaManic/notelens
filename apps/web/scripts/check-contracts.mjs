import { createHash, randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');
const SOURCES = ['apps/web/src/lib/contracts/consumer.ts', 'apps/web/tests/contracts.test.ts',
  'apps/web/tests/tsconfig.contracts.json', 'apps/web/scripts/check-contracts.mjs'];
const sha = value => createHash('sha256').update(value).digest('hex');
const read = path => JSON.parse(readFileSync(resolve(ROOT, path), 'utf8'));
const requireCheck = (condition, rule) => { if (!condition) throw new Error(rule); };
const hashFiles = files => Object.fromEntries([...files].sort().map(path => [path, sha(readFileSync(resolve(ROOT, path)))]));
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/** Exported for isolated evidence-failure probes; never treats compilation alone as a pass. */
export function verifyEvidence({ evidence, expected, nonce, before, after, exits, tap }) {
  requireCheck(expected.length > 0 && new Set(expected).size === expected.length, 'CASE_CATALOG');
  requireCheck(equal(before, after), 'INPUT_CHANGED');
  requireCheck(exits.catalog === 0 && exits.typecheck === 0 && exits.test === 0, 'CHILD_EXIT');
  requireCheck(evidence?.nonce === nonce && Array.isArray(evidence.results), 'CASE_EVIDENCE');
  const results = evidence.results;
  requireCheck(results.length === expected.length && new Set(results.map(c => c.id)).size === expected.length, 'CASE_COMPLETENESS');
  requireCheck(results.every(c => expected.includes(c.id) && c.passed === true && c.boundary === 'web-consumer'), 'CASE_FAILED');
  const counts = Object.fromEntries([...tap.matchAll(/^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$/gm)]
    .map(match => [match[1], Number(match[2])]));
  requireCheck(counts.tests === expected.length && counts.pass === expected.length &&
    ['fail', 'cancelled', 'skipped', 'todo'].every(key => counts[key] === 0), 'RUNNER_COUNTS');
  const executed = [...tap.matchAll(/^ok \d+ - ([^\r\n]+)\r?$/gm)].map(match => match[1]);
  requireCheck(equal(executed, expected), 'RUNNER_CASES');
  return counts;
}

function cleanEnvironment(nonce, reportPath) {
  const env = { ...process.env };
  for (const key of Object.keys(env)) {
    if (/^(OPENAI|ANTHROPIC|AZURE|COHERE|GOOGLE|GEMINI|NOTELENS|RAG|CLASSIFIER|EXTRACTION|CHROMA|CORPUS|INDEX|MODEL|PROMPTFOO)(_|$)/i.test(key) ||
      /(^|_)(API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIALS?)($|_)/i.test(key) || ['NODE_OPTIONS', 'NODE_PATH', 'LD_PRELOAD', 'DYLD_INSERT_LIBRARIES'].includes(key)) delete env[key];
  }
  return { ...env, FORCE_COLOR: '0', NO_COLOR: '1', NOTELENS_B010_NONCE: nonce, NOTELENS_B010_REPORT: reportPath };
}

function main() {
  const base = resolve(ROOT, '.cache/review/b010-contracts');
  mkdirSync(base, { recursive: true });
  // Reject redirected cache roots before writing. Each invocation owns a new directory.
  requireCheck(realpathSync(base) === base, 'CACHE_ORIGIN');
  const nonce = randomUUID();
  const directory = resolve(base, `run-${nonce}`);
  mkdirSync(directory);
  const latest = resolve(base, 'latest.json');
  writeFileSync(latest, JSON.stringify({ passed: false, nonce, stage: 'started' }, null, 2) + '\n');
  const result = { passed: false, nonce, node: process.version, typecheck: null, test: null, catalog: null };
  let stage = 'origin';
  try {
    const installed = realpathSync(fileURLToPath(import.meta.resolve('@notelens/contracts/v1')));
    requireCheck(installed === realpathSync(resolve(ROOT, 'contracts/generated/typescript/v1.mjs')), 'PACKAGE_ORIGIN');
    const inventory = read('scripts/project/scaffold_inputs.json');
    const frozen = hashFiles(Object.keys(inventory.frozen_files));
    for (const [path, hash] of Object.entries(inventory.frozen_files)) requireCheck(frozen[path] === hash, 'FROZEN_INPUT');
    const freeze = read('contracts/v1/freeze.json');
    requireCheck(freeze.schema_sha256 === '707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78', 'SCHEMA_ORIGIN');
    requireCheck(sha(readFileSync(resolve(ROOT, 'contracts/generated/typescript/schema.json'))) === freeze.schema_sha256, 'INSTALLED_SCHEMA');
    const before = { sources: hashFiles(SOURCES), frozen };
    result.inputs = before;
    result.binding = 'contracts/generated/typescript/v1.mjs';
    result.typescript = read('node_modules/typescript/package.json').version;
    const env = cleanEnvironment(nonce, resolve(directory, 'cases.json'));
    const run = args => {
      const child = spawnSync(process.execPath, args, { cwd: ROOT, env, encoding: 'utf8', timeout: 120000,
        windowsHide: true, maxBuffer: 4 * 1024 * 1024 });
      return { status: child.status, stdout: child.stdout ?? '', stderr: child.stderr ?? '' };
    };
    stage = 'catalog';
    const catalog = run(['--experimental-strip-types', SOURCES[1], '--list-cases']);
    result.catalog = catalog.status;
    requireCheck(catalog.status === 0, 'CATALOG_EXIT');
    const expected = JSON.parse(catalog.stdout);
    requireCheck(Array.isArray(expected) && expected.every(id => typeof id === 'string' && /^[A-Za-z0-9/_-]+$/.test(id)), 'CASE_CATALOG');
    result.expected = expected;
    stage = 'typecheck';
    const compiler = run(['node_modules/typescript/bin/tsc', '--noEmit', '--project', SOURCES[2]]);
    result.typecheck = compiler.status;
    requireCheck(compiler.status === 0, 'TYPECHECK_EXIT');
    stage = 'test';
    const test = run(['--experimental-strip-types', '--test', '--test-reporter=tap', '--test-isolation=none', SOURCES[1]]);
    result.test = test.status;
    result.runner_output_sha256 = sha(test.stdout);
    result.runner_stderr_sha256 = sha(test.stderr);
    stage = 'evidence';
    const evidence = JSON.parse(readFileSync(resolve(directory, 'cases.json'), 'utf8'));
    result.counts = verifyEvidence({ evidence, expected, nonce, before,
      after: { sources: hashFiles(SOURCES), frozen: hashFiles(Object.keys(inventory.frozen_files)) },
      exits: { catalog: catalog.status, typecheck: compiler.status, test: test.status }, tap: test.stdout });
    result.cases = evidence.results;
    result.passed = true;
  } catch (error) {
    // No exception body, document, raw header, environment or provider message is logged.
    result.stage = stage;
    result.rule = error instanceof Error && /^[A-Z][A-Z0-9_]{0,63}$/.test(error.message) ? error.message : 'VERIFICATION_FAILED';
  }
  const serialized = JSON.stringify(result, null, 2) + '\n';
  writeFileSync(resolve(directory, 'result.json'), serialized, { flag: 'wx' });
  writeFileSync(latest, serialized);
  process.stdout.write(JSON.stringify({ passed: result.passed, cases: result.counts?.tests ?? 0,
    stage: result.stage, rule: result.rule, report: '.cache/review/b010-contracts/latest.json' }) + '\n');
  if (!result.passed) process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
