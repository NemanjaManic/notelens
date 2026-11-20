import { randomBytes } from 'node:crypto';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { pageContentPolicy } from './lib/security/content-policy.ts';

export function proxy(request: NextRequest) {
  const nonce = randomBytes(16).toString('base64');
  const policy = pageContentPolicy(nonce, process.env.NODE_ENV === 'development');
  const headers = new Headers(request.headers);
  // Next uses the forwarded policy to nonce its dynamically rendered scripts.
  headers.set('Content-Security-Policy', policy);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set('Content-Security-Policy', policy);
  response.headers.set('Cache-Control', 'no-store');
  return response;
}

export const config = { matcher: ['/', '/demo'] };
