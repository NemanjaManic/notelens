import { mockServiceClients } from '../../../lib/clients/mock-services.ts';

export const dynamic = 'force-dynamic';

export function GET() {
  const clients = mockServiceClients();
  if (!clients) return Response.json({ mode: 'unavailable' }, { status: 503 });
  return Response.json({ mode: clients.evaluation ?? 'mock', run: process.env.NOTELENS_DEMO_RUN }, {
    headers: { 'Cache-Control': 'no-store' },
  });
}
