"""Start the built NoteLens web workspace and three locked mocks on loopback."""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from uuid import uuid4

from scaffold_process import owned_process

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'apps/web'
SERVICES = {
    'rag': ('notelens_rag', 'NOTELENS_RAG_SERVICE_TOKEN'),
    'classifier': ('notelens_classifier', 'NOTELENS_CLASSIFIER_SERVICE_TOKEN'),
    'extraction': ('notelens_extraction', 'NOTELENS_SERVICE_TOKEN'),
}
STARTUP_SECONDS = 35


class MockStartupError(RuntimeError):
    pass


@dataclass(frozen=True)
class MockStack:
    web_port: int
    processes: dict[str, subprocess.Popen]
    ports: dict[str, int]

    @property
    def web_origin(self):
        return f'http://localhost:{self.web_port}'

    @property
    def demo_url(self):
        return self.web_origin + '/demo'


def get(port, path, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        connection.request('GET', path, headers=headers or {})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def await_ready(name, port, child, token):
    deadline = time.monotonic() + STARTUP_SECONDS
    while time.monotonic() < deadline and child.poll() is None:
        try:
            if name == 'web':
                status, body = get(port, '/demo/health')
                if status == 200 and json.loads(body) == {'mode': 'mock', 'run': token}:
                    return
            else:
                status, body = get(port, '/health/ready', {'Authorization': f'Bearer {token}'})
                if status == 200:
                    record = json.loads(body)
                    if (record.get('mode'), record.get('service'), record.get('status')) == ('mock', name, 'ok'):
                        return
        except (OSError, ValueError, AttributeError, http.client.HTTPException):
            pass
        time.sleep(0.1)
    raise MockStartupError(f'{name} did not become ready. Check the locked setup and rebuild the web workspace.')


def child_environment():
    blocked = ('NOTELENS_', 'OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'AWS_', 'GEMINI', 'GOOGLE_API')
    env = {name: value for name, value in os.environ.items()
           if not name.upper().startswith(blocked)
           and not name.upper().endswith('_API_KEY')
           and name.upper() not in {'NODE_OPTIONS', 'PYTHONPATH', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY'}}
    env.update(NOTELENS_MODE='mock', NOTELENS_RAG_MODE='mock', NOTELENS_CLASSIFIER_MODE='mock',
               PYTHONDONTWRITEBYTECODE='1', NEXT_TELEMETRY_DISABLED='1', ANONYMIZED_TELEMETRY='False',
               OTEL_SDK_DISABLED='true', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    return env


@contextmanager
def start_stack(*, rag_scenario='sufficient') -> Iterator[MockStack]:
    node = shutil.which('node')
    next_bin = ROOT / 'node_modules/next/dist/bin/next'
    if not node or not next_bin.is_file() or not (WEB / '.next/BUILD_ID').is_file():
        raise MockStartupError('Install the locked web workspace and run npm.cmd run build first.')
    interpreters = {name: ROOT / 'services' / name / '.venv/Scripts/python.exe' for name in SERVICES}
    for name, interpreter in interpreters.items():
        if not interpreter.is_file():
            raise MockStartupError(f'Install the locked {name} environment first.')

    ports = {}
    processes = {}
    with ExitStack() as owned, ExitStack() as port_reservations:
        sockets = {}
        for name in (*SERVICES, 'web'):
            reservation = port_reservations.enter_context(socket.socket())
            reservation.bind(('127.0.0.1', 0))
            ports[name] = reservation.getsockname()[1]
            sockets[name] = reservation
        # Separate service tokens from the public, opaque web readiness marker.
        token = uuid4().hex
        run_marker = uuid4().hex
        env = child_environment()
        service_env = {
            **env, 'NOTELENS_RAG_MOCK_SCENARIO': rag_scenario,
            'PYTHONPATH': str(ROOT / 'scripts/project/scaffold_guard'),
        }
        for name, (module, token_key) in SERVICES.items():
            command = [str(interpreters[name]), '-B', '-m', 'uvicorn', f'{module}.main:app',
                       '--host', '127.0.0.1', '--port', str(ports[name]), '--no-proxy-headers',
                       '--no-access-log', '--log-level', 'error']
            sockets[name].close()
            processes[name] = owned.enter_context(owned_process(
                command, cwd=ROOT, env={**service_env, token_key: token}, stdout=subprocess.DEVNULL))
        for name in SERVICES:
            await_ready(name, ports[name], processes[name], token)
        stack = MockStack(ports['web'], processes, ports)
        web_env = {**env, 'NOTELENS_DEMO_RUN': run_marker, 'NOTELENS_DEMO_TOKEN': token,
                   'NOTELENS_SESSION_ORIGIN': stack.web_origin,
                   **{f'NOTELENS_DEMO_{name.upper()}_PORT': str(ports[name]) for name in SERVICES}}
        command = [node, str(next_bin), 'start', '--hostname', '127.0.0.1', '--port', str(ports['web'])]
        sockets['web'].close()
        processes['web'] = owned.enter_context(owned_process(command, cwd=WEB, env=web_env, stdout=subprocess.DEVNULL))
        await_ready('web', ports['web'], processes['web'], run_marker)
        yield stack


def main():
    try:
        with start_stack() as stack:
            print(f'NoteLens mock demo: {stack.demo_url}\nPress Ctrl+C to stop.', flush=True)
            while all(process.poll() is None for process in stack.processes.values()):
                time.sleep(0.25)
            raise MockStartupError('A mock process exited. The local stack was stopped.')
    except KeyboardInterrupt:
        print('NoteLens mock processes stopped.')
        return 0
    except (MockStartupError, OSError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, MockStartupError) else 'Could not start or stop the local mock stack.',
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
