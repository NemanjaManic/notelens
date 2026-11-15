import { scaffoldStatus } from '../lib/scaffold/status';

// Read mock-only configuration per request rather than baking it into static output.
export const dynamic = 'force-dynamic';

export default async function Home() {
  await scaffoldStatus();
  return (
    <main>
      <header><span className="wordmark">NoteLens</span><span className="badge">Mock mode</span></header>
      <section aria-labelledby="workspace-title">
        <p className="eyebrow">Educational demonstration</p>
        <h1 id="workspace-title">A clearer view of medical reports.</h1>
        <p className="intro">An English-language workspace for exploring public and synthetic medical text.</p>
        <aside aria-label="Demo notices">
          <strong>This demonstration does not replace a doctor.</strong>
          <p>Do not upload real personal medical reports.</p>
        </aside>
        <div className="workspace">
          <span className="status">Web workspace ready</span>
          <h2>The foundation starts here.</h2>
          <p>This scaffold uses synthetic fixtures. Document input, report analysis and questions will be added in later stages.</p>
        </div>
      </section>
      <footer>NoteLens · SITA capstone · Demo only</footer>
    </main>
  );
}
