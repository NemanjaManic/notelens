import { headers } from 'next/headers';
import { Suspense } from 'react';
import type { PreparedDocument } from '@notelens/contracts/v1';
import { BuiltinExampleButton } from '../../components/builtin-example-button.tsx';
import { ReportWorkspace } from '../../components/report-workspace.tsx';
import { SubmissionForm } from '../../components/submission-form.tsx';
import { QuestionAnswer } from '../../components/question-answer.tsx';
import { QuestionForm } from '../../components/question-form.tsx';
import { demoWorkspace, isBuiltinDemoDocument, isDemoConfigured, selectDemoEvidence } from '../../lib/scaffold/demo.ts';
import { demoQuestions } from '../../lib/routing/demo-questions.ts';
import { DOCUMENT_ID } from '../../lib/routing/question-input.ts';
import { readBrowserSession } from '../../lib/sessions/browser.ts';
import { getSessionStore } from '../../lib/sessions/route.ts';

export const dynamic = 'force-dynamic';
type DemoQuery = Record<string, string | string[] | undefined>;

function ownedDocument(owner: string | null, id: DemoQuery[string]) {
  if (typeof id !== 'string' || !DOCUMENT_ID.test(id)) return null;
  if (owner === null) return null;
  const result = getSessionStore().getDocument(owner, id);
  return 'kind' in result ? null : result;
}

async function DemoReport({ query, owner, document }: {
  query: DemoQuery;
  owner: string | null;
  document: PreparedDocument | null;
}) {
  const workspace = await demoWorkspace(query, document);
  // Recheck document ownership and history after the report services respond.
  const history = owner && workspace.document ? getSessionStore().questionHistory(owner, workspace.document.doc_id) : null;
  const turn = history?.find(item => item.id === query.turn);
  const view = selectDemoEvidence(workspace.document && !history ? await demoWorkspace(query, null) : workspace,
    query.evidence, turn?.answer);
  const builtin = isBuiltinDemoDocument(view.document);
  const reportHref = view.document ? `/demo?document=${view.document.doc_id}` : '/demo';
  const evidenceHref = turn ? `${reportHref}&turn=${turn.id}` : reportHref;
  const picker = <>
    <BuiltinExampleButton />
    {query.prepare === 'unavailable' && <p role="status">The example could not be prepared. Return to an open report or try opening a new session.</p>}
    <p>Use public or synthetic English documents. PDFs must have selectable text and be 2 MiB or smaller. Documents may contain up to 100,000 Unicode code points.</p>
    <div className="submission-grid"><SubmissionForm input="text" /><SubmissionForm input="pdf" /></div>
  </>;
  const questions = view.document ? <>
    <QuestionForm documentId={view.document.doc_id} presets={demoQuestions(builtin)} hasHistory={Boolean(history?.length)}>
      {query.turn !== undefined && !turn && <p role="status">This answer is no longer in the conversation history.</p>}
      {turn && <>
        {turn.plan.document && turn.plan.literature ? <ul>
          <li>Document: {turn.plan.document}</li><li>Literature: {turn.plan.literature}</li>
        </ul> : <p>{turn.plan.label}</p>}
        <QuestionAnswer answer={turn.answer} href={evidenceHref} />
      </>}
    </QuestionForm>
    {history && history.length > 0 && <section aria-label="Conversation history">
      <h4>Conversation history</h4>
      <ul>{[...history].reverse().map(item => <li key={item.id}>
        <a href={`${reportHref}&turn=${item.id}#questions-heading`} aria-current={turn?.id === item.id ? 'page' : undefined}>
          {item.plan.label}
        </a>
      </li>)}</ul>
    </section>}
  </> : <p>Open a document to ask a question.</p>;
  return <ReportWorkspace view={view} demo={{ picker, evidenceHref, questions }} />;
}

export default async function DemoPage({ searchParams }: { searchParams: Promise<DemoQuery> }) {
  if (!isDemoConfigured()) {
    return <main><h1>NoteLens mock demo</h1><p>Start the local mock stack to open this workspace.</p></main>;
  }
  const [query, requestHeaders] = await Promise.all([searchParams, headers()]);
  const owner = readBrowserSession(getSessionStore(), requestHeaders);
  const document = ownedDocument(owner, query.document);
  const report = <DemoReport query={query} owner={owner} document={document} />;
  if (!document) return report;

  return <Suspense fallback={<main>
    <h1>Opening report</h1>
    <p className="state-message" role="status">Loading report analysis…</p>
  </main>}>
    {report}
  </Suspense>;
}
