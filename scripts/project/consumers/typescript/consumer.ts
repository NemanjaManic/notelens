import { validateRecord, type ClassificationResult, type ExtractionResult, type AnswerResult } from '@notelens/contracts/v1';

export async function classificationConsumer(payload: unknown): Promise<ClassificationResult> {
  return validateRecord('ClassificationResult', payload);
}
export async function analysisConsumer(payload: unknown): Promise<ExtractionResult> {
  return validateRecord('ExtractionResult', payload);
}
export async function answerConsumer(payload: unknown): Promise<AnswerResult> {
  return validateRecord('AnswerResult', payload);
}
// Static spellings are checked; cross-field/evidence constraints require runtime validation.
// @ts-expect-error The contract uses status, not state.
const obsoleteStatus: ClassificationResult['state'] = 'supported';
// @ts-expect-error This category is not one of the five agreed labels.
const invalidCategory: ClassificationResult['category'] = 'Surgery';
void obsoleteStatus; void invalidCategory;
