'use client';

import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';
import type { Workspace } from '../lib/report/model.ts';
import { evidenceParts } from '../lib/report/evidence.ts';
import { cardiologyExample, cardiologySpan, cardiologyText } from './reader-example.ts';

type Tab = 'explanation' | 'questions';
type Props = {
  view: Workspace;
  picker: ReactNode;
  questions: ReactNode;
  children: ReactNode;
  profile: string;
  privacy: string;
};
type Position = { note: number; line: number; left: number; width: number };

export function ReaderShell({ view, picker, questions, children, profile, privacy }: Props) {
  const [curated, setCurated] = useState(false);
  const [tab, setTab] = useState<Tab>('explanation');
  const [position, setPosition] = useState<Position | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const grid = useRef<HTMLDivElement>(null);
  const report = useRef<HTMLDivElement>(null);
  const sidebar = useRef<HTMLElement>(null);
  const tabs = useRef<HTMLDivElement>(null);
  const note = useRef<HTMLElement>(null);
  const connector = useRef<HTMLSpanElement>(null);
  const explanationTab = useRef<HTMLButtonElement>(null);
  const questionsTab = useRef<HTMLButtonElement>(null);
  const selected = curated ? { key: 'curated-1', label: cardiologyExample.annotation.title, span: cardiologySpan } : view.selected;
  const text = curated ? cardiologyText : view.document?.text;
  const valid = text && selected ? evidenceParts(text, selected.span) : null;
  const title = curated ? cardiologyExample.title : view.document
    ? view.document.source.name === 'Synthetic contract fixture' && view.document.text.startsWith('Demo ')
      ? 'Chest pain report' : view.document.source.name
    : view.heading;
  const subtitle = curated ? cardiologyExample.subtitle : view.document?.source.kind === 'text_pdf'
    ? 'Text-based PDF' : view.document?.source.kind === 'synthetic_text' ? 'Synthetic report' : 'English report';
  const annotationTitle = curated ? cardiologyExample.annotation.title : selected?.label;

  useEffect(() => {
    function syncLocation() {
      const query = new URLSearchParams(window.location.search);
      const example = query.get('example') === cardiologyExample.id;
      setCurated(example);
      setTab(!example && (query.has('turn') || window.location.hash === '#questions-heading') ? 'questions' : 'explanation');
    }
    syncLocation();
    window.addEventListener('popstate', syncLocation);
    window.addEventListener('hashchange', syncLocation);
    return () => {
      window.removeEventListener('popstate', syncLocation);
      window.removeEventListener('hashchange', syncLocation);
    };
  }, [view.document?.doc_id, view.selected?.key]);

  useEffect(() => {
    if (!valid || tab !== 'explanation') { setPosition(null); return; }
    let active = true;
    let frame = 0;
    function measure() {
      const mark = report.current?.querySelector('mark');
      if (!mark || !grid.current || !sidebar.current || !tabs.current) { setPosition(null); return; }
      const rects = mark.getClientRects();
      const span = rects[rects.length - 1];
      if (!span) { setPosition(null); return; }
      const area = grid.current.getBoundingClientRect();
      const column = sidebar.current.getBoundingClientRect();
      const baseline = span.top + span.height * .6;
      const minimum = tabs.current.getBoundingClientRect().bottom - column.top + 24;
      const top = Math.max(minimum, baseline - column.top - 40);
      const left = span.right - area.left + 24;
      setPosition({ note: top - (tabs.current.getBoundingClientRect().bottom - column.top), line: baseline - area.top, left, width: Math.max(0, column.left - area.left + 5 - left) });
    }
    const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(measure); };
    const observer = new ResizeObserver(schedule);
    if (grid.current) observer.observe(grid.current);
    if (report.current) observer.observe(report.current);
    if (note.current) observer.observe(note.current);
    window.addEventListener('resize', schedule);
    void document.fonts.ready.then(() => { if (active) schedule(); });
    schedule();
    return () => { active = false; cancelAnimationFrame(frame); observer.disconnect(); window.removeEventListener('resize', schedule); };
  }, [text, selected?.key, tab, Boolean(valid)]);

  useEffect(() => {
    // CSSOM updates preserve the existing policy that blocks inline style attributes.
    if (!position) return;
    note.current?.style.setProperty('--note-top', `${position.note}px`);
    if (connector.current) {
      connector.current.style.top = `${position.line}px`;
      connector.current.style.left = `${position.left}px`;
      connector.current.style.width = `${position.width}px`;
    }
  }, [position]);

  useEffect(() => {
    if (!curated && valid && window.location.hash === '#document-passage') showPassage();
  }, [curated, view.selected?.key, Boolean(valid)]);

  function showPassage() {
    const target = report.current?.querySelector('mark');
    if (!target) return;
    target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center' });
  }

  function chooseExample(example: boolean) {
    const url = new URL(window.location.href);
    if (example) { url.searchParams.set('example', cardiologyExample.id); url.hash = ''; }
    else url.searchParams.delete('example');
    window.history.pushState(null, '', url);
    setCurated(example);
    setTab(!example && url.searchParams.has('turn') ? 'questions' : 'explanation');
    dialog.current?.close();
  }

  function tabKey(event: KeyboardEvent<HTMLButtonElement>) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 'explanation' : event.key === 'End' ? 'questions' : tab === 'explanation' ? 'questions' : 'explanation';
    setTab(next);
    (next === 'explanation' ? explanationTab : questionsTab).current?.focus();
  }

  function renderText(value: string, offset = 0) {
    const length = Array.from(value).length;
    if (!valid || !selected || selected.span.end <= offset || selected.span.start >= offset + length) return value;
    const points = Array.from(value);
    const start = Math.max(0, selected.span.start - offset);
    const end = Math.min(length, selected.span.end - offset);
    return <>{points.slice(0, start).join('')}<mark>{points.slice(start, end).join('')}</mark><sup className="passage-number" aria-label="Annotation 1" aria-describedby="selected-annotation">1</sup>{points.slice(end).join('')}</>;
  }

  let sectionOffset = 0;
  return <main className="reader">
    <a className="skip-link" href="#report-content">Skip to report</a>
    <header className="reader-header">
      <nav className="breadcrumbs" aria-label="Breadcrumb">
        <a className="wordmark" href="/">NoteLens</a><span aria-hidden="true">/</span>
        <button type="button" onClick={() => dialog.current?.showModal()}>Examples</button><span aria-hidden="true">/</span>
        <span className="breadcrumb-title" aria-current="page">{title}</span>
      </nav>
      <button type="button" className="open-example" onClick={() => dialog.current?.showModal()}>Open example</button>
    </header>
    <dialog ref={dialog} className="example-dialog" aria-labelledby="example-dialog-title" onClick={event => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
      <div className="dialog-heading"><h2 id="example-dialog-title">Open a report</h2><button type="button" onClick={() => dialog.current?.close()}>Close</button></div>
      <aside className="notices"><strong>This demonstration does not replace a doctor.</strong><p>Do not upload real personal medical reports.</p></aside>
      <section className="examples" aria-label="Synthetic examples"><h3>Choose an example</h3>
        <button type="button" onClick={() => chooseExample(true)}>Cardiology follow-up</button>
        <p className="muted">Curated synthetic example with a prepared explanation. No model call.</p>
        {curated && view.document && <p><button type="button" onClick={() => chooseExample(false)}>Return to open report</button></p>}
        {picker}
      </section>
      <p className="privacy">{privacy}</p><p className="muted">Processing mode: {profile}</p>
    </dialog>
    <div className="reader-body">
      <div ref={grid} className="reader-grid" id="report-content">
        <section className="report-sheet" aria-labelledby="report-heading">
          <div className="paper-heading"><h1 id="report-heading">{title}</h1><p>{subtitle}</p></div>
          <h2 className="sr-only">Canonical document</h2>
          <div ref={report} className={`canonical-text${curated ? ' structured-report' : ''}`} id="document-passage" tabIndex={-1} aria-label="Canonical document text">
            {curated ? cardiologyExample.sections.map((section, index) => {
              const offset = sectionOffset;
              sectionOffset += Array.from(`${section.heading}\n${section.text}`).length + 2;
              return <section className="report-section" key={section.heading}><h2>{section.heading}</h2>{'\n'}<p>{renderText(section.text, offset + Array.from(`${section.heading}\n`).length)}</p>{index < cardiologyExample.sections.length - 1 ? '\n\n' : ''}</section>;
            }) : text ? renderText(text) : <p className="state-message">{view.scenario === 'no-document' ? 'Choose a synthetic example to begin.' : 'The document is unavailable. Choose a synthetic example.'}</p>}
          </div>
        </section>
        <aside ref={sidebar} className="reader-sidebar" aria-label="Report companion">
          <div ref={tabs} role="tablist" aria-label="Report tools" className="reader-tabs">
            <button ref={explanationTab} type="button" role="tab" id="explanation-tab" aria-controls="explanation-panel" aria-selected={tab === 'explanation'} tabIndex={tab === 'explanation' ? 0 : -1} onKeyDown={tabKey} onClick={() => setTab('explanation')}>Explanation</button>
            <button ref={questionsTab} type="button" role="tab" id="questions-tab" aria-controls="questions-panel" aria-selected={tab === 'questions'} tabIndex={tab === 'questions' ? 0 : -1} onKeyDown={tabKey} onClick={() => setTab('questions')}>Questions</button>
          </div>
          <div role="tabpanel" id="explanation-panel" aria-labelledby="explanation-tab" hidden={tab !== 'explanation'} tabIndex={0}>
            {valid && <article ref={note} id="selected-annotation" className="margin-note" aria-label="Selected document evidence">
              <h2><span className="annotation-number">1</span>{annotationTitle}</h2>
              {curated ? <p>{cardiologyExample.annotation.text}</p> : <blockquote>{valid.quote}</blockquote>}
              <a href="#document-passage" onClick={event => { event.preventDefault(); showPassage(); }}>Show in report</a>
              {!curated && <details><summary>Evidence details</summary><p>Source: document evidence · code points [{selected!.span.start}, {selected!.span.end})</p></details>}
            </article>}
            {!curated && <details className="analysis-details" open={!valid}><summary>Summary, findings and specialty</summary>{children}</details>}
          </div>
          <div role="tabpanel" id="questions-panel" aria-labelledby="questions-tab" hidden={tab !== 'questions'} tabIndex={0}>
            <section className="questions-content" aria-labelledby="questions-heading"><h2 id="questions-heading">Questions and literature</h2>
              {curated ? <><p>This curated example includes a prepared explanation. Open a processed report to ask questions.</p><button type="button" onClick={() => dialog.current?.showModal()}>Open a report</button></> : questions}
            </section>
          </div>
        </aside>
        {position && valid && tab === 'explanation' && <span ref={connector} aria-hidden="true" className="annotation-connector" />}
      </div>
      <footer className="reader-footer">Educational demo · {curated || view.document?.source.kind === 'synthetic_text' ? 'Synthetic report' : 'English report'}</footer>
    </div>
  </main>;
}
