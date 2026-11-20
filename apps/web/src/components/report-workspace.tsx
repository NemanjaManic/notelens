import type { Workspace, Passage } from '../lib/report/model.ts';
import type { ReactNode } from 'react';
import { SCENARIOS } from '../lib/report/model.ts';
import { evidenceParts } from '../lib/report/evidence.ts';

type DemoPanel = { picker: ReactNode; evidenceHref: string; questions: ReactNode };

export function ReportWorkspace({ view, demo }: { view: Workspace; demo?: DemoPanel }) {
  const evidenceHref = demo?.evidenceHref ?? `?scenario=${view.scenario}`;
  const passageLink = (passage: Passage) => `${evidenceHref}&evidence=${passage.key}#document-passage`;
  const classification = view.classification.state === 'ready' ? view.classification.record : null;
  const extraction = view.extraction.state === 'ready' ? view.extraction.record : null;
  const summary = extraction?.summary.status === 'completed' ? extraction.summary.result : null;
  const selected = view.document && view.selected ? evidenceParts(view.document.text, view.selected.span) : null;
  return <main>
    <a className="skip-link" href="#report-content">Skip to report</a>
    <header><a className="wordmark" href={demo ? '/demo' : '/'}>NoteLens</a><span className="badge">Mock mode</span></header>
    <section className="welcome" aria-labelledby="workspace-title">
      <p className="eyebrow">Educational demonstration</p><h1 id="workspace-title">Explore a report, with its evidence.</h1>
      <p className="intro">{demo ? 'Open a built-in example or prepare a public or synthetic document.' : 'Inspect a synthetic example and follow each finding back to its exact passage.'}</p>
      <aside className="notices" aria-label="Demo notices"><strong>This demonstration does not replace a doctor.</strong>
        <p>Do not upload real personal medical reports.{demo ? '' : ' This workspace displays versioned synthetic examples only.'}</p></aside>
    </section>
    {demo ? <nav className="examples" aria-label="Synthetic examples"><h2>Choose an example</h2>
      {demo.picker}
    </nav> : <nav className="examples" aria-label="Synthetic example states">
      <h2>Browse fixture previews</h2><p>These links demonstrate UI states. No analysis or service request is started.</p>
      <ul>{SCENARIOS.map(([key, label]) => <li key={key}><a href={`?scenario=${key}`} aria-current={view.scenario === key ? 'page' : undefined}>{label}</a></li>)}</ul>
    </nav>}
    <section id="report-content" aria-labelledby="report-heading">
      <div className="report-heading"><div><p className="eyebrow">{demo ? 'English document' : 'Synthetic report · English'}</p><h2 id="report-heading">{view.heading}</h2></div><span className="badge">{demo ? 'Local mocks' : 'Fixture preview'}</span></div>
      <p className="privacy">{demo ? 'Documents stay in server memory for up to 60 minutes and are cleared when the session ends or the server restarts.'
        : 'Submitted reports are not accepted here. The planned submission flow keeps documents in server memory for at most 60 minutes and loses them on restart.'}</p>
      <div className="report-grid">
        <section className="panel document-panel" aria-labelledby="document-heading">
          <h3 id="document-heading">Canonical document</h3>
          {view.document ? <><p className="muted">Canonical text.{view.passages.length > 0 && ' Select a passage link to highlight its exact occurrence.'}</p>
            <div className="canonical-text" id="document-passage" tabIndex={-1} aria-label="Canonical document text">
              {selected ? <>{selected.before}<mark>{selected.quote}</mark>{selected.after}</> : view.document.text}
            </div>
            {selected && view.selected ? <aside className="source-details" aria-label="Selected document evidence">
              <strong>{view.selected.label}</strong><p>Source: document evidence · code points [{view.selected.span.start}, {view.selected.span.end})</p>
              <blockquote>{selected.quote}</blockquote><a href={`${evidenceHref}#document-passage`}>Clear highlight</a>
            </aside> : <p className="muted">No passage selected.</p>}
          </> : <p className="state-message">{view.scenario === 'no-document' ? 'Choose a synthetic example to begin.' : 'The document is unavailable. Choose a synthetic example.'}</p>}
        </section>
        <div className="report-sections">
          <section className="panel" aria-labelledby="specialty-heading"><h3 id="specialty-heading">Document specialty</h3>
            {classification ? <><p className="result-label">{classification.status === 'supported' ? classification.category
              : classification.status === 'uncertain' ? 'Specialty uncertain' : 'Outside the supported specialties'}</p>
              <p>{classification.confidence_note}</p><p className="muted">{classification.classification_execution === 'skipped' ? 'Classification was not run.' : 'Classification was performed on this fixture.'} Specialty is a document label, not a diagnosis.</p>
              {classification.scope_reason && <p>{classification.scope_reason}</p>}
              {classification.scores.length > 0 && <details><summary>Score details and limitations</summary>
                <p>Score kind: {classification.score_kind}. Scores are not clinical confidence.</p>
                <ul>{classification.scores.map(s => <li key={s.category}>{s.category}: {s.score}</li>)}</ul>
                <p>Model version: {classification.model_version}</p></details>}
            </> : <p className="state-message">{view.classification.state !== 'ready' && view.classification.notice}</p>}
          </section>
          <section className="panel" aria-labelledby="findings-heading"><h3 id="findings-heading">Document findings</h3>
            {extraction ? extraction.extraction_status === 'failed' ? <p className="state-message">Findings unavailable. The independent summary is shown when supported.</p>
              : <><p className="section-state">Extraction: {extraction.extraction_status}</p>
                {extraction.extraction_status === 'partial' && <p className="caution">Some findings are unavailable. Only the supplied supported items are shown.</p>}
                {extraction.items.length === 0 && <p>No findings were returned for this document. This does not establish an absence of medical conditions.</p>}
                <ul className="findings">{extraction.items.map((item, i) => <li key={item.entity_id}>
                  <h4>{item.name}</h4><dl className="attributes"><div><dt>Type</dt><dd>{item.type}</dd></div>
                    <div><dt>Assertion</dt><dd>{item.assertion}</dd></div><div><dt>Temporality</dt><dd>{item.temporality}</dd></div>
                    <div><dt>Subject</dt><dd>{item.subject}</dd></div>{item.procedure_status && <div><dt>Procedure status</dt><dd>{item.procedure_status}</dd></div>}</dl>
                  {item.icd && <p>Source ICD code: {item.icd.code}</p>}
                  <ul className="passages">{view.passages.filter(p => p.key.startsWith(`finding-${i}-`)).map(p => <li key={p.key}><a href={passageLink(p)}>View passage {Number(p.key.split('-')[2]) + 1}</a><q>{p.span.quote}</q></li>)}</ul>
                </li>)}</ul>
                {extraction.warnings.length > 0 && <ul className="caution">{extraction.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>}
              </> : <p className="state-message">{view.extraction.state !== 'ready' && view.extraction.notice}</p>}
          </section>
          <section className="panel" aria-labelledby="summary-heading"><h3 id="summary-heading">Document summary</h3>
            {summary ? <><p className="section-state">Evidence: {summary.evidence_state}</p>{summary.claims.length === 0 && <p>{summary.text}</p>}
              <ul className="claims">{summary.claims.map(claim => <li key={claim.claim_id}><p>{claim.text}</p><p className="muted">Document-supported claim</p>
                {claim.source_ids.map(id => { const p = view.passages.find(p => p.sourceId === id); return p ? <a className="citation" key={id} href={passageLink(p)}>{p.label} · document</a> : null; })}</li>)}</ul>
              {summary.warnings.length > 0 && <ul className="caution">{summary.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>}
            </> : <p className="state-message">{extraction ? 'Summary unavailable. Valid findings remain visible.' : view.extraction.state !== 'ready' && view.extraction.notice}</p>}
          </section>
        </div>
      </div>
      <section className="panel next-step" aria-labelledby="questions-heading"><h3 id="questions-heading">Questions and literature</h3>
        {demo?.questions ?? <p>Question routing and literature answers are not connected in this fixture preview. No medical answer is generated here.</p>}</section>
    </section>
    <footer>Web workspace ready · NoteLens · Demo only · Synthetic fixtures</footer>
  </main>;
}
