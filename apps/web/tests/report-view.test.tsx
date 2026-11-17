import { test } from 'node:test';
import { renderToStaticMarkup } from 'react-dom/server';
import { createHash } from 'node:crypto';
import documents from '../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import payloads from '../../../contracts/v1/fixtures/payloads.json' with { type: 'json' };
import { ReportWorkspace } from '../src/components/report-workspace.tsx';
import { fixtureWorkspace, buildReport, SCENARIOS } from '../src/lib/report/model.ts';
import type { Workspace } from '../src/lib/report/model.ts';
import { evidenceParts } from '../src/lib/report/evidence.ts';

const equal = (a: unknown, b: unknown) => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error('REPORT_CHECK_FAILED'); };
const contains = (html: string, text: string) => equal(html.includes(text), true);
const render = (view: Workspace) => renderToStaticMarkup(<ReportWorkspace view={view} />);
for (const [scenario] of SCENARIOS) test(`fixture/${scenario}`, async () => {
  const view = await fixtureWorkspace(scenario);
  const html = render(view);
  for (const label of ['Mock mode', 'Fixture preview', 'does not replace a doctor', 'Do not upload real personal medical reports',
    'Canonical document', 'Document specialty', 'Document findings', 'Document summary']) contains(html, label);
  equal(/<(form|input|textarea)\b/.test(html), false);
  contains(html, `href="?scenario=${scenario}" aria-current="page"`);
});
test('render/validated-default', async () => {
  const view = await fixtureWorkspace(); const html = render(view);
  equal(view.classification.state, 'ready'); equal(view.extraction.state, 'ready');
  for (const label of ['Cardiovascular / Pulmonary', 'negated', 'unknown', 'decision_score', 'Summary source 1', 'Document-supported claim']) contains(html, label);
  equal(html.includes('<mark>'), false);
});
test('evidence/repeated-codepoint-occurrence', async () => {
  const view = await fixtureWorkspace('ready', 'finding-0-0'); const html = render(view);
  contains(html, 'Demo 🩺\nNo chest pain.\nChest pain is suspected.\n<mark>No chest pain.</mark>');
  contains(html, 'code points [47, 61)'); equal((html.match(/<mark>/g) ?? []).length, 1);
});
test('evidence/summary-citation', async () => {
  const view = await fixtureWorkspace('ready', 'summary-0');
  equal(view.selected?.sourceId, 'doc-source'); contains(render(view), '<mark>No chest pain.</mark>');
});
test('evidence/invalid-selection-cleared', async () => {
  const view = await fixtureWorkspace('ready', 'PRIVATE_MARKER');
  equal(view.selected, null); equal(render(view).includes('PRIVATE_MARKER'), false);
});
test('evidence/navigation-clears-selection', async () => {
  const html = render(await fixtureWorkspace('ready', 'finding-0-0'));
  contains(html, 'href="?scenario=procedure"'); equal(html.includes('?scenario=procedure&amp;evidence='), false);
});
test('evidence/helper-non-bmp-and-repeated', () => {
  equal(evidenceParts('🩺 same same', { start: 7, end: 11, quote: 'same' }), { before: '🩺 same ', quote: 'same', after: '' });
});
for (const [id, span] of [
  ['utf16', { start: 8, end: 12, quote: 'same' }], ['quote', { start: 2, end: 6, quote: 'wrong' }],
  ['reversed', { start: 6, end: 2, quote: 'same' }], ['fractional', { start: 2.5, end: 6, quote: 'same' }],
] as const) test(`evidence/reject-${id}`, () => equal(evidenceParts('🩺 same same', span), null));
test('render/independent-summary-failure', async () => {
  const html = render(await fixtureWorkspace('summary-unavailable'));
  contains(html, '<h4>Chest pain</h4>'); contains(html, 'Summary unavailable.'); equal(html.includes('Summary source 1'), false);
});
test('render/independent-findings-failure', async () => {
  const html = render(await fixtureWorkspace('findings-unavailable'));
  contains(html, 'Findings unavailable.'); contains(html, 'Summary source 1'); equal(html.includes('<h4>Chest pain</h4>'), false);
});
test('render/empty-is-not-absence-of-conditions', async () => {
  const html = render(await fixtureWorkspace('empty'));
  contains(html, 'No findings were returned'); contains(html, 'does not establish an absence'); contains(html, 'Evidence: insufficient');
});
test('render/unsupported-has-no-fake-scores', async () => {
  const html = render(await fixtureWorkspace('unsupported'));
  contains(html, 'Classification was not run.'); equal(html.includes('Score details and limitations'), false);
  contains(html, '<h4>Chest pain</h4>');
});
test('render/partial-and-procedure-states', async () => {
  contains(render(await fixtureWorkspace('partial')), 'Extraction: partial');
  const html = render(await fixtureWorkspace('procedure', 'finding-0-0'));
  contains(html, '<dd>planned</dd>'); contains(html, '<mark>Colonoscopy is planned for next week.</mark>');
});
test('render/invalid-entire-extraction-withheld', async () => {
  const view = await fixtureWorkspace('invalid-result'); const html = render(view);
  equal(view.extraction.state, 'invalid'); equal(view.classification.state, 'ready'); equal(view.passages, []);
  contains(html, 'could not be validated'); equal(html.includes('<h4>Chest pain</h4>'), false); equal(html.includes('Summary source 1'), false);
});
test('render/unavailable-clears-document-and-highlights', async () => {
  const view = await fixtureWorkspace('unavailable', 'finding-0-0'); const html = render(view);
  equal(view.document, null); equal(view.selected, null); equal(view.passages, []);
  equal(html.includes('Demo 🩺'), false); equal(html.includes('<mark>'), false);
});
test('render/loading-does-not-invent-output', async () => {
  const html = render(await fixtureWorkspace('loading', 'summary-0'));
  contains(html, 'Loading state preview'); equal(html.includes('Summary source 1'), false);
  equal(html.includes('<h4>Chest pain</h4>'), false); equal(html.includes('<mark>'), false);
});
test('admission/invalid-document-withholds-all-results', async () => {
  const result = await buildReport({ ...documents.offset, text_sha256: '0'.repeat(64) }, payloads['classification-supported'], payloads['extraction-valid']);
  equal(result.document, null); equal(result.passages, []); equal(result.classification.state, 'unavailable');
});
test('admission/stale-and-live-classification-isolated', async () => {
  for (const update of [{ doc_id: 'other' }, { mode: 'live' }]) {
    const report = await buildReport(documents.offset, { ...payloads['classification-supported'], ...update }, payloads['extraction-valid']);
    equal(report.classification.state, 'invalid'); equal(report.extraction.state, 'ready');
  }
});
test('admission/fixtures-not-mutated', async () => {
  const before = JSON.stringify([documents, payloads]);
  await fixtureWorkspace('procedure', 'finding-0-0'); await fixtureWorkspace('invalid-result');
  equal(JSON.stringify([documents, payloads]), before);
});
test('security/react-escapes-source-text', async () => {
  const text = 'Synthetic <script>alert(1)</script> & report.';
  const document = { ...documents.offset, text, text_sha256: createHash('sha256').update(text).digest('hex') };
  const classification = { ...payloads['classification-supported'], text_sha256: document.text_sha256, confidence_note: '<img src=x onerror=alert(1)>' };
  const extraction = { ...payloads['extraction-empty'], text_sha256: document.text_sha256 };
  const report = await buildReport(document, classification, extraction);
  const html = render({ ...report, scenario: 'ready', selected: null, heading: 'Report overview' });
  contains(html, '&lt;script&gt;'); contains(html, '&lt;img'); equal(html.includes('<script>'), false); equal(html.includes('<img '), false);
});
test('security/upstream-error-message-hidden', async () => {
  const extraction = structuredClone(payloads['analysis-summary-failed-findings-kept']); extraction.summary.error!.message = 'PRIVATE_MARKER';
  const report = await buildReport(documents.offset, payloads['classification-supported'], extraction);
  const html = render({ ...report, scenario: 'summary-unavailable', selected: null, heading: 'Some results are unavailable' });
  equal(html.includes('PRIVATE_MARKER'), false); contains(html, 'Summary unavailable.');
});
test('security/unknown-query-not-reflected', async () => {
  const view = await fixtureWorkspace('<script>PRIVATE_MARKER</script>', 'javascript:PRIVATE_MARKER');
  equal(view.scenario, 'ready'); equal(view.selected, null); equal(render(view).includes('PRIVATE_MARKER'), false);
});
