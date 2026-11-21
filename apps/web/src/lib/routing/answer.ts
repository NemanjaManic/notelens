import type { AnswerResult, PreparedDocument } from '@notelens/contracts/v1';
import type { MockResult, MockServiceClients } from '../clients/mock-services.ts';
import type { QuestionPlan } from './demo-questions.ts';

type Origin = 'document' | 'literature';
type Branch = { origin: Origin; result: MockResult<AnswerResult> };
export type RoutedAnswer = {
  route: Origin | 'mixed' | 'none';
  state: 'sufficient' | 'partial' | 'insufficient' | 'unavailable' | 'unsupported';
  branches: Branch[];
};

function branch(origin: Origin, result: MockResult<AnswerResult>): Branch {
  if (result.kind !== 'accepted') return { origin, result };
  const answer = result.record;
  if (answer.attempted_routes.length !== 1 || answer.attempted_routes[0] !== origin) {
    return { origin, result: { kind: 'invalid' } };
  }
  if (answer.route === 'none' && answer.evidence_state === 'insufficient' && answer.claims.length === 0) {
    return { origin, result };
  }
  if (answer.route !== origin || answer.evidence_state === 'insufficient' || !answer.claims.length ||
    answer.sources.some(source => source.kind !== origin)) return { origin, result: { kind: 'invalid' } };

  const scoped = (id: string) => `${origin}:${id}`;
  return { origin, result: { kind: 'accepted', record: {
    ...answer,
    claims: answer.claims.map(claim => ({
      ...claim, claim_id: scoped(claim.claim_id), component_id: scoped(claim.component_id),
      source_ids: claim.source_ids.map(scoped),
    })),
    sources: answer.sources.map(source => ({
      ...source, source_id: scoped(source.source_id), component_id: scoped(source.component_id),
    })),
    components: answer.components.map(component => ({ ...component, component_id: scoped(component.component_id) })),
  } } };
}

export async function routeQuestion(clients: Pick<MockServiceClients, 'documentAnswer' | 'literatureAnswer'>,
  plan: QuestionPlan, document: PreparedDocument): Promise<RoutedAnswer> {
  const pending: Promise<Branch>[] = [];
  if (plan.document) pending.push(clients.documentAnswer(document, plan.document).then(result => branch('document', result)));
  // A's answer endpoint performs retrieval and decides whether generation should run.
  if (plan.literature) pending.push(clients.literatureAnswer(plan.literature).then(result => branch('literature', result)));
  if (!pending.length) return { route: 'none', state: 'unsupported', branches: [] };
  const branches = await Promise.all(pending);
  const supported = branches.filter(({ result }) => result.kind === 'accepted' && result.record.claims.length > 0);
  if (!supported.length) {
    const state = branches.some(({ result }) => result.kind === 'unavailable' || result.kind === 'invalid')
      ? 'unavailable' : branches.some(({ result }) => result.kind === 'unsupported') ? 'unsupported' : 'insufficient';
    return { route: 'none', state, branches };
  }
  const partial = supported.length < branches.length ||
    supported.some(({ result }) => result.kind === 'accepted' && result.record.evidence_state === 'partial');
  return { route: supported.length === 2 ? 'mixed' : supported[0].origin, state: partial ? 'partial' : 'sufficient', branches };
}
