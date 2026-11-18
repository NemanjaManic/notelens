"""Run four public cases through the local ASGI HTTP boundary using saved vectors."""

from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from notelens_rag.answer_trial import load_answer_trial, prepare_from_history
from notelens_rag.answers import PARTIAL_POLICY, checked_answer_response
from notelens_rag.assessment_trial import AssessmentSettings
from notelens_rag.contracts import Contracts
from notelens_rag.embeddings import local_tokenizer, plan_corpus
from notelens_rag.indexing import load_index, read_json
from notelens_rag.ingestion import load_corpus
from notelens_rag.main import Settings, create_app
from notelens_rag.qa_vector_trial import NEW_CACHE, NEW_IDS, PROPOSAL_PATH, SCOPE_PATH, ProposalQuerySession
from notelens_rag.query_smoke import CACHE_DIRECTORY, REGISTRY, PublicQuerySession
from notelens_rag.retrieval import CandidateRetriever
from notelens_rag.runtime import RagService
from notelens_rag.support import evaluate_support, support_context_sha256

from prepare_answer_review import PARAMETERS, _fixture_completion, _proposal_judgments, _trace_reference


CASES = {'A-QA-01': ('CQ-01', 'sufficient', 'cached_actual_text'),
         'A-QA-07': (None, 'sufficient', 'authored_fixture'),
         'A-QA-02': ('CQ-02', 'partial', 'authored_fixture'),
         'A-QA-03': ('CQ-08', 'insufficient', 'local_abstention')}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _protected_hashes(folders):
    return {path: _digest(path) for folder in folders for path in sorted(folder.rglob('*.json'))}


def cached_retrieval(root, provider_factory):
    """Open the pinned QA query caches and return exact public vector rankings."""
    scope = read_json(root/SCOPE_PATH)
    proposals = read_json(root/PROPOSAL_PATH)
    previous = read_json(root/REGISTRY)
    comparison = read_json(root/'docs/rag/evaluation/vector-proposal-comparison.json')
    old_cache, new_cache = root/CACHE_DIRECTORY, root/NEW_CACHE
    _require(_digest(root/PROPOSAL_PATH) == scope['proposal_sha256']
             and _digest(root/REGISTRY) == scope['prior_registry_sha256']
             and _digest(old_cache/'usage.json') == scope['prior_query_ledger_sha256']
             and scope['approval']['scope_sha256'] == comparison['scope_sha256'], 'The cached QA scope changed.')
    cases = {case['id']: case for case in proposals['cases']}
    encoder = local_tokenizer()
    corpus = load_corpus(repository_root=root)
    index = load_index(corpus, repository_root=root, plan=plan_corpus(corpus, encoder=encoder))
    retriever = CandidateRetriever(index)
    _require(index.spec['index_version'] == scope['index_version']
             and retriever.retriever_version == comparison['retriever_versions']['vector']
             and corpus.corpus_version == proposals['corpus_version'], 'The real index differs from the evaluated one.')

    original = PublicQuerySession(retriever=retriever, registry=previous, cache_dir=old_cache,
                                  encoder=encoder, provider_factory=provider_factory)
    new_registry = {'registry_version': 'qa-proposals-five-new-questions-v1', 'language': 'en', 'public_development_only': True,
                    'cases': [{'question_id': key, 'question': cases[key]['question']} for key in NEW_IDS]}
    newer = ProposalQuerySession(trial_scope=scope, retriever=retriever, registry=new_registry, cache_dir=new_cache,
                                 encoder=encoder, provider_factory=provider_factory)
    expected_ranks = {row['case_id']: [part['passage_id'] for part in row['vector']['top_five']]
                      for row in comparison['results']}
    prior_by_question = {case['question']: case['question_id'] for case in previous['cases']}

    def rank(case_id):
        question = cases[case_id]['question']
        prior_id = prior_by_question.get(question)
        result = original.run(prior_id, execute=False) if prior_id else newer.run(case_id, execute=False)
        _require(result['question'] == question
                 and result['query_embedding'] == {'cache_hit': True, 'provider_calls_this_run': 0}
                 and [p['passage_id'] for p in result['passages']] == expected_ranks[case_id],
                 'Cached vector retrieval changed the reviewed candidate order.')
        return result

    return cases, corpus, index, retriever, (old_cache, new_cache), rank


def run(root):
    attempts = []

    def forbidden(*args, **kwargs):
        attempts.append('provider_or_key')
        raise AssertionError('This offline flow cannot create a provider or load credentials.')

    cases, corpus, index, retriever, query_folders, rank_cached = cached_retrieval(root, forbidden)
    completed = load_answer_trial(root)
    completed.settings = AssessmentSettings()
    completed.client_factory = forbidden
    history = completed.coverage
    check_folders = (*query_folders, history.original_folder, history.retry_folder,
                     history.previous_folder, history.folder, completed.folder)
    before = _protected_hashes(check_folders)
    emitted = Counter()
    traces = {}

    with patch('notelens_rag.assessment_trial.read_assessment_settings', forbidden), \
         patch('notelens_rag.assessment_trial._client', forbidden), \
         patch('notelens_rag.query_smoke.read_settings', forbidden), patch('socket.create_connection', forbidden):
        saved = completed.run()
        _require(saved['cache_hit'] is True, 'The actual answer must come from its verified cache.')
        original_answer = json.loads(saved['result']['body_json'])
        original_trace = json.loads(saved['result']['quote_trace_json'])
        historical_inputs = {key: json.loads(prepare_from_history(history, cq, mock=True).inputs_json)
                             for key, (cq, _, _) in CASES.items() if cq is not None}
        definitions = {}
        for key in CASES:
            requirements, reviews, drafts = _proposal_judgments(cases[key], corpus)
            if key in historical_inputs:
                requirements = historical_inputs[key]['requirements']
                reviews = historical_inputs[key]['assessment']['parts']
            definitions[key] = requirements, reviews, drafts

        by_question = {cases[key]['question']: key for key in CASES}

        def admit(request):
            return set(request) == {'schema_version', 'question'} and request['question'] in by_question

        def rank(request):
            key = by_question[request['question']]
            result = rank_cached(key)
            emitted['chroma_rankings'] += 1
            for field in ('question_id', 'question', 'registry_sha256', 'query_embedding', 'query_run_budget'):
                result.pop(field)
            return {**result, 'mode': 'mock'}

        def assess(request, candidates, requirements):
            key = by_question[request['question']]
            decision = evaluate_support(request, candidates, requirements, {'format_version': 'rag-support-assessment-v1',
                'context_sha256': support_context_sha256(request, candidates, requirements), 'parts': definitions[key][1]})
            return SimpleNamespace(mode='mock', decision=decision)

        def generate(prepared, *, partial_policy):
            key = by_question[json.loads(prepared.inputs_json)['request']['question']]
            options = json.loads(prepared.evidence_json)
            if key == 'A-QA-01':
                option_ids = {(row['requirement_id'], row['passage_id'], row['start'], row['end']): row['evidence_id']
                              for row in options}
                claims = []
                for claim in original_answer['claims']:
                    refs = [part for part in original_trace if part['claim_id'] == claim['claim_id']]
                    requirement, = {ref['requirement_id'] for ref in refs}
                    claims.append({'requirement_id': requirement, 'text': claim['text'],
                        'evidence_ids': [option_ids[requirement, ref['passage_id'], ref['start'], ref['end']] for ref in refs]})
            else:
                drafts = list(definitions[key][2].values())
                requirements = list(dict.fromkeys(row['requirement_id'] for row in options))
                claims = [{'requirement_id': part, 'text': text,
                           'evidence_ids': [row['evidence_id'] for row in options if row['requirement_id'] == part]}
                          for part, text in zip(requirements, drafts, strict=True)]
            result = checked_answer_response(_fixture_completion(claims), prepared, PARAMETERS, mode='mock',
                                             partial_policy=partial_policy)
            traces[key] = [_trace_reference(trace, corpus) for trace in json.loads(result.quote_trace_json)]
            emitted['answer_replays_or_fixtures'] += 1
            return result

        backend = RagService(mode='mock', admit=admit, rank=rank,
            requirements=lambda request: definitions[by_question[request['question']]][0],
            assessor=SimpleNamespace(assess=assess), generator=SimpleNamespace(generate=generate),
            health_check=lambda: True, model_version='public-cached-flow-v1', partial_policy=PARTIAL_POLICY)
        contract = Contracts()
        results = []
        with TestClient(create_app(Settings(mode='mock'), backend=backend), client=('127.0.0.1', 45000)) as client:
            status = client.get('/health/ready')
            _require(status.status_code == 200 and status.json()['mode'] == 'mock', 'Unexpected readiness.')
            for key, (_, state, origin) in CASES.items():
                question = cases[key]['question']
                payload = {'schema_version': '1.0.0', 'question': question}
                for path, definition in (('/v1/retrieve', 'RetrievalResult'), ('/v1/literature-answer', 'AnswerResult')):
                    request_id = str(uuid4())
                    response = client.post(path, json=payload, headers={'X-Request-ID': request_id})
                    _require(response.status_code == 200 and response.headers['X-Request-ID'] == request_id,
                             f'The public fixture {key} failed its HTTP check.')
                    body = contract.validate(definition, response.json())
                    if definition == 'RetrievalResult':
                        retrieval = body
                _require(body['evidence_state'] == state and body['mode'] == 'mock'
                         and body['retrieval_provenance']['state'] == retrieval['state'], 'The answer lost its evidence state.')
                if key == 'A-QA-01':
                    _require(body['text'] == original_answer['text'], 'The live answer was not replayed exactly.')
                elif key == 'A-QA-07':
                    _require({source['topic_id'] for source in body['sources']} == {'179', '1624'}
                             and len(body['claims']) == 2, 'One of two topics was lost.')
                elif key == 'A-QA-02':
                    _require(len(body['claims']) == 1 and any('infectiousness' in item for item in body['warnings']),
                             'The partial answer lost its explicit gap.')
                else:
                    _require(body['route'] == 'none' and not body['claims'] and not body['sources'] and key not in traces,
                             'An unsupported search promoted a claim or called composition.')
                results.append({'case_id': key, 'http_mode': body['mode'], 'retrieval_state': retrieval['state'],
                                'evidence_state': body['evidence_state'], 'answer_origin': origin,
                                'claims': len(body['claims']), 'cited_topics': sorted({p['topic_id'] for p in body['sources']}),
                                'exact_quote_references': len(traces.get(key, []))})
            rejected = client.post('/v1/literature-answer', json={'schema_version': '1.0.0', 'question': 'Unregistered synthetic question?'},
                                   headers={'X-Request-ID': str(uuid4())})
            _require(rejected.status_code == 422 and rejected.json()['error']['code'] == 'validation_failure',
                     'An unregistered question passed admission.')

    _require(not attempts and emitted == {'chroma_rankings': 8, 'answer_replays_or_fixtures': 3}
             and before == _protected_hashes(check_folders)
             and not any((path/'.build.lock').exists() for path in check_folders), 'The offline flow changed protected state.')
    return {'format_version': 'rag-public-local-flow-v1', 'transport': 'in_process_asgi_http',
            'index_version': index.spec['index_version'], 'corpus_version': corpus.corpus_version,
            'retriever_version': retriever.retriever_version, 'real_chroma_rankings': emitted['chroma_rankings'],
            'answer_replays_or_fixtures': emitted['answer_replays_or_fixtures'], 'provider_calls': 0,
            'protected_cache_and_ledger_files_unchanged': len(before), 'unregistered_question_http_status': rejected.status_code,
            'cases': results}


if __name__ == '__main__':
    print(json.dumps(run(Path(__file__).resolve().parents[3]), indent=2, allow_nan=False))
