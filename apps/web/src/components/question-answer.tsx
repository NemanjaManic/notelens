import type { RoutedAnswer } from '../lib/routing/answer.ts';
import { sourceLink } from '../lib/security/source-link.ts';
import type { EvaluationProfile } from '../lib/clients/bounded-evaluation.ts';

const routeNames = { document: 'Document', literature: 'Literature', mixed: 'Document and literature', none: 'None' };
const stateNames = { sufficient: 'Sufficient evidence', partial: 'Partial evidence',
  insufficient: 'Insufficient evidence', unavailable: 'Answer unavailable', unsupported: 'Question outside demo scope' };

export function QuestionAnswer({ answer, href, evaluation }: { answer: RoutedAnswer; href?: string; evaluation?: EvaluationProfile }) {
  const savedReplay = !evaluation && answer.branches.some(({ result }) => result.kind === 'accepted' && result.record.mode === 'live');
  const label = evaluation === 'public-live' ? 'Live answer' : evaluation ? 'Bounded evaluation answer' : savedReplay ? 'Saved document answer replay' : 'Mock answer';
  return <section aria-label={label} data-answer-route={answer.route} data-answer-state={answer.state}>
    <h4>{stateNames[answer.state]}</h4>
    <p className="section-state">Sources: {routeNames[answer.route]}</p>
    {answer.state === 'unsupported' && <p>{evaluation === 'public-live'
      ? 'NoteLens cannot answer this question from the document or the literature corpus.'
      : 'This local demo answers a limited set of questions. Try a preset.'}</p>}
    {answer.branches.map(({ origin, result }) => <section key={origin} aria-label={routeNames[origin]}>
      <h5>{routeNames[origin]}</h5>
      {savedReplay && result.kind === 'accepted' && result.record.mode === 'live' && <p className="muted">Saved-response replay</p>}
      {result.kind !== 'accepted' ? <p className="state-message">{result.kind === 'invalid'
        ? `The ${origin} answer could not be verified.`
        : result.kind === 'unsupported' ? 'This question is outside the literature mock’s supported set. Try a preset.'
          : `${routeNames[origin]} answer unavailable. Try again.`}</p>
        : <>
          {result.record.claims.length === 0 && <><p>{result.record.text}</p>
            {origin === 'document' && result.record.mode === 'mock' &&
              <p>This document mock answers a limited set of questions. Try a preset.</p>}</>}
          <ul className="claims">{result.record.claims.map(claim => <li key={claim.claim_id}>
            <p>{claim.text}</p>
            {claim.source_ids.map(id => {
              const index = result.record.sources.findIndex(source => source.source_id === id);
              const source = result.record.sources[index];
              if (!source) return null;
              if (source.kind === 'document') {
                return href ? <a className="citation" key={id} href={`${href}&evidence=answer-${origin}-${index}#document-passage`}>View document evidence</a>
                  : <details key={id}><summary>View document evidence</summary><blockquote>{source.evidence.quote}</blockquote></details>;
              }
              const url = sourceLink(source.url);
              return <div key={id}><cite>{source.title}</cite>
                <blockquote>{source.text}</blockquote>
                {url && <a className="citation" href={url} rel="noreferrer">Literature source URL</a>}</div>;
            })}
          </li>)}</ul>
          {result.record.warnings.length > 0 && <ul className="caution">{result.record.warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul>}
        </>}
    </section>)}
  </section>;
}
