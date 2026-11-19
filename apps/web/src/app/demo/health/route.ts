import { isDemoConfigured } from '../../../lib/scaffold/demo.ts';

export const dynamic = 'force-dynamic';

export function GET() {
  if (!isDemoConfigured()) return Response.json({ mode: 'unavailable' }, { status: 503 });
  return Response.json({ mode: 'mock', run: process.env.NOTELENS_DEMO_RUN }, {
    headers: { 'Cache-Control': 'no-store' },
  });
}
