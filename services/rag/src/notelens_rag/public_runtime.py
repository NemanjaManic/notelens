"""Public live RAG service for the hosted demo.

Reuses the frozen final-runtime stack (pinned corpus/index, model, prompts, validation,
single bounded re-attempt and abstention handling) with process-wide caps instead of the
D-009 question allowlist. A failed request does not stop the service; reaching the
request or USD cap does. No question or answer text is written to the receipt.
"""

import argparse
import dataclasses
import hashlib
import sys
from decimal import Decimal
import json
import os
from pathlib import Path
import ssl
import uuid

import openai
import uvicorn

from importlib.resources import files

from . import final_runtime as fr
from . import question_parts as qp
from .answers import PARTIAL_POLICY
from .assessor import AssessmentError
from .embeddings import OpenAIEmbedder, TokenBudget, local_tokenizer
from .ingestion import DEFAULT_MANIFEST, load_corpus
from .main import Settings, create_app
from .runtime import IndexedBackend

STOPPING_CODES = frozenset({'budget_exceeded', 'unapproved_or_repeated_request'})
PUBLIC_QUESTION_PROMPT = 'prompts/question-parts-public-v2.txt'
PUBLIC_QUESTION_PROMPT_VERSION = 'literature-question-parts-public-v2'
_frozen_prepare_question_parts = qp.prepare_question_parts


def _public_prepare_question_parts(request):
    """Prepare question parts with the public scope prompt.

    The frozen v1 prompt treats general treatment questions as out of scope. The public
    service uses v2, which keeps personal diagnosis/treatment decisions out of scope but
    accepts general medical information questions. Binding, schema and anchor checks are
    unchanged; the frozen evaluation runtime and its pinned files keep using v1.
    """
    frozen = _frozen_prepare_question_parts(request)
    try:
        instructions = files('notelens_rag').joinpath(PUBLIC_QUESTION_PROMPT).read_bytes().decode('utf-8')
    except (OSError, UnicodeError):
        raise AssessmentError('configuration_required') from None
    return dataclasses.replace(frozen, prompt_sha256=hashlib.sha256(instructions.encode()).hexdigest(),
                               instructions=instructions, prompt_version=PUBLIC_QUESTION_PROMPT_VERSION)


def use_public_question_scope():
    """Bind the public prompt for both preparation and response checking in this process."""
    qp.prepare_question_parts = _public_prepare_question_parts
    fr.prepare_question_parts = _public_prepare_question_parts


class PublicLedger(fr.Ledger):
    """A capped ledger whose individual request failures do not halt the service."""

    def halt(self, code):
        if code in STOPPING_CODES:
            return super().halt(code)
        print(json.dumps({'rag_request_failed': code}), file=sys.stderr, flush=True)
        with self.receipt_lock:
            self.state['last_error'] = code
            self.state['failed_requests'] = self.state.get('failed_requests', 0) + 1
            self.save()


def _positive(name, default, kind):
    value = kind(os.environ.get(name, default))
    fr._require(value > 0)
    return value


def load_freeze(root):
    manifest = json.loads((root / 'services/rag/config/frozen-rag-v1.json').read_bytes())
    for name, digest in manifest['file_sha256'].items():
        candidate = (root / name).resolve()
        fr._require(candidate.is_relative_to(root) and fr._hash(candidate.read_bytes()) == digest)
    fr._require(manifest['responses']['development_model'] == fr.MODEL
                and manifest['retrieval']['selected_method'] == 'vector')
    return manifest


def build_app(root=fr.ROOT):
    root = Path(root).resolve()
    use_public_question_scope()
    fr._require(os.environ.get('NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS') == 'true'
                and os.environ.get('NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS') == 'true')
    key, token = os.environ.get('OPENAI_API_KEY'), os.environ.get('NOTELENS_RAG_SERVICE_TOKEN')
    fr._require(isinstance(key, str) and bool(key.strip()) and isinstance(token, str) and bool(token.strip()))
    max_requests = _positive('NOTELENS_RAG_PUBLIC_MAX_REQUESTS', '300', int)
    cap = _positive('NOTELENS_RAG_PUBLIC_BUDGET_USD', '1.00', Decimal)
    freeze = load_freeze(root)
    corpus = load_corpus(repository_root=root, expected_corpus_version=freeze['corpus']['version'])
    fr._require(corpus.passage_count == 617 and corpus.artifact_sha256 == freeze['corpus_artifact_sha256'])
    run_id = str(uuid.uuid4())
    receipt = Path(os.environ.get('NOTELENS_RAG_PUBLIC_RECEIPT_DIR', root / 'services/rag/.cache/public')) / f'{run_id}.json'
    ledger = PublicLedger({'question_sha256': [], 'run_id': run_id}, receipt, 'public',
                          max_requests=max_requests, cap=cap, wall_seconds=10 * 365 * 24 * 3600,
                          question_quotas=False)
    encoder = local_tokenizer()
    client = openai.OpenAI(api_key=key, timeout=fr.TIMEOUT, max_retries=0, base_url='https://api.openai.com/v1',
                           http_client=openai.DefaultHttpxClient(verify=ssl.create_default_context(),
                                                                 follow_redirects=False))
    embedder = OpenAIEmbedder(api_key=key, enabled=True, timeout_seconds=fr.TIMEOUT, encoder=encoder,
        budget=TokenBudget(Decimal(max_requests * fr.EMBEDDING_LIMIT) * Decimal('0.02') / 1_000_000, Decimal('0.02')),
        http_client=openai.DefaultHttpxClient(verify=ssl.create_default_context(), follow_redirects=False))
    providers = fr.Providers(ledger, client, embedder, encoder)
    indexed = IndexedBackend(index_version=freeze['retrieval']['index_version'], model_version=fr.MODEL,
        embedder=providers, admit=lambda request: True, requirements=providers.requirements,
        assessor=providers, generator=providers, partial_policy=PARTIAL_POLICY)
    backend = indexed.bind(corpus, repository_root=root, mode='live')
    app = create_app(Settings(mode='live', service_token=token, corpus_manifest=DEFAULT_MANIFEST,
        repository_root=str(root), expected_corpus_version=freeze['corpus']['version']),
        backend=fr.BoundedBackend(backend, ledger))
    fr.attach_request_identity(app)

    @app.on_event('shutdown')
    def shutdown():
        ledger.stop_watchdog()
        client.close()
        embedder.close()

    app.state.public_ledger = ledger
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    try:
        app = build_app()
    except Exception as exc:  # report the stage without secrets or document text
        print(json.dumps({'status': 'blocked', 'code': 'configuration_required', 'error': type(exc).__name__}))
        return 1
    uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False, proxy_headers=False, log_level='warning')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
