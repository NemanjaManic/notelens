import hashlib
import json
from pathlib import Path

from notelens_rag import final_runtime as fr
from notelens_rag import public_runtime as pr
from notelens_rag import question_parts as qp

ROOT = Path(__file__).resolve().parents[3]
REQUEST = {'schema_version': '1.0.0', 'question': 'How is high blood pressure treated?'}


def test_public_scope_binds_v2_prompt_without_touching_frozen_v1():
    frozen_prepare = qp.prepare_question_parts
    try:
        frozen = qp.prepare_question_parts(REQUEST)
        pr.use_public_question_scope()
        public = qp.prepare_question_parts(REQUEST)
        assert fr.prepare_question_parts is qp.prepare_question_parts
        assert public.prompt_version == pr.PUBLIC_QUESTION_PROMPT_VERSION
        assert 'How is high blood pressure treated?' in public.instructions
        assert public.prompt_sha256 != frozen.prompt_sha256
        # Binding to the exact question is unchanged.
        assert (public.context_sha256, public.inputs_json, public.schema_json) == (
            frozen.context_sha256, frozen.inputs_json, frozen.schema_json)
    finally:
        qp.prepare_question_parts = frozen_prepare
        fr.prepare_question_parts = frozen_prepare
    freeze = json.loads((ROOT / 'services/rag/config/frozen-rag-v1.json').read_bytes())
    v1 = 'services/rag/src/notelens_rag/prompts/question-parts-v1.txt'
    assert hashlib.sha256((ROOT / v1).read_bytes()).hexdigest() == freeze['file_sha256'][v1]
    assert qp.prepare_question_parts(REQUEST).prompt_version == qp.PROMPT_VERSION
