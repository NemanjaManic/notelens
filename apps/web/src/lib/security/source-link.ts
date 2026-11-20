/** Permit a user-initiated HTTPS citation link. The server never fetches the URL. */
export function sourceLink(raw: string): string | null {
  if (!/^https:\/\//i.test(raw) || /[\s\\\p{Cc}]/u.test(raw)) return null;
  try {
    const url = new URL(raw);
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
  } catch {
    return null;
  }
}
