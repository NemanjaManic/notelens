import documents from '../../../../../contracts/v1/fixtures/documents.json' with { type: 'json' };
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { validateRecord } from '@notelens/contracts/v1';
import type { PreparedDocument, ClassificationResult, ExtractionResult, EvidenceSpan } from '@notelens/contracts/v1';
import { consumeRecord } from '../contracts/consumer.ts';
import type { EvaluationProfile } from '../clients/bounded-evaluation.ts';

export const SCENARIOS = [
  ['ready', 'Report overview'], ['uncertain', 'Uncertain specialty'], ['unsupported', 'Unsupported specialty'],
  ['partial', 'Partial findings'], ['summary-unavailable', 'Summary unavailable'],
  ['findings-unavailable', 'Findings unavailable'], ['empty', 'Empty findings'], ['procedure', 'Planned procedure'],
  ['invalid-result', 'Invalid result'], ['failed-call', 'Failed call'], ['loading', 'Loading preview'],
  ['no-document', 'Empty workspace'], ['unavailable', 'Unavailable document'],
] as const;
export type Scenario = typeof SCENARIOS[number][0];
export type Panel<T> = { state: 'ready'; record: T } | { state: 'loading' | 'empty' | 'unavailable' | 'invalid'; notice: string };
export type Passage = { key: string; label: string; span: EvidenceSpan; sourceId?: string };
export type Report = { document: PreparedDocument | null; classification: Panel<ClassificationResult>;
  extraction: Panel<ExtractionResult>; passages: Passage[] };
export type Workspace = Report & { scenario: Scenario; selected: Passage | null; heading: string;
  fittedClassifier?: true; d005Replay?: true; evaluation?: EvaluationProfile };
// The frozen catalog includes intentionally invalid Unicode test inputs. Read it
// only on the server: a JSON bundler must not reinterpret or rewrite that catalog.
// The local preview supports the documented repository-root and apps/web commands.
const catalog = [resolve(process.cwd(), 'contracts/v1/fixtures/payloads.json'),
  resolve(process.cwd(), '../../contracts/v1/fixtures/payloads.json')].find(path => existsSync(path));
if (!catalog) throw new Error('The synthetic fixture catalog is unavailable.');
const values: Record<string, unknown> = JSON.parse(readFileSync(catalog, 'utf8'));
const blocked = { state: 'unavailable' as const, notice: 'The document is unavailable. Choose a synthetic example.' };

/** Validates the full selected document and each independent result before presentation. */
export async function buildReport(
  documentInput: unknown, classificationInput: unknown, extractionInput: unknown,
  classificationMode: 'mock' | 'live' = 'mock', extractionMode: 'mock' | 'live' = 'mock',
): Promise<Report> {
  let document: PreparedDocument;
  try { document = await validateRecord('PreparedDocument', structuredClone(documentInput)); }
  catch { return { document: null, classification: blocked, extraction: blocked, passages: [] }; }
  const [classification, extraction] = await Promise.all([
    consumeRecord('ClassificationResult', { kind: 'native', value: structuredClone(classificationInput) }, { document }, classificationMode),
    consumeRecord('ExtractionResult', { kind: 'native', value: structuredClone(extractionInput) }, { document }, extractionMode),
  ]);
  const result: Report = { document,
    classification: classification.kind === 'accepted' ? { state: 'ready', record: classification.record }
      : { state: 'invalid', notice: 'The specialty result could not be validated.' },
    extraction: extraction.kind === 'accepted' ? { state: 'ready', record: extraction.record }
      : { state: 'invalid', notice: 'The findings and summary result could not be validated.' }, passages: [] };
  if (result.extraction.state === 'ready') {
    const record = result.extraction.record;
    record.items.forEach((item, i) => item.evidence.forEach((span, j) => result.passages.push({
      key: `finding-${i}-${j}`, label: `${item.name}: supporting passage ${j + 1}`, span,
    })));
    if (record.summary.status === 'completed' && record.summary.result) {
      record.summary.result.sources.forEach((source, i) => result.passages.push({
        key: `summary-${i}`, label: `Summary source ${i + 1}`, sourceId: source.source_id, span: source.evidence,
      }));
    }
  }
  return result;
}

export async function fixtureWorkspace(requested?: string, evidence?: string): Promise<Workspace> {
  const scenario: Scenario = SCENARIOS.find(([key]) => key === requested)?.[0] ?? 'ready';
  let doc: unknown = documents.offset;
  let classification: unknown = values['classification-supported'];
  let extraction: unknown = values['extraction-valid'];
  if (scenario === 'uncertain') classification = values['classification-uncertain'];
  if (scenario === 'unsupported') classification = values['classification-unsupported'];
  const examples: Partial<Record<Scenario, string>> = { partial: 'analysis-extraction-partial',
    'summary-unavailable': 'analysis-summary-failed-findings-kept',
    'findings-unavailable': 'analysis-extraction-failed-summary-kept', empty: 'extraction-empty' };
  const example = examples[scenario];
  if (example) extraction = values[example];
  if (scenario === 'procedure') {
    doc = documents.procedure;
    extraction = { ...structuredClone(values['extraction-empty'] as ExtractionResult), doc_id: documents.procedure.doc_id,
      text_sha256: documents.procedure.text_sha256, items: [structuredClone(values['procedure-planned'])] };
    classification = { ...structuredClone(values['classification-supported'] as ClassificationResult),
      doc_id: documents.procedure.doc_id, text_sha256: documents.procedure.text_sha256 };
  }
  if (scenario === 'invalid-result') extraction = { ...structuredClone(values['extraction-valid'] as ExtractionResult), text_sha256: '0'.repeat(64) };
  let report: Report;
  if (scenario === 'unavailable' || scenario === 'no-document') {
    const panel = scenario === 'unavailable' ? blocked : { state: 'empty' as const, notice: 'Choose a synthetic example to begin.' };
    report = { document: null, classification: panel, extraction: panel, passages: [] };
  } else {
    report = await buildReport(doc, classification, extraction);
    if (scenario === 'loading') report = { ...report,
      classification: { state: 'loading', notice: 'Specialty loading preview.' },
      extraction: { state: 'loading', notice: 'Findings and summary loading preview.' }, passages: [] };
    if (scenario === 'failed-call') report = { ...report,
      extraction: { state: 'unavailable', notice: 'The findings and summary call could not complete.' }, passages: [] };
  }
  const failure = report.classification.state === 'invalid' || report.extraction.state === 'invalid' ||
    report.extraction.state === 'unavailable' || (report.extraction.state === 'ready' &&
      (report.extraction.record.extraction_status === 'failed' || report.extraction.record.summary.status === 'failed'));
  const heading = scenario === 'no-document' ? 'Choose a synthetic example' : !report.document ? 'Document unavailable'
    : scenario === 'loading' ? 'Loading state preview' : failure ? 'Some results are unavailable' : 'Report overview';
  return { ...report, scenario, heading, selected: report.passages.find(p => p.key === evidence) ?? null };
}
