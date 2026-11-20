"""Verify the local F-007 checkpoint against the reviewed source and receipts."""

import json
from pathlib import Path
import re
import subprocess

from check_handoffs import check_handoffs, check_reviewed_foundation, require
from check_health import PROFILES, completion_issues, registry
from scaffold_state import inventory_issues, receipt_issues, runtime_facts, sha, source_fingerprint


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = 'docs/team/foundation-checkpoint.md'
WORKING_COPIES = 'docs/team/working-copies.md'
ORIGIN = 'https://github.com/NemanjaManic/notelens.git'
HEALTH_CACHE = Path('.cache/review/f011-health')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args],
                                   text=True, stderr=subprocess.DEVNULL, timeout=15).strip()


def verify_instructions(root):
    body = (root / CHECKPOINT).read_text(encoding='utf-8')
    base = re.search(r'^\*\*Preparation base\*\* `([0-9a-f]{40})`\.$', body, re.M)
    require(base, CHECKPOINT, 'missing exact preparation base')
    require(git(root, 'merge-base', base[1], 'HEAD') == base[1], CHECKPOINT,
            'preparation base is outside this branch')
    require(git(root, 'remote', 'get-url', 'origin') == ORIGIN, CHECKPOINT, 'unexpected origin')
    guide = (root / WORKING_COPIES).read_text(encoding='utf-8')
    require(ORIGIN in guide and 'NOTELENS_FOUNDATION_SHA' in guide
            and 'SPECIFY_FEATURE_NO_PERSIST' in guide and 'check-prerequisites.ps1' in guide,
            WORKING_COPIES, 'missing pinned working-copy or feature-selection instructions')


def verify_health_receipt(root, fingerprint):
    cache = (root / HEALTH_CACHE).resolve()
    pointer = json.loads((cache / 'latest.json').read_bytes())
    path = (root / pointer['report']).resolve()
    require(path.is_relative_to(cache) and path.name == 'report.json',
            HEALTH_CACHE, 'invalid health report path')
    raw = path.read_bytes()
    require(sha(raw) == pointer['sha256'] and pointer['passed'] is True and pointer['complete'] is True,
            HEALTH_CACHE, 'health pointer does not identify complete current evidence')
    report = json.loads(raw)
    require(report['format'] == 'notelens-f011-run-v1' and report['mode'] == 'mock'
            and report['scope'] == 'all-three-services' and report['passed'] is True
            and report['complete'] is True and report['source_fingerprint'] == fingerprint,
            HEALTH_CACHE, 'health receipt is stale, incomplete or outside the mock scope')
    count = len(registry())
    require(report['case_count'] == count and report['counts'] == {'passed': count}
            and not report['issues'] and not completion_issues(report['cases'], report['processes']),
            HEALTH_CACHE, 'health case coverage or process cleanup is incomplete')
    required = {f'{service}-{profile}.{kind}' for service, profile in PROFILES for kind in ('json', 'log')}
    require(required <= report['artifacts'].keys(), HEALTH_CACHE, 'missing health worker evidence')
    for name, digest in report['artifacts'].items():
        artifact = (path.parent / name).resolve()
        require(artifact.parent == path.parent and digest == sha(artifact.read_bytes()),
                HEALTH_CACHE, 'health artifact is outside the run or has changed')
    return count


def check_checkpoint(root):
    tasks, _ = check_handoffs(root)
    check_reviewed_foundation(root, tasks)
    require(any(task.alias == 'F-013' and task.done for task in tasks.values()),
            CHECKPOINT, 'F-013 must be recorded complete')
    verify_instructions(root)
    issues = inventory_issues(root)
    require(not issues, CHECKPOINT, f'{len(issues)} source inventory mismatches. First: {", ".join(issues[:3])}')
    fingerprint = source_fingerprint(root)
    scaffold = json.loads((root / '.cache/scaffold/receipt.json').read_bytes())
    issues = receipt_issues(root, scaffold, fingerprint, runtime_facts(root))
    require(not issues, CHECKPOINT, f'scaffold receipt issues {", ".join(issues)}')
    cases = verify_health_receipt(root, fingerprint)
    require(source_fingerprint(root) == fingerprint, CHECKPOINT, 'candidate sources changed during verification')
    return fingerprint, cases


def main():
    try:
        fingerprint, cases = check_checkpoint(ROOT)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        print(f'FAIL: {error}')
        return 1
    print(f'PASS: local checkpoint evidence, including all {cases} mock health cases.')
    print(f'Candidate source SHA-256: {fingerprint}')
    print('Publication is tracked separately under F-014.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
