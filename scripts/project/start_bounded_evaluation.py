"""Start the bounded web profile against explicitly selected loopback services."""

import argparse
from contextlib import contextmanager, closing, nullcontext
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from uuid import uuid4

from scaffold_process import owned_process
from smoke_mock import verify_shutdown
from start_mock import MockStack, MockStartupError, ROOT, WEB, child_environment, get


OPERATIONS = {'extract', 'document-answer', 'literature-answer'}
TOKEN_ENV = {'rag': 'NOTELENS_RAG_SERVICE_TOKEN', 'extraction': 'NOTELENS_SERVICE_TOKEN',
             'classifier': 'NOTELENS_CLASSIFIER_SERVICE_TOKEN'}


@dataclass(frozen=True)
class Endpoint:
    port: int
    model_version: str
    token: str = field(repr=False)

    def __post_init__(self):
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError('A valid loopback service port is required.')
        if not self.model_version.strip() or not self.token or not self.token.isascii() or any(c.isspace() for c in self.token):
            raise ValueError('The expected service model and token are required.')


def claim_approved_run(config_path, run_id, config_bytes):
    """Keep a source-free, single-use startup receipt alongside the approval."""
    if not isinstance(run_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', run_id):
        raise ValueError('The approved run requires a stable identifier.')
    receipt = config_path.resolve().parent / f'{run_id}.start-receipt.json'
    with receipt.open('x', encoding='utf-8') as output:
        json.dump({'run_id': run_id, 'approved_config_sha256': sha256(config_bytes).hexdigest(),
                   'started_utc': datetime.now(timezone.utc).isoformat()}, output, indent=2)
        output.write('\n')
    return receipt


@contextmanager
def start_bounded_web(endpoints, limits, *, profile, http_timeout_ms, deadline_unix_ms=None, owner=None,
                      reviewed_literature_hashes=None):
    if profile not in {'provider-backed', 'offline'}:
        raise ValueError('Select an explicit bounded evaluation profile.')
    if (set(limits) != OPERATIONS or any(type(limit) is not int or not 0 <= limit < 2**53
                                         for limit in limits.values())):
        raise ValueError('Set an explicit nonnegative HTTP ceiling for each operation.')
    if type(http_timeout_ms) is not int or not 1 <= http_timeout_ms <= 60 * 60 * 1000:
        raise ValueError('Set a bounded HTTP timeout in milliseconds.')
    if set(endpoints) != set(TOKEN_ENV) or len({ep.port for ep in endpoints.values()}) != len(TOKEN_ENV):
        raise ValueError('Use separate loopback listeners for the three services.')

    def check_deadline():
        if deadline_unix_ms is not None and time.time_ns() // 1_000_000 >= deadline_unix_ms:
            raise TimeoutError('The bounded run deadline expired during startup.')

    for name, endpoint in endpoints.items():
        startup_deadline = time.monotonic() + 35
        while True:
            check_deadline()
            try:
                status, body = get(endpoint.port, '/health/ready', {'Authorization': f'Bearer {endpoint.token}'})
                record = json.loads(body)
                if status == 200 and isinstance(record, dict) and (record.get('service'), record.get('mode'),
                        record.get('status'), record.get('model_version')) == (name, 'live', 'ok', endpoint.model_version):
                    break
                if status in (200, 401, 403):
                    raise MockStartupError(f'{name} did not match the bounded profile readiness pin.')
            except (OSError, ValueError, HTTPException):
                pass
            if owner is None or time.monotonic() >= startup_deadline:
                raise MockStartupError(f'{name} did not match the bounded profile readiness pin.')
            time.sleep(0.1)

    node = shutil.which('node')
    next_bin = ROOT / 'node_modules/next/dist/bin/next'
    if not node or not next_bin.is_file() or not (WEB / '.next/BUILD_ID').is_file():
        raise MockStartupError('Install the locked web workspace and run npm.cmd run build first.')
    with closing(socket.socket()) as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    env = child_environment()
    run = uuid4().hex
    classifier = endpoints['classifier']
    env.update(
        NOTELENS_BOUNDED_EVALUATION=profile, NOTELENS_BOUNDED_LIMITS=json.dumps(limits),
        NOTELENS_BOUNDED_HTTP_TIMEOUT_MS=str(http_timeout_ms),
        NOTELENS_BOUNDED_RAG_TOKEN=endpoints['rag'].token, NOTELENS_BOUNDED_EXTRACTION_TOKEN=endpoints['extraction'].token,
        NOTELENS_DEMO_RUN=run, NOTELENS_DEMO_TOKEN=uuid4().hex, NOTELENS_SESSION_ORIGIN=f'http://localhost:{port}',
        NOTELENS_LOCAL_CLASSIFIER_PROFILE='fitted', NOTELENS_LOCAL_CLASSIFIER_PORT=str(classifier.port),
        NOTELENS_LOCAL_CLASSIFIER_MODEL_VERSION=classifier.model_version, NOTELENS_CLASSIFIER_SERVICE_TOKEN=classifier.token,
    )
    env.update({f'NOTELENS_DEMO_{name.upper()}_PORT': str(endpoint.port) for name, endpoint in endpoints.items()})
    if deadline_unix_ms is not None:
        env['NOTELENS_BOUNDED_DEADLINE_UNIX_MS'] = str(deadline_unix_ms)
    if reviewed_literature_hashes is not None:
        env['NOTELENS_BOUNDED_REVIEWED_LITERATURE_HASHES'] = json.dumps(reviewed_literature_hashes)
    stack = None
    try:
        check_deadline()
        command = [node, str(next_bin), 'start', '--hostname', '127.0.0.1', '--port', str(port)]
        options = {'cwd': WEB, 'env': env, 'stdout': subprocess.DEVNULL}
        context = owned_process(command, **options) if owner is None else nullcontext(owner.start(command, **options))
        with context as web:
            stack = MockStack(port, {'web': web}, {'web': port})
            deadline = time.monotonic() + 35
            while time.monotonic() < deadline and web.poll() is None:
                check_deadline()
                try:
                    status, body = get(port, '/demo/health')
                    if status == 200 and json.loads(body) == {'mode': profile, 'run': run}:
                        break
                except (OSError, ValueError, HTTPException):
                    pass
                time.sleep(0.1)
            else:
                raise MockStartupError('The bounded web listener did not become ready.')
            yield stack
    finally:
        if stack and owner is None:
            verify_shutdown(stack)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('approved_config', type=Path, help='Approved local JSON configuration without credentials.')
    args = parser.parse_args()
    try:
        config_bytes = args.approved_config.read_bytes()
        config = json.loads(config_bytes)
        if config.get('approved') is not True:
            raise ValueError('The bounded provider profile requires an approved configuration.')
        endpoints = {name: Endpoint(**config['services'][name], token=os.environ[key]) for name, key in TOKEN_ENV.items()}
        receipt = claim_approved_run(args.approved_config, config['run_id'], config_bytes)
        print(f'Bounded startup receipt: {receipt}', flush=True)
        with start_bounded_web(endpoints, config['http_limits'], profile='provider-backed',
                               http_timeout_ms=config['http_timeout_ms']) as stack:
            print(f'NoteLens bounded provider evaluation: {stack.demo_url}', flush=True)
            while stack.processes['web'].poll() is None:
                time.sleep(0.25)
            raise MockStartupError('The bounded web process exited.')
    except KeyboardInterrupt:
        return 0
    except FileExistsError:
        print('This run already has a startup receipt. Keep the existing receipt and reconcile the attempt.', file=sys.stderr)
        return 1
    except (ValueError, TypeError, AttributeError, KeyError, OSError, HTTPException, MockStartupError):
        print('Could not start the bounded profile. Verify the approved configuration and readiness pins.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
