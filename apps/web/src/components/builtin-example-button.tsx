'use client';

import { useState } from 'react';

const endpoint = '/api/documents/builtin';
const openError = 'The example could not be opened. Try again.';

export function BuiltinExampleButton() {
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');

  async function openExample() {
    setPending(true);
    setNotice('');
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        mode: 'same-origin',
        redirect: 'error',
        headers: { Accept: 'application/json' },
      });
      const result: { document?: unknown; notice?: unknown } = await response.json();
      if (response.status === 201 && typeof result.document === 'string' &&
          /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(result.document)) {
        window.location.assign(`/demo?document=${result.document}`);
        return;
      }
      setNotice(typeof result.notice === 'string' ? result.notice : openError);
    } catch {
      setNotice(openError);
    } finally {
      setPending(false);
    }
  }

  return <>
    <button id="open-builtin-example" type="button" data-endpoint={endpoint} disabled={pending} onClick={openExample}>
      {pending ? 'Preparing example...' : 'Chest pain report'}
    </button>
    {notice && <p role="alert">{notice}</p>}
  </>;
}
