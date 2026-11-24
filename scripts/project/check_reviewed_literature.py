"""Replay a pinned runtime-only inventory with local doubles and capture verified hashes."""

import argparse
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from check_bounded_evaluation import billable_paths, exercise_profile, open_example
from check_bounded_operator import read, verify_checksums
from run_bounded_evaluation import RunError, Web, digest, encoded, execute_workload, load_workload, question_payload, require
from start_mock import ROOT


def verify_inventory(args):
    raw = args.hash_inventory.read_bytes()
    require(digest(raw) == args.inventory_sha256, 'hash_inventory_sha256_mismatch')
    inventory = json.loads(raw)
    manifest_pin = args.manifest_sha256 or inventory['runtime_manifest']['sha256']
    workload = load_workload(args.manifest, manifest_pin, args.runtime_zip)
    require(workload.bundle_sha256 == inventory['runtime_bundle']['sha256'], 'inventory_runtime_zip_mismatch')
    cases = [case for case in workload.cases if case['route'] in ('literature_only', 'mixed')]
    planned = inventory['planned_question_sha256']
    require(len(cases) == len(inventory['cases']) == len(planned) == 16, 'expected_sixteen_literature_requests')
    identities = []
    for index, (case, item, pin) in enumerate(zip(cases, inventory['cases'], planned, strict=True), start=1):
        identity = {key: case[key] for key in ('case_id', 'case_version', 'route')}
        require(all(item[key] == value for key, value in identity.items()) and
                digest(case['question'].encode('utf-8')) == pin == item['question_sha256'], 'planned_question_pin_mismatch')
        identities.append({'ordinal': index, **identity, 'question_sha256': pin})
    return workload, cases, planned, identities


def verify_http(workload, cases, planned):
    fixtures = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_bytes())
    counts = workload.required_calls()
    limits = {'extract': 0, 'document-answer': sum(case['route'] == 'mixed' for case in cases),
              'literature-answer': counts['literature-answer']}
    observed = []
    with exercise_profile(fixtures, limits, reviewed_question_hashes=replace(workload, cases=cases).reviewed_question_hashes(),
                          observed_questions={'/v1/literature-answer': observed}) as (stack, calls):
        web = Web(stack, time.monotonic() + 60)
        for index, case in enumerate(cases):
            if index % 8 == 0:
                report, cookie = open_example(stack)
                document = report.split('=', 1)[1]
            try:
                turn, _ = web.request('/api/questions', 200, body=encoded(question_payload(case, document)),
                                      content_type='application/json', cookie=cookie)
            except RunError as error:
                raise RunError(f"{case['case_id']}: {error}") from None
            branches = turn['answer']['branches']
            expected = ['document', 'literature'] if case['route'] == 'mixed' else ['literature']
            require([branch['origin'] for branch in branches] == expected and
                    all(branch['result']['kind'] == 'accepted' for branch in branches), 'offline_answer_branch_mismatch')
            require(observed == planned[:index + 1], 'observed_literature_hash_or_order_mismatch')
        require(billable_paths(calls).count('/v1/document-answer') == limits['document-answer'] and
                '/v1/extract' not in billable_paths(calls), 'unexpected_offline_document_calls')
    return observed


def verify_full_http(workload, planned, app_sha):
    fixtures = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_bytes())
    fixtures['extraction-valid'] = fixtures['extraction-empty']
    fixtures['answer-document'] = {**fixtures['answer-none'], 'attempted_routes': ['document'], 'retrieval_provenance': None}
    limits = workload.required_calls()
    observed = {'/v1/document-answer': [], '/v1/literature-answer': []}
    calls = []

    @contextmanager
    def stack_context(_deadline, deadline_unix_ms, _watchdog):
        with exercise_profile(fixtures, limits, reviewed_question_hashes=workload.reviewed_question_hashes(),
                              observed_questions=observed, deadline_unix_ms=deadline_unix_ms) as (stack, exchanges):
            yield stack
            calls.extend(exchanges)

    with TemporaryDirectory() as folder:
        output = Path(folder) / 'offline-runtime'
        result = execute_workload(workload, output, stack_context, run_id='offline-reviewed-runtime', app_sha=app_sha,
                                  deadline_seconds=60, scope='synthetic', profile='offline')
        verify_checksums(output)
        if result['status'] != 'completed':
            failure = read(output, 'failures.json')[0]
            raise RunError(f"{failure['stage']} {failure['case_id'] or ''}: {failure['reason']}")
        require(result['saved_cases'] == 26 and result['saved_sources'] == 16 and result['web_shutdown_verified'],
                'full_runtime_capture_incomplete')
        identities = []
        for number, case in enumerate(workload.cases, start=1):
            saved = read(output, f'case-{number:03}.json')
            require(saved['case_id'] == case['case_id'] and saved['case_version'] == case['case_version'],
                    'saved_case_identity_mismatch')
            if case['route'] == 'out_of_scope':
                require(saved['answer']['state'] == 'unsupported' and not saved['answer']['branches'],
                        'out_of_scope_dispatch_detected')
            identities.append({'ordinal': number, 'case_id': case['case_id'], 'case_version': case['case_version'],
                               'route': case['route'], 'question_sha256': digest(case['question'].encode('utf-8')),
                               'http_status': 200, 'answer_state': saved['answer']['state']})
    require(observed['/v1/literature-answer'] == planned, 'observed_literature_hash_or_order_mismatch')
    require(observed['/v1/document-answer'] == [row['question_sha256'] for row in identities
            if row['route'] in ('document_only', 'mixed')], 'observed_document_hash_or_order_mismatch')
    extracted = [source for path, source in calls if path == '/v1/extract']
    require(len(extracted) == len(set(extracted)) == 16 and set(extracted) == set(workload.sources), 'extraction_source_mismatch')
    require(len(billable_paths(calls)) == sum(limits.values()), 'unexpected_service_dispatch')
    return identities, limits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', help='Exact pin when the manifest supersedes the hash inventory manifest.')
    parser.add_argument('--runtime-zip', type=Path, required=True)
    parser.add_argument('--hash-inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--full-runtime', action='store_true', help='Replay all reviewed cases with local doubles.')
    args = parser.parse_args()
    workload, cases, planned, identities = verify_inventory(args)
    require(not args.receipt.exists(), 'preserve_existing_replay_receipt')
    base = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    if args.full_runtime:
        identities, dispatches = verify_full_http(workload, planned, base)
    else:
        observed = verify_http(workload, cases, planned)
        require(observed == planned, 'final_literature_order_mismatch')
    diff = subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--binary', 'HEAD', '--',
                                    'apps/web/src', 'scripts/project/run_bounded_evaluation.py',
                                    'scripts/project/start_bounded_evaluation.py'])
    result = {'format': 'notelens-reviewed-literature-replay-v1', 'profile': 'offline-loopback-doubles',
              'document_inputs': 'built-in synthetic anchors', 'app_base_sha': base,
              'runtime_patch_sha256': digest(diff), 'runtime_manifest_sha256': workload.manifest_sha256,
              'runtime_zip_sha256': workload.bundle_sha256, 'hash_inventory_sha256': args.inventory_sha256,
              'requests_verified': len(planned), 'exact_order_and_hashes': True, 'provider_calls': 0,
              'loopback_listeners_closed': 4, 'cases': identities}
    if args.full_runtime:
        result.update(format='notelens-reviewed-runtime-replay-v1', document_inputs='pinned runtime-only sources',
                      cases_verified=len(identities), service_dispatches=dispatches)
    with args.receipt.open('xb') as file:
        file.write(encoded(result))
    if args.full_runtime:
        print(f'PASS: {len(identities)} runtime cases, exact A/D request order and hashes, and one extraction per source.')
    print(f'PASS: {len(planned)} A-bound requests in exact order with matching hashes; all four listeners stopped.')
    print(f'Receipt SHA-256: {digest(args.receipt.read_bytes())}')


if __name__ == '__main__':
    try:
        main()
    except RunError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
