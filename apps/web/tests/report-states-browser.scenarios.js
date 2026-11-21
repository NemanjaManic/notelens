async () => {
  const assertions = [];
  const check = (condition, id) => {
    if (!condition) throw new Error(id);
    assertions.push(id);
  };
  const profile = location.hash.slice(1);

  if (profile === 'slow') {
    const frame = document.createElement('iframe');
    frame.title = 'Report loading verification';
    frame.src = location.pathname + location.search;
    document.body.append(frame);
    try {
      const deadline = performance.now() + 8_000;
      let sawLoading = false;
      let completed = false;
      while (performance.now() < deadline) {
        const report = frame.contentDocument;
        const status = [...(report?.querySelectorAll('[role="status"]') ?? [])]
          .find(element => element.textContent.includes('Loading report analysis') && element.getClientRects().length);
        if (status && !sawLoading) {
          sawLoading = true;
          check(!report.querySelector('#document-passage, .findings, .citation'), 'loading-withholds-report-content');
        }
        if (report?.querySelector('#document-passage')?.textContent.includes('No chest pain.')) {
          completed = true;
          check(!status, 'loading-status-clears');
          check(report.querySelector('.findings .passages a') && report.querySelector('.claims .citation'),
            'findings-and-summary-load');
          break;
        }
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      check(sawLoading, 'loading-status-visible-during-request');
      check(completed, 'slow-request-finishes');
    } finally {
      frame.remove();
    }
    return assertions;
  }

  const report = document.querySelector('#document-passage');
  const specialty = document.querySelector('#specialty-heading').closest('section');
  const findings = document.querySelector('#findings-heading').closest('section');
  const summary = document.querySelector('#summary-heading').closest('section');
  const expectedText = profile === 'empty' ? 'This synthetic medical report' : 'No chest pain.';
  check(report?.textContent.includes(expectedText), 'canonical-document-remains-visible');
  check(![...document.querySelectorAll('[role="status"]')]
    .some(element => element.textContent.includes('Loading report analysis') && element.getClientRects().length),
  'settled-report-has-no-loading-state');

  switch (profile) {
    case 'classifier-failure':
      check(specialty.textContent.includes('The specialty result is unavailable.') &&
        !specialty.querySelector('.result-label, details'), 'classifier-failure-withholds-label-and-scores');
      check(findings.querySelector('.passages a') && summary.querySelector('.citation'), 'classifier-failure-preserves-evidence');
      check(!document.body.textContent.includes('The mock classifier simulated provider unavailability.'), 'service-diagnostic-hidden');
      break;
    case 'summary-failure':
      check(summary.textContent.includes('Summary unavailable.') && !summary.querySelector('.citation'), 'summary-failure-withholds-citations');
      check(findings.querySelector('.passages a'), 'summary-failure-preserves-findings');
      break;
    case 'findings-failure':
      check(findings.textContent.includes('Findings unavailable.') && !findings.querySelector('.findings'), 'findings-failure-withholds-findings');
      check(summary.querySelector('.citation'), 'findings-failure-preserves-summary');
      break;
    case 'extraction-failure':
      check(findings.textContent.includes('The findings and summary are unavailable.') &&
        summary.textContent.includes('The findings and summary are unavailable.'), 'extraction-failure-shows-unavailable-panels');
      check(!findings.querySelector('.findings') && !summary.querySelector('.citation'), 'extraction-failure-withholds-evidence');
      check(specialty.querySelector('.result-label')?.textContent === 'Cardiovascular / Pulmonary', 'extraction-failure-preserves-specialty');
      break;
    case 'uncertain':
      check(specialty.querySelector('.result-label')?.textContent === 'Specialty uncertain', 'uncertain-specialty-visible');
      check(findings.querySelector('.passages a') && summary.querySelector('.citation'), 'uncertainty-preserves-evidence');
      break;
    case 'empty':
      check(findings.textContent.includes('No findings were returned') && !findings.querySelector('.passages a'),
        'empty-findings-show-no-evidence');
      check(summary.textContent.includes('Evidence: insufficient') && !summary.querySelector('.citation'),
        'empty-summary-shows-insufficient-evidence');
      break;
    default:
      throw new Error('Unknown report browser profile.');
  }
  return assertions;
}
