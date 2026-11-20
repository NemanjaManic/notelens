import type { RoutedAnswer } from '../lib/routing/answer.ts';

const routeNames = { document: 'Document', literature: 'Literature', mixed: 'Document and literature', none: 'None' };
const stateNames = { sufficient: 'Sufficient evidence', partial: 'Partial evidence',
  insufficient: 'Insufficient evidence', unavailable: 'Answer unavailable', unsupported: 'Question outside demo scope' };

export function QuestionAnswer({ answer, href }: { answer: RoutedAnswer; href?: string }) {
  return <section aria-label="Mock answer" data-answer-route={answer.route} data-answer-state={answer.state}>
    <h4>{stateNames[answer.state]}</h4>
    <p className="section-state">Sources: {routeNames[answer.route]}</p>
    {answer.state === 'unsupported' && <p>This local demo answers a limited set of questions. Try a preset.</p>}
    {answer.branches.map(({ origin, result }) => <section key={origin} aria-label={routeNames[origin]}>
      <h5>{routeNames[origin]}</h5>
      {result.kind !== 'accepted' ? <p className="state-message">{result.kind === 'invalid'
        ? `The ${origin} answer could not be verified.`
        : result.kind === 'unsupported' ? 'This question is outside the literature mock’s supported set. Try a preset.'
          : `${routeNames[origin]} answer unavailable. Try again.`}</p>
        : <>
          {result.record.claims.length === 0 && <><p>{result.record.text}</p>
            {origin === 'document' && <p>This document mock answers a limited set of questions. Try a preset.</p>}</>}
          <ul className="claims">{result.record.claims.map(claim => <li key={claim.claim_id}>
            <p>{claim.text}</p>
            {claim.source_ids.map(id => {
              const index = result.record.sources.findIndex(source => source.source_id === id);
              const source = result.record.sources[index];
              if (!source) return null;
              return source.kind === 'document'
                ? (href ? <a className="citation" key={id} href={`${href}&evidence=answer-${origin}-${index}#document-passage`}>View document evidence</a>
                  : <details key={id}><summary>View document evidence</summary><blockquote>{source.evidence.quote}</blockquote></details>)
                : <div key={id}><cite>{source.title}</cite>
                  <blockquote>{source.text}</blockquote>
                  {source.url.startsWith('https://') && <a className="citation" href={source.url}>Literature source URL</a>}</div>;
            })}
          </li>)}</ul>
          {result.record.warnings.length > 0 && <ul className="caution">{result.record.warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul>}
        </>}
    </section>)}
  </section>;
}
