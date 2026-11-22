"""Re-score saved development rankings against D's relayed review and A's ranges.

This owner-local report does not freeze D's canonical benchmark or run a model.
"""

import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
from statistics import mean

from notelens_rag.reference_metrics import alternative_topic_metrics, evidence_at_five, verify_reference


REFERENCE_FILE = 'docs/rag/evaluation/reviewed-development-references.json'


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _unique_cases(rows, key):
    indexed = {row[key]: row for row in rows}
    _require(len(indexed) == len(rows), 'Duplicate development case identities.')
    return indexed


def _sets(parts):
    supported = [part for part in parts if part['status'] == 'supported']
    if not supported:
        return []
    choices = [[{ref['topic_id'] for ref in option} for option in part['evidence_options']]
               for part in supported]
    _require(all(choices), 'Supported parts need reviewed evidence options.')
    return sorted({tuple(sorted(set().union(*combination))) for combination in product(*choices)})


def _group(rows):
    metrics = [row['topic_metrics'] for row in rows if row['topic_metrics'] is not None]
    parts = [part for row in rows for part in row['parts'] if part['expected_status'] == 'supported']
    return {'case_count': len(rows), 'topic_metric_denominator': len(metrics),
            'mean_topic_recall_at_5': mean(m['recall_at_5'] for m in metrics) if metrics else None,
            'topic_mrr_at_5': mean(m['reciprocal_rank_at_5'] for m in metrics) if metrics else None,
            'all_required_topics_at_5_cases': sum(m['all_required_topics_at_5'] for m in metrics),
            'supported_part_denominator': len(parts),
            'supported_parts_with_evidence_at_5': sum(part['evidence_at_5'] for part in parts),
            'cases_with_all_supported_parts_at_5': sum(
                bool(row['supported_parts']) and all(p['evidence_at_5'] for p in row['parts']
                                                   if p['expected_status'] == 'supported') for row in rows)}


def evaluate_reviewed(root, *, references=REFERENCE_FILE):
    root = Path(root).resolve()
    reference_path = root / references
    reference_bytes = reference_path.read_bytes()
    reviewed = json.loads(reference_bytes)
    _require(reviewed['partition'] == 'development', 'Only development references may be evaluated.')
    hashes = {references: hashlib.sha256(reference_bytes).hexdigest()}
    inputs = {}
    for name, binding in reviewed['source_inputs'].items():
        path = (root / binding['path']).resolve()
        _require(path.is_relative_to(root / 'docs/rag'), 'Evaluation inputs must be A-owned development records.')
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        _require(digest == binding['sha256'], 'A bound development input changed.')
        hashes[binding['path']] = digest
        inputs[name] = json.loads(raw)
    corpus_path = (root / reviewed['corpus']['path']).resolve()
    _require(corpus_path.is_relative_to(root / 'data/knowledge'), 'The pinned corpus must be A-owned.')
    raw = corpus_path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == reviewed['corpus']['sha256'], 'The pinned corpus digest changed.')
    passages = _unique_cases([json.loads(line) for line in raw.decode('utf-8').splitlines()], 'passage_id')
    hashes[reviewed['corpus']['path']] = reviewed['corpus']['sha256']
    proposals, vector, lexical, scope = (inputs[k] for k in ('proposals', 'vector', 'lexical', 'scope'))
    proposal_hash = reviewed['source_inputs']['proposals']['sha256']
    _require(proposals['partition'] == 'development_candidate'
             and proposals['corpus_version'] == reviewed['corpus']['version'] == lexical['configuration']['corpus_version']
             and lexical['proposal_sha256'] == scope['proposal_sha256'] == proposal_hash
             and vector['scope_sha256'] == scope['approval']['scope_sha256'], 'The saved ranking scope differs.')
    original = _unique_cases(proposals['cases'], 'id')
    cases = _unique_cases(reviewed['cases'], 'case_id')
    vectors = _unique_cases(vector['results'], 'case_id')
    lexicals = _unique_cases(lexical['cases'], 'case_id')
    _require(original.keys() == cases.keys() == vectors.keys() == lexicals.keys(), 'Development case sets differ.')
    checked_references = set()
    for case_id, case in cases.items():
        old = original[case_id]
        _require(case['expected_coverage'] == old['answerability']
                 and case['source_shape'] == old['source_shape']
                 and len(case['parts']) == len(old['parts']), 'The relayed coverage or case structure differs.')
        for part, previous in zip(case['parts'], old['parts'], strict=True):
            _require(part['requested_fact'] == previous['requested_fact'] and part['status'] == previous['status'],
                     'A requested fact or its support label changed.')
            options = part['evidence_options']
            _require(bool(options) == (part['status'] == 'supported') and all(options),
                     'Evidence options must match the reviewed part status.')
            context = part.get('additional_context', [])
            for option in options:
                for ref in [*option, *context]:
                    verify_reference(ref, passages)
                    checked_references.add((ref['passage_id'], ref['passage_start'], ref['passage_end'], ref['quote_sha256']))
            if context:
                original_topics = {ref['topic_id'] for ref in previous['evidence']}
                _require({ref['topic_id'] for ref in context} <= original_topics,
                         'Additional context cannot introduce a required topic.')

    outputs = {}
    for method in ('vector', 'hybrid', 'bm25'):
        result_rows = []
        for case_id, case in cases.items():
            ranked = lexicals[case_id]['top_five'] if method == 'bm25' else vectors[case_id][method]['top_five']
            _require(len(ranked) <= 5, 'Saved rankings must respect the five-passage cutoff.')
            for hit in ranked:
                _require(hit['passage_id'] in passages
                         and passages[hit['passage_id']]['topic_id'] == hit['topic_id'],
                         'A ranked passage identity differs from the corpus.')
            topic_sets = _sets(case['parts'])
            part_rows = [{'requested_fact': part['requested_fact'], 'expected_status': part['status'],
                          'evidence_at_5': evidence_at_five(ranked, part['evidence_options'], part.get('additional_context', []))}
                         for part in case['parts']]
            result_rows.append({'case_id': case_id, 'source_shape': case['source_shape'],
                'expected_coverage': case['expected_coverage'], 'accepted_candidate_topic_sets': topic_sets,
                'topic_metrics': alternative_topic_metrics(ranked, topic_sets),
                'supported_parts': sum(p['expected_status'] == 'supported' for p in part_rows),
                'parts': part_rows, 'top_five': ranked})
        outputs[method] = {'groups': {group: _group([r for r in result_rows if r['source_shape'] == group])
                                      for group in ('single_topic', 'multi_topic', 'no_supported_topic')},
                           'overall': _group(result_rows), 'cases': result_rows}
    return {'format_version': 'rag-reviewed-development-evaluation-v1', 'partition': 'development',
            'reference_status': reviewed['reference_status'], 'review_provenance': reviewed['review_provenance'],
            'input_sha256': hashes, 'corpus_version': reviewed['corpus']['version'], 'index_version': scope['index_version'],
            'retriever_versions': {**vector['retriever_versions'], 'bm25': lexical['retriever_version']},
            'verified_unique_reference_spans': len(checked_references),
            'case_count': len(cases), 'methods': outputs, 'new_provider_calls': 0, 'fresh_rankings': 0,
            'semantic_support_model_run': False, 'final_test_accessed': False,
            'limitations': ['Saved rankings re-scored; no new retrieval, generation or semantic assessment.',
                            'Missing requested parts remain gaps even when their supported subset is retrieved.',
                            'D owns the shared canonical reference freeze; B still verifies application routing.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write a new result file; existing files are preserved.')
    args = parser.parse_args()
    report = evaluate_reviewed(Path(__file__).resolve().parents[3])
    encoded = json.dumps(report, indent=2, allow_nan=False) + '\n'
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(encoded)
    else:
        print(encoded, end='')
