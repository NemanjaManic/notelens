async () => {
  const cases = [];
  const check = (condition, id) => {
    if (!condition) throw new Error(id);
    cases.push(id);
  };
  const english = 'This synthetic medical report describes a scheduled follow-up. The patient reports no new symptoms today.';
  const pasted = english + '\nThe next appointment will take place on Monday.';
  const spanish = 'El paciente fue atendido por la enfermera y volverá la próxima semana para una revisión programada.';
  const pdfLine = 'This synthetic PDF describes a scheduled follow-up with no new symptoms.';
  const pageUrl = new URL(location.href);
  const mode = pageUrl.hash.slice(1);

  function pdf(content, padding = 0) {
    const objects = [
      '<< /Type /Catalog /Pages 2 0 R >>',
      '<< /Type /Pages /Count 1 /Kids [3 0 R] >>',
      '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
      `<< /Length ${content.length} >>\nstream\n${content}\nendstream`,
      '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ];
    let value = '%PDF-1.4\n';
    const offsets = objects.map((object, index) => {
      const offset = value.length;
      value += `${index + 1} 0 obj\n${object}\nendobj\n`;
      return String(offset).padStart(10, '0') + ' 00000 n \n';
    });
    if (padding > 0) value += '%' + ' '.repeat(padding - 2) + '\n';
    return `${value}xref\n0 6\n0000000000 65535 f \n${offsets.join('')}trailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n${value.length}\n%%EOF\n`;
  }

  const submit = (body, mime = 'text/plain', scope = 'synthetic') => fetch('/api/documents/submit', {
    method: 'POST', headers: { 'Content-Type': mime, 'X-NoteLens-Input-Scope': scope }, body,
  });

  async function reject(body, status, label, mime, scope) {
    const response = await submit(body, mime, scope);
    const result = await response.json();
    return response.status === status && response.headers.get('Cache-Control') === 'no-store'
      && typeof result.notice === 'string' && result.notice.includes(label) && !('document' in result);
  }

  if (mode === 'text-submit' || mode === 'pdf-submit') {
    const kind = mode === 'text-submit' ? 'text' : 'pdf';
    const input = document.querySelector(`#submission-${kind}`);
    document.querySelector(`#scope-${kind}`).value = 'synthetic';
    if (kind === 'text') {
      input.value = pasted;
    } else {
      const files = new DataTransfer();
      const content = `BT /F1 10 Tf 72 700 Td (${pdfLine}) Tj ET`;
      files.items.add(new File([pdf(content)], 'synthetic.pdf', { type: 'application/pdf' }));
      input.files = files.files;
    }
    input.form.requestSubmit();
    return [mode];
  }

  if (mode === 'reject') {
    check(await reject('', 422, 'Paste text'), 'empty-text-rejected');
    check(await reject('Report.', 422, 'English could not be verified'), 'inconclusive-text-rejected');
    check(await reject(spanish, 422, 'Only English'), 'non-english-text-rejected');
    check(await reject(english + '\n\n' + spanish, 422, 'Only English'), 'mixed-language-text-rejected');
    check(await reject(new Uint8Array([0xc3, 0x28]), 422, 'invalid Unicode'), 'invalid-utf8-rejected');
    check(await reject('a'.repeat(100_001), 413, '100,000'), 'excess-code-points-rejected');
    check(await reject(english, 400, 'public or synthetic', 'text/plain', ''), 'source-confirmation-required');
    check(await reject(english, 415, 'text-based PDF', 'application/json'), 'unsupported-media-rejected');
    check(await reject('%PDF-1.4\ninvalid', 422, 'could not be read', 'application/pdf'), 'invalid-pdf-rejected');
    check(await reject(pdf('0 0 40 40 re f'), 422, 'no selectable text', 'application/pdf'), 'pdf-without-text-rejected');
    check(await reject(new Uint8Array(2_097_153), 413, '2 MiB', 'application/pdf'), 'pdf-byte-limit-rejected');
    const content = `BT /F1 10 Tf 72 700 Td (${pdfLine}) Tj ET`;
    const limit = 2_097_152;
    let padding = limit - pdf(content).length;
    padding -= pdf(content, padding).length - limit;
    const exact = pdf(content, padding);
    check(exact.length === limit && (await submit(exact, 'application/pdf')).status === 201, 'pdf-exact-byte-limit-accepted');
    return cases;
  }

  const canonical = document.querySelector('#document-passage')?.textContent;
  if (mode === 'other') {
    check((await fetch('/api/session', { method: 'POST' })).status === 204, 'separate-browser-session');
    const response = await fetch(pageUrl.pathname + pageUrl.search, { cache: 'no-store' });
    const html = new DOMParser().parseFromString(await response.text(), 'text/html');
    check(!canonical && !html.querySelector('#document-passage') &&
      html.querySelector('#report-heading').textContent === 'Document unavailable', 'other-session-cannot-read-submission');
    return cases;
  }

  check(document.querySelector('#report-heading').textContent === 'Prepared document', 'owner-sees-prepared-document');
  check(mode === 'text' ? canonical === pasted : canonical?.trim() === pdfLine, 'canonical-text-matches-input');
  check(!document.querySelector('[data-answer-route]'), 'submitted-document-has-no-fixture-answer');
  check(!document.cookie.includes('__Host-notelens-session='), 'owner-cookie-is-http-only');
  const response = await fetch(pageUrl.pathname + pageUrl.search, { cache: 'no-store' });
  check(response.ok && response.headers.get('Cache-Control')?.includes('no-store'), 'prepared-document-is-not-cacheable');
  return cases;
}
