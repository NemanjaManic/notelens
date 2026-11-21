import { francAll } from 'franc';

export const SUBMITTED_LANGUAGE_POLICY = 'franc-6.2.0-en-v1';
const minimumLetters = 24;
const minimumSeparation = 0.04;
const segmenter = new Intl.Segmenter('en', { granularity: 'sentence' });

function letterCount(text: string) {
  return text.match(/\p{L}/gu)?.length ?? 0;
}

/** Evaluate the full document in bounded windows plus substantial individual sentences. */
export function englishLanguage(text: string): 'accepted' | 'unsupported' | 'inconclusive' {
  const windows: string[] = text.match(/[\s\S]{1,1200}/gu) ?? [];
  if (letterCount(text) < minimumLetters) return 'inconclusive';
  for (const { segment } of segmenter.segment(text)) {
    if (letterCount(segment) >= 60) windows.push(segment.slice(0, 1200));
  }
  let english = false;
  let inconclusive = false;
  for (const window of windows) {
    if (letterCount(window) < minimumLetters) continue;
    const ranked = francAll(window);
    const [best] = ranked;
    if (best[0] === 'und') {
      inconclusive = true;
    } else if (best[0] === 'eng') {
      english = true;
    } else {
      const candidate = ranked.find(([language]) => language === 'eng');
      if (!candidate || best[1] - candidate[1] >= minimumSeparation) return 'unsupported';
    }
  }
  return english && !inconclusive ? 'accepted' : 'inconclusive';
}
