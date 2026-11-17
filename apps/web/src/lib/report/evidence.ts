import type { EvidenceSpan } from '@notelens/contracts/v1';

// JavaScript slices use UTF-16; frozen evidence uses half-open Unicode code points.
export function evidenceParts(text: string, span: EvidenceSpan): { before: string; quote: string; after: string } | null {
  const points = Array.from(text);
  if (!Number.isInteger(span.start) || !Number.isInteger(span.end) || span.start < 0 ||
    span.end <= span.start || span.end > points.length) return null;
  const quote = points.slice(span.start, span.end).join('');
  if (quote !== span.quote) return null;
  return { before: points.slice(0, span.start).join(''), quote, after: points.slice(span.end).join('') };
}
