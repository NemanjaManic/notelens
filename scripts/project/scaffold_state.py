"""Current-source and installed-runtime evidence for the local F-004 candidate."""

import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
STEPS = ('contracts', 'generation', 'project-tests', 'rag-tests', 'rag-bindings',
         'classifier-tests', 'classifier-bindings', 'extraction-tests', 'extraction-bindings',
         'web-typecheck', 'web-build', 'web-bindings', 'web-config', 'web-render', 'http')
SERVICE_TEST_TOTALS = {'rag': 309, 'classifier': 84, 'extraction': 60}
HTTP_CASES = (
    'rag-retrieve-sufficient', 'rag-answer-sufficient', 'rag-retrieve-insufficient',
    'rag-answer-insufficient', 'rag-clarification',
    *tuple(f'rag-{op}-{failure}' for failure in ('timeout', 'rate_limit', 'provider_unavailable', 'internal_error') for op in ('retrieve', 'answer')),
    *tuple(f'classifier-{scenario}-{document}' for scenario in ('supported', 'uncertain', 'unsupported_skipped', 'unsupported_performed') for document in ('offset', 'history')),
    'extraction-planned', 'extraction-procedure-answer', 'extraction-summary',
    'extraction-partial-answer', 'extraction-no-answer', 'extraction-invalid-digest',
    'rag-invalid-id', 'classifier-invalid-id', 'extraction-invalid-id',
)
HTTP_PROCESSES = (
    *(('rag', scenario) for scenario in ('sufficient', 'insufficient', 'clarification',
                                        'timeout', 'rate_limit', 'provider_unavailable', 'internal_error')),
    *(('classifier', scenario) for scenario in ('supported', 'uncertain', 'unsupported_skipped', 'unsupported_performed')),
    ('extraction', 'default'),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def source_files(root=ROOT):
    manifest = json.loads((root / 'scripts/project/scaffold_inputs.json').read_text())
    required = set(manifest['base_files']) | set(manifest['imports']) | set(manifest['b_input_files']) | set(manifest['b_additions'])
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-c', '-o', '--exclude-standard'], text=True).splitlines()
    # Additional Markdown documentation is outside this package. Pinned documentation,
    # including the runbook and owner test helpers, remains required and fingerprinted.
    names = set(names) | required
    return {name: sha((root / name).read_bytes()) for name in sorted(names)
            if (root / name).is_file() and
            (name in required or not (name.startswith('docs/') and name.endswith('.md')))}


def source_fingerprint(root=ROOT):
    return sha(encoded(source_files(root)))


def inventory_issues(root=ROOT):
    try:
        manifest = json.loads((root / 'scripts/project/scaffold_inputs.json').read_text())
        actual = source_files(root)
        issues = []
        generated = manifest.get('b_generated_outputs', {})
        if set(generated) - {'apps/web/next-env.d.ts'}:
            return ['GENERATED_OUTPUT_SCOPE']
        for name, digest in manifest['base_files'].items():
            if name not in manifest['b_input_files'] and name not in manifest['imports'] and actual.get(name) != digest:
                issues.append('BASE_DRIFT:' + name)
        for name, item in manifest['imports'].items():
            if actual.get(name) != item['sha256']:
                issues.append('OWNER_DRIFT:' + name)
        for name, digest in manifest['b_input_files'].items():
            if name not in actual:
                issues.append('MISSING_B_SOURCE:' + name)
            elif name not in manifest['b_editable'] and actual[name] != generated.get(name, digest):
                issues.append('B_INPUT_DRIFT:' + name)
        allowed = set(manifest['base_files']) | set(manifest['imports']) | set(manifest['b_input_files']) | set(manifest['b_additions'])
        issues += ['UNLISTED_SOURCE:' + name for name in actual.keys() - allowed]
        issues += ['MISSING_B_SOURCE:' + name for name in manifest['b_additions'] if name not in actual]
        return issues
    except (OSError, ValueError, KeyError, TypeError):
        return ['INVENTORY_INVALID']


def runtime_facts(root=ROOT):
    facts = {}
    probe = '''import hashlib,importlib.util,importlib.metadata,json,sys
from pathlib import Path
package=Path(importlib.util.find_spec("notelens_contracts").origin).parent
print(json.dumps({"prefix":sys.prefix,"python":sys.version.split()[0],"contract_path":str(package),"schema_sha256":hashlib.sha256((package/"schema.json").read_bytes()).hexdigest(),"contract_source":json.loads(importlib.metadata.distribution("notelens-contracts").read_text("direct_url.json"))["url"],"versions":{d.metadata["Name"].lower():d.version for d in importlib.metadata.distributions()}}))'''
    expected_schema = sha((root / 'contracts/v1/schema.json').read_bytes())
    for service in ('rag', 'classifier', 'extraction'):
        environment = root / 'services' / service / '.venv'
        python = environment / 'Scripts/python.exe'
        data = json.loads(subprocess.check_output([str(python), '-B', '-c', probe], cwd=root, text=True, timeout=30))
        if Path(data['prefix']).resolve() != environment.resolve() or not Path(data['contract_path']).resolve().is_relative_to(root.resolve()):
            raise ValueError('Installed interpreter/package is outside this candidate')
        if data['schema_sha256'] != expected_schema or data['contract_source'].rstrip('/') != (root / 'contracts/generated/python').resolve().as_uri():
            raise ValueError('Installed contract source/schema mismatch')
        if service == 'rag' and 'chromadb' in data['versions']:
            raise ValueError('Installed RAG dependencies must match the default mock profile')
        facts[service] = data
    node = shutil.which('node')
    script = '''import fs from 'node:fs';import{fileURLToPath}from'node:url';
console.log(JSON.stringify({node:process.version,contract:fs.realpathSync(fileURLToPath(import.meta.resolve('@notelens/contracts/v1'))),versions:Object.fromEntries(['next','react','react-dom','typescript'].map(p=>[p,JSON.parse(fs.readFileSync('node_modules/'+p+'/package.json')).version]))}));'''
    facts['web'] = json.loads(subprocess.check_output([node, '--input-type=module', '-e', script], cwd=root, text=True, timeout=30))
    if Path(facts['web']['contract']).resolve() != (root / 'contracts/generated/typescript/v1.mjs').resolve():
        raise ValueError('TypeScript package is outside this candidate')
    return facts


def service_test_counts(path, service):
    """Validate the pinned default-profile coverage from an owner JUnit report."""
    suite = ET.parse(path).getroot().find('testsuite')
    if suite is None:
        raise ValueError('Missing service test suite: ' + service)
    counts = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
    skips = [(case, skipped) for case in suite.findall('testcase') for skipped in case.findall('skipped')]
    expected_skips = int(service == 'rag')
    if (counts != {'tests': SERVICE_TEST_TOTALS[service], 'failures': 0, 'errors': 0, 'skipped': expected_skips}
            or len(skips) != expected_skips):
        raise ValueError('Unexpected service test coverage: ' + service)
    if skips:
        case, skipped = skips[0]
        if (case.get('name') != 'tests.test_index_version' or skipped.get('message') != 'collection skipped'
                or 'Index tests require the optional indexing extra.' not in (skipped.text or '')):
            raise ValueError('Unexpected skipped service test: ' + service)
    return counts


def receipt_issues(root, receipt, sources, runtimes):
    """Check full current-run evidence, including logs and precise required case coverage."""
    try:
        issues = []
        if receipt['format'] != 'notelens-f004-run-v1' or receipt['candidate'] != str(root.resolve()):
            issues.append('RECEIPT_CONTEXT')
        if receipt['source_fingerprint'] != sources:
            issues.append('RECEIPT_SOURCE_STALE')
        if receipt['runtime_fingerprint'] != sha(encoded(runtimes)):
            issues.append('RECEIPT_RUNTIME_STALE')
        steps = receipt['steps']
        if [step['id'] for step in steps] != list(STEPS) or any(step['exit_code'] != 0 for step in steps):
            issues.append('RECEIPT_STEPS')
        cache = (root / '.cache/scaffold').resolve()
        for item in receipt['artifacts']:
            target = (root / item['path']).resolve()
            if not target.is_relative_to(cache) or sha(target.read_bytes()) != item['sha256']:
                issues.append('RECEIPT_ARTIFACT')
        expected_logs = {f'.cache/scaffold/{step}.log' for step in STEPS}
        if not expected_logs.issubset({item['path'] for item in receipt['artifacts']}):
            issues.append('RECEIPT_LOGS')
        report_path = root / '.cache/scaffold/http.json'
        if '.cache/scaffold/http.json' not in {item['path'] for item in receipt['artifacts']}:
            issues.append('RECEIPT_HTTP_ARTIFACT')
        http = json.loads(report_path.read_text())
        if not http['passed'] or [case['id'] for case in http['cases']] != list(HTTP_CASES) or not all(case['passed'] for case in http['cases']):
            issues.append('RECEIPT_HTTP_CASES')
        processes = http['processes']
        if Counter((p['service'], p['scenario']) for p in processes) != Counter(HTTP_PROCESSES):
            issues.append('RECEIPT_PROCESS_COVERAGE')
        if not processes or not all(p['stopped'] is True and p['port_closed'] is True and
                                    type(p['pid']) is int and p['pid'] > 0 for p in processes):
            issues.append('RECEIPT_PROCESS_CLEANUP')
        for service in SERVICE_TEST_TOTALS:
            relative = f'.cache/scaffold/{service}.xml'
            if relative not in {item['path'] for item in receipt['artifacts']}:
                issues.append('RECEIPT_TEST_ARTIFACT')
            try:
                service_test_counts(root / relative, service)
            except ValueError:
                issues.append('RECEIPT_TEST_COVERAGE')
        return issues
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError):
        return ['RECEIPT_INVALID']
