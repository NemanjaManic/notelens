"""Explicit bounded final-run RAG profile; default CLI performs offline preflight only."""

import argparse
from collections import Counter
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import queue
import ssl
import threading
import time
from uuid import UUID

import openai
import uvicorn

from .answers import PARTIAL_POLICY, answer_request, checked_answer_response
from .assessment_trial import _call, _count_request
from .assessor import MODEL, AssessmentError, AssessmentParameters, assessment_request, checked_completion_content
from .embeddings import OpenAIEmbedder, TokenBudget, count_tokens, local_tokenizer
from .evidence_selection import checked_selection_response, prepare_selection
from .indexing import atomic_json
from .ingestion import DEFAULT_MANIFEST, load_corpus, valid_hash
from .main import Settings, create_app
from .question_parts import checked_question_parts_response, prepare_question_parts, question_parts_request
from .runtime import IndexedBackend, RagServiceError


ROOT = Path(__file__).resolve().parents[4]
FORMAT = 'notelens-final-rag-policy-v1'
APP_SHA = '42adf725a464e1c74697dc619dd97d02c88c0332'
INPUT_LIMITS = {'question_parts': 4096, 'support': 20000, 'answer': 4096}
OUTPUT_LIMIT = 512
EMBEDDING_LIMIT = 128
MAX_CASES = 16
TIMEOUT = 30
WALL_SECONDS = 3600
CAP = Decimal('0.08')
PARAMETERS = AssessmentParameters(max_output_tokens=OUTPUT_LIMIT, reasoning_effort='none', timeout_seconds=TIMEOUT)
REQUEST_ID = ContextVar('notelens_final_rag_request_id', default=None)


def _require(condition, code='configuration_required'):
    if not condition:
        raise AssessmentError(code)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _amount(value):
    try:
        result = Decimal(value)
        _require(result.is_finite() and result >= 0)
        return result
    except (InvalidOperation, TypeError, ValueError):
        raise AssessmentError('configuration_required') from None


def _cost(inputs, outputs=0, *, embedding=False):
    return ((Decimal(inputs) * Decimal('0.02' if embedding else '0.125')
             + Decimal(outputs) * Decimal('0.50')) / 1_000_000) * Decimal('1.10')


def read_policy(path, *, root=ROOT):
    raw = Path(path).read_bytes()
    policy = json.loads(raw)
    _require(isinstance(policy, dict) and policy.get('format_version') == FORMAT
             and policy.get('app_sha') == APP_SHA and type(policy.get('approved')) is bool
             and policy.get('provider_timeout_seconds') == TIMEOUT
             and policy.get('wall_clock_seconds') == WALL_SECONDS
             and _amount(policy.get('a_budget_usd')) == CAP
             and policy.get('automatic_retries') == 0)
    _require(isinstance(policy.get('question_sha256'), list)
             and len(policy['question_sha256']) in (0, MAX_CASES)
             and all(valid_hash(value) for value in policy['question_sha256']))
    try:
        UUID(policy['run_id'])
    except (KeyError, ValueError, TypeError, AttributeError):
        raise AssessmentError('configuration_required') from None
    root = Path(root).resolve()
    receipt = (root / policy['receipt_path']).resolve()
    _require(receipt.is_relative_to(root / 'services/rag/.cache/final') and receipt.suffix == '.json')
    _require(valid_hash(policy.get('launcher_sha256'))
             and _hash(Path(__file__).read_bytes()) == policy['launcher_sha256'])
    manifest_raw = (root / 'services/rag/config/frozen-rag-v1.json').read_bytes()
    _require(_hash(manifest_raw) == policy.get('freeze_manifest_sha256'))
    freeze = json.loads(manifest_raw)
    for name, digest in freeze['file_sha256'].items():
        candidate = (root / name).resolve()
        _require(candidate.is_relative_to(root) and _hash(candidate.read_bytes()) == digest)
    _require(freeze['responses']['development_model'] == MODEL
             and freeze['retrieval']['selected_method'] == 'vector'
             and freeze['retrieval']['top_k'] == 5
             and freeze['retrieval']['embedding_model'] == 'text-embedding-3-small'
             and freeze['retrieval']['embedding_dimensions'] == 1536)
    return policy, freeze, receipt, _hash(raw)


def preflight(path, *, root=ROOT):
    policy, freeze, receipt, digest = read_policy(path, root=root)
    corpus = load_corpus(repository_root=root, expected_corpus_version=freeze['corpus']['version'])
    _require(corpus.passage_count == 617 and corpus.artifact_sha256 == freeze['corpus_artifact_sha256'])
    # Loading the tokenizer verifies the local vocabulary without network access.
    local_tokenizer()
    ready = (policy['approved'] is True and policy.get('pricing_confirmed') is True
             and len(policy['question_sha256']) == MAX_CASES
             and all(isinstance(policy.get(key), str) and policy[key].strip()
                     for key in ('approval_id', 'operator')) and not receipt.exists())
    return {'status': 'preflight_ready_for_operator_checks' if ready else 'preflight_blocked',
            'provider_calls': 0, 'policy_sha256': digest, 'app_sha': APP_SHA,
            'corpus_passages': corpus.passage_count, 'max_answer_requests': MAX_CASES,
            'max_embedding_requests': MAX_CASES, 'max_generation_requests': MAX_CASES * 3,
            'max_free_count_requests': MAX_CASES * 3, 'max_embedding_input_tokens': MAX_CASES * EMBEDDING_LIMIT,
            'max_generation_input_tokens': MAX_CASES * sum(INPUT_LIMITS.values()),
            'max_generation_output_tokens': MAX_CASES * 3 * OUTPUT_LIMIT,
            'conservative_reservation_usd': str(MAX_CASES * (_cost(sum(INPUT_LIMITS.values()), 3 * OUTPUT_LIMIT)
                                                           + _cost(EMBEDDING_LIMIT, embedding=True))),
            'budget_usd': str(CAP), 'provider_timeout_seconds': TIMEOUT,
            'wall_clock_seconds': WALL_SECONDS, 'resume_allowed': False,
            'approved_policy': policy['approved'], 'receipt_already_exists': receipt.exists()}


class Ledger:
    """One durable attempt, with reservations retained after ambiguous failures."""

    def __init__(self, policy, path, policy_hash, *, clock=time.monotonic):
        self.path, self.clock = Path(path), clock
        self.deadline = clock() + WALL_SECONDS
        self.lock = threading.RLock()
        self.receipt_lock = threading.RLock()
        self.watchdog_stop = threading.Event()
        self.quotas = Counter(policy['question_sha256'])
        self.current = None
        self.state = {'format_version': 'notelens-final-rag-receipt-v1', 'run_id': policy['run_id'],
                      'policy_sha256': policy_hash, 'app_sha': APP_SHA, 'status': 'running',
                      'budget_usd': str(CAP), 'reserved_usd': '0', 'invoice_verified': False,
                      'requests': [], 'provider_attempts': 0, 'generation_attempts': 0,
                      'embedding_attempts': 0, 'free_count_attempts': 0}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents an existing attempt from being reset by restart.
        with self.path.open('xb') as handle:
            handle.write(_encoded(self.state))
        threading.Thread(target=self._watchdog, daemon=True).start()

    def _watchdog(self):
        while not self.watchdog_stop.wait(min(.1, max(.001, self.deadline - self.clock()))):
            with self.receipt_lock:
                if self.state['status'] != 'running':
                    return
                if self.clock() >= self.deadline:
                    self.halt('wall_clock_limit')
                    return

    def stop_watchdog(self):
        self.watchdog_stop.set()

    def save(self):
        with self.receipt_lock:
            atomic_json(self.path, self.state)

    def check(self):
        with self.receipt_lock:
            if self.state.get('stop_code') == 'wall_clock_limit':
                raise AssessmentError('timeout')
            _require(self.state['status'] == 'running', 'configuration_required')
            if self.clock() >= self.deadline:
                self.halt('wall_clock_limit')
                raise AssessmentError('timeout')

    def halt(self, code):
        with self.receipt_lock:
            if self.state['status'] != 'running':
                return
            self.state['status'] = 'halted'
            self.state['stop_code'] = code
            self.save()

    def admit(self, request, request_id):
        self.check()
        digest = _hash(request['question'].encode('utf-8'))
        if (self.quotas[digest] <= 0 or len(self.state['requests']) >= MAX_CASES
                or request_id is None or any(row['request_id'] == request_id for row in self.state['requests'])):
            self.halt('unapproved_or_repeated_request')
            raise AssessmentError('validation_failure')
        with self.receipt_lock:
            self.check()
            self.quotas[digest] -= 1
            self.current = {'request_id': request_id, 'question_sha256': digest, 'status': 'attempted', 'operations': []}
            self.state['requests'].append(self.current)
            self.save()

    def operation(self, stage, function, *, reserve=Decimal('0')):
        self.check()
        _require(self.current is not None and not any(row['stage'] == stage for row in self.current['operations']))
        counter = ('free_count_attempts' if stage.endswith('_count') else
                   'embedding_attempts' if stage == 'embedding' else 'generation_attempts')
        limit = MAX_CASES if counter == 'embedding_attempts' else MAX_CASES * 3
        if self.state[counter] >= limit or _amount(self.state['reserved_usd']) + reserve > CAP:
            self.halt('budget_exceeded')
            raise AssessmentError('budget_exceeded')
        with self.receipt_lock:
            self.check()
            record = {'stage': stage, 'status': 'reserved', 'reserved_usd': str(reserve)}
            self.current['operations'].append(record)
            self.state[counter] += 1
            self.state['provider_attempts'] += 1
            self.state['reserved_usd'] = str(_amount(self.state['reserved_usd']) + reserve)
            self.save()
        result_queue = queue.Queue(maxsize=1)

        def execute():
            try:
                _require(self.state['status'] == 'running' and self.clock() < self.deadline, 'timeout')
                result_queue.put((True, function()))
            except Exception as exc:
                result_queue.put((False, exc))

        threading.Thread(target=execute, daemon=True).start()
        try:
            success, result = result_queue.get(timeout=min(TIMEOUT, max(0.001, self.deadline - self.clock())))
        except queue.Empty:
            record['status'] = 'uncertain_timeout_reserved'
            if self.state['status'] == 'running':
                self.halt('timeout')
            else:
                self.save()
            raise AssessmentError('timeout') from None
        if not success:
            record['status'] = 'failed_reserved'
            code = getattr(result, 'code', 'provider_unavailable')
            self.halt(code if code in {'timeout', 'rate_limit', 'provider_unavailable', 'budget_exceeded'}
                      else 'provider_or_validation_failure')
            raise result
        with self.receipt_lock:
            try:
                self.check()
            except AssessmentError:
                record['status'] = 'late_result_reserved'
                self.save()
                raise
            record['status'] = 'received_reserved'
            self.save()
        return result, record


class Providers:
    """The sole provider accounting boundary for a serial admitted request."""

    mode = 'live'

    def __init__(self, ledger, client, embedder, encoder):
        self.ledger, self.client, self.embedder, self.encoder = ledger, client, embedder, encoder

    def complete(self, stage, payload):
        count_payload = {k: v for k, v in payload.items()
                         if k not in ('max_output_tokens', 'store', 'stream', 'background')}
        count, count_record = self.ledger.operation(stage + '_count',
            lambda: _count_request(self.client, count_payload, INPUT_LIMITS[stage]))
        count_record['input_tokens'] = count
        self.ledger.save()

        def completion():
            raw = _call(self.client.responses.with_raw_response.create, **payload, service_tier='default')
            body = raw.http_response.json()
            usage = body.get('usage') if isinstance(body, dict) else None
            _require(isinstance(usage, dict) and type(usage.get('input_tokens')) is int
                     and usage['input_tokens'] == count and type(usage.get('output_tokens')) is int
                     and 0 <= usage['output_tokens'] <= OUTPUT_LIMIT and body.get('service_tier') == 'default',
                     'invalid_upstream')
            checked_completion_content(raw.http_response.content, PARAMETERS, mode='live')
            upstream_id = raw.http_response.headers.get('x-request-id')
            upstream_id = upstream_id if isinstance(upstream_id, str) and len(upstream_id) <= 200 else None
            return raw.http_response.content, usage, upstream_id

        (data, usage, upstream_id), record = self.ledger.operation(stage, completion, reserve=_cost(count, OUTPUT_LIMIT))
        record.update(input_tokens=usage['input_tokens'], output_tokens=usage['output_tokens'],
                      measured_conservative_cost_usd=str(_cost(count, usage['output_tokens'])))
        if upstream_id is not None:
            record['provider_request_id'] = upstream_id
        self.ledger.save()
        return data

    def requirements(self, request):
        _require(count_tokens(request['question'], self.encoder) <= EMBEDDING_LIMIT, 'input_limit_exceeded')
        prepared = prepare_question_parts(request)
        return checked_question_parts_response(self.complete('question_parts', question_parts_request(prepared, PARAMETERS)),
                                               prepared, PARAMETERS)

    def assess(self, request, candidates, requirements):
        prepared = prepare_selection(request, candidates, requirements)
        return checked_selection_response(self.complete('support', assessment_request(prepared, PARAMETERS)),
                                          prepared, PARAMETERS, mode='live')

    def generate(self, prepared, *, partial_policy):
        return checked_answer_response(self.complete('answer', answer_request(prepared, PARAMETERS)),
                                       prepared, PARAMETERS, mode='live', partial_policy=partial_policy)

    def embed(self, texts):
        _require(len(texts) == 1, 'validation_failure')
        tokens = count_tokens(texts[0], self.encoder)
        _require(tokens <= EMBEDDING_LIMIT, 'input_limit_exceeded')
        batch, record = self.ledger.operation('embedding', lambda: self.embedder.embed(texts),
                                               reserve=_cost(tokens, embedding=True))
        record.update(input_tokens=batch.input_tokens, measured_conservative_cost_usd=str(_cost(tokens, embedding=True)))
        self.ledger.save()
        return batch


class BoundedBackend:
    mode = 'live'
    model_version = MODEL

    def __init__(self, backend, ledger):
        self.backend, self.ledger = backend, ledger

    def is_ready(self):
        return self.ledger.state['status'] == 'running' and self.ledger.clock() < self.ledger.deadline and self.backend.is_ready()

    def retrieve(self, request):
        with self.ledger.lock:
            self.ledger.halt('separate_retrieve_not_allowed')
        raise RagServiceError('validation_failure')

    def answer(self, request):
        with self.ledger.lock:
            try:
                self.ledger.admit(request, REQUEST_ID.get())
                result = self.backend.answer(request)
                with self.ledger.receipt_lock:
                    self.ledger.check()
                    self.ledger.current.update(status='completed', response_sha256=_hash(_encoded(result)))
                    self.ledger.save()
                return result
            except Exception as exc:
                code = getattr(exc, 'code', 'internal_error')
                if self.ledger.state['status'] == 'running':
                    self.ledger.halt('request_failed')
                known = {'timeout', 'rate_limit', 'provider_unavailable', 'budget_exceeded', 'validation_failure',
                         'configuration_required', 'unsupported_language', 'needs_clarification', 'out_of_scope'}
                raise RagServiceError(code if code in known else 'internal_error') from None
            finally:
                self.ledger.current = None


def build_app(path, *, root=ROOT):
    check = preflight(path, root=root)
    _require(check['status'] == 'preflight_ready_for_operator_checks')
    policy, freeze, receipt, digest = read_policy(path, root=root)
    _require(os.environ.get('NOTELENS_RAG_ALLOW_PAID_EMBEDDINGS') == 'true'
             and os.environ.get('NOTELENS_RAG_ALLOW_PAID_ASSESSMENTS') == 'true')
    key, token = os.environ.get('OPENAI_API_KEY'), os.environ.get('NOTELENS_RAG_SERVICE_TOKEN')
    _require(isinstance(key, str) and bool(key.strip()) and isinstance(token, str) and bool(token.strip()))
    ledger = Ledger(policy, receipt, digest)
    client = embedder = None
    try:
        encoder = local_tokenizer()
        client = openai.OpenAI(api_key=key, timeout=TIMEOUT, max_retries=0,
            base_url='https://api.openai.com/v1', http_client=openai.DefaultHttpxClient(
                verify=ssl.create_default_context(), follow_redirects=False))
        embedder = OpenAIEmbedder(api_key=key, enabled=True, timeout_seconds=TIMEOUT, encoder=encoder,
            budget=TokenBudget(Decimal(MAX_CASES * EMBEDDING_LIMIT) * Decimal('0.02') / 1_000_000, Decimal('0.02')),
            http_client=openai.DefaultHttpxClient(verify=ssl.create_default_context(), follow_redirects=False))
        providers = Providers(ledger, client, embedder, encoder)
        indexed = IndexedBackend(index_version=freeze['retrieval']['index_version'], model_version=MODEL,
            embedder=providers, admit=lambda request: True, requirements=providers.requirements,
            assessor=providers, generator=providers, partial_policy=PARTIAL_POLICY)
        corpus = load_corpus(repository_root=root, expected_corpus_version=freeze['corpus']['version'])
        backend = indexed.bind(corpus, repository_root=root, mode='live')
        app = create_app(Settings(mode='live', service_token=token, corpus_manifest=DEFAULT_MANIFEST,
            repository_root=str(root), expected_corpus_version=freeze['corpus']['version']),
            backend=BoundedBackend(backend, ledger))
    except Exception:
        ledger.halt('startup_configuration_error')
        ledger.stop_watchdog()
        for resource in (client, embedder):
            if resource is not None:
                resource.close()
        raise AssessmentError('configuration_required') from None

    attach_request_identity(app)

    @app.on_event('shutdown')
    def shutdown():
        ledger.stop_watchdog()
        with ledger.lock:
            if ledger.state['status'] == 'running':
                ledger.state['status'] = 'stopped'
                ledger.save()
        client.close()
        embedder.close()

    app.state.final_ledger = ledger
    return app


def attach_request_identity(app):
    """Carry the already validated HTTP request identity into the worker context."""
    @app.middleware('http')
    async def request_identity(request, call_next):
        identity = request.headers.get('X-Request-ID')
        try:
            identity = str(UUID(identity))
        except (ValueError, TypeError, AttributeError):
            identity = None
        context = REQUEST_ID.set(identity)
        try:
            return await call_next(request)
        finally:
            REQUEST_ID.reset(context)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--serve', action='store_true', help='Requires approved policy and operator environment.')
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    try:
        _require(1 <= args.port <= 65535)
        if not args.serve:
            print(json.dumps(preflight(args.config), indent=2))
        else:
            app = build_app(args.config)
            uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False, proxy_headers=False, log_level='warning')
        return 0
    except Exception:
        print(json.dumps({'status': 'blocked', 'code': 'configuration_required',
                          'execution_status': 'inspect_existing_receipt_before_any_new_attempt'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
