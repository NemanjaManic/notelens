import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'NoteLens | Medical report workspace',
  description: 'An educational demonstration for understanding English medical reports.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
