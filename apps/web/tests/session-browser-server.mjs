import { readFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { readBrowserSession } from '../src/lib/sessions/browser.ts';
import { MemorySessions, UNAVAILABLE } from '../src/lib/sessions/memory.ts';
import { handleSessionRequest } from '../src/lib/sessions/route.ts';

// Standalone loopback test server. The clock and fixture routes are outside Next's app tree.
const port = Number(process.argv[2]);
if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new Error('Provide a test port.');
process.env.NOTELENS_MODE = 'mock';
const origin = `http://localhost:${port}`;
const fixture = JSON.parse(readFileSync(new URL('../../../contracts/v1/fixtures/documents.json', import.meta.url))).offset;
let now = 0;
let foreignStatus = null;
const timers = new Set();
const store = new MemorySessions({ runtime: {
  now: () => now,
  schedule(callback, delay) {
    const timer = { callback, at: now + delay };
    timers.add(timer);
    return () => timers.delete(timer);
  },
} });

async function handle(request) {
  const { pathname, searchParams } = new URL(request.url);
  if (pathname === '/api/session') {
    const response = handleSessionRequest(request, () => store, origin);
    if (request.headers.get('Origin') === `http://127.0.0.1:${port}`) foreignStatus = response.status;
    return response;
  }
  if (pathname === '/test/foreign-status') return Response.json(foreignStatus);
  if (pathname === '/test/time' && request.method === 'POST') {
    const target = Number(searchParams.get('to'));
    if (!searchParams.has('to') || !Number.isSafeInteger(target) || target < now) return new Response(null, { status: 400 });
    now = target;
    for (const timer of [...timers]) {
      if (timer.at <= now && timers.delete(timer)) timer.callback();
    }
    return new Response(null, { status: 204 });
  }
  if (pathname === '/test/document') {
    const owner = readBrowserSession(store, request.headers);
    if (owner !== null && request.method === 'POST') {
      const ticket = store.beginDocument(owner);
      if (ticket && (await store.storeDocument(owner, ticket, fixture)).kind === 'stored') {
        return new Response(null, { status: 201 });
      }
    }
    if (owner !== null && request.method === 'GET') {
      if (store.getDocument(owner, fixture.doc_id) !== UNAVAILABLE) return new Response(null, { status: 200 });
    }
    return new Response(null, { status: 404 });
  }
  return new Response('<!doctype html><title>NoteLens session browser verification</title>', {
    headers: { 'Content-Type': 'text/html; charset=utf-8' },
  });
}

const server = createServer(async (incoming, outgoing) => {
  try {
    const request = new Request(new URL(incoming.url, origin), {
      method: incoming.method,
      headers: incoming.headers,
    });
    const response = await handle(request);
    for (const [name, value] of response.headers) outgoing.setHeader(name, value);
    const cookies = response.headers.getSetCookie();
    if (cookies.length) outgoing.setHeader('Set-Cookie', cookies);
    outgoing.setHeader('Cache-Control', 'no-store');
    outgoing.writeHead(response.status).end(Buffer.from(await response.arrayBuffer()));
  } catch {
    outgoing.writeHead(500).end();
  }
});
server.listen(port, '127.0.0.1', () => console.log(`Ready at ${origin}`));
