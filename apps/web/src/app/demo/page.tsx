import { headers } from 'next/headers';
import { ReportWorkspace } from '../../components/report-workspace.tsx';
import { SubmissionForm } from '../../components/submission-form.tsx';
import { demoQuestions, demoWorkspace, isBuiltinDemoDocument, isDemoConfigured } from '../../lib/scaffold/demo.ts';
import type { DemoAnswer } from '../../lib/scaffold/demo.ts';
import { readBrowserSession } from '../../lib/sessions/browser.ts';
import { getSessionStore } from '../../lib/sessions/route.ts';

export const dynamic = 'force-dynamic';

function ownedDocument(requestHeaders: Awaited<ReturnType<typeof headers>>, id: string | string[] | undefined) {
  if (typeof id !== 'string' || !/^[0-9a-f-]{36}$/.test(id)) return null;
  const store = getSessionStore();
  const owner = readBrowserSession(store, requestHeaders);
  if (owner === null) return null;
  const result = store.getDocument(owner, id);
  return 'kind' in result ? null : result;
}

const routeNames = { document: 'Document', literature: 'Literature', mixed: 'Document and literature', none: 'None' };
const stateNames = { sufficient: 'Sufficient evidence', partial: 'Partial evidence',
  insufficient: 'Insufficient evidence', unavailable: 'Answer unavailable' };

function Answer({ answer, href }: { answer: DemoAnswer; href: string }) {
  return <section aria-label="Mock answer" data-answer-route={answer.route} data-answer-state={answer.state}>
    <h4>{stateNames[answer.state]}</h4>
    <p className="section-state">Sources: {routeNames[answer.route]}</p>
    {answer.branches.map(({ origin, answer: branch }) => <section key={origin} aria-label={routeNames[origin]}>
      <h5>{routeNames[origin]}</h5>
      {!branch ? <p className="state-message">{routeNames[origin]} answer unavailable. Try the example again.</p>
        : <>
          {branch.claims.length === 0 && <p>{branch.text}</p>}
          <ul className="claims">{branch.claims.map(claim => <li key={claim.claim_id}>
            <p>{claim.text}</p>
            {claim.source_ids.map(id => {
              const index = branch.sources.findIndex(source => source.source_id === id);
              const source = branch.sources[index];
              if (!source) return null;
              return source.kind === 'document'
                ? <a className="citation" key={id} href={`${href}&evidence=answer-${origin}-${index}#document-passage`}>View document evidence</a>
                : <div key={id}><cite>{source.title}</cite>
                  <blockquote>{source.text}</blockquote>
                  {source.url.startsWith('https://') && <a className="citation" href={source.url}>Literature source URL</a>}</div>;
            })}
          </li>)}</ul>
          {branch.warnings.length > 0 && <ul className="caution">{branch.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul>}
        </>}
    </section>)}
  </section>;
}

export default async function DemoPage({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  if (!isDemoConfigured()) {
    return <main><h1>NoteLens mock demo</h1><p>Start the local mock stack to open this workspace.</p></main>;
  }
  const query = await searchParams;
  const document = ownedDocument(await headers(), query.document);
  const { view, question, answer } = await demoWorkspace(query, document);
  const builtin = isBuiltinDemoDocument(view.document);
  const reportHref = document ? `/demo?document=${document.doc_id}` : '/demo';
  const evidenceHref = question ? `${reportHref}&question=${question}` : reportHref;
  const picker = <>
    <form action="/api/documents/builtin" method="post">
      <button type="submit">Chest pain report</button>
    </form>
    {query.prepare === 'unavailable' && <p role="status">The example could not be prepared. Return to an open report or try opening a new session.</p>}
    <p>Use public or synthetic English documents. PDFs must have selectable text and be 2 MiB or smaller. Documents may contain up to 100,000 Unicode code points.</p>
    <div className="submission-grid"><SubmissionForm input="text" /><SubmissionForm input="pdf" /></div>
  </>;
  const questions = builtin ? <>
    <p>Choose a preset question for this synthetic report.</p>
    <ul>{demoQuestions.map(({ key, label }) => <li key={key}>
      <a href={`${reportHref}&question=${key}#questions-heading`} aria-current={question === key ? 'page' : undefined}>{label}</a>
    </li>)}</ul>
    {answer && <Answer answer={answer} href={evidenceHref} />}
  </> : <p>Choose the built-in example to see its preset questions.</p>;
  return <ReportWorkspace view={view} demo={{ picker, evidenceHref, questions }} />;
}
