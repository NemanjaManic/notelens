import { canonicalText } from '../documents/canonical.ts';
import { englishLanguage } from '../documents/language.ts';
import { isReviewedQuestion, selectedDemoQuestion } from './demo-questions.ts';
import type { QuestionPlan } from './demo-questions.ts';

export const MAX_QUESTION_BODY_BYTES = 16 * 1024;
const MAX_QUESTION_CODE_POINTS = 1_000;
export const DOCUMENT_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const fields = {
  document: ['documentQuestion'],
  literature: ['literatureQuestion'],
  both: ['documentQuestion', 'literatureQuestion'],
  'out-of-scope': ['question'],
} as const;
const singleQuestion = ['question'] as const;
const invalid = 'Enter an English question for each selected source.';
const tooLong = 'Questions may contain up to 1,000 Unicode code points in total.';

export function questionDocument(input: unknown): string | null {
  if (!input || typeof input !== 'object' || !('document' in input)) return null;
  return typeof input.document === 'string' && DOCUMENT_ID.test(input.document) ? input.document : null;
}

export function questionPlan(input: Record<string, unknown>, builtin: boolean, evaluationCapture = false):
    { plan: QuestionPlan } | { notice: string; status: number } {
  if (Object.hasOwn(input, 'preset')) {
    const selected = typeof input.preset === 'string' && selectedDemoQuestion(input.preset, builtin);
    return selected && Object.keys(input).length === 2
      ? { plan: selected.plan } : { notice: 'Choose an available demo question.', status: 422 };
  }
  const scope = input.scope;
  if (scope !== 'document' && scope !== 'literature' && scope !== 'both' &&
      !(evaluationCapture && scope === 'out-of-scope')) return { notice: invalid, status: 422 };
  const sharedQuestion = evaluationCapture && scope === 'both' && Object.hasOwn(input, 'question');
  const selected = sharedQuestion ? singleQuestion : fields[scope];
  if (Object.keys(input).length !== selected.length + 2) return { notice: invalid, status: 422 };
  const questions: Partial<Record<(typeof fields)[keyof typeof fields][number], string>> = {};
  let rawLength = 0;
  let canonicalLength = 0;
  for (const field of selected) {
    const raw = input[field];
    if (typeof raw !== 'string') return { notice: invalid, status: 422 };
    rawLength += Array.from(raw).length;
    if (rawLength > MAX_QUESTION_CODE_POINTS) return { notice: tooLong, status: 413 };
    const canonical = canonicalText(raw);
    if (canonical.kind === 'rejected') return { notice: invalid, status: 422 };
    canonicalLength += Array.from(canonical.text).length;
    if (canonicalLength > MAX_QUESTION_CODE_POINTS) return { notice: tooLong, status: 413 };
    questions[field] = canonical.text.trim();
  }
  for (const text of Object.values(questions)) {
    const english = isReviewedQuestion(text) ? 'accepted' : englishLanguage(text);
    if (english === 'unsupported') return { notice: 'Only English questions are supported.', status: 422 };
    if (english === 'inconclusive') return { notice: 'English could not be verified. Enter a longer question in English.', status: 422 };
  }
  if (scope === 'out-of-scope') return { plan: { label: questions.question ?? '' } };
  if (sharedQuestion) {
    const question = questions.question ?? '';
    return { plan: { label: question, document: question, literature: question } };
  }
  const document = questions.documentQuestion;
  const literature = questions.literatureQuestion;
  return { plan: { label: document ?? literature ?? '', document, literature } };
}
