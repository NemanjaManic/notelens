import { scaffoldStatus } from '../lib/scaffold/status';
import { fixtureWorkspace } from '../lib/report/model.ts';
import { ReportWorkspace } from '../components/report-workspace.tsx';
import DemoPage from './demo/page.tsx';

// Read mock-only configuration per request rather than baking it into static output.
export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  // The public live app is served at the site root.
  if (process.env.NOTELENS_BOUNDED_EVALUATION === 'public-live') return DemoPage({ searchParams });
  await scaffoldStatus();
  const query = await searchParams;
  const scenario = typeof query.scenario === 'string' ? query.scenario : undefined;
  const evidence = typeof query.evidence === 'string' ? query.evidence : undefined;
  return <ReportWorkspace view={await fixtureWorkspace(scenario, evidence)} />;
}
