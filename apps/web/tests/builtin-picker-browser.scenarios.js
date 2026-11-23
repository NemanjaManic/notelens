async () => {
  const cases = [];
  const check = (condition, id) => {
    if (!condition) throw new Error(id);
    cases.push(id);
  };
  const current = new URL(location.href);
  const docId = current.searchParams.get('document');
  const reportPath = `/demo?document=${docId}`;
  const canonicalText = page => page.querySelector('#document-passage')?.textContent;
  const parsePage = async response => new DOMParser().parseFromString(await response.text(), 'text/html');
  const read = (path = reportPath) => fetch(path, { cache: 'no-store' });
  const denied = async path => {
    const response = await read(path);
    const page = await parsePage(response);
    return response.ok && page.querySelector('#report-heading')?.textContent === 'Document unavailable'
      && !canonicalText(page) && !page.querySelector('[data-answer-route]');
  };

  switch (current.hash.slice(1)) {
    case 'other':
      check(!canonicalText(document) && document.querySelector('#report-heading')?.textContent === 'Document unavailable',
        'anonymous-context-denied');
      check((await fetch('/api/session', { method: 'POST' })).status === 204, 'independent-session-created');
      check(await denied(), 'independent-session-cannot-open-owner-report');
      check(await denied(reportPath + '&question=document'), 'independent-session-cannot-open-owner-answer');
      check(!canonicalText(await parsePage(await read('/demo?example=offset'))), 'legacy-link-cannot-open-report');
      break;
    case 'revoke':
      check(canonicalText(document)?.includes('No chest pain.'), 'owner-before-revocation');
      check((await fetch('/api/session', { method: 'DELETE' })).status === 204, 'owner-session-closed');
      check(await denied(), 'revoked-owner-link-denied');
      break;
    case 'foreign': {
      const response = await fetch('/api/documents/builtin', { method: 'POST' });
      check(response.status === 403 && response.headers.get('Cache-Control') === 'no-store', 'untrusted-origin-cannot-prepare');
      break;
    }
    default: {
      check(/^[0-9a-f-]{36}$/.test(docId ?? ''), 'picker-opens-prepared-report-url');
      check(canonicalText(document)?.includes('No chest pain.'), 'owner-sees-canonical-document');
      check(!document.cookie.includes('__Host-notelens-session='), 'session-cookie-hidden-from-script');
      const response = await read();
      check(response.ok && response.headers.get('Cache-Control')?.includes('no-store'), 'owner-report-is-not-cacheable');
      check(canonicalText(await parsePage(response)) === canonicalText(document), 'owner-can-reopen-same-document');
      check(!document.querySelector('#open-builtin-example')?.closest('form') &&
        document.querySelector('#open-builtin-example')?.type === 'button', 'picker-avoids-native-post');
      check(Boolean(document.querySelector('form[action="/api/questions"] #document-question')),
        'prepared-report-offers-document-question');
      break;
    }
  }
  return cases;
}
