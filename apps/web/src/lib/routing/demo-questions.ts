export type QuestionPlan = { label: string; document?: string; literature?: string; submitted?: true };

const documentQuestion = 'What does the document say about chest pain?';
const literatureQuestion = 'What is the synthetic demo topic?';
const partialQuestion = "What does the document say about chest pain and the patient's age?";
const findingsQuestion = 'What diagnoses or symptoms are mentioned?';
const presets = {
  document: { label: documentQuestion, document: documentQuestion },
  literature: { label: literatureQuestion, literature: literatureQuestion },
  mixed: { label: 'What does the report say about chest pain, and what is the synthetic demo topic?',
    document: documentQuestion, literature: literatureQuestion },
  insufficient: { label: "What is the patient's age?", document: "What is the patient's age?" },
  'partial-document': { label: partialQuestion, document: partialQuestion },
  'out-of-scope': { label: 'Can NoteLens recommend a treatment?' },
  findings: { label: findingsQuestion, document: findingsQuestion, submitted: true },
} as const satisfies Record<string, QuestionPlan>;

export type DemoQuestion = keyof typeof presets;

export function isReviewedQuestion(text: string): boolean {
  // The indexed RAG demo also supports this reviewed free-text question.
  return text === 'What is the synthetic demo topic, and when did it begin?' ||
    (Object.values(presets) as QuestionPlan[]).some(plan => text === plan.document || text === plan.literature);
}

export function demoQuestions(builtin: boolean) {
  return (Object.keys(presets) as DemoQuestion[])
    .filter(key => builtin || 'submitted' in presets[key])
    .map(key => ({ key, label: presets[key].label }));
}

export function selectedDemoQuestion(value: string | string[] | undefined, builtin: boolean) {
  if (typeof value !== 'string' || !Object.hasOwn(presets, value)) return;
  const key = value as DemoQuestion;
  const plan = presets[key];
  if (builtin || 'submitted' in plan) return { key, plan };
}
