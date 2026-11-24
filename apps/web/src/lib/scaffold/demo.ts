import type { PreparedDocument } from '@notelens/contracts/v1';
import { mockServiceClients } from '../clients/mock-services.ts';
import { localFittedClassifier } from '../clients/classifier-client.ts';
import { buildReport, fixtureWorkspace } from '../report/model.ts';
import type { Workspace } from '../report/model.ts';
import type { RoutedAnswer } from '../routing/answer.ts';
import { getSessionStore } from '../sessions/route.ts';

/** The public live app is served at the site root; the mock workspace stays under /demo. */
export function reportBasePath(): '/' | '/demo' {
  return process.env.NOTELENS_BOUNDED_EVALUATION === 'public-live' ? '/' : '/demo';
}

export function isDemoConfigured() {
  return mockServiceClients() !== null;
}

export function isBuiltinDemoDocument(document: PreparedDocument | null): boolean {
  return document?.language_validation.policy_version === 'fixture-language-policy-v0';
}

export async function demoWorkspace(query: Record<string, string | string[] | undefined>, document: PreparedDocument | null,
  owner: string | null = null):
    Promise<Workspace> {
  const fitted = localFittedClassifier();
  const clients = mockServiceClients();
  const profile = {
    ...(fitted ? { fittedClassifier: true as const } : {}),
    ...(clients?.d005Replay ? { d005Replay: true as const } : {}),
    ...(clients?.evaluation ? { evaluation: clients.evaluation } : {}),
  };
  if (!document) return { ...await fixtureWorkspace(query.document === undefined ? 'no-document' : 'unavailable'), ...profile };
  if (!clients) return fixtureWorkspace('unavailable');
  const builtin = isBuiltinDemoDocument(document);
  const [classification, extraction] = await Promise.all([
    fitted ? fitted.client?.classify(document) ?? { kind: 'unavailable' as const }
      : builtin ? clients.classify(document) : undefined,
    clients.evaluation ? owner
      ? getSessionStore().extractionOnce(owner, document.doc_id, () => clients.extract(document))
      : { kind: 'unavailable' as const }
      : clients.extract(document),
  ]);
  const report = await buildReport(document, classification?.kind === 'accepted' ? classification.record : undefined,
    extraction.kind === 'accepted' ? extraction.record : undefined, fitted ? 'live' : 'mock',
    clients.d005Replay || clients.evaluation ? 'live' : 'mock');
  if (!classification) {
    report.classification = { state: 'empty', notice: 'Mock specialty classification is available for the built-in example.' };
  } else if (classification.kind === 'unavailable' || classification.kind === 'unauthorized') {
    report.classification = { state: 'unavailable', notice: 'The specialty result is unavailable.' };
  }
  if (extraction.kind === 'unavailable') {
    report.extraction = { state: 'unavailable', notice: 'The findings and summary are unavailable.' };
  }
  return { ...report, ...profile, scenario: 'ready', heading: builtin ? 'Report overview' : 'Prepared document', selected: null };
}

export function selectDemoEvidence(view: Workspace, key: unknown, answer?: RoutedAnswer): Workspace {
  const passages = [...view.passages];
  for (const { origin, result } of answer?.branches ?? []) {
    if (result.kind !== 'accepted') continue;
    result.record.sources.forEach((source, index) => {
      if (source.kind === 'document') passages.push({
        key: `answer-${origin}-${index}`, label: `Answer source ${index + 1}`, span: source.evidence,
      });
    });
  }
  return { ...view, passages, selected: passages.find(passage => passage.key === key) ?? null };
}
