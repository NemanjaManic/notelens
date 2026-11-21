import { Worker } from 'node:worker_threads';
import { MAX_DOCUMENT_CODE_POINTS } from '../config/session-policy.ts';

type PdfResult = { kind: 'text'; text: string } | { kind: 'invalid-pdf' | 'no-text' | 'too-large' };
const PDF_PARSE_DEADLINE_MS = 8_000;

export async function pdfText(input: Uint8Array<ArrayBuffer>): Promise<PdfResult> {
  if (new TextDecoder().decode(input.subarray(0, 5)) !== '%PDF-') return { kind: 'invalid-pdf' };
  const worker = new Worker(new URL('./pdf-worker.mjs', import.meta.url), {
    workerData: { bytes: input, maxCodePoints: MAX_DOCUMENT_CODE_POINTS },
    transferList: [input.buffer],
    resourceLimits: { maxOldGenerationSizeMb: 64 },
    stdout: true,
    stderr: true,
  });
  worker.stdout.resume();
  worker.stderr.resume();
  let timeout: NodeJS.Timeout | undefined;
  try {
    return await new Promise<PdfResult>(resolve => {
      timeout = setTimeout(() => resolve({ kind: 'invalid-pdf' }), PDF_PARSE_DEADLINE_MS);
      worker.once('message', resolve);
      worker.once('error', () => resolve({ kind: 'invalid-pdf' }));
      worker.once('exit', () => resolve({ kind: 'invalid-pdf' }));
    });
  } finally {
    clearTimeout(timeout);
    await worker.terminate();
  }
}
