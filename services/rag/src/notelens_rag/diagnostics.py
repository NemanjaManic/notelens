"""Closed diagnostic vocabulary: never copy untrusted values into failure reports."""

from dataclasses import dataclass
import re


_STAGES = frozenset({'validation', 'context', 'response', 'assessment'})
_RULES = frozenset({
    'validation_failed', 'json_value', 'json_invalid', 'json_duplicate_key', 'json_nonfinite',
    'context_request', 'context_shape', 'context_binding', 'context_passage', 'context_requirements',
    'assessment_shape', 'assessment_format', 'assessment_binding', 'parts_shape', 'parts_count',
    'part_shape', 'requirement_reference', 'duplicate_requirement', 'part_status', 'reason_empty',
    'evidence_shape', 'evidence_policy', 'quote_shape', 'source_reference', 'offset_type',
    'offset_bounds', 'quote_empty', 'quote_mismatch', 'duplicate_evidence', 'requirement_coverage',
    'response_identity', 'response_incomplete', 'response_output', 'response_item',
    'response_content', 'response_refusal', 'response_text', 'response_text_count',
    'usage_shape', 'usage_total', 'usage_limit', 'model_output_shape', 'coverage_flag_type',
    'requirements_incomplete',
})
_FIELDS = frozenset({
    'request', 'candidates', 'requirements', 'question_sha256', 'top_k', 'passages',
    'assessment', 'format_version', 'context_sha256', 'parts', 'requirement_id', 'status',
    'reason', 'evidence', 'passage_id', 'start', 'end', 'quote', 'response', 'output',
    'content', 'text', 'usage', 'input_tokens', 'output_tokens', 'total_tokens',
    'requirements_cover_question',
})


def _safe_fields(stage, rule, path):
    if (type(stage) is str and stage in _STAGES and type(rule) is str and rule in _RULES
            and type(path) is str and len(path) <= 256 and path.startswith('/')
            and (path == '/' or all(token in _FIELDS or re.fullmatch(r'0|[1-9][0-9]{0,5}', token)
                                    for token in path[1:].split('/')))):
        return stage, rule, path
    return 'validation', 'validation_failed', '/'


@dataclass(frozen=True, slots=True)
class ValidationDiagnostic:
    """Only static rule/field names and bounded numeric positions may be serialized."""

    stage: str = 'validation'
    rule: str = 'validation_failed'
    path: str = '/'

    def __post_init__(self):
        for name, value in zip(('stage', 'rule', 'path'), _safe_fields(self.stage, self.rule, self.path)):
            object.__setattr__(self, name, value)

    def as_dict(self):
        stage, rule, path = _safe_fields(self.stage, self.rule, self.path)
        return {'format_version': 'rag-validation-diagnostic-v1',
                'stage': stage, 'rule': rule, 'path': path}


def safe_diagnostic(error):
    diagnostic = getattr(error, 'diagnostic', None)
    if type(diagnostic) is not ValidationDiagnostic:
        diagnostic = ValidationDiagnostic()
    return diagnostic.as_dict()
