"""B-owned finite secret, workflow and public dependency-advisory checks."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from uuid import uuid4

import check_scope as scope
from scaffold_process import run_owned

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = '.github/workflows/key-free-ci.yml'
PR_WORKFLOW = '.github/workflows/f010-key-free.yml'
PR_SECURITY_STEP = 'Check mock security and platform regressions'
PR_SECURITY_ENV = {'NEXT_TELEMETRY_DISABLED': '1', 'NOTELENS_MODE': 'mock'}
PR_SECURITY_RUN = '\n'.join((
    "$ErrorActionPreference = 'Stop'",
    "$PSNativeCommandUseErrorActionPreference = $true",
    "& ./scripts/project/.venv/Scripts/python.exe -B scripts/project/check_mock_security.py",
    "node apps/web/scripts/check-contracts.mjs",
    "node apps/web/scripts/check-preparation.mjs",
    "node apps/web/scripts/check-sessions.mjs",
    "node apps/web/scripts/check-report.mjs",
    "& ./node_modules/.bin/tsc.cmd --noEmit --project apps/web/tests/tsconfig.routing.json",
    "node --test apps/web/tests/routing.test.ts",
))
ACTIONS = {
    'actions/checkout': 'd23441a48e516b6c34aea4fa41551a30e30af803',
    'actions/setup-python': 'ece7cb06caefa5fff74198d8649806c4678c61a1',
    'actions/setup-node': '48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e',
}
PATTERNS = {
    'PRIVATE_KEY': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'),
    'PROVIDER_TOKEN': re.compile(rb'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}'),
    'GITHUB_TOKEN': re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}'),
    'AWS_ACCESS_KEY': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'GOOGLE_API_KEY': re.compile(rb'\bAIza[A-Za-z0-9_-]{35}\b'),
}


# Only these reviewed PowerShell bodies are accepted by the bounded workflow guard.
# A body change needs B review of the trusted guard as well as the workflow file.
RUN_POLICY = {
    'Bootstrap gate': (
        "$ErrorActionPreference = 'Stop'\n"
        "foreach ($guard in @('check_scope.py', 'check_ci.py')) {\n"
        "  if (-not (Test-Path -LiteralPath (Join-Path 'trusted/scripts/project' $guard))) {\n"
        "    throw 'BOOTSTRAP_REVIEW_REQUIRED: the trusted target base needs maintainer review.'\n"
        '  }\n'
        '}'
    ),
    'Trusted guard': (
        "$ErrorActionPreference = 'Stop'\n"
        '$eventData = Get-Content -LiteralPath $env:EVENT_PATH -Raw | ConvertFrom-Json\n'
        "if ($null -eq $eventData.pull_request) { throw 'A pull request event is required.' }\n"
        '& python -B trusted/scripts/project/check_scope.py --repo candidate --event $env:EVENT_PATH\n'
        "if ($LASTEXITCODE -ne 0) { throw 'Declared scope is invalid or needs coordination review.' }\n"
        '& python -B trusted/scripts/project/check_ci.py --repo candidate --secrets --event $env:EVENT_PATH\n'
        "if ($LASTEXITCODE -ne 0) { throw 'Secret guard failed.' }\n"
        '& python -B trusted/scripts/project/check_ci.py --repo candidate --workflow\n'
        "if ($LASTEXITCODE -ne 0) { throw 'Workflow policy failed.' }"
    ),
}


def secret_issues(path, raw):
    scope.safe_path(path)
    name = Path(path).name.lower()
    issues = []
    if (name.startswith('.env') and name != '.env.example') or name.endswith(('.pem', '.key', '.p12', '.pfx')) or \
            path.lower().endswith(('.aws/credentials', 'credentials.json')):
        issues.append({'rule': 'SECRET_FILE', 'path': path})
    for rule, pattern in PATTERNS.items():
        if pattern.search(raw):
            issues.append({'rule': rule, 'path': path})
    return issues


def tree_blobs(repo, revision=None, staged=False):
    if staged:
        records = scope.git(repo, 'ls-files', '--stage', '-z')
    else:
        records = scope.git(repo, 'ls-tree', '-r', '-z', revision)
    for record in records.split(b'\0'):
        if not record:
            continue
        meta, path = record.split(b'\t', 1)
        fields = meta.decode('ascii').split()
        if staged:
            mode, oid, stage = fields
            if stage != '0':
                raise scope.Invalid('UNMERGED_INDEX')
        else:
            mode, kind, oid = fields
            if kind != 'blob':
                raise scope.Invalid('SECRET_SCAN_FILE_MODE')
        path = scope.safe_path(path.decode('utf-8'))
        if mode not in ('100644', '100755'):
            raise scope.Invalid('SECRET_SCAN_FILE_MODE')
        yield path, oid


def scan_secrets(repo, base=None, head=None, staged=False):
    if staged and (base or head):
        raise scope.Invalid('SECRET_INPUT')
    if base or head:
        scope.commit(repo, base)
        scope.commit(repo, head)
        revisions = scope.git(repo, 'rev-list', base + '..' + head).decode().splitlines()
        revisions.append(head)
    else:
        revisions = [scope.git(repo, 'rev-parse', 'HEAD').decode().strip()]
    seen, findings = set(), []
    for revision in revisions if not staged else [None]:
        for path, oid in tree_blobs(repo, revision, staged):
            if (path, oid) in seen:
                continue
            seen.add((path, oid))
            findings.extend(secret_issues(path, scope.git(repo, 'cat-file', 'blob', oid)))
    return {'format': 'notelens-secret-report-v1', 'passed': not findings,
            'provenance': 'git-index' if staged else 'git-history' if base else 'git-head',
            'base': base, 'head': head or revisions[-1], 'blobs_checked': len(seen),
            'blobs_sha256': scope.digest(json.dumps(sorted(seen)).encode()), 'issues': findings}


def workflow_issues(value):
    """Validate the exact guard-only profile in the supported JSON subset of YAML."""
    if not isinstance(value, dict) or set(value) != {'name', 'on', 'permissions', 'concurrency', 'jobs'}:
        return ['WORKFLOW_SHAPE']
    issues = []
    if value['name'] != 'Key-free bootstrap guard (F-011/F-014 pending)':
        issues.append('WORKFLOW_NAME')
    if value['on'] != {'pull_request': {}}:
        issues.append('WORKFLOW_EVENTS')
    if value['permissions'] != {'contents': 'read'}:
        issues.append('TOKEN_PERMISSIONS')
    concurrency = value['concurrency']
    if (not isinstance(concurrency, dict) or set(concurrency) != {'group', 'cancel-in-progress'}
            or concurrency['group'] != 'key-free-${{ github.event.pull_request.number || github.ref }}'
            or concurrency['cancel-in-progress'] is not True):
        issues.append('CONCURRENCY')

    jobs = value['jobs']
    if not isinstance(jobs, dict) or set(jobs) != {'bootstrap-guard'}:
        return issues + ['JOB_COVERAGE']
    job = jobs['bootstrap-guard']
    if not isinstance(job, dict) or set(job) != {'name', 'runs-on', 'timeout-minutes', 'steps'}:
        return issues + ['JOB_SHAPE']
    if job['name'] != 'Trusted scope, secrets and workflow policy':
        issues.append('JOB_NAME')
    if (job['runs-on'] != 'windows-2022' or type(job['timeout-minutes']) is not int
            or job['timeout-minutes'] != 45):
        issues.append('RUNNER_OR_DEADLINE')

    steps = job['steps']
    names = ['Checkout trusted base', 'Checkout candidate', 'Setup Python', 'Bootstrap gate', 'Trusted guard']
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        return issues + ['STEP_SHAPE']
    if [step.get('name') for step in steps] != names:
        return issues + ['STEP_ORDER_OR_COVERAGE']

    for step, path, ref in zip(steps[:2], ('trusted', 'candidate'),
                               ('${{ github.event.pull_request.base.sha }}', '${{ github.event.pull_request.head.sha }}')):
        if set(step) != {'name', 'uses', 'with'}:
            issues.append('STEP_SHAPE')
        if step.get('uses') != 'actions/checkout@' + ACTIONS['actions/checkout']:
            issues.append('ACTION_PIN')
        options = step.get('with')
        if (not isinstance(options, dict)
                or set(options) != {'path', 'ref', 'fetch-depth', 'persist-credentials'}
                or options['path'] != path or options['ref'] != ref):
            issues.append('CHECKOUT_TRUST')
        elif (type(options['fetch-depth']) is not int or options['fetch-depth'] != 0
              or options['persist-credentials'] is not False):
            issues.append('CHECKOUT_CREDENTIALS_OR_HISTORY')

    setup = steps[2]
    if set(setup) != {'name', 'uses', 'with'}:
        issues.append('STEP_SHAPE')
    if setup.get('uses') != 'actions/setup-python@' + ACTIONS['actions/setup-python']:
        issues.append('ACTION_PIN')
    if setup.get('with') != {'python-version': '3.13.7'}:
        issues.append('PYTHON_SETUP')

    for step in steps[3:]:
        fields = {'name', 'shell', 'run'}
        if step['name'] == 'Trusted guard':
            fields.add('env')
            if step.get('env') != {'EVENT_PATH': '${{ github.event_path }}'}:
                issues.append('STEP_ENV')
        if set(step) != fields or step.get('shell') != 'pwsh':
            issues.append('RUN_SHAPE')
        if step.get('run') != RUN_POLICY[step['name']]:
            issues.append('RUN_POLICY')
    return sorted(set(issues))


def pr_workflow_issues(value):
    """Check the current PR workflow's event, token, runner and checkout boundary."""
    try:
        if set(value) != {'name', 'on', 'permissions', 'concurrency', 'jobs'}:
            return ['WORKFLOW_SHAPE']
        if value['on'] != {'pull_request': {'branches': ['main'], 'types': [
                'opened', 'reopened', 'synchronize', 'ready_for_review', 'edited']}}:
            return ['WORKFLOW_EVENTS']
        if value['permissions'] != {'contents': 'read'}:
            return ['TOKEN_PERMISSIONS']
        if set(value['jobs']) != {'key-free'}:
            return ['JOB_COVERAGE']
        job = value['jobs']['key-free']
        if (set(job) != {'name', 'runs-on', 'timeout-minutes', 'steps'}
                or job['runs-on'] != 'windows-2022' or job['timeout-minutes'] != 45
                or job['name'] != 'NoteLens key-free checks'):
            return ['JOB_SHAPE']
        steps = job['steps']
        if [step['name'] for step in steps] != [
                'Checkout trusted base', 'Checkout candidate', 'Setup Python',
                'Check trusted scope and commit history', 'Setup Node', 'Install locked workspaces',
                'Check contracts, dependency advisories and mock flow', PR_SECURITY_STEP]:
            return ['STEP_ORDER_OR_COVERAGE']
        for step, path, side in zip(steps[:2], ('trusted', 'candidate'), ('base', 'head')):
            if (set(step) != {'name', 'uses', 'with'}
                    or step['uses'] != 'actions/checkout@' + ACTIONS['actions/checkout']
                    or step['with'] != {'path': path, 'fetch-depth': 0, 'persist-credentials': False,
                                        'ref': '${{ github.event.pull_request.' + side + '.sha }}'}):
                return ['CHECKOUT_TRUST']
        for index, action, options in (
                (2, 'actions/setup-python', {'python-version': '3.13.7'}),
                (4, 'actions/setup-node', {'node-version': '24', 'package-manager-cache': False})):
            step = steps[index]
            if set(step) != {'name', 'uses', 'with'} or step['uses'] != action + '@' + ACTIONS[action] or step['with'] != options:
                return ['ACTION_PIN']
        for index in (3, 5, 6, 7):
            step = steps[index]
            fields = {'name', 'shell', 'run'} if index == 3 else {'name', 'shell', 'run', 'working-directory', 'env'}
            if (set(step) != fields or step['shell'] != 'pwsh'
                    or (index != 3 and step['working-directory'] != 'candidate')
                    or '${{' in step['run']):
                return ['RUN_SHAPE']
        if steps[-1]['env'] != PR_SECURITY_ENV:
            return ['SECURITY_ENVIRONMENT']
        if steps[-1]['run'] != PR_SECURITY_RUN:
            return ['SECURITY_RUN_POLICY']
        return []
    except (KeyError, TypeError, AttributeError):
        return ['WORKFLOW_SHAPE']


def workflow_report(repo):
    current = repo / PR_WORKFLOW
    current_profile = current.is_file()
    raw = (current if current_profile else repo / WORKFLOW).read_bytes()
    value = scope.loads(raw)
    problems = pr_workflow_issues(value) if current_profile else workflow_issues(value)
    return {'format': 'notelens-workflow-report-v1', 'passed': not problems,
            'workflow_sha256': scope.digest(raw), 'issues': [{'rule': p} for p in problems],
            'hosted_verified': False, 'routing_verified': False, 'f011_pending': not current_profile, 'f014_pending': True}


def clean_environment():
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if upper.startswith(('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'AWS_', 'NOTELENS_', 'PYTEST_', 'NPM_CONFIG_', 'PIP_', 'UV_')) or \
                upper.endswith(('_API_KEY', '_TOKEN')) or upper in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NODE_OPTIONS', 'PYTHONPATH'):
            env.pop(key)
    env.update(PYTHONDONTWRITEBYTECODE='1', PIP_DISABLE_PIP_VERSION_CHECK='1',
               PIP_NO_INPUT='1', NPM_CONFIG_AUDIT_LEVEL='info')
    return env


def normal_name(name):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name):
        raise scope.Invalid('PACKAGE_NAME')
    return re.sub(r'[-_.]+', '-', name).lower()


def python_audit_issues(value, expected, exit_code):
    if not isinstance(value, dict) or not isinstance(value.get('dependencies'), list):
        return ['PYTHON_AUDIT_FORMAT']
    observed, findings = {}, False
    for dep in value['dependencies']:
        if not isinstance(dep, dict) or not isinstance(dep.get('vulns'), list) or 'skip_reason' in dep:
            return ['PYTHON_AUDIT_SKIPPED_OR_INVALID']
        name = normal_name(dep.get('name'))
        if name in observed:
            return ['PYTHON_AUDIT_COVERAGE']
        observed[name] = dep.get('version')
        findings |= bool(dep['vulns'])
    if observed != expected:
        return ['PYTHON_AUDIT_COVERAGE']
    if findings:
        return ['DEPENDENCY_VULNERABILITY']
    return [] if exit_code == 0 else ['ADVISORY_QUERY_FAILED']


def npm_audit_issues(value, exit_code):
    try:
        if value.get('auditReportVersion') != 2 or 'error' in value or not isinstance(value['vulnerabilities'], dict):
            return ['NPM_AUDIT_FORMAT']
        counts = value['metadata']['vulnerabilities']
        numbers = [counts[k] for k in ('info', 'low', 'moderate', 'high', 'critical')]
        if any(type(n) is not int or n < 0 for n in numbers) or type(counts['total']) is not int or sum(numbers) != counts['total']:
            return ['NPM_AUDIT_FORMAT']
        total = value['metadata']['dependencies']['total']
        if type(total) is not int or total <= 0:
            return ['NPM_AUDIT_COVERAGE']
        if counts['total'] or value['vulnerabilities']:
            return ['DEPENDENCY_VULNERABILITY']
        return [] if exit_code == 0 else ['ADVISORY_QUERY_FAILED']
    except (KeyError, TypeError, AttributeError):
        return ['NPM_AUDIT_FORMAT']


def environment_inventory(python, repo):
    code = '''import importlib.metadata as m,json,sys
print(json.dumps({"prefix":sys.prefix,"packages":[[d.metadata["Name"],d.version] for d in m.distributions()]}))'''
    value = scope.loads(subprocess.check_output([str(python), '-B', '-c', code], cwd=repo,
                                               env=clean_environment(), stderr=subprocess.DEVNULL, timeout=30))
    if Path(value['prefix']).resolve() != python.parent.parent.resolve():
        raise scope.Invalid('AUDIT_ENVIRONMENT_ORIGIN')
    packages = {}
    for name, version in value['packages']:
        name = normal_name(name)
        if name in packages or not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9.+!_-]+', version):
            raise scope.Invalid('AUDIT_PACKAGE_METADATA')
        packages[name] = version
    if not packages:
        raise scope.Invalid('AUDIT_EMPTY_ENVIRONMENT')
    return packages


def validate_service_origin(project, prefix, value, expected_version):
    """Only the pinned owner project may be classified as local, never a name prefix."""
    package_name = normal_name(value['name'])
    package_dir = package_name.replace('-', '_')
    expected_source = project / 'src' / package_dir
    if value['version'] != expected_version or Path(value['prefix']).resolve() != prefix.resolve() or \
            not Path(value['metadata']).resolve().is_relative_to(prefix.resolve()) or \
            value['direct']['url'].rstrip('/') != project.resolve().as_uri():
        raise scope.Invalid('LOCAL_SERVICE_ORIGIN')
    origin = Path(value['origin']).resolve().parent
    editable = value['direct'].get('dir_info', {}).get('editable') is True
    if editable:
        if origin != expected_source.resolve():
            raise scope.Invalid('LOCAL_SERVICE_ORIGIN')
    elif not origin.is_relative_to(prefix.resolve()):
        raise scope.Invalid('LOCAL_SERVICE_ORIGIN')
    # Verify every installed source module, including wheel installs, against owner source.
    expected = {p.relative_to(expected_source).as_posix(): scope.digest(p.read_bytes())
                for p in expected_source.rglob('*.py')}
    actual = {p.relative_to(origin).as_posix(): scope.digest(p.read_bytes()) for p in origin.rglob('*.py')}
    if not expected or actual != expected:
        raise scope.Invalid('LOCAL_SERVICE_SOURCE_DRIFT')


def service_local_package(repo, project_name, packages):
    project = repo / project_name
    config = tomllib.loads((project / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    name, version = normal_name(config['name']), config['version']
    if packages.get(name) != version:
        raise scope.Invalid('LOCAL_SERVICE_VERSION')
    python = project / '.venv/Scripts/python.exe'
    code = '''import importlib.metadata as m,importlib.util as u,json,sys
d=m.distribution(sys.argv[1])
print(json.dumps({"name":d.metadata["Name"],"version":d.version,"prefix":sys.prefix,
"metadata":str(d.locate_file("")),"origin":u.find_spec(sys.argv[1].replace("-","_")).origin,
"direct":json.loads(d.read_text("direct_url.json"))}))'''
    value = scope.loads(subprocess.check_output([str(python), '-B', '-c', code, name], cwd=repo,
                                               env=clean_environment(), stderr=subprocess.DEVNULL, timeout=30))
    validate_service_origin(project, project / '.venv', value, version)
    return name, packages.pop(name)


def dependencies(repo, *, pull_request=False):
    from scaffold_state import inventory_issues, source_fingerprint, runtime_facts
    # Ordinary owner PRs change source beyond the checkpoint's pinned inventory.
    # They still require matching installed origins and a stable source fingerprint.
    if not pull_request and inventory_issues(repo):
        raise scope.Invalid('AUDIT_SOURCE_INVENTORY')
    before = source_fingerprint(repo)
    runtime_facts(repo)  # Independently validates the local installed contract source/schema.
    cache = repo / '.cache/review/f010'
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='audit-', dir=cache) as temporary:
        folder = Path(temporary)
        env = clean_environment()
        env.update(TMP=str(folder), TEMP=str(folder), TMPDIR=str(folder), NPM_CONFIG_CACHE=str(repo / '.cache/npm'))
        config = folder / 'empty.npmrc'
        config.write_text('', encoding='utf-8')
        npm_output = folder / 'npm.json'
        with npm_output.open('wb') as output:
            done = run_owned([shutil.which('npm.cmd'), 'audit', '--json', '--audit-level=info', '--loglevel=silent',
                              '--registry=https://registry.npmjs.org', '--userconfig=' + str(config)],
                             cwd=repo, env=env, stdout=output, timeout=240)
        try:
            npm_value = scope.loads(npm_output.read_bytes())
            issues = npm_audit_issues(npm_value, done.returncode)
            vulnerable_names = sorted(normal_name(n) for n in npm_value.get('vulnerabilities', {}))
        except (ValueError, TypeError):
            issues, vulnerable_names = ['NPM_AUDIT_FORMAT'], []
        results.append({'environment': 'npm-workspaces', 'exit_code': done.returncode,
                        'issues': issues, 'vulnerable_packages': vulnerable_names})
        auditor = repo / 'scripts/project/.venv/Scripts/python.exe'
        for label, project in [('tooling', 'scripts/project'), ('rag', 'services/rag'),
                               ('classifier', 'services/classifier'), ('extraction', 'services/extraction')]:
            packages = environment_inventory(repo / project / '.venv/Scripts/python.exe', repo)
            local = {}
            if 'notelens-contracts' in packages:
                if packages['notelens-contracts'] != '1.0.0':
                    raise scope.Invalid('LOCAL_CONTRACT_VERSION')
                local['notelens-contracts'] = packages.pop('notelens-contracts')
            if label != 'tooling' and local != {'notelens-contracts': '1.0.0'}:
                raise scope.Invalid('LOCAL_CONTRACT_MISSING')
            if label != 'tooling':
                name, version = service_local_package(repo, project, packages)
                local[name] = version
            if label == 'tooling' and packages.get('pip-audit') != '2.10.1':
                raise scope.Invalid('AUDITOR_VERSION')
            requirement = folder / (label + '.txt')
            requirement.write_text(''.join(n + '==' + v + '\n' for n, v in sorted(packages.items())), encoding='utf-8')
            target = folder / (label + '.json')
            done = run_owned([str(auditor), '-B', '-m', 'pip_audit', '--no-deps', '--disable-pip',
                              '--progress-spinner', 'off', '--cache-dir', str(repo / '.cache/pip-audit'),
                              '--format', 'json', '-r', str(requirement), '-o', str(target)],
                             cwd=repo, env=env, stdout=subprocess.DEVNULL, timeout=240)
            try:
                value = scope.loads(target.read_bytes())
                issues = python_audit_issues(value, packages, done.returncode)
                vulnerable_names = sorted(normal_name(d['name']) for d in value.get('dependencies', []) if d.get('vulns'))
            except (OSError, ValueError, KeyError, TypeError):
                issues, vulnerable_names = ['PYTHON_AUDIT_FORMAT'], []
            results.append({'environment': label, 'exit_code': done.returncode, 'issues': issues,
                            'external_packages': packages, 'source_checked_local_packages': local,
                            'vulnerable_packages': vulnerable_names})
    issues = []
    if source_fingerprint(repo) != before or (not pull_request and inventory_issues(repo)):
        issues.append({'rule': 'AUDIT_SOURCE_DRIFT'})
    return {'format': 'notelens-dependency-report-v1', 'passed': not issues and all(not r['issues'] for r in results),
            'provenance': 'online-public-advisories', 'queried_at': datetime.now(timezone.utc).isoformat(),
            'profile': 'pull-request' if pull_request else 'checkpoint',
            'source_fingerprint': before, 'environments': results, 'issues': issues,
            'auto_fixes_applied': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for name in ('self-test', 'secrets', 'dependencies', 'pr-dependencies', 'workflow'):
        modes.add_argument('--' + name, action='store_true')
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--base')
    parser.add_argument('--head')
    parser.add_argument('--event', type=Path)
    args = parser.parse_args(argv)
    if args.self_test:
        return scope.self_test('test_ci.py')
    repo = args.repo.resolve()
    label = 'secrets' if args.secrets else 'workflow'
    if args.dependencies:
        label = 'dependencies'
    elif args.pr_dependencies:
        label = 'pr-dependencies'
    nonce = str(uuid4())
    scope.save(repo, label + '.json', {'passed': False, 'run_id': nonce, 'issues': [{'rule': 'IN_PROGRESS'}]})
    try:
        if args.event:
            if args.staged or args.base or args.head:
                parser.error('--event cannot be combined with range/staged inputs')
            _, args.base, args.head = scope.event_declaration(args.event.read_bytes())
        if args.secrets:
            result = scan_secrets(repo, args.base, args.head, args.staged)
        elif args.dependencies:
            result = dependencies(repo)
        elif args.pr_dependencies:
            result = dependencies(repo, pull_request=True)
        else:
            result = workflow_report(repo)
    except scope.Invalid as error:
        result = {'passed': False, 'issues': [{'rule': str(error)}]}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result = {'passed': False, 'issues': [{'rule': 'CI_INPUT_OR_TOOL_FAILURE'}]}
    result['run_id'] = nonce
    scope.save(repo, label + '.json', result)
    print(('PASS' if result['passed'] else 'FAIL') + ': ' + label)
    for issue in result.get('issues', []):
        print(json.dumps(issue, ensure_ascii=True))
    for item in result.get('environments', []):
        print(item['environment'] + ': ' + ','.join(item['issues'] or ['clear']))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
