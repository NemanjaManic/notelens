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

// Common English function and question words. Words shared with other Latin-script languages
// (for example "a", "in", "to", "die") are deliberately excluded.
const ENGLISH_QUESTION_WORDS = new Set([
  'what', 'which', 'who', 'whom', 'whose', 'why', 'when', 'where', 'how', 'is', 'are', 'was', 'were', 'be',
  'been', 'does', 'do', 'did', 'the', 'of', 'and', 'or', 'for', 'with', 'about', 'from', 'this', 'that',
  'these', 'those', 'can', 'could', 'should', 'would', 'will', 'may', 'might', 'it', 'its', 'there', 'their',
  'they', 'my', 'your', 'have', 'has', 'had', 'an', 'any', 'report', 'describe', 'patient', 'treatment',
  'treated', 'symptoms', 'causes', 'cause', 'follow', 'up', 'document', 'plan', 'mentioned', 'list',
]);

/**
 * Questions are often too short for statistical detection. A question written only in ASCII
 * Latin letters with at least two known English words making up at least 35% of its words is
 * accepted deterministically. Everything else (including any accented or non-Latin letters)
 * falls back to the document detector, so non-English questions are still rejected.
 */
export function englishQuestion(text: string): 'accepted' | 'unsupported' | 'inconclusive' {
  const letters = text.match(/\p{L}/gu) ?? [];
  const words = text.toLowerCase().match(/[a-z]+(?:'[a-z]+)?/g) ?? [];
  if (letters.length > 0 && letters.every(letter => /[A-Za-z]/.test(letter)) && words.length >= 3) {
    const known = words.filter(word => ENGLISH_QUESTION_WORDS.has(word)).length;
    if (known >= 2 && known / words.length >= 0.35) return 'accepted';
  }
  return englishLanguage(text);
}
