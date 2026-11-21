async () => {
  const cases = [];
  const check = (condition, id) => {
    if (!condition) throw new Error(id);
    cases.push(id);
  };
  const call = (path, method = 'GET', credentials = 'same-origin') =>
    fetch(path, { method, credentials, cache: 'no-store' });
  const open = () => call('/api/session', 'POST');
  const close = () => call('/api/session', 'DELETE');
  const create = () => call('/test/document', 'POST');
  const read = () => call('/test/document');
  const advance = (to) => call(`/test/time?to=${to}`, 'POST');
  const hasCookieInScript = () => document.cookie.includes('__Host-notelens-session=');

  switch (new URL(location.href).searchParams.get('role')) {
    case 'next': {
      const opened = await open();
      check(opened.status === 204 && opened.headers.get('Cache-Control') === 'no-store', 'next-open');
      check(!hasCookieInScript() && await opened.text() === '', 'next-no-script-visible-capability');
      const closed = await close();
      check(closed.status === 204 && closed.headers.get('Cache-Control') === 'no-store', 'next-close');
      break;
    }
    case 'owner':
      check((await read()).status === 404, 'no-implicit-session');
      check((await open()).status === 204 && !hasCookieInScript(), 'http-only-cookie');
      check((await create()).status === 201 && (await read()).status === 200, 'browser-owner-access');
      check((await open()).status === 204 && (await read()).status === 200, 'browser-reuse-preserves-access');
      break;
    case 'other':
      check((await open()).status === 204, 'second-context-opens');
      check((await read()).status === 404, 'second-context-cannot-read-owner');
      break;
    case 'foreign':
      await fetch(`http://localhost:${location.port}/api/session`, {
        method: 'POST', mode: 'no-cors', credentials: 'include',
      });
      check(await (await call('/test/foreign-status')).json() === 403, 'browser-cross-origin-rejected');
      break;
    case 'expiry':
      check((await advance(1_799_999)).status === 204 && (await read()).status === 200, 'idle-activity-extends-session');
      check((await advance(3_599_998)).status === 204 && (await read()).status === 200, 'active-session-before-absolute-boundary');
      check((await advance(3_600_000)).status === 204 && (await read()).status === 404, 'absolute-session-expiry');
      check((await open()).status === 204 && (await create()).status === 201, 'fresh-session-after-expiry');
      check((await advance(5_400_000)).status === 204 && (await read()).status === 404, 'idle-session-expiry');
      check((await open()).status === 204 && (await create()).status === 201, 'fresh-session-after-idle-expiry');
      check((await close()).status === 204 && (await read()).status === 404, 'close-revokes-access');
      check((await open()).status === 204 && (await create()).status === 201, 'seed-for-process-restart');
      break;
    case 'restart':
      check((await read()).status === 404, 'process-restart-revokes-stale-cookie');
      check((await open()).status === 204 && (await create()).status === 201, 'process-restart-allows-fresh-session');
      break;
    case 'limits': {
      for (let minute = 1; minute <= 3; minute++) {
        check((await advance(minute * 60_000)).status === 204, `rate-clock-${minute}`);
        for (let i = 0; i < 10; i++) {
          const response = await call('/api/session', 'POST', 'omit');
          if (response.status !== 204) throw new Error(`issuance-${minute}-${i}`);
        }
        const limited = await call('/api/session', 'POST', 'omit');
        check(limited.status === 429 && limited.headers.get('Retry-After') === '60', `rate-boundary-${minute}`);
      }
      check((await advance(240_000)).status === 204, 'capacity-clock');
      check((await call('/api/session', 'POST', 'omit')).status === 204, 'last-session-slot');
      check((await call('/api/session', 'POST', 'omit')).status === 503, 'session-capacity-boundary');
      check((await open()).status === 204 && (await read()).status === 200, 'existing-session-usable-at-capacity');
      check((await close()).status === 204 && (await read()).status === 404, 'close-available-at-capacity');
      check((await open()).status === 204, 'closed-slot-reusable');
      break;
    }
    default:
      throw new Error('Unknown browser test role.');
  }
  return cases;
}
