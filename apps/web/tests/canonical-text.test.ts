// Current canonical fixture verification, with no application input or service launch.
import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { writeFileSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { cases, root } from './helpers/unicode-reference.ts';
import type { Result } from './helpers/unicode-reference.ts';

const suite = cases();
const results = new Map<string, Result>();
for (const c of suite) test(c.id, async () => {
  const value = await c.run();
  results.set(c.id, { id: c.id, passed: true, ...value });
});

after(() => {
  const target = process.env.NOTELENS_UNICODE_REPORT;
  if (!target) return; // Standalone test invocation writes only case names/counts.
  const directory = realpathSync(path.dirname(target));
  const cache = realpathSync(path.join(root, '.cache/review/f012-unicode'));
  const relative = path.relative(cache, directory);
  assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative), 'Report must stay in the owned run directory');
  assert.equal(path.basename(target), 'typescript.json');
  writeFileSync(target, JSON.stringify({ format: 'notelens-f012-typescript-v1',
    run_id: process.env.NOTELENS_UNICODE_RUN_ID, node: process.version,
    passed: results.size === suite.length, cases: suite.map(c => results.get(c.id) ?? { id: c.id, passed: false }) }, null, 2) + '\n', 'utf8');
});
