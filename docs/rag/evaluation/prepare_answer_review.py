"""Produce a reviewer packet from one live answer and checked public fixtures."""

import argparse
import hashlib
import json
from pathlib import Path

from notelens_rag.answers import PARTIAL_POLICY, checked_answer_response, prepare_answer, unsupported_answer
from notelens_rag.assessor import MODEL, AssessmentParameters
from notelens_rag.ingestion import load_corpus
from notelens_rag.support import evaluate_support, support_context_sha256


PARAMETERS = AssessmentParameters(max_output_tokens=512, reasoning_effort='none', timeout_seconds=30)
FIXTURE_IDS = ('A-QA-02', 'A-QA-03', 'A-QA-07', 'A-QA-08', 'A-QA-09')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _source(passage, corpus, score):
    return {'source_id': passage.passage_id, 'kind': 'literature', 'topic_id': passage.topic_id,
            'passage_id': passage.passage_id, 'title': passage.title, 'url': passage.url,
            'text': passage.text, 'snapshot_date': corpus.snapshot_date, 'score': score}


def _trace_reference(trace, corpus):
    passage = corpus.by_id[trace['passage_id']]
    start, end = trace['start'], trace['end']
    if not 0 <= start < end <= len(passage.text):
        raise ValueError('The review reference is outside the canonical passage.')
    exact = passage.text[start:end]
    if not exact.strip():
        raise ValueError('The review reference must contain source text.')
    digest = _sha(exact.encode('utf-8'))
    if (('quote' in trace and trace['quote'] != exact)
            or ('quote_sha256' in trace and trace['quote_sha256'] != digest)):
        raise ValueError('The review reference does not match the recorded source.')
    return {'evidence_id': trace['evidence_id'], 'passage_id': passage.passage_id,
            'topic_id': passage.topic_id, 'title': passage.title, 'url': passage.url,
            'start': start, 'end': end, 'quote_sha256': digest}


def _proposal_judgments(case, corpus):
    requirements = [{'requirement_id': f'part-{i}', 'description': part['requested_fact']}
                    for i, part in enumerate(case['parts'], start=1)]
    reviews, drafted = [], {}
    for part, requirement in zip(case['parts'], requirements, strict=True):
        identifier = requirement['requirement_id']
        if part['status'] == 'supported':
            evidence = []
            for item in part['evidence']:
                passage = corpus.by_id[item['passage_id']]
                start, end = item['passage_start'], item['passage_end']
                quote = passage.text[start:end]
                if _sha(quote.encode('utf-8')) != item['quote_sha256']:
                    raise ValueError('A proposal quote differs from the canonical slice.')
                evidence.append({'passage_id': passage.passage_id, 'start': start, 'end': end, 'quote': quote})
            reviews.append({'requirement_id': identifier, 'status': 'supported',
                            'reason': 'Evidence specified in the public proposal fixture.', 'evidence': evidence})
            drafted[identifier] = part['expected_fact']
        else:
            reviews.append({'requirement_id': identifier, 'status': 'not_supported',
                            'reason': part['reason'], 'evidence': []})
    return requirements, reviews, drafted


def _fixture_completion(claims):
    content = json.dumps({'language': 'en', 'claims': claims})
    native = {'object': 'response', 'model': MODEL, 'status': 'completed', 'error': None,
        'incomplete_details': None, 'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
            'content': [{'type': 'output_text', 'text': content}]}],
        'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
    return json.dumps(native).encode()


def _fixture(case, ranking, corpus, index_version):
    request = {'schema_version': '1.0.0', 'question': case['question']}
    candidates = {'record_format_version': 'rag-candidate-ranking-v1', 'status': 'ranked_candidates',
        'answerability': 'not_assessed', 'mode': 'mock', 'question_sha256': _sha(case['question'].encode()),
        'top_k': 5, 'signals_used': ['question'], 'corpus_version': corpus.corpus_version,
        'index_version': index_version, 'retriever_version': 'public-qa-saved-ranking-fixture-v1',
        'score_note': 'Fixture scores encode saved passage order only.',
        'passages': [_source(corpus.by_id[item['passage_id']], corpus, 1.0/rank)
                     for rank, item in enumerate(ranking['top_five'], start=1)]}
    requirements, reviews, drafted = _proposal_judgments(case, corpus)
    digest = support_context_sha256(request, candidates, requirements)
    decision = evaluate_support(request, candidates, requirements, {'format_version': 'rag-support-assessment-v1',
        'context_sha256': digest, 'parts': reviews})
    if decision.coverage != case['answerability']:
        raise ValueError('The proposal and reconstructed support decision differ.')
    prepared = prepare_answer(request, candidates, requirements, decision)
    if decision.coverage == 'none':
        result = unsupported_answer(prepared)
    else:
        options = json.loads(prepared.evidence_json)
        claims = [{'requirement_id': identifier, 'text': draft,
            'evidence_ids': [o['evidence_id'] for o in options if o['requirement_id'] == identifier]}
            for identifier, draft in drafted.items()]
        result = checked_answer_response(_fixture_completion(claims), prepared, PARAMETERS, mode='mock',
            partial_policy=PARTIAL_POLICY if decision.coverage == 'partial' else None)

    answer = result.body
    trace = json.loads(result.quote_trace_json)
    claims = [{'claim_id': claim['claim_id'], 'text': claim['text'],
               'evidence': [_trace_reference(item, corpus) for item in trace if item['claim_id'] == claim['claim_id']]}
              for claim in answer['claims']]
    return {'case_id': case['id'], 'question': case['question'], 'mode': answer['mode'],
            'origin': 'authored_output_fixture' if claims else 'local_abstention_fixture',
            'review_scope': 'Prompt, labels and draft text reflect this public proposal. No generated answer is measured.',
            'route': answer['route'], 'evidence_state': answer['evidence_state'], 'text': answer['text'],
            'warnings': answer['warnings'], 'claims': claims,
            'candidate_sources': [{k: p[k] for k in ('passage_id', 'topic_id', 'url', 'title')} for p in candidates['passages']]}


def build(root):
    files = {'proposals': 'docs/rag/qa-proposals.json',
             'rankings': 'docs/rag/evaluation/vector-proposal-comparison.json',
             'scope': 'docs/rag/evaluation/vector-proposal-scope.json',
             'live': 'docs/rag/evaluation/answer-trial-results.json',
             'manifest': 'services/rag/config/development-handoff.json'}
    raw = {name: (root/path).read_bytes() for name, path in files.items()}
    proposals, rankings, live, manifest = (json.loads(raw[k]) for k in ('proposals', 'rankings', 'live', 'manifest'))
    corpus = load_corpus(repository_root=root)
    index_version = manifest['retrieval']['index_version']
    if (proposals['partition'] != 'development_candidate' or proposals['corpus_version'] != corpus.corpus_version
            or json.loads(raw['scope'])['proposal_sha256'] != _sha(raw['proposals'])
            or json.loads(raw['scope'])['approval']['scope_sha256'] != rankings['scope_sha256']
            or manifest['corpus']['version'] != corpus.corpus_version
            or rankings['retriever_versions']['vector'] != manifest['retrieval']['development_retriever_version']
            or live['retrieval_provenance']['index_version'] != index_version
            or live['retrieval_provenance']['corpus_version'] != corpus.corpus_version):
        raise ValueError('The review inputs come from different development configurations.')
    case_by_id = {case['id']: case for case in proposals['cases']}
    ranked = {case['case_id']: case['vector'] for case in rankings['results']}
    if case_by_id['A-QA-01']['question'] != live['question'] or live['mode'] != 'live':
        raise ValueError('The saved actual answer does not match its public review question.')
    actual_claims = [{'claim_id': claim['claim_id'], 'text': claim['text'],
                      'evidence': [_trace_reference(item, corpus) for item in claim['evidence']]}
                     for claim in live['claims']]
    first = {'case_id': 'A-QA-01', 'question': live['question'], 'mode': live['mode'],
             'origin': 'actual_public_development_completion', 'prompt_version': live['prompt_version'],
             'answer_version': live['answer_version'], 'configuration_version': live['component']['configuration_version'],
             'route': live['route'], 'evidence_state': live['evidence_state'],
             'text': '\n\n'.join(claim['text'] for claim in actual_claims), 'claims': actual_claims}
    fixtures = [_fixture(case_by_id[identifier], ranked[identifier], corpus, index_version) for identifier in FIXTURE_IDS]
    return {'format_version': 'rag-development-answer-review-packet-v1', 'corpus_version': corpus.corpus_version,
            'index_version': index_version, 'input_sha256': {files[k]: _sha(v) for k, v in raw.items()},
            'new_provider_calls': 0, 'cases': [first, *fixtures]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a review packet or inspect its exact public source slices.')
    parser.add_argument('--evidence-case', help='Show exact local canonical text for this case only.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    packet = build(root)
    if args.evidence_case:
        matches = [row for row in packet['cases'] if row['case_id'] == args.evidence_case]
        if not matches:
            parser.error('Use a case ID from the packet.')
        corpus = load_corpus(repository_root=root)
        case, = matches
        evidence = [{**ref, 'quote': corpus.by_id[ref['passage_id']].text[ref['start']:ref['end']]}
                    for claim in case['claims'] for ref in claim['evidence']]
        output = {'case_id': case['case_id'], 'evidence': evidence}
        if case['evidence_state'] in ('partial', 'insufficient'):
            output['reviewed_candidates'] = [{**source, 'text': corpus.by_id[source['passage_id']].text}
                                             for source in case['candidate_sources']]
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(packet, indent=2, allow_nan=False))
