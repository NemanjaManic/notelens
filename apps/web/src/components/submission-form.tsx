'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';

export function SubmissionForm({ input }: { input: 'text' | 'pdf' }) {
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;
    const fields = new FormData(event.currentTarget);
    const content = fields.get('document');
    const scope = fields.get('scope');
    if ((input === 'text' ? typeof content !== 'string' : !(content instanceof File)) ||
      (scope !== 'public' && scope !== 'synthetic')) return;
    setPending(true);
    setNotice('');
    try {
      const response = await fetch('/api/documents/submit', {
        method: 'POST',
        headers: { 'Content-Type': input === 'text' ? 'text/plain; charset=utf-8' : 'application/pdf', 'X-NoteLens-Input-Scope': scope },
        body: content,
      });
      const result = await response.json();
      if (response.ok && typeof result.document === 'string' && /^[0-9a-f-]{36}$/.test(result.document)) {
        window.location.assign(`/demo?document=${result.document}`);
        return;
      }
      setNotice(typeof result.notice === 'string' ? result.notice : 'The document could not be opened.');
    } catch {
      setNotice('The document could not be opened. Try again.');
    } finally {
      setPending(false);
    }
  }

  const label = input === 'text' ? 'Paste English text' : 'Upload a text-based PDF';
  return <form action="/api/documents/submit" method="post" onSubmit={submit} aria-label={label}>
    <fieldset disabled={pending}>
      <legend>{label}</legend>
      <label htmlFor={`submission-${input}`}>{input === 'text' ? 'English document text' : 'PDF file'}</label>
      {input === 'text'
        ? <textarea id="submission-text" name="document" rows={5} required />
        : <input id="submission-pdf" name="document" type="file" accept="application/pdf,.pdf" required />}
      <label htmlFor={`scope-${input}`}>Source of this input</label>
      <select id={`scope-${input}`} name="scope" defaultValue="" required>
        <option value="" disabled>Choose the source</option>
        <option value="public">Public material</option>
        <option value="synthetic">Synthetic example</option>
      </select>
      <button type="submit">{pending ? 'Preparing…' : input === 'text' ? 'Open pasted text' : 'Open PDF'}</button>
      {notice && <p role="alert">{notice}</p>}
    </fieldset>
  </form>;
}
