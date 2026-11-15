"""Run key-free F-004 checks in this candidate; never install or start a shared stack."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from scaffold_state import ROOT, STEPS, encoded, inventory_issues, runtime_facts, sha, source_fingerprint
from scaffold_process import run_owned


def main():
    issues = inventory_issues()
    if issues:
        raise RuntimeError('Candidate inventory failed: ' + ', '.join(issues))
    cache = ROOT / '.cache/scaffold'
    cache.mkdir(parents=True, exist_ok=True)
    (cache / 'tmp').mkdir(exist_ok=True)
    # An interrupted/new run must never leave an older successful receipt usable.
    (cache / 'receipt.json').unlink(missing_ok=True)
    source_before = source_fingerprint()
    facts = runtime_facts()
    env = os.environ.copy()
    for name in list(env):
        if name.upper().startswith(('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'AWS_', 'NOTELENS_', 'PYTEST_')) or name.upper().endswith('_API_KEY') or name.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NODE_OPTIONS'):
            env.pop(name)
    env.update(PYTHONPATH=os.pathsep.join([str(ROOT / 'scripts/project/scaffold_guard'), str(ROOT / 'scripts/project')]), PYTHONDONTWRITEBYTECODE='1',
               NOTELENS_MODE='mock', NOTELENS_RAG_MODE='mock', NOTELENS_CLASSIFIER_MODE='mock',
               NOTELENS_CLASSIFIER_MOCK_SCENARIO='supported', NOTELENS_RAG_MOCK_SCENARIO='sufficient',
               NEXT_TELEMETRY_DISABLED='1', ANONYMIZED_TELEMETRY='False', OTEL_SDK_DISABLED='true',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               NOTELENS_REVIEW_NETWORK_LOG=str(cache / 'network-blocks.jsonl'),
               TMP=str(cache / 'tmp'), TEMP=str(cache / 'tmp'), TMPDIR=str(cache / 'tmp'))
    (cache / 'network-blocks.jsonl').unlink(missing_ok=True)
    npm = shutil.which('npm.cmd')
    node = shutil.which('node')
    tooling = ROOT / 'scripts/project/.venv/Scripts/python.exe'
    commands = {
        'contracts': [str(tooling), '-B', 'scripts/project/check_contracts.py', '--require-freeze'],
        'generation': [str(tooling), '-B', 'scripts/project/generate_contracts.py', '--check'],
        'project-tests': [str(tooling), '-B', '-m', 'unittest', 'discover', '-s', 'scripts/project/tests'],
        'web-typecheck': [npm, 'run', 'typecheck', '--workspace', 'apps/web'],
        'web-build': [npm, 'run', 'build', '--workspace', 'apps/web'],
        'web-bindings': [node, 'apps/web/scripts/check-bindings.mjs'],
        'web-config': [node, 'apps/web/scripts/check-config.mjs'],
        'web-render': [str(tooling), '-B', 'apps/web/scripts/check-render.py'],
        'http': [node, 'scripts/project/scaffold_http.mjs'],
    }
    for service in ('rag', 'classifier', 'extraction'):
        python = str(ROOT / 'services' / service / '.venv/Scripts/python.exe')
        commands[service + '-tests'] = [python, '-B', '-m', 'pytest', f'services/{service}/tests', '-q', '--tb=short', f'--junitxml={cache / (service + ".xml")}']
        commands[service + '-bindings'] = [python, '-B', 'scripts/project/check_bindings.py']
    receipt = {'format': 'notelens-f004-run-v1', 'candidate': str(ROOT.resolve()),
               'started_at': datetime.now(timezone.utc).isoformat(), 'steps': [],
               'runtime_fingerprint': sha(encoded(facts)), 'runtimes': facts}
    for step in STEPS:
        with (cache / (step + '.log')).open('w', encoding='utf-8') as output:
            result = run_owned(commands[step], cwd=ROOT, env=env, stdout=output, timeout=240)
        receipt['steps'].append({'id': step, 'command': commands[step], 'exit_code': result.returncode})
        print(f'{step}: exit {result.returncode}', flush=True)
        if result.returncode:
            (cache / 'failed-run.json').write_text(json.dumps(receipt, indent=2) + '\n')
            return 1
    counts = {}
    for service, expected in [('rag', 319), ('classifier', 51), ('extraction', 59)]:
        suite = ET.parse(cache / (service + '.xml')).getroot().find('testsuite')
        counts[service] = {key: int(suite.attrib[key]) for key in ('tests', 'failures', 'errors', 'skipped')}
        if counts[service] != {'tests': expected, 'failures': 0, 'errors': 0, 'skipped': 0}:
            raise RuntimeError('Unexpected service test coverage: ' + service)
    if inventory_issues() or source_fingerprint() != source_before or runtime_facts() != facts:
        raise RuntimeError('Candidate source/runtime changed during verification')
    if (cache / 'network-blocks.jsonl').exists() and (cache / 'network-blocks.jsonl').read_text().strip():
        raise RuntimeError('Runtime attempted external Python networking')
    receipt.update(source_fingerprint=source_before, service_counts=counts,
                   finished_at=datetime.now(timezone.utc).isoformat())
    artifacts = [cache / (step + '.log') for step in STEPS] + [cache / 'http.json'] + [cache / (s + '.xml') for s in counts]
    receipt['artifacts'] = [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())} for p in artifacts]
    (cache / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS: current-source F-004 candidate receipt recorded; no published foundation claim')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('FAIL: ' + str(error))
        sys.exit(1)
