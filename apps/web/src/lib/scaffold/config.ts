export function requireMockMode(mode: string | undefined = process.env.NOTELENS_MODE): 'mock' {
  if (mode !== undefined && mode !== 'mock') {
    throw new Error('This scaffold supports mock mode only.');
  }
  return 'mock';
}
