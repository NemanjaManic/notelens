import { handleSessionRequest } from '../../../lib/sessions/route.ts';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export function POST(request: Request): Response {
  return handleSessionRequest(request);
}

export function DELETE(request: Request): Response {
  return handleSessionRequest(request);
}
