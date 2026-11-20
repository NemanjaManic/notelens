"""Replay one evidence-gap family through both frozen RAG routes without provider calls."""

from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx2 as httpx

from notelens_rag.answers import PARTIAL_POLICY, OfflineLiteratureGenerator
from notelens_rag.contracts import Contracts
from notelens_rag.hybrid import BM25Passages
from notelens_rag.ingestion import load_corpus
from notelens_rag.main import Settings, create_app
from notelens_rag.runtime import RagService
from notelens_rag.support import evaluate_support, support_context_sha256

from prepare_answer_review import PARAMETERS, _fixture_completion, _source, _trace_reference
from verify_evidence_gap_proposals import ranking_settings


FAMILY = ('EG-03', 'EG-04', 'EG-07')
SUPPORTED_TEXT = 'The viruses that cause colds and flu often cause acute bronchitis.'
INVALID_TEXT = 'Synthetic unsupported claim marker.'
ROUTES = {'/v1/retrieve': 'RetrievalResult', '/v1/literature-answer': 'AnswerResult'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reviews_for(case, corpus):
    requirements, reviews = [], []
    for position, part in enumerate(case['parts'], start=1):
        identifier = f'part-{position}'
        requirements.append({'requirement_id': identifier, 'description': part['requested_fact']})
        evidence = []
        for span in part['evidence']:
            key, start, end = span['passage_id'], span['start'], span['end']
            canonical = corpus.by_id[key].text
            quote = canonical[start:end]
            require(key in case['ranked_passage_ids'] and 0 <= start < end <= len(canonical)
                    and sha256(quote.encode('utf-8')).hexdigest() == span['quote_sha256'],
                    'A recorded evidence span differs from the ranked canonical text.')
            evidence.append({'passage_id': key, 'start': start, 'end': end, 'quote': quote})
        require(part['status'] == ('supported' if evidence else 'missing_in_top_five'),
                'A proposal label differs from its evidence.')
        reviews.append({'requirement_id': identifier, 'status': 'supported' if evidence else 'not_supported',
                        'reason': part['review_note'], 'evidence': evidence})
    return requirements, reviews


def probe(case, corpus, ranker, *, policy=PARTIAL_POLICY, unsupported_claim=False):
    request = {'schema_version': '1.0.0', 'question': case['question']}
    requirements, reviews = reviews_for(case, corpus)
    supported_ids = [part['requirement_id'] for part in reviews if part['status'] == 'supported']
    expected_status = 500 if unsupported_claim else 503 if policy is None else 200
    rankings, generations, refs = [], [], []

    def rank(value):
        ranks = ranker.rank(value['question'])[:5]
        require(list(ranks) == case['ranked_passage_ids'], 'The reviewed BM25 ranking changed.')
        require(len(ranks) == 5 and corpus.by_id[ranks[0]].topic_id == case['target_topic_id'],
                'The target topic is missing at rank one.')
        rankings.append(ranks)
        return {'record_format_version': 'rag-candidate-ranking-v1', 'status': 'ranked_candidates',
                'answerability': 'not_assessed', 'mode': 'mock', 'top_k': 5, 'signals_used': ['question'],
                'question_sha256': sha256(value['question'].encode('utf-8')).hexdigest(),
                'corpus_version': corpus.corpus_version, 'index_version': 'local-bm25-corpus-replay-v1',
                'retriever_version': 'bm25-passage-words-v1',
                'score_note': 'Reciprocal rank describes BM25 order only. It does not measure answer support.',
                'passages': [_source(corpus.by_id[key], corpus, 1.0/position)
                             for position, key in enumerate(ranks, start=1)]}

    def assess(value, candidates, requested):
        decision = evaluate_support(value, candidates, requested, {'format_version': 'rag-support-assessment-v1',
            'context_sha256': support_context_sha256(value, candidates, requested), 'parts': reviews})
        require(decision.coverage == case['expected_coverage'], 'Unexpected coverage from the reviewed fixture.')
        return SimpleNamespace(mode='mock', decision=decision)

    def completion(native_request):
        native = json.loads(native_request.content)
        payload = json.loads(native['input'])
        schema = native['text']['format']['schema']['properties']['claims']['items']['properties']
        options = payload['evidence']
        require(payload['question'] == case['question'] and supported_ids == ['part-1']
                and [part['requirement_id'] for part in payload['supported_parts']] == supported_ids
                and schema['requirement_id']['enum'] == supported_ids
                and len(options) == 1 and options[0]['requirement_id'] == 'part-1'
                and options[0]['quote'] == reviews[0]['evidence'][0]['quote'],
                'The generator received evidence for the wrong requested part.')
        generations.append(supported_ids)
        claims = [{'requirement_id': 'part-1', 'text': SUPPORTED_TEXT, 'evidence_ids': [options[0]['evidence_id']]}]
        if unsupported_claim:
            claims.append({'requirement_id': 'part-2', 'text': INVALID_TEXT, 'evidence_ids': [options[0]['evidence_id']]})
        return httpx.Response(200, content=_fixture_completion(claims), headers={'Content-Type': 'application/json'})

    adapter = OfflineLiteratureGenerator(transport=httpx.MockTransport(completion), parameters=PARAMETERS)

    def generate(prepared, *, partial_policy):
        result = adapter.generate(prepared, partial_policy=partial_policy)
        refs.extend(_trace_reference(trace, corpus) for trace in json.loads(result.quote_trace_json))
        return result

    service = RagService(mode='mock', admit=lambda value: value == request, rank=rank,
        requirements=lambda value: requirements, assessor=SimpleNamespace(assess=assess),
        generator=SimpleNamespace(generate=generate), health_check=lambda: True,
        model_version='partial-evidence-flow-fixture-v1', partial_policy=policy)
    responses = {}
    contract = Contracts()
    try:
        with TestClient(create_app(Settings(mode='mock'), backend=service), client=('127.0.0.1', 45000)) as client:
            routes = ('/v1/literature-answer',) if unsupported_claim else ROUTES
            for route in routes:
                request_id = str(uuid4())
                response = client.post(route, json=request, headers={'X-Request-ID': request_id})
                require(response.status_code == expected_status and response.headers.get('X-Request-ID') == request_id,
                        f'{case["id"]} received unexpected HTTP status {response.status_code} at {route}.')
                definition = ROUTES[route] if expected_status == 200 else 'ErrorEnvelope'
                responses[route] = contract.validate(definition, response.json())
    finally:
        adapter.close()

    body = responses['/v1/literature-answer']
    summary = {'case_id': case['id'], 'http_status': expected_status, 'ranking_runs': len(rankings),
               'simulated_generator_requests': len(generations)}
    if expected_status != 200:
        code = 'internal_error' if unsupported_claim else 'configuration_required'
        require(all(item['error']['code'] == code for item in responses.values()) and not refs
                and len(generations) == int(unsupported_claim) and INVALID_TEXT not in json.dumps(body),
                'An out-of-policy answer escaped or produced an unsafe error.')
        return {**summary, 'check': 'unsupported_claim' if unsupported_claim else 'unconfirmed_partial_policy', 'code': code}

    retrieval = responses['/v1/retrieve']
    expected_state = {'full': 'sufficient', 'partial': 'partial', 'none': 'insufficient'}[case['expected_coverage']]
    gap_prefix = 'The retrieved sources do not support the requested information: '
    gaps = [gap_prefix + part['requested_fact']
            for part in case['parts'] if part['status'] == 'missing_in_top_five']
    require(body['evidence_state'] == expected_state and body['mode'] == 'mock'
            and retrieval['state'] == ('sufficient' if supported_ids else 'insufficient')
            and all(body['retrieval_provenance'][key] == retrieval[key] for key in
                    ('state', 'mode', 'corpus_version', 'index_version', 'retriever_version', 'score_note'))
            and [warning for warning in body['warnings'] if warning.startswith(gap_prefix)] == gaps,
            'The HTTP response lost its evidence state or gap.')
    if supported_ids:
        claim, = body['claims']
        source, = body['sources']
        reference, = refs
        span, = case['parts'][0]['evidence']
        require(body['route'] == 'literature' and body['text'] == claim['text'] == SUPPORTED_TEXT
                and claim['source_ids'] == [source['source_id']] and source['passage_id'] == reference['passage_id']
                and source['url'] == reference['url'] and len(generations) == 1
                and all(reference[key] == value for key, value in span.items()),
                'The supported claim lost its exact citation.')
    else:
        require(body['route'] == 'none' and not (body['claims'] or body['sources'] or generations or refs),
                'A missing-only case reached generation or returned evidence.')
    return {**summary, 'evidence_state': body['evidence_state'], 'retrieval_state': retrieval['state'],
            'answer_text': body['text'], 'gaps': gaps, 'citations': refs}


def run(root):
    raw = (root/'docs/rag/evaluation/evidence-gap-proposals.json').read_bytes()
    record = json.loads(raw)
    require(record['ranking'] == ranking_settings(), 'The proposal BM25 configuration changed.')
    corpus = load_corpus(repository_root=root, expected_corpus_version=record['corpus_version'])
    ranker = BM25Passages(corpus.passages)
    cases = {case['id']: case for case in record['cases']}

    def forbid_network(*args, **kwargs):
        raise AssertionError('This local verification cannot open network connections.')

    with patch('socket.create_connection', forbid_network), patch('socket.getaddrinfo', forbid_network):
        results = [probe(cases[key], corpus, ranker) for key in FAMILY]
        results.append(probe(cases['EG-07'], corpus, ranker, policy=None))
        results.append(probe(cases['EG-07'], corpus, ranker, unsupported_claim=True))
    return {'format_version': 'rag-partial-evidence-http-v1', 'mode': 'mock', 'new_provider_calls': 0,
            'proposal_sha256': sha256(raw).hexdigest(), 'corpus_version': corpus.corpus_version,
            'results': results}


if __name__ == '__main__':
    print(json.dumps(run(Path(__file__).resolve().parents[3]), indent=2, allow_nan=False))
