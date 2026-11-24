"""Verify an approved runtime-only inventory reaches a loopback literature double in order."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from check_bounded_evaluation import billable_paths, exercise_profile, open_example
from run_bounded_evaluation import RunError, Web, digest, encoded, load_workload, question_payload, require
from start_mock import ROOT


def verify_inventory(args):
    raw = args.hash_inventory.read_bytes()
    require(digest(raw) == args.inventory_sha256, 'hash_inventory_sha256_mismatch')
    inventory = json.loads(raw)
    workload = load_workload(args.manifest, inventory['runtime_manifest']['sha256'], args.runtime_zip)
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
    with exercise_profile(fixtures, limits, reviewed_literature_hashes=workload.reviewed_literature_hashes(),
                          observed_literature=observed) as (stack, calls):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--runtime-zip', type=Path, required=True)
    parser.add_argument('--hash-inventory', type=Path, required=True)
    parser.add_argument('--inventory-sha256', required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    workload, cases, planned, identities = verify_inventory(args)
    require(not args.receipt.exists(), 'preserve_existing_replay_receipt')
    observed = verify_http(workload, cases, planned)
    require(observed == planned, 'final_literature_order_mismatch')
    base = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    diff = subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--binary', 'HEAD', '--',
                                    'apps/web/src', 'scripts/project/run_bounded_evaluation.py',
                                    'scripts/project/start_bounded_evaluation.py'])
    result = {'format': 'notelens-reviewed-literature-replay-v1', 'profile': 'offline-loopback-doubles',
              'document_inputs': 'built-in synthetic anchors', 'app_base_sha': base,
              'runtime_patch_sha256': digest(diff), 'runtime_manifest_sha256': workload.manifest_sha256,
              'runtime_zip_sha256': workload.bundle_sha256, 'hash_inventory_sha256': args.inventory_sha256,
              'requests_verified': len(observed), 'exact_order_and_hashes': True, 'provider_calls': 0,
              'loopback_listeners_closed': 4, 'cases': identities}
    with args.receipt.open('xb') as file:
        file.write(encoded(result))
    print(f'PASS: {len(observed)} A-bound requests in exact order with matching hashes; all four listeners stopped.')
    print(f'Receipt SHA-256: {digest(args.receipt.read_bytes())}')


if __name__ == '__main__':
    try:
        main()
    except RunError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        sys.exit(1)
