"""Read-only F-004 verifier; require current-source module evidence for shared passes."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
WORKSPACES = ['apps/web', 'contracts/generated/typescript']


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def web_issues(root):
    """Structural preflight; runtime probes below are also required for a web pass."""
    issues = []
    try:
        package = read_json(root / 'package.json')
        web = read_json(root / 'apps/web/package.json')
        lock = read_json(root / 'package-lock.json')
        if package.get('private') is not True or package.get('workspaces') != WORKSPACES:
            issues.append('ROOT_WORKSPACES')
        if web.get('dependencies', {}).get('@notelens/contracts') != '1.0.0':
            issues.append('CONTRACT_DEPENDENCY')
        link = lock.get('packages', {}).get('node_modules/@notelens/contracts', {})
        if link.get('link') is not True or link.get('resolved') != WORKSPACES[1]:
            issues.append('CONTRACT_LOCK_LINK')
        for script in ('dev', 'build', 'start', 'typecheck'):
            if not web.get('scripts', {}).get(script):
                issues.append('WEB_SCRIPT_' + script.upper())
    except (OSError, ValueError, TypeError, AttributeError):
        issues.append('WORKSPACE_METADATA')
    required = (
        '.env.example', 'apps/web/tsconfig.json', 'apps/web/next.config.ts',
        'apps/web/src/app/page.tsx', 'apps/web/src/app/layout.tsx',
        'apps/web/src/lib/scaffold/status.ts', 'apps/web/scripts/check-bindings.mjs',
        'apps/web/scripts/check-config.mjs',
    )
    for name in required:
        if not (root / name).is_file():
            issues.append('MISSING:' + name)
    if (root / 'apps/web/package-lock.json').exists():
        issues.append('NESTED_WEB_LOCK')
    build = root / 'apps/web/.next/BUILD_ID'
    if not build.is_file():
        issues.append('BUILD_NOT_VERIFIED')
    else:
        sources = [root / name for name in required]
        sources += [root / 'package-lock.json', root / 'apps/web/package.json']
        sources += list((root / 'apps/web/src').rglob('*'))
        if any(p.is_file() and p.stat().st_mtime_ns > build.stat().st_mtime_ns for p in sources):
            issues.append('BUILD_STALE')
    return issues


def service_issues(root, service):
    base = root / 'services' / service
    required = ['pyproject.toml', 'uv.lock', f'src/notelens_{service}/main.py']
    missing = [name for name in required if not (base / name).is_file()]
    if missing:
        return [f'{service}: missing ' + ', '.join(missing)]
    try:
        manifest = tomllib.loads((base / 'pyproject.toml').read_text(encoding='utf-8'))
        deps = manifest.get('project', {}).get('dependencies', [])
        if not any(str(dep).startswith('notelens-contracts') for dep in deps):
            return [f'{service}: frozen package dependency not declared']
    except (OSError, ValueError, TypeError, AttributeError):
        return [f'{service}: invalid manifest']
    # File presence cannot certify owner-local install, mock HTTP behavior or compatibility.
    return [f'{service}: owner-local installation/runtime verification still required']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-only', action='store_true', help='Verify B contribution only; does not close shared F-004')
    args = parser.parse_args()
    issues = web_issues(ROOT)
    node = shutil.which('node')
    tsc = ROOT / 'node_modules/typescript/bin/tsc'
    if not node or not tsc.is_file():
        issues.append('NODE_OR_TYPESCRIPT_MISSING')
    if not issues:
        probes = [
            [node, str(tsc), '--noEmit', '--incremental', 'false', '--project', str(ROOT / 'apps/web/tsconfig.json')],
            [node, str(ROOT / 'apps/web/scripts/check-bindings.mjs')],
            [node, str(ROOT / 'apps/web/scripts/check-config.mjs')],
        ]
        for index, command in enumerate(probes, 1):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
            if result.returncode:
                issues.append(f'WEB_PROBE_{index}_FAILED')
    if issues:
        for issue in issues:
            print('FAIL: ' + issue)
        return 1
    print('PASS: B web scaffold (installed types/runtime and current build artifact)')
    print('Local HTTP render verification is separate; this checker does not launch processes.')
    if args.web_only:
        print('Shared F-004 not evaluated; B-only scope.')
        return 0
    from scaffold_state import inventory_issues, receipt_issues, runtime_facts, source_fingerprint
    problems = inventory_issues(ROOT)
    try:
        receipt = read_json(ROOT / '.cache/scaffold/receipt.json')
        problems += receipt_issues(ROOT, receipt, source_fingerprint(ROOT), runtime_facts(ROOT))
    except (OSError, ValueError, subprocess.SubprocessError):
        problems.append('CURRENT_CANDIDATE_EVIDENCE_MISSING')
    for problem in problems:
        print('INCOMPLETE: ' + problem)
    if problems:
        return 1
    print('PASS: all current-source F-004 candidate checks; no shared startup/publication claim')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, subprocess.SubprocessError):
        print('FAIL: scaffold check could not execute a local probe')
        sys.exit(1)
