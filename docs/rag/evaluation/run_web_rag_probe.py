"""Check B's unchanged TypeScript client/router with actual key-free RAG HTTP."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from notelens_rag.contracts import Contracts

from run_local_flow import _http_client
from serve_indexed_demo import _app


ROOT = Path(__file__).resolve().parents[3]
PROTECTED = ('apps/web/src/lib/clients/mock-services.ts', 'apps/web/src/lib/routing/answer.ts',
             'apps/web/src/lib/contracts/consumer.ts', 'contracts/generated/typescript/v1.mjs',
             'contracts/generated/typescript/schema.json', 'contracts/v1/fixtures/documents.json',
             'contracts/v1/fixtures/payloads.json', 'package-lock.json')


def run(web_root=ROOT):
    web_root = Path(web_root).resolve()
    node = shutil.which('node')
    if node is None or not (web_root/'node_modules/@notelens/contracts/package.json').is_file():
        raise ValueError('Node 24 and the locked web workspace dependencies are required.')
    before = {path: hashlib.sha256((web_root/path).read_bytes()).hexdigest() for path in PROTECTED}
    if before != {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in PROTECTED}:
        raise ValueError('The selected web working copy differs from the inspected client/router sources.')
    revision = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
    contracts = Contracts()
    token = uuid4().hex
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(('OPENAI', 'NOTELENS_', 'AZURE', 'ANTHROPIC', 'AWS_', 'GEMINI', 'GOOGLE_API'))
                   and not key.endswith('_API_KEY')
                   and key.upper() not in {'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                                           'NODE_OPTIONS', 'NODE_PATH', 'NODE_USE_ENV_PROXY'}}
    environment['NO_PROXY'] = '127.0.0.1,localhost'
    environment['NOTELENS_WEB_RAG_PROBE_TOKEN'] = token
    results = []

    def forbidden(*args, **kwargs):
        raise AssertionError('The web/RAG probe forbids providers, tokenizer download and external Python connections.')

    def probe(port, phase):
        child = subprocess.run([node, str(Path(__file__).with_name('probe_web_routing.mjs')),
                                str(web_root), str(port), phase], cwd=web_root, env=environment,
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
        if child.returncode:
            raise ValueError(f'The key-free web/RAG {phase} probe failed; no document bodies or credentials are logged.')
        result = json.loads(child.stdout)
        expected = 10 if phase == 'healthy' else 2
        if result['phase'] != phase or len(result['cases']) != expected or result['literature_attempts'] != expected:
            raise ValueError('The web/RAG probe did not complete every required case.')
        return result

    cache = ROOT/'services/rag/.cache'
    cache.mkdir(exist_ok=True)
    connect = socket.create_connection
    with TemporaryDirectory(prefix='web-rag-probe-', dir=cache, ignore_cleanup_errors=True) as temporary:
        with patch('openai.OpenAI', forbidden), patch('notelens_rag.embeddings.local_tokenizer', forbidden), \
             patch('socket.create_connection', forbidden):
            app = _app(Path(temporary), token)
            with _http_client(app, loopback=True, connect=connect, forbidden=forbidden) as client:
                for endpoint, schema, expected in (('live', 'LivenessResult', 'alive'), ('ready', 'HealthResult', 'ok')):
                    response = client.get(f'/health/{endpoint}', headers={'Authorization': f'Bearer {token}'})
                    health = contracts.validate(schema, response.json())
                    if response.status_code != 200 or health['status'] != expected or health['mode'] != 'mock':
                        raise ValueError('The RAG fixture did not start with valid health responses.')
                port = client.base_url.port
                results.append(probe(port, 'healthy'))
            results.append(probe(port, 'stopped'))
    after = {path: hashlib.sha256((web_root/path).read_bytes()).hexdigest() for path in PROTECTED}
    if before != after:
        raise ValueError('Protected web sources or fixtures changed during the probe.')
    return {'format_version': 'rag-web-client-routing-probe-v1', 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
            'mode': 'mock', 'base_reference': revision.stdout.strip() if revision.returncode == 0 else None,
            'probe_source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                    for path in (Path(__file__), Path(__file__).with_name('probe_web_routing.mjs'))},
            'web_source_sha256': before, 'protected_web_sources_unchanged': True,
            'document_backend': 'Frozen synthetic contract fixture; no D HTTP integration is claimed.',
            'RAG_backend': 'Actual local Python HTTP service with a synthetic Chroma index and fixture adapters.',
            'case_count': sum(len(row['cases']) for row in results), 'health_responses': 2,
            'provider_calls': 0, 'final_test_accessed': False, 'phases': results,
            'acceptance_limits': ['Owner-local client/router verification; B application/browser acceptance remains separate.',
                                  'The D-owned shared QA benchmark and final freeze are not completed by this probe.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-root', type=Path, default=ROOT, help='Working copy with the locked Node workspace installed.')
    parser.add_argument('--output', type=Path, help='Write a new metadata-only report; existing reports are preserved.')
    args = parser.parse_args()
    report = json.dumps(run(args.web_root), indent=2, allow_nan=False)+'\n'
    if args.output:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(report)
    else:
        print(report, end='')
