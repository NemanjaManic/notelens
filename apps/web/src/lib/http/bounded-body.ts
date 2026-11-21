export function exceedsDeclaredBodyLimit(request: Request, limit: number): boolean {
  return Number(request.headers.get('Content-Length')) > limit;
}

export async function boundedBody(request: Request, limit: number): Promise<Uint8Array<ArrayBuffer> | null> {
  if (exceedsDeclaredBodyLimit(request, limit)) return null;
  if (!request.body) return new Uint8Array(0);
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let length = 0;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > limit) {
        void reader.cancel().catch(() => {});
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return bytes;
}
