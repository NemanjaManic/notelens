"""Build an offline A-owned accounting proposal and immutable CQ review handoff."""

import argparse
import ast
import copy
import csv
from decimal import Decimal, ROUND_CEILING
import hashlib
import io
import json
from pathlib import Path
import zipfile

from notelens_rag.ingestion import load_corpus


ROOT = Path(__file__).resolve().parents[3]
EXPECTED_ARCHIVE = 'b1fdf1593839ee0c60ce45afe6723dffd7b9fd8c3599af801c969caec5a1b9bd'
EXPECTED_REVIEW = 'a588cbe0abd49c175d49bfa599ff8f13e625378cc89062a84d8fdd91942dfe9a'
EXPECTED_RECEIPT = '9c5a16ef6020ba4963ae4f3be20aab2ac85a8a65d6a3a7da35de6ec536d7509a'
FILES = {'d009-A-metadata-handoff-v1.json', 'original-CQ-ratings.transcribed.csv',
         'rag-five-answer-feedback-from-d.md', 'README.md', 'SHA256SUMS.txt'}
CRITERIA = ('source_support', 'required_facts', 'extra_facts', 'uncertainty_and_context',
            'evidence_gaps', 'scope_and_safety', 'clarity_and_english')
CASE_IDS = ('CQ-03', 'CQ-05', 'CQ-09')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def supplied_files(path):
    raw = path.read_bytes()
    require(sha(raw) == EXPECTED_ARCHIVE, 'Unexpected metadata archive identity.')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(len(entries) == len(FILES) and {e.filename for e in entries} == FILES
                and all(e.file_size <= 16384 for e in entries), 'Unexpected archive inventory.')
        supplied = {name: archive.read(name) for name in FILES}
    sums = supplied['SHA256SUMS.txt'].decode('utf-8').splitlines()
    require(len(sums) == 4, 'Unexpected checksum count.')
    checked = set()
    for line in sums:
        digest, name = line.split(maxsplit=1)
        require(name in FILES - {'SHA256SUMS.txt'} and name not in checked
                and sha(supplied[name]) == digest, 'Supplied checksum mismatch.')
        checked.add(name)
    require(checked == FILES - {'SHA256SUMS.txt'}, 'Incomplete checksum coverage.')
    require(sha(supplied['rag-five-answer-feedback-from-d.md']) == EXPECTED_REVIEW,
            'Original CQ review changed.')
    return supplied


def ratings(supplied):
    rows = list(csv.DictReader(io.StringIO(supplied['original-CQ-ratings.transcribed.csv'].decode())))
    require(len(rows) == 5 and {row['case_id'] for row in rows}
            == {'CQ-01', 'CQ-03', 'CQ-05', 'CQ-07', 'CQ-09'}, 'Unexpected rating inventory.')
    result = {row['case_id']: {key: int(row[key]) for key in CRITERIA} for row in rows}
    original = supplied['rag-five-answer-feedback-from-d.md'].decode('utf-8')
    for identifier, scores in result.items():
        expected = '| ' + identifier + ' | Full | ' + ' | '.join(str(scores[k]) for k in CRITERIA) + ' |'
        require(expected in original, 'CSV ratings differ from the original Markdown review.')
    require(sum(len(v) for v in result.values()) == 35, 'Incomplete original ratings.')
    return result


def checked_trace(trace, corpus):
    result = copy.deepcopy(trace)
    passage = corpus.by_id[result['passage_id']]
    start, end = result['start'], result['end']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(passage.text)
            and passage.text[start:end] == result['quote'], 'Canonical citation mismatch.')
    result.update(topic_id=passage.topic_id, title=passage.title, url=passage.url,
                  quote_sha256=sha(result['quote'].encode('utf-8')),
                  offset_unit='unicode_code_points', interval='[start,end)')
    return result


def cq_cases(receipt, old_scores, corpus):
    cases = []
    questions = {row['question_id']: row['question'] for row in receipt['scope']['questions']}
    for identifier in CASE_IDS:
        source, = (row for row in receipt['cases'] if row['question_id'] == identifier)
        require(source['http_status'] == 200, 'Original case was not successful.')
        claims = [{key: c[key] for key in ('claim_id', 'text', 'scope', 'source_ids')}
                  for c in source['claims']]
        original = {'origin': 'actual_public_development_completion', 'claims': claims,
                    'citation_trace': [checked_trace(t, corpus) for t in source['citation_trace']]}
        revised = copy.deepcopy(original)
        revised['origin'] = 'authored_development_revision_not_new_provider_output'
        if identifier == 'CQ-03':
            extra = copy.deepcopy(revised['citation_trace'][1])
            passage = corpus.by_id[extra['passage_id']]
            extra.update(evidence_id='e3', start=754, end=973, quote=passage.text[754:973])
            revised['citation_trace'].append(checked_trace(extra, corpus))
        elif identifier == 'CQ-05':
            revised['claims'][1]['text'] = 'The yellow color occurs when too much bilirubin builds up.'
        else:
            before = 'bad-smelling or cloudy or reddish urine'
            require(before in revised['claims'][0]['text'], 'Unexpected original CQ-09 text.')
            revised['claims'][0]['text'] = revised['claims'][0]['text'].replace(
                before, 'urine that smells bad or looks cloudy or reddish')
        for variant in (original, revised):
            require(all(any(t['claim_id'] == c['claim_id'] for t in variant['citation_trace'])
                        for c in variant['claims']), 'Claim has no citation.')
        cases.append({'case_id': identifier, 'question': questions[identifier], 'coverage_original': 'Full',
                      'original': original, 'corrected': revised,
                      'original_ratings': old_scores[identifier],
                      'corrected_ratings': {key: None for key in CRITERIA},
                      'corrected_review_status': 'pending_D_review',
                      'original_severity_adjudication': 'pending_separate_CQ05_decision'
                      if identifier == 'CQ-05' else 'no_new_decision_recorded'})
    return cases


def accounting(metadata, freeze):
    require(metadata['case_count'] == 26 and metadata['route_counts'] == {
        'document_only': 8, 'literature_only': 8, 'mixed': 8, 'out_of_scope': 2}, 'Unexpected routes.')
    n = metadata['module_work_inventory']['A_literature_question_branches']
    require(n == 16 and metadata['module_work_inventory']['distinct_runtime_documents'] == 16,
            'Unexpected work inventory.')
    profile = freeze['responses']['historical_verified_profile']
    runner = ast.parse((ROOT / 'docs/rag/evaluation/run_live_http_smoke.py').read_text(encoding='utf-8'))
    embedding_limit, = (ast.literal_eval(node.value) for node in runner.body if isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'EMBEDDING_LIMIT' for t in node.targets))
    require(embedding_limit == 128 and profile['automatic_retries'] == 0
            and profile['timeout_seconds'] == 30 and profile['max_output_tokens_per_completion'] == 512
            and profile['input_token_ceilings'] == {'question_parts': 4096, 'support': 20000, 'answer': 4096},
            'Historical profile changed; re-review the proposal.')
    stages = {key: {'max_requests': n, 'max_input_tokens_per_request': limit,
                    'max_input_tokens_total': n * limit, 'max_output_tokens_per_request': 512,
                    'max_output_tokens_total': n * 512}
              for key, limit in profile['input_token_ceilings'].items()}
    response_input = sum(v['max_input_tokens_total'] for v in stages.values())
    response_output = sum(v['max_output_tokens_total'] for v in stages.values())
    embedding_tokens = n * embedding_limit
    response_upper = (Decimal(response_input) * Decimal('0.125')
                      + Decimal(response_output) * Decimal('0.50')) / 1_000_000
    embedding_upper = Decimal(embedding_tokens) * Decimal('0.02') / 1_000_000
    upper = (response_upper + embedding_upper) * Decimal('1.10')
    cap = upper.quantize(Decimal('0.01'), rounding=ROUND_CEILING)
    return {'basis': 'Conditional ceiling for one A call per literature/mixed case; not actual usage.',
            'model': profile['model'], 'reasoning_effort': 'none', 'service_tier': 'default',
            'embedding_model': freeze['retrieval']['embedding_model'], 'embedding_dimensions': 1536,
            'stages': stages, 'max_A_answer_endpoint_requests': n,
            'max_embedding_requests': n, 'max_embedding_tokens_per_request': embedding_limit,
            'max_embedding_input_tokens': embedding_tokens, 'max_generation_requests': n * 3,
            'max_response_input_tokens': response_input, 'max_response_output_tokens': response_output,
            'max_free_input_count_requests': n * 3, 'max_provider_HTTP_requests_including_counting': n * 7,
            'max_chargeable_embedding_plus_generation_requests': n * 4,
            'corpus_reembedding_requests': 0, 'automatic_retries': 0, 'structural_repair_requests': 0,
            'provider_request_timeout_seconds_proposed': 30,
            'absolute_provider_deadline_required': True,
            'sequential_provider_timeout_sum_seconds': n * 7 * 30,
            'A_absolute_wall_deadline_seconds_proposed': 3600,
            'A_wall_deadline_status': 'new proposed stop limit, not a completion estimate or implemented timer',
            'prices_usd_per_million': {'response_input': '0.10', 'response_cache_write_upper': '0.125',
                                     'response_output': '0.50', 'embedding_input': '0.02'},
            'regional_allowance_multiplier': '1.10', 'price_checked_on': '2026-11-24',
            'price_sources': ['https://developers.openai.com/api/docs/models/gpt-6-luna',
                              'https://developers.openai.com/api/docs/models/text-embedding-3-small',
                              'https://help.openai.com/en/articles/4936856-understanding-and-counting-tokens'],
            'conservative_A_usage_upper_usd': str(upper), 'A_new_cap_usd_proposed': str(cap),
            'new_provider_execution_authorized': False, 'joint_cost_cap_usd': None,
            'joint_duration_limit_seconds': None,
            'joint_limits_reason': 'D provider profile/limits and B counted final app profile are not supplied.'}


def report(packet):
    a = packet['A_accounting_proposal']
    lines = ['# D-009: A contribution to CQ review and final execution limits', '',
             'Prepared: 2026-11-24. Owner: Nemanja (A). Status: proposal only; joint execution is not ready.', '',
             'The user confirmed one frozen 26-case pass with no model tuning. No new paid execution is authorized.',
             'The supplied archive contains metadata and public development review only. No final question or scoring content was opened.', '',
             '## Receipt and original ratings', '',
             f"Archive SHA-256: `{EXPECTED_ARCHIVE}`. All four supplied checksum entries match.",
             f"Original D review SHA-256: `{EXPECTED_REVIEW}`; all 35 CSV scores match its Markdown table.",
             'The original remains Draft (2026-11-19); no new human or independent-review status is inferred.',
             'The JSON preserves the original review and CSV verbatim as UTF-8 strings, all ratings, and exact claim/source traces.', '',
             '| Case | Source support | Required facts | Extra facts | Uncertainty/context | Evidence gaps | Scope/safety | Clarity/English |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for identifier, scores in packet['original_ratings_all_five'].items():
        lines.append('| ' + identifier + ' | ' + ' | '.join(str(scores[k]) for k in CRITERIA) + ' |')
    lines += ['', 'Scores: 2 meets, 1 minor issue, 0 major issue, U unable to judge. Corrected ratings remain unmeasured.',
              'CQ-05 original severity adjudication is separate from review of its narrower correction.', '',
              '## Exact original and authored corrected claims', '',
              'Claims are copied exactly from the verified public live receipt. Corrections are authored examples, not fresh model outputs.']
    for case in packet['CQ_cases']:
        lines += ['', f"### {case['case_id']}", '', case['question'], '', 'Original:', '']
        lines += [f"- `{c['claim_id']}`: {c['text']}" for c in case['original']['claims']]
        lines += ['', 'Corrected:', '']
        lines += [f"- `{c['claim_id']}`: {c['text']}" for c in case['corrected']['claims']]
        lines += ['', 'Corrected citation mapping (original mapping is retained in JSON):', '']
        for t in case['corrected']['citation_trace']:
            lines += [f"- `{t['claim_id']}` / `{t['evidence_id']}`: [{t['title']}]({t['url']}), "
                      f"`{t['passage_id']}`, code points `[{t['start']}, {t['end']})`.",
                      f"  Exact quote: {t['quote']}"]
    lines += ['', '## Proposed A request and token ceilings', '',
              'These are maximum reservations, not measured usage or a promise that every stage will run.',
              'Conditions: one literature-answer operation for each of 8 literature-only + 8 mixed cases; no duplicate retrieve call, re-render, preview, repair, retry, corpus embedding or scoring-model call.',
              'The other 8 document-only and 2 out-of-scope cases must make zero A calls, verified before execution.', '',
              '| Operation | Max requests | Input tokens/request | Input tokens/total | Output tokens/total |',
              '| --- | ---: | ---: | ---: | ---: |',
              '| Query embedding | 16 | 128 | 2,048 | 0 |']
    for key, v in a['stages'].items():
        lines.append(f"| {key} | 16 | {v['max_input_tokens_per_request']:,} | {v['max_input_tokens_total']:,} | {v['max_output_tokens_total']:,} |")
    lines += ['', 'Totals: at most 16 embeddings + 48 generations; generation input <=451,072 tokens, output <=24,576 tokens; embedding input <=2,048 tokens.',
              'Each generation is preceded by an input-count request: at most 48 additional free counting requests, or 112 provider HTTP requests in total (64 potentially chargeable).',
              'Each generation is capped at 512 output tokens, reasoning none, Standard/default tier. Unsupported, empty-evidence and first-error paths may reduce the totals.', '',
              '## Price and duration proposal', '',
              'Official rates checked on 2026-11-24: GPT-6 Luna input $0.10, cache-write upper $0.125, output $0.50; text-embedding-3-small input $0.02, all per million tokens.',
              'The upper calculation uses the cache-write rate for every generation input, no cache discount, and a conservative 10% regional allowance for the entire subtotal.', '',
              '`((451072 * 0.125 + 24576 * 0.50 + 2048 * 0.02) / 1000000) * 1.10 = USD 0.075584256`', '',
              '**Proposed new A-only cap: USD 0.08. It is not approved or shared with D. Historical budgets remain closed.**',
              'This is an API-usage reservation; provider billing is unmeasured. No hosting or tax amount is inferred.', '',
              'Propose a 30-second timeout plus an absolute deadline for each embedding, counting and generation operation; zero SDK/HTTP/application retries and zero structural repairs.',
              '112 operations x 30 seconds gives a 3,360-second (56-minute) sequential provider timeout sum.',
              'Propose a separate enforced 3,600-second (60-minute) A wall-clock stop limit including local work. It is a cutoff, not an execution-time forecast.',
              'Existing SDK timeouts alone do not prove an absolute wall-clock bound. The final operator profile must implement and demonstrate cancellation and accounting for in-flight calls.', '',
              'Stop on the first unexpected transport/provider/validation/usage/pricing error or exceeded limit. Record a valid expected partial/refusal response and continue; do not treat it as an infrastructure failure.',
              'Reserve each attempt before sending; keep completed outputs and usage and mark uncertain in-flight costs as reserved. No automatic restart, replay or budget release after failure.', '',
              'Price sources:', '']
    lines += [f'- [{url.rsplit("/", 1)[-1]}]({url})' for url in a['price_sources']]
    lines += ['', '## What still prevents a joint executable freeze', '',
              '- Metadata names v2 as received and v3 as custodian-declared, with v3 bytes not received. D/custodian must reconcile the authoritative manifest, 26 case identities and replacement receipt before releasing runtime inputs to the operator. Scoring stays evaluator-only.',
              '- B must supply the final app SHA, B-009 evidence, designated operator and a ready bounded live profile. The last local source inspection is not a new B acceptance.',
              '- The current local web client has a 5-second service timeout and accepts mock mode only; its consumer rejects live records. It cannot serve as the final live profile unchanged.',
              '- D must supply the chosen provider/model, extraction and document-answer token limits, request/counting multiplicity and timeouts. The current local D service is mock-only, and its default offline repair bound is two attempts. The proposed live policy requires one attempt.',
              '- A/B need a counted synthetic dry run on the exact chosen profile proving 16 A calls, zero A calls for the remaining routes, no separate retrieve duplication and no render-triggered processing. A numerical inventory check is not that dry run.',
              '- A ceiling of 32 D generations is conditional on exactly 16 extraction operations plus 16 document-answer operations, one generation each, no hidden summary/repair/judge calls and no re-extraction during rendering. Sixteen distinct documents alone do not prove this.',
              '- Joint new cost limit and wall deadline remain unset until those D/B bounds exist. Neither zero nor USD 0.08 is a valid whole-system total. If D is proven to use 32 one-shot generations, the conditional billable ceiling is 16 embeddings + 80 generations, with D counting requests added separately.',
              '- The operator must enforce the existing in-memory 60-minute submitted-document retention, processing documents just in time if necessary; the run deadline does not extend retention.',
              '- Exact submission time on 2026-11-24 must come from the tutor. Midnight and completion before submission are not assumed.', '',
              'Final extraction F1 remains explicitly unmeasured because separate final reference annotations are missing; record this scope decision in the joint report.', '',
              '## Reproduction and verification', '',
              'From the repository root, with the existing RAG environment and pinned public corpus:', '',
              '```powershell',
              "& ./services/rag/.venv/Scripts/python.exe -B ./docs/rag/evaluation/prepare_d009_handoff.py --metadata-zip 'C:/Users/Nemanja/Downloads/D009-metadata-and-original-CQ-review-v1.zip'",
              '```', '',
              'The utility has no provider client or execution switch. It checks ZIP checksums, all 35 original ratings, the original live receipt, canonical citation slices, all 56 freeze hashes and Decimal accounting, then writes only A-owned handoff artifacts.',
              'This is offline inventory validation, not the B counted runtime dry run, final scoring, independent corrected-answer review or a Spec Kit implementation workflow.']
    return ('\n'.join(lines) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-zip', required=True, type=Path)
    args = parser.parse_args()
    supplied = supplied_files(args.metadata_zip)
    old_scores = ratings(supplied)
    metadata = json.loads(supplied['d009-A-metadata-handoff-v1.json'])
    freeze_raw = (ROOT / 'services/rag/config/frozen-rag-v1.json').read_bytes()
    freeze = json.loads(freeze_raw)
    for path, digest in freeze['file_sha256'].items():
        require(sha((ROOT / path).read_bytes()) == digest, 'A frozen file hash differs: ' + path)
    receipt_raw = (ROOT / 'services/rag/.cache/live-http-smoke-2026-11-19/run.json').read_bytes()
    require(sha(receipt_raw) == EXPECTED_RECEIPT, 'Original live receipt changed.')
    corpus = load_corpus(repository_root=ROOT, expected_corpus_version=freeze['corpus']['version'])
    cases = cq_cases(json.loads(receipt_raw), old_scores, corpus)
    packet = {'format_version': 'd009-A-offline-handoff-v1', 'prepared_on': '2026-11-24',
              'owner': 'Nemanja (A)', 'status': 'proposal_only_joint_execution_blocked',
              'metadata_archive_sha256': EXPECTED_ARCHIVE, 'metadata': metadata,
              'source_sha256': {name: sha(raw) for name, raw in supplied.items()},
              'frozen_manifest_sha256': sha(freeze_raw), 'original_live_receipt_sha256': EXPECTED_RECEIPT,
              'original_review_verbatim_utf8': supplied['rag-five-answer-feedback-from-d.md'].decode('utf-8'),
              'original_ratings_csv_verbatim_utf8': supplied['original-CQ-ratings.transcribed.csv'].decode('utf-8'),
              'original_ratings_all_five': old_scores, 'original_review_status': 'Draft, 2026-11-19',
              'CQ_cases': cases, 'A_accounting_proposal': accounting(metadata, freeze),
              'final_extraction_F1': {'value': None, 'status': 'unmeasured',
                                     'reason': 'Separate final reference annotations missing.'},
              'verification': {'supplied_checksum_entries': 4, 'original_scores_verified': 35,
                               'freeze_file_hashes_verified': len(freeze['file_sha256']),
                               'canonical_citation_links_verified': sum(len(c[v]['citation_trace'])
                                   for c in cases for v in ('original', 'corrected')),
                               'public_corpus_passages_validated': corpus.passage_count,
                               'provider_calls': 0, 'final_test_accessed': False,
                               'counted_B_runtime_dry_run_performed': False}}
    artifacts = {'d009-a-preflight-v1.json': encoded(packet), 'd009-a-preflight-v1.md': report(packet)}
    output = ROOT / 'docs/rag/evaluation'
    for name, raw in artifacts.items():
        target = output / name
        require(not target.exists() or target.read_bytes() == raw, 'Refusing to replace different evidence: ' + name)
    for name, raw in artifacts.items():
        (output / name).write_bytes(raw)
    package_files = artifacts | {'original-live-http-run.json': receipt_raw,
                                'source-metadata-handoff.zip': args.metadata_zip.read_bytes()} | supplied
    package_files['source-SHA256SUMS.txt'] = supplied['SHA256SUMS.txt']
    package_files['SHA256SUMS.txt'] = ''.join(f'{sha(raw)}  {name}\n' for name, raw in package_files.items()
                                            if name != 'SHA256SUMS.txt').encode('utf-8')
    archive_path = ROOT / 'services/rag/.cache/d009-handoff/D009-A-RAG-CQ-and-limits-v1.zip'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in package_files.items():
            entry = zipfile.ZipInfo(name, date_time=(2026, 11, 24, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, raw)
    archive_raw = buffer.getvalue()
    require(not archive_path.exists() or archive_path.read_bytes() == archive_raw,
            'Refusing to replace a different handoff archive.')
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(archive_raw)
    print(json.dumps({'status': 'offline_inventory_verified_not_execution_ready',
                      **packet['verification'], 'A_usage_upper_usd': packet['A_accounting_proposal']['conservative_A_usage_upper_usd'],
                      'A_cap_usd_proposed': packet['A_accounting_proposal']['A_new_cap_usd_proposed'],
                      'archive': archive_path.relative_to(ROOT).as_posix(), 'archive_sha256': sha(archive_raw)}, indent=2))


if __name__ == '__main__':
    main()
