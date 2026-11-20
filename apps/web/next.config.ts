import type { NextConfig } from 'next';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const config: NextConfig = {
  turbopack: { root },
  outputFileTracingRoot: root,
  serverExternalPackages: ['pdfjs-dist'],
  poweredByHeader: false,
};
export default config;
