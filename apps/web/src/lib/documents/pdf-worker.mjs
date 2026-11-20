import { parentPort, workerData } from 'node:worker_threads';
import { dirname, join, sep } from 'node:path';
import { getDocument, VerbosityLevel } from 'pdfjs-dist/legacy/build/pdf.mjs';

// Resolve the installed data files in Node. The bundler resolves imports to chunk IDs.
const resolveInstalledPackage = process.getBuiltinModule('node:module').createRequire(import.meta.url).resolve;
const distribution = dirname(resolveInstalledPackage('pdfjs-dist/package.json'));
const { bytes, maxCodePoints } = workerData;
const assetDirectory = name => join(distribution, name).split(sep).join('/') + '/';
const task = getDocument({
  data: bytes, cMapUrl: assetDirectory('cmaps'), standardFontDataUrl: assetDirectory('standard_fonts'), useWorkerFetch: false,
  disableFontFace: true, enableXfa: false, stopAtErrors: true,
  verbosity: VerbosityLevel.ERRORS,
});

async function extractText() {
  const document = await task.promise;
  const parts = [];
  let points = 0;
  function append(value) {
    for (const _ of value) {
      if (++points > maxCodePoints) return false;
    }
    parts.push(value);
    return true;
  }

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber++) {
    const page = await document.getPage(pageNumber);
    const reader = page.streamTextContent({ disableNormalization: true }).getReader();
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        for (const item of value.items) {
          if (!('str' in item)) continue;
          if (!append(item.str) || (item.hasEOL && !append('\n'))) return { kind: 'too-large' };
        }
      }
    } finally {
      await reader.cancel().catch(() => {});
      page.cleanup();
    }
    if (pageNumber < document.numPages && !append('\n')) return { kind: 'too-large' };
  }
  const text = parts.join('');
  return text.trim() ? { kind: 'text', text } : { kind: 'no-text' };
}

const result = await extractText().catch(() => ({ kind: 'invalid-pdf' }));
await task.destroy();
parentPort.postMessage(result);
