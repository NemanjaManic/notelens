"""Run the approved five public RAG questions once through the local HTTP app."""

import argparse
from contextlib import ExitStack
from decimal import Decimal
from importlib.resources import files
import json
from pathlib import Path
import ssl
import sys
from uuid import uuid4

from fastapi.testclient import TestClient
import openai

from notelens_rag.answers import PARTIAL_POLICY, answer_request, checked_answer_response
from notelens_rag.assessment_trial import _call, _count_request, read_assessment_settings
from notelens_rag.assessor import (
    MODEL, AssessmentError, AssessmentParameters, _require, checked_completion_content,
    assessment_request,
)
from notelens_rag.contracts import Contracts
from notelens_rag.embeddings import MODEL as EMBEDDING_MODEL
from notelens_rag.embeddings import OpenAIEmbedder, TokenBudget, count_tokens, local_tokenizer, identity, read_settings
from notelens_rag.evidence_selection import checked_selection_response, prepare_selection
from notelens_rag.indexing import atomic_json, exclusive_build, read_json
from notelens_rag.ingestion import DEFAULT_MANIFEST
from notelens_rag.main import Settings, create_app
from notelens_rag.question_parts import checked_question_parts_response, prepare_question_parts, question_parts_request
from notelens_rag.runtime import IndexedBackend


ROOT = Path(__file__).resolve().parents[3]
CASE_IDS = ('CQ-01', 'CQ-03', 'CQ-05', 'CQ-07', 'CQ-09')
LIMIT = Decimal('0.025')
EXECUTION_SCOPE_OPEN = False
TIMEOUT = 30
EMBEDDING_LIMIT = 128
INPUT_LIMITS = {'question_parts': 4096, 'support': 20000, 'answer': 4096}
OUTPUT_LIMIT = 512
PARAMETERS = AssessmentParameters(max_output_tokens=OUTPUT_LIMIT, reasoning_effort='none', timeout_seconds=TIMEOUT)
MILLION = Decimal(1_000_000)
INPUT_PRICE = Decimal('0.10')
INPUT_PRICE_UPPER = Decimal('0.125')
OUTPUT_PRICE = Decimal('0.50')
EMBEDDING_PRICE = Decimal('0.02')
REGIONAL_FACTOR = Decimal('1.10')


def cost(input_tokens, output_tokens, *, input_price=INPUT_PRICE):
    return (input_tokens * input_price + output_tokens * OUTPUT_PRICE) / MILLION


def preflight(root):
    registry = read_json(root / 'docs/rag/retrieval-smoke-questions.json')
    handoff = read_json(root / 'services/rag/config/development-handoff.json')
    by_id = {item['question_id']: item for item in registry['cases']}
    cases = [by_id[key] for key in CASE_IDS]
    _require(registry['public_development_only'] is True and registry['language'] == 'en'
             and len({case['specialty'] for case in cases}) == len(CASE_IDS)
             and all(case['prior_agent_support_assessment'] == 'fully_supported' for case in cases),
             'smoke_scope_invalid')
    encoder = local_tokenizer()
    _require(all(count_tokens(case['question'], encoder) <= EMBEDDING_LIMIT for case in cases),
             'smoke_embedding_limit_exceeded')
    per_case = cost(sum(INPUT_LIMITS.values()), OUTPUT_LIMIT * len(INPUT_LIMITS), input_price=INPUT_PRICE_UPPER)
    per_case += EMBEDDING_LIMIT * EMBEDDING_PRICE / MILLION
    upper = per_case * len(cases) * REGIONAL_FACTOR
    _require(upper <= LIMIT, 'budget_exceeded')
    prompts = {name: identity(files('notelens_rag').joinpath('prompts', name).read_text(encoding='utf-8'))
               for name in ('question-parts-v1.txt', 'support-selection-v2.txt', 'literature-answer-v1.txt')}
    scope = {'question_ids': list(CASE_IDS), 'questions': [{key: case[key] for key in ('question_id', 'specialty', 'question')}
             for case in cases], 'corpus_version': handoff['corpus']['version'],
             'index_version': handoff['retrieval']['index_version'],
             'embedding_model': EMBEDDING_MODEL, 'model': MODEL,
             'embedding_input_limit': EMBEDDING_LIMIT, 'input_limits': INPUT_LIMITS,
             'output_limit_per_completion': OUTPUT_LIMIT, 'timeout_seconds': TIMEOUT, 'automatic_retries': 0,
             'approved_budget_usd': str(LIMIT), 'conservative_reference_reservation_usd': str(upper),
             'service_tier': 'default', 'prompt_identities': prompts}
    return scope | {'scope_sha256': identity(scope)}, encoder


class Completions:
    def __init__(self, client, log):
        self.client = client
        self.log = log
        self.case = None
        self.pricing_valid = True

    def complete(self, stage, payload):
        _require(self.pricing_valid and self.case is not None
                 and stage not in self.case['stages'], 'smoke_attempt_used')
        self.case['stages'][stage] = record = {'status': 'counting'}
        self.log()
        count_payload = {key: value for key, value in payload.items()
                         if key not in ('max_output_tokens', 'store', 'stream', 'background')}
        count = _count_request(self.client, count_payload, INPUT_LIMITS[stage])
        record.update(status='reserved', counted_input_tokens=count)
        self.log()
        raw = _call(self.client.responses.with_raw_response.create, **payload, service_tier='default')
        data = raw.http_response.content
        try:
            body = raw.http_response.json()
        except ValueError:
            self.pricing_valid = False
            raise AssessmentError('smoke_pricing_or_usage_mismatch') from None
        usage = body.get('usage') if isinstance(body, dict) else None
        if (not isinstance(usage, dict) or type(usage.get('input_tokens')) is not int
                or type(usage.get('output_tokens')) is not int or usage['input_tokens'] != count
                or not 0 <= usage['output_tokens'] <= OUTPUT_LIMIT or body.get('service_tier') != 'default'):
            self.pricing_valid = False
            raise AssessmentError('smoke_pricing_or_usage_mismatch')
        record.update(status='received', input_tokens=count, output_tokens=usage['output_tokens'],
                      reference_standard_usd=str(cost(count, usage['output_tokens'])))
        self.log()
        checked_completion_content(data, PARAMETERS, mode='live')
        return data

    def requirements(self, request):
        prepared = prepare_question_parts(request)
        data = self.complete('question_parts', question_parts_request(prepared, PARAMETERS))
        return checked_question_parts_response(data, prepared, PARAMETERS)

    def assess(self, request, candidates, requirements):
        prepared = prepare_selection(request, candidates, requirements)
        data = self.complete('support', assessment_request(prepared, PARAMETERS))
        return checked_selection_response(data, prepared, PARAMETERS, mode='live')

    def generate(self, prepared, *, partial_policy):
        data = self.complete('answer', answer_request(prepared, PARAMETERS))
        result = checked_answer_response(data, prepared, PARAMETERS, mode='live', partial_policy=partial_policy)
        self.case['citation_trace'] = json.loads(result.quote_trace_json)
        self.log()
        return result


class TrackedEmbedder:
    mode = 'live'

    def __init__(self, embedder, completions):
        self.embedder = embedder
        self.completions = completions

    def embed(self, texts):
        case = self.completions.case
        _require(case is not None and 'embedding' not in case['stages'], 'smoke_attempt_used')
        case['stages']['embedding'] = record = {'status': 'attempted'}
        self.completions.log()
        batch = self.embedder.embed(texts)
        record.update(status='received', input_tokens=batch.input_tokens,
                      reference_standard_usd=str(batch.input_tokens * EMBEDDING_PRICE / MILLION))
        self.completions.log()
        return batch


def http_case(client, headers, case, corpus, scope):
    request_id = str(uuid4())
    response = client.post('/v1/literature-answer', json={'schema_version': '1.0.0', 'question': case['question']},
                           headers={**headers, 'X-Request-ID': request_id})
    _require(response.headers.get('X-Request-ID') == request_id, 'smoke_request_id_mismatch')
    definition = 'AnswerResult' if response.status_code == 200 else 'ErrorEnvelope'
    body = Contracts().validate(definition, response.json())
    if response.status_code != 200:
        return {'http_status': response.status_code, 'error_code': body['error']['code']}
    provenance = body['retrieval_provenance']
    _require(body['mode'] == 'live' and provenance is not None
             and provenance['index_version'] == scope['index_version']
             and provenance['corpus_version'] == scope['corpus_version'], 'smoke_provenance_mismatch')
    for source in body['sources']:
        _require(corpus.by_id[source['passage_id']].text == source['text'], 'smoke_canonical_source_mismatch')
    return {'http_status': 200, 'evidence_state': body['evidence_state'], 'claims': body['claims'],
            'source_topics': sorted({source['topic_id'] for source in body['sources']}),
            'source_passage_ids': sorted({source['passage_id'] for source in body['sources']}),
            'warnings': body['warnings']}


def execute(root, scope, encoder):
    _require(EXECUTION_SCOPE_OPEN, 'smoke_execution_not_approved')
    folder = root / 'services/rag/.cache/live-http-smoke-2026-11-19'
    path = folder / 'run.json'
    _require(not path.exists(), 'smoke_attempt_used')
    settings = read_assessment_settings()
    embedding_settings = read_settings()
    _require(settings.enabled and embedding_settings.enabled and settings.api_key, 'smoke_provider_not_enabled')
    folder.mkdir(parents=True, exist_ok=True)
    with exclusive_build(folder), ExitStack() as resources:
        _require(not path.exists(), 'smoke_attempt_used')
        state = {'status': 'reserved', 'scope': scope, 'cases': []}

        def log():
            atomic_json(path, state)

        log()
        try:
            sdk = resources.enter_context(openai.OpenAI(api_key=settings.api_key, timeout=TIMEOUT, max_retries=0,
                base_url='https://api.openai.com/v1', http_client=openai.DefaultHttpxClient(
                    verify=ssl.create_default_context(), follow_redirects=False)))
            completions = Completions(sdk, log)
            embedder = OpenAIEmbedder(api_key=settings.api_key, enabled=True, timeout_seconds=TIMEOUT, encoder=encoder,
                budget=TokenBudget(len(CASE_IDS) * EMBEDDING_LIMIT * EMBEDDING_PRICE / MILLION, EMBEDDING_PRICE),
                http_client=openai.DefaultHttpxClient(verify=ssl.create_default_context(), follow_redirects=False))
            resources.callback(embedder.close)
            requests = [{'schema_version': '1.0.0', 'question': case['question']} for case in scope['questions']]
            backend = IndexedBackend(index_version=scope['index_version'], model_version=MODEL,
                embedder=TrackedEmbedder(embedder, completions), admit=lambda request: request in requests,
                requirements=completions.requirements, assessor=completions, generator=completions,
                partial_policy=PARTIAL_POLICY)
            token = uuid4().hex
            app = create_app(Settings(mode='live', service_token=token, corpus_manifest=DEFAULT_MANIFEST,
                repository_root=str(root), expected_corpus_version=scope['corpus_version']), indexed_backend=backend)
            client = resources.enter_context(TestClient(app))
            headers = {'Authorization': 'Bearer ' + token}
            health = client.get('/health/ready', headers=headers)
            state['readiness_http_status'] = health.status_code
            _require(health.status_code == 200 and health.json()['mode'] == 'live', 'smoke_not_ready')
            for case in scope['questions']:
                if not completions.pricing_valid:
                    break
                receipt = {'question_id': case['question_id'], 'specialty': case['specialty'], 'stages': {}}
                state['cases'].append(receipt)
                completions.case = receipt
                log()
                receipt.update(http_case(client, headers, case, app.state.prepared_corpus, scope))
                log()
            state['status'] = 'finished' if len(state['cases']) == len(CASE_IDS) else 'halted'
            return state
        finally:
            if state['status'] == 'reserved':
                state['status'] = 'halted'
            log()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--budget-usd')
    parser.add_argument('--scope-sha256')
    args = parser.parse_args()
    try:
        scope, encoder = preflight(ROOT)
        if args.execute:
            _require(args.budget_usd == str(LIMIT) and args.scope_sha256 == scope['scope_sha256'],
                     'smoke_execution_not_approved')
            result = execute(ROOT, scope, encoder)
        else:
            result = {'status': 'preflight', 'provider_calls': 0, 'scope': scope}
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['status'] != 'halted' else 1
    except AssessmentError as failure:
        print(json.dumps({'status': 'error', 'code': failure.code}), file=sys.stderr)
        return 1
    except Exception:
        print(json.dumps({'status': 'error', 'code': 'live_http_smoke_failed'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
