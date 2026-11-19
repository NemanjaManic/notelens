"""F-012: independent Python/TypeScript fixture checks, with metadata-only local evidence."""

import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unicodedata
from uuid import uuid4

from scaffold_process import run_owned

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / 'contracts/generated/python/src'
SCHEMA_SHA256 = '707e0bb3a44cb4de71384fd4c152aa2c4038c4c0cd4089c2c531fb58103a0f78'
OWNED = ('scripts/project/check_unicode.py', 'apps/web/tests/canonical-text.test.ts',
         'apps/web/tests/helpers/unicode-reference.ts', 'apps/web/tests/fixtures/unicode-vectors.json',
         'apps/web/tests/tsconfig.unicode.json')


class VerificationFailure(RuntimeError):
    """Only a case/stage identifier may be rendered, never the checked values."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def same(actual, expected, identifier):
    if actual != expected:
        raise VerificationFailure(identifier)


def scalar_text(text):
    if any(0xd800 <= ord(c) <= 0xdfff for c in text):
        raise ValueError('Invalid scalar text')
    return text


def prepare_example(text):
    return unicodedata.normalize('NFC', scalar_text(text).replace('\r\n', '\n').replace('\r', '\n'))


def boundary(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('Invalid boundary')


def to_utf16(text, position):
    scalar_text(text)
    boundary(position, len(text))
    return len(text[:position].encode('utf-16-le')) // 2


def to_codepoint(text, position):
    raw = scalar_text(text).encode('utf-16-le')
    boundary(position, len(raw) // 2)
    # Strict decoding rejects a prefix ending in half of a surrogate pair.
    return len(raw[:position * 2].decode('utf-16-le', errors='strict'))


def rejected(function, *arguments):
    try:
        function(*arguments)
    except (ValueError, UnicodeError):
        return
    raise ValueError('Invalid boundary/scalar was accepted')


def reference_results(package):
    vectors = read('apps/web/tests/fixtures/unicode-vectors.json')
    same(vectors['format'], 'notelens-f012-vectors-v1', 'vectors-format')
    documents = read('contracts/v1/fixtures/documents.json')
    payloads = read('contracts/v1/fixtures/payloads.json')
    manifest = read('contracts/v1/fixtures/manifest.json')
    references = read('contracts/v1/fixtures/references.json')
    results = []

    def add(identifier, **data):
        results.append({'id': identifier, 'passed': True, **data})

    def issues(definition, value, **context):
        try:
            package.validate_record(definition, value, **context)
            return []
        except package.ContractValidationError as error:
            return [{'rule': issue.rule, 'path': issue.path} for issue in error.issues]

    for v in vectors['preparation']:
        text = prepare_example(v['raw'])
        same(text, v['canonical'], v['id'])
        same(prepare_example(text), text, v['id'])
        same(sha(text.encode('utf-8')), v['sha256'], v['id'])
        same(len(text), v['code_points'], v['id'])
        same(len(text.encode('utf-16-le')) // 2, v['utf16_units'], v['id'])
        document = {**copy.deepcopy(documents['offset']), 'doc_id': 'unicode-' + v['id'],
                    'text': text, 'text_sha256': v['sha256']}
        same(issues('PreparedDocument', document), [], v['id'])
        add('prepare-' + v['id'], sha256=v['sha256'], code_points=v['code_points'], utf16_units=v['utf16_units'])
    for name in vectors['canonical_documents']:
        document = documents[name]
        original = copy.deepcopy(document)
        same(sha(document['text'].encode('utf-8')), document['text_sha256'], name)
        same(issues('PreparedDocument', document), [], name)
        same(document, original, name)
        add('document-' + name, sha256=document['text_sha256'], code_points=len(document['text']),
            utf16_units=len(document['text'].encode('utf-16-le')) // 2)
    for name in vectors['metadata_payloads']:
        value = payloads[name]
        original = copy.deepcopy(value)
        case = next(c for c in manifest['cases'] if c['id'] == name)
        same(issues(case['definition'], value, document=documents[case['document']],
                    reference=references.get(case.get('reference'))), [], name)
        same(value, original, name)
        add('metadata-' + name, issues=[])
    document = documents['offset']
    text = document['text']
    for v in vectors['spans']:
        start, end = to_utf16(text, v['start']), to_utf16(text, v['end'])
        same([start, end], v['utf16'], v['id'])
        same(text[v['start']:v['end']], v['quote'], v['id'])
        same(text.encode('utf-16-le')[start*2:end*2].decode('utf-16-le'), v['quote'], v['id'])
        same([to_codepoint(text, start), to_codepoint(text, end)], [v['start'], v['end']], v['id'])
        same(issues('EvidenceSpan', {key: v[key] for key in ('start', 'end', 'quote')}, document=document), [], v['id'])
        if v['id'] == 'second-occurrence':
            same(text.find(v['quote']) != v['start'], True, v['id'])
            same(text.encode('utf-16-le')[v['start']*2:v['end']*2].decode('utf-16-le') != v['quote'], True, v['id'])
        add('span-' + v['id'], codepoints=[v['start'], v['end']], utf16=v['utf16'])
    for v in vectors['boundaries']:
        same(to_utf16(text, v['codepoint']), v['utf16'], 'boundary')
        same(to_codepoint(text, v['utf16']), v['codepoint'], 'boundary')
        add('boundary-' + str(v['codepoint']), codepoint=v['codepoint'], utf16=v['utf16'])
    for kind, function in [('codepoint', to_utf16), ('utf16', to_codepoint)]:
        for index, value in enumerate(vectors['invalid_indices'][kind]):
            rejected(function, text, value)
            add(f'invalid-{kind}-{index}', rejected=True)
    for name, surrogate in [('high', '\ud800'), ('low', '\udc00')]:
        rejected(prepare_example, surrogate)
        rejected(to_utf16, surrogate, 0)
        rejected(to_codepoint, surrogate, 0)
        add('helper-surrogate-' + name, rejected=True)
    for v in vectors['negatives']:
        if v['kind'] == 'document':
            definition, base, context = 'PreparedDocument', document, {}
        elif v['kind'] == 'span':
            definition, base, context = 'EvidenceSpan', {'start': 47, 'end': 61, 'quote': 'No chest pain.'}, {'document': document}
        else:
            same(v['kind'], 'identity', 'negative-kind')
            definition, base, context = 'ClassificationResult', payloads['classification-supported'], {'document': document}
        value = {**copy.deepcopy(base), **v['patch']}
        actual = issues(definition, value, **context)
        same(actual, v['expected'], v['id'])
        add('negative-' + v['id'], issues=actual)
    identifiers = [c['id'] for c in results]
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ValueError('Case IDs must be nonempty and unique')
    return results


def main():
    cache = ROOT / '.cache/review/f012-unicode'
    cache.mkdir(parents=True, exist_ok=True)
    (cache / 'latest.json').unlink(missing_ok=True)
    run = Path(tempfile.mkdtemp(prefix='run-', dir=cache))
    nonce = str(uuid4())
    manifest = read('scripts/project/scaffold_inputs.json')
    inputs = sorted(set(OWNED) | set(manifest['frozen_files']))
    before = {name: sha((ROOT / name).read_bytes()) for name in inputs}
    same(sha((ROOT / 'contracts/v1/schema.json').read_bytes()), SCHEMA_SHA256, 'frozen-schema')
    for name, digest in manifest['frozen_files'].items():
        same(before[name], digest, 'frozen-input:' + name)
    sys.path.insert(0, str(GENERATED))
    package = importlib.import_module('notelens_contracts.v1')
    same(Path(package.__file__).resolve(), (GENERATED / 'notelens_contracts/v1.py').resolve(), 'python-package-origin')
    same(sha((GENERATED / 'notelens_contracts/schema.json').read_bytes()), SCHEMA_SHA256, 'generated-schema')
    python_cases = reference_results(package)
    (run / 'python.json').write_text(json.dumps({'passed': True, 'cases': python_cases}, indent=2) + '\n', encoding='utf-8')
    env = os.environ.copy()
    for name in list(env):
        if name.upper().startswith(('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'AWS_', 'NOTELENS_', 'PYTEST_')) or name.upper().endswith('_API_KEY') or name.upper() in ('NODE_OPTIONS', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'):
            env.pop(name)
    temporary = run / 'tmp'
    temporary.mkdir()
    env.update(PYTHONDONTWRITEBYTECODE='1', NEXT_TELEMETRY_DISABLED='1',
               PYTHONPATH=str(ROOT / 'scripts/project/scaffold_guard'),
               NOTELENS_REVIEW_NETWORK_LOG=str(run / 'network-blocks.jsonl'),
               NOTELENS_UNICODE_RUN_ID=nonce, NOTELENS_UNICODE_REPORT=str(run / 'typescript.json'),
               TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary))
    node = shutil.which('node')
    if not node:
        raise ValueError('Installed Node is required')
    commands = [
        ('typecheck', [node, str(ROOT / 'node_modules/typescript/bin/tsc'), '--noEmit', '--project', str(ROOT / 'apps/web/tests/tsconfig.unicode.json')]),
        ('typescript', [node, '--experimental-strip-types', '--test', str(ROOT / 'apps/web/tests/canonical-text.test.ts')]),
    ]
    for label, command in commands:
        with (run / (label + '.log')).open('w', encoding='utf-8') as output:
            result = run_owned(command, cwd=run, env=env, stdout=output, timeout=60)
        if result.returncode:
            raise ValueError('Unicode ' + label + ' failed; inspect the ignored run log')
    typescript = json.loads((run / 'typescript.json').read_text(encoding='utf-8'))
    same(typescript['format'], 'notelens-f012-typescript-v1', 'typescript-format')
    same(typescript['passed'], True, 'typescript-suite')
    same(typescript['run_id'], nonce, 'fresh-run')
    same(typescript['cases'], python_cases, 'cross-runtime-results')
    same({name: sha((ROOT / name).read_bytes()) for name in inputs}, before, 'input-drift')
    if (run / 'network-blocks.jsonl').exists() and (run / 'network-blocks.jsonl').read_text().strip():
        raise ValueError('Unexpected external Python networking')
    report = {'format': 'notelens-f012-run-v1', 'passed': True, 'run_id': nonce,
              'case_count': len(python_cases), 'cases': python_cases,
              'python': sys.version.split()[0], 'node': typescript['node'],
              'python_validation': 'generated-source', 'python_origin': str(package.__file__),
              'source_hashes': before, 'commands': [command for label, command in commands],
              'artifacts': {p.name: sha(p.read_bytes()) for p in run.iterdir() if p.is_file()}}
    path = run / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (cache / 'latest.json').write_text(json.dumps({'report': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes())}, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: F-012 {len(python_cases)}/{len(python_cases)} cases agree across Python/TypeScript; test typecheck passed')
    print('Evidence: ' + str(path.relative_to(ROOT)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        # Diagnostics never print canonical text, request bodies, environment or secrets.
        code = str(error) if isinstance(error, VerificationFailure) else type(error).__name__
        if not re.fullmatch(r'[A-Za-z0-9_:/.-]{1,160}', code):
            code = 'verification'
        print('FAIL: F-012 ' + code + '; inspect metadata-only logs under .cache/review/f012-unicode')
        sys.exit(1)
