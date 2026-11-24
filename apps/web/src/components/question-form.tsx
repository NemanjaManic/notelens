'use client';

import { useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import type { DemoQuestion } from '../lib/routing/demo-questions.ts';
import type { QuestionTurn } from '../lib/sessions/memory.ts';
import { QuestionAnswer } from './question-answer.tsx';
import type { EvaluationProfile } from '../lib/clients/bounded-evaluation.ts';

type Scope = 'document' | 'literature' | 'both';
type QuestionResponse = { kind: 'saved'; id: string } | { kind: 'transient'; turn: QuestionTurn } | { notice: string };

export function QuestionForm({ documentId, presets, hasHistory, children, evaluation }: {
  documentId: string;
  presets: { key: DemoQuestion; label: string }[];
  hasHistory: boolean;
  children: ReactNode;
  evaluation?: EvaluationProfile;
}) {
  const [scope, setScope] = useState<Scope>('document');
  const [action, setAction] = useState<'ask' | 'clear' | null>(null);
  const [notice, setNotice] = useState('');
  const [transient, setTransient] = useState<QuestionTurn>();
  const pending = useRef(false);
  const form = useRef<HTMLFormElement>(null);
  const report = `/demo?document=${documentId}`;

  async function send(body?: object) {
    if (pending.current) return;
    pending.current = true;
    setAction(body ? 'ask' : 'clear');
    setNotice('');
    try {
      const response = body
        ? await fetch('/api/questions', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ document: documentId, ...body }), cache: 'no-store',
        })
        : await fetch(`/api/questions?document=${documentId}`, { method: 'DELETE', cache: 'no-store' });
      if (!body && response.status === 204) {
        setTransient(undefined);
        window.location.replace(`${report}#questions-heading`);
        return;
      }
      const result: QuestionResponse = await response.json();
      if ('notice' in result) {
        setNotice(result.notice);
      } else if (result.kind === 'saved') {
        window.location.assign(`${report}&turn=${result.id}#questions-heading`);
      } else {
        form.current?.reset();
        setTransient(result.turn);
        setNotice('This answer exceeds the history size limit and is available on this page only.');
      }
    } catch {
      setNotice(body ? 'The question service is unavailable. Try again.' : 'Conversation history could not be cleared. Try again.');
    } finally {
      pending.current = false;
      setAction(null);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    void send({
      scope,
      ...(scope !== 'literature' && { documentQuestion: values.get('documentQuestion') }),
      ...(scope !== 'document' && { literatureQuestion: values.get('literatureQuestion') }),
    });
  }

  return <>
    <form ref={form} action="/api/questions" method="post" autoComplete="off" onSubmit={submit}>
      <p id="question-help">Ask a self-contained English question, up to 1,000 Unicode code points in total. This local demo answers a limited set of questions.</p>
      <fieldset disabled={action !== null} aria-describedby="question-help">
        <label htmlFor="question-source">Source</label>{' '}
        <select id="question-source" value={scope} onChange={event => setScope(event.target.value as Scope)}>
          <option value="document">Document</option>
          <option value="literature">Literature</option>
          <option value="both">Both</option>
        </select>
        {scope !== 'literature' && <p><label htmlFor="document-question">Document question</label><br />
          <textarea id="document-question" name="documentQuestion" rows={3} required /></p>}
        {scope !== 'document' && <p><label htmlFor="literature-question">Literature question</label><br />
          <textarea id="literature-question" name="literatureQuestion" rows={3} required /></p>}
        <button type="submit">Ask question</button>
      </fieldset>
    </form>
    <details>
      <summary>Try a preset question</summary>
      <ul>{presets.map(({ key, label }) => <li key={key}>
        <button type="button" disabled={action !== null} onClick={() => void send({ preset: key })}>{label}</button>
      </li>)}</ul>
    </details>
    {(hasHistory || transient) && <button type="button" disabled={action !== null} onClick={() => void send()}>Clear conversation history</button>}
    <p role="status">{action === 'ask' ? evaluation ? 'Waiting for the answer…' : 'Waiting for the mock answer…'
      : action === 'clear' ? 'Clearing conversation history…' : notice}</p>
    {transient ? <QuestionAnswer answer={transient.answer} evaluation={evaluation} /> : children}
  </>;
}
