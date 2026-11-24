import { redirect } from 'next/navigation';
import { scaffoldStatus } from '../lib/scaffold/status';
import { fixtureWorkspace } from '../lib/report/model.ts';
import { ReportWorkspace } from '../components/report-workspace.tsx';

// Read mock-only configuration per request rather than baking it into static output.
export const dynamic = 'force-dynamic';

export default async function Home({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  // The public live demo starts at the working report page, not the fixture preview.
  if (process.env.NOTELENS_BOUNDED_EVALUATION === 'public-live') redirect('/demo');
  await scaffoldStatus();
  const query = await searchParams;
  const scenario = typeof query.scenario === 'string' ? query.scenario : undefined;
  const evidence = typeof query.evidence === 'string' ? query.evidence : undefined;
  return <ReportWorkspace view={await fixtureWorkspace(scenario, evidence)} />;
}
