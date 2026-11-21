"""Serve the key-free indexed RAG demo on loopback or check its HTTP responses."""

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
from types import MappingProxyType, SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import uvicorn

from notelens_rag.answers import PARTIAL_POLICY, checked_answer_response
from notelens_rag.contracts import Contracts
from notelens_rag.embeddings import DIMENSIONS, EmbeddingBatch, identity, plan_corpus
from notelens_rag.indexing import build_index, load_index
from notelens_rag.ingestion import PreparedCorpus, PreparedPassage, sha256
from notelens_rag.main import DEMO_QUESTION, Settings, create_app
from notelens_rag.retrieval import CandidateRetriever
from notelens_rag.runtime import RagService
from notelens_rag.support import evaluate_support, support_context_sha256

from prepare_answer_review import PARAMETERS, _fixture_completion
from run_local_flow import _http_client


ROOT = Path(__file__).resolve().parents[3]
INDEX_ROOT = ROOT / 'services/rag/.cache/indexed-demo'
SNAPSHOT_DATE = '2026-11-20'
TOPIC_TEXT = 'The synthetic demo topic is a placeholder used to demonstrate cited answers.'
REFERENCE_TEXT = 'The reference topic is a separate placeholder for checking retrieval order.'
DEMO_PASSAGE = 'indexed-demo-topic'
PARTIAL_QUESTION = 'What is the synthetic demo topic, and when did it begin?'
MISSING_QUESTION = 'When did the synthetic demo topic begin?'
QUESTIONS = {DEMO_QUESTION: ('definition',), PARTIAL_QUESTION: ('definition', 'start-date'),
             MISSING_QUESTION: ('start-date',)}
PARTS = {'definition': 'Definition of the synthetic demo topic', 'start-date': 'Start date of the synthetic demo topic'}


def _fixture_corpus():
    rows = (('1', DEMO_PASSAGE, 'Synthetic demo topic', TOPIC_TEXT),
            ('2', 'indexed-demo-reference', 'Synthetic reference topic', REFERENCE_TEXT))
    artifact_hash = identity(rows)
    source = MappingProxyType({'name': 'NoteLens synthetic integration fixture', 'snapshot_date': SNAPSHOT_DATE})
    passages = tuple(PreparedPassage(topic_id=topic_id, passage_id=passage_id, title=title,
        url=f'https://example.invalid/notelens/{passage_id}', language='en', date_created=None,
        synonyms=(), groups=(), source=source, specialties=(), topic_text_sha256=sha256(text.encode('utf-8')),
        cleaning_version='indexed-demo-v1', start=0, end=len(text), overlap_code_points=0, text=text)
        for topic_id, passage_id, title, text in rows)
    configuration = {'profile': 'indexed-demo-v1', 'corpus_artifact_sha256': artifact_hash}
    manifest_hash = identity(configuration)
    return PreparedCorpus(corpus_version=manifest_hash, snapshot_date=SNAPSHOT_DATE, manifest_sha256=manifest_hash,
        artifact_sha256=artifact_hash, configuration=MappingProxyType(configuration),
        topic_ids=tuple(passage.topic_id for passage in passages), passages=passages,
        by_id=MappingProxyType({passage.passage_id: passage for passage in passages}),
        by_topic_id=MappingProxyType({passage.topic_id: (passage,) for passage in passages}))


class FixtureEncoder:
    def encode(self, text, *, disallowed_special):
        return list(text.encode('utf-8'))


class FixtureEmbedder:
    mode = 'mock'
    budget = None

    def embed(self, texts):
        definition = (1.0, 0.0) + (0.0,) * (DIMENSIONS - 2)
        reference = (0.0, 1.0) + (0.0,) * (DIMENSIONS - 2)
        vectors = tuple(reference if text == REFERENCE_TEXT else definition for text in texts)
        fixture_units = sum(len(text.encode('utf-8')) for text in texts)
        if self.budget is not None:
            self.budget.reserve(fixture_units)
        return EmbeddingBatch(vectors, fixture_units)


def _requirements(request):
    return [{'requirement_id': part, 'description': PARTS[part]} for part in QUESTIONS[request['question']]]


def _assess(request, candidates, requirements):
    source = next((passage for passage in candidates['passages'] if passage['passage_id'] == DEMO_PASSAGE), None)
    parts = []
    for requirement in requirements:
        part = requirement['requirement_id']
        supported = source is not None and part == 'definition'
        evidence = [{'passage_id': DEMO_PASSAGE, 'start': 0, 'end': len(TOPIC_TEXT), 'quote': TOPIC_TEXT}] if supported else []
        parts.append({'requirement_id': part, 'status': 'supported' if supported else 'not_supported',
                      'reason': 'The demo passage defines the topic.' if supported else 'The fixture has no evidence for this part.',
                      'evidence': evidence})
    assessment = {'format_version': 'rag-support-assessment-v1', 'parts': parts,
                  'context_sha256': support_context_sha256(request, candidates, requirements)}
    return SimpleNamespace(mode='mock', decision=evaluate_support(request, candidates, requirements, assessment))


def _generate(prepared, *, partial_policy):
    evidence, = json.loads(prepared.evidence_json)
    claims = [{'requirement_id': 'definition', 'text': TOPIC_TEXT, 'evidence_ids': [evidence['evidence_id']]}]
    return checked_answer_response(_fixture_completion(claims), prepared, PARAMETERS, partial_policy=partial_policy)


def _app(index_root, token, *, mock_ready=True):
    corpus = _fixture_corpus()
    plan = plan_corpus(corpus, encoder=FixtureEncoder())
    build_index(corpus, repository_root=index_root, plan=plan, embedder=FixtureEmbedder(), max_usd=Decimal('0.01'))
    index = load_index(corpus, repository_root=index_root, plan=plan, mode='mock')
    retriever, embedder = CandidateRetriever(index), FixtureEmbedder()
    service = RagService(mode='mock', admit=lambda request: request['question'] in QUESTIONS,
        rank=lambda request: retriever.retrieve(request, embedder), requirements=_requirements,
        assessor=SimpleNamespace(assess=_assess), generator=SimpleNamespace(generate=_generate),
        health_check=lambda: index.collection.count() == corpus.passage_count,
        model_version='indexed-demo-v1', partial_policy=PARTIAL_POLICY)
    return create_app(Settings(mode='mock', service_token=token, mock_ready=mock_ready), backend=service)


def _forbid_transport(*args, **kwargs):
    raise AssertionError('The indexed demo check attempted provider or external network access.')


def _check(app, token, connect):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    contracts = Contracts()
    auth = {'Authorization': f'Bearer {token}'} if token is not None else {}
    results = []
    with _http_client(app, loopback=True, connect=connect, forbidden=_forbid_transport) as client:
        for endpoint, schema, expected_status in (('live', 'LivenessResult', 'alive'), ('ready', 'HealthResult', 'ok')):
            response = client.get(f'/health/{endpoint}', headers=auth)
            health = contracts.validate(schema, response.json())
            require(response.status_code == 200 and health['mode'] == 'mock' and health['status'] == expected_status,
                    'The indexed demo failed its mock health check.')
        if token is not None:
            denied = client.get('/health/ready')
            require(denied.status_code == 401
                    and contracts.validate('ErrorEnvelope', denied.json())['error']['code'] == 'unauthorized',
                    'The indexed demo did not enforce its configured service token.')
        for question, expected in zip(QUESTIONS, ('sufficient', 'partial', 'insufficient'), strict=True):
            request = {'schema_version': '1.0.0', 'question': question}
            records = []
            for path, schema in (('/v1/retrieve', 'RetrievalResult'), ('/v1/literature-answer', 'AnswerResult')):
                identifier = str(uuid4())
                response = client.post(path, json=request, headers=auth | {'X-Request-ID': identifier})
                require(response.status_code == 200 and response.headers.get('X-Request-ID') == identifier,
                        f'Unexpected HTTP response from {path}.')
                records.append(contracts.validate(schema, response.json()))
            retrieved, answered = records
            require(retrieved['mode'] == answered['mode'] == 'mock' and answered['evidence_state'] == expected
                    and retrieved['state'] == ('insufficient' if expected == 'insufficient' else 'sufficient')
                    and retrieved['index_version'] == answered['retrieval_provenance']['index_version']
                    and retrieved['passages'][0]['passage_id'] == DEMO_PASSAGE,
                    f'The indexed demo lost its retrieval or evidence state for {expected}.')
            if expected == 'insufficient':
                require(answered['claims'] == answered['sources'] == [] and answered['route'] == 'none'
                        and answered['prompt_version'] is None, 'The demo emitted unsupported claims.')
            else:
                require(len(answered['claims']) == 1 and answered['claims'][0]['text'] == TOPIC_TEXT
                        and answered['claims'][0]['source_ids'] == [DEMO_PASSAGE]
                        and answered['sources'][0]['text'] == TOPIC_TEXT, 'The demo lost its citation.')
            if expected == 'partial':
                require(any('Start date' in warning for warning in answered['warnings']), 'The demo lost its evidence gap.')
            results.append({'question': question, 'retrieval_state': retrieved['state'],
                            'evidence_state': answered['evidence_state'], 'claims': len(answered['claims'])})
        rejected_id = str(uuid4())
        rejected = client.post('/v1/literature-answer', headers=auth | {'X-Request-ID': rejected_id},
            json={'schema_version': '1.0.0', 'question': 'An unregistered synthetic question?'})
        rejection = contracts.validate('ErrorEnvelope', rejected.json())
        require(rejected.status_code == 422 and rejected.headers.get('X-Request-ID') == rejected_id
                and rejection['request_id'] == rejected_id and rejection['error']['code'] == 'validation_failure',
                'The indexed demo accepted an unregistered question.')
    return {'mode': 'mock', 'health_http_responses': 2, 'readiness_http_status': 200,
            'business_http_responses': 6, 'admission_rejection_http_status': 422,
            'authentication_denial_http_status': 401 if token is not None else None,
            'provider_calls': 0, 'cases': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001, help='Loopback port for the long-running server.')
    parser.add_argument('--check', action='store_true', help='Verify both routes on a temporary loopback server and stop.')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    mock_ready = os.environ.get('NOTELENS_RAG_MOCK_READY', 'true')
    if mock_ready not in ('true', 'false'):
        parser.error('NOTELENS_RAG_MOCK_READY must be true or false')
    token = os.environ.get('NOTELENS_RAG_SERVICE_TOKEN')
    if args.check:
        connect = socket.create_connection
        with patch('openai.OpenAI', _forbid_transport), patch('socket.create_connection', _forbid_transport):
            result = _check(_app(INDEX_ROOT, token, mock_ready=mock_ready == 'true'), token, connect)
        print(json.dumps(result, indent=2))
    else:
        uvicorn.run(_app(INDEX_ROOT, token, mock_ready=mock_ready == 'true'), host='127.0.0.1', port=args.port,
                    proxy_headers=False, access_log=False)


if __name__ == '__main__':
    main()
