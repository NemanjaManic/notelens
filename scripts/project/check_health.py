"""B-owned F-011 HTTP checker. Missing owner capabilities keep the shared gate incomplete."""

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import http.client
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from uuid import uuid4

from scaffold_process import run_owned
from scaffold_state import inventory_issues, source_fingerprint

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.cache/review/f011-health'
SERVICES = ('rag', 'classifier', 'extraction')
FAILURES = {'timeout': 504, 'rate_limit': 429, 'provider_unavailable': 503, 'internal_error': 500}
PROFILES = tuple((service, profile) for service in SERVICES for profile in ('open', 'token')) + tuple(
    ('rag', 'failure-' + failure) for failure in FAILURES)
IDS = {'absent': [], 'canonical': [('X-Request-ID', '11111111-1111-4111-8111-111111111111')],
       'malformed': [('X-Request-ID', 'invalid-probe-id')],
       'duplicate': [('X-Request-ID', '11111111-1111-4111-8111-111111111111'),
                     ('X-Request-ID', '22222222-2222-4222-8222-222222222222')]}
ROUTES = {'rag': (('/v1/retrieve', 'RetrievalResult'), ('/v1/literature-answer', 'AnswerResult')),
          'classifier': (('/v1/classify', 'ClassificationResult'),),
          'extraction': (('/v1/extract', 'ExtractionResult'), ('/v1/document-answer', 'AnswerResult'))}


@dataclass(frozen=True)
class Case:
    id: str
    service: str
    profile: str | None
    path: str
    status: int
    definition: str
    method: str = 'GET'
    request_id: str = 'canonical'
    auth: str = 'valid'
    body: str = 'valid'
    code: str | None = None
    retryable: bool | None = None
    blocked: str | None = None


def registry():
    cases = []
    for service in SERVICES:
        for profile in ('open', 'token'):
            for path in ('/health/live', '/health/ready'):
                route = path.rsplit('/', 1)[1]
                definition = 'LivenessResult' if route == 'live' else 'HealthResult'
                for identity in IDS:
                    cases.append(Case(f'{service}-{profile}-{route}-{identity}', service, profile,
                                      path, 200, definition, request_id=identity))
                if profile == 'token':
                    for auth in ('missing', 'wrong', 'valid-first', 'invalid-first'):
                        for identity in IDS:
                            cases.append(Case(f'{service}-deny-{route}-{auth}-{identity}', service, profile,
                                              path, 401, 'ErrorEnvelope', request_id=identity, auth=auth,
                                              code='unauthorized', retryable=False))
                    cases.append(Case(f'{service}-deny-{route}-repeat', service, profile, path, 401,
                                      'ErrorEnvelope', auth='missing', code='unauthorized', retryable=False))
            for path, definition in ROUTES[service]:
                route = path.rsplit('/', 1)[1]
                cases.append(Case(f'{service}-{profile}-{route}-success', service, profile,
                                  path, 200, definition, method='POST'))
                if profile == 'token':
                    for identity in ('absent', 'malformed', 'duplicate'):
                        cases.append(Case(f'{service}-{route}-admission-{identity}', service, profile,
                                          path, 400, 'ErrorEnvelope', method='POST', request_id=identity,
                                          auth='wrong', code='validation_failure'))
                    cases.append(Case(f'{service}-{route}-auth', service, profile, path, 401,
                                      'ErrorEnvelope', method='POST', auth='wrong', code='unauthorized'))
                    for body, status in [('malformed', 400), ('invalid', 422)]:
                        cases.append(Case(f'{service}-{route}-{body}', service, profile, path, status,
                                          'ErrorEnvelope', method='POST', body=body, code='validation_failure'))
        cases.append(Case(f'{service}-not-ready', service, None, '/health/ready', 503, 'HealthResult',
                          blocked='NOT_READY_TRIGGER_PENDING_OWNER'))
        for failure, status in FAILURES.items():
            if failure == 'internal_error' and service != 'rag':
                continue
            for path, definition in ROUTES[service]:
                route = path.rsplit('/', 1)[1]
                cases.append(Case(f'{service}-{route}-{failure}', service,
                                  'failure-' + failure if service == 'rag' else None,
                                  path, status, 'ErrorEnvelope', method='POST', code=failure,
                                  retryable=False if service == 'rag' else None,
                                  blocked=None if service == 'rag' else 'FAILURE_TRIGGER_PENDING_OWNER'))
    if len({c.id for c in cases}) != len(cases):
        raise ValueError('Duplicate case identifiers')
    return cases


def sha(data):
    return hashlib.sha256(data).hexdigest()


def contracts():
    generated = ROOT / 'contracts/generated/python/src'
    sys.path.insert(0, str(generated))
    package = importlib.import_module('notelens_contracts.v1')
    if Path(package.__file__).resolve() != (generated / 'notelens_contracts/v1.py').resolve():
        raise ValueError('Contract package origin')
    if (generated / 'notelens_contracts/schema.json').read_bytes() != (ROOT / 'contracts/v1/schema.json').read_bytes():
        raise ValueError('Contract schema mismatch')
    return package


def headers_named(headers, name):
    return [value for key, value in headers if key.lower() == name.lower()]


def response_issues(case, status, headers, raw, request_headers, package, secrets=(), document=None):
    """Validate a real or explicitly labeled fixture response; never return its contents."""
    if any(value and (value.encode() in raw or any(value in v for k, v in headers)) for value in secrets):
        return ['UNSAFE_ECHO']
    if status == 404:
        return ['MISSING_ENDPOINT']
    if status != case.status:
        return ['HTTP_STATUS']
    types = headers_named(headers, 'Content-Type')
    if len(types) != 1 or types[0].split(';')[0].strip().lower() != 'application/json':
        return ['CONTENT_TYPE']
    try:
        context = {'document': document} if document and status == 200 and case.method == 'POST' else {}
        body = package.validate_json(case.definition, raw.decode('utf-8'), **context)
        if case.method == 'GET' and status in (200, 503):
            if body['service'] != case.service:
                return ['SERVICE_IDENTITY']
            if body['mode'] != 'mock':
                return ['MOCK_MODE']
            expected = 'alive' if case.path == '/health/live' else 'ok' if status == 200 else 'not_ready'
            if body['status'] != expected:
                return ['HEALTH_STATUS']
            outgoing = headers_named(headers, 'X-Request-ID')
            if outgoing:
                if len(outgoing) != 1:
                    return ['RESPONSE_ID']
                package.validate_record('RequestId', outgoing[0])
                if outgoing[0] in headers_named(request_headers, 'X-Request-ID'):
                    return ['HEALTH_ID_REUSED']
            return []
        # The frozen exchange validator accepts health 401 only, not health 200/503.
        issues = package.validate_exchange({'path': case.path, 'request_headers': request_headers,
                    'response_headers': headers, 'status': status, 'body': body,
                    'disposition': 'accepted_result' if status == 200 else 'failed_call'})
        if issues:
            return issues
        if status != 200:
            if body['error']['code'] != case.code:
                return ['ERROR_CODE']
            if case.retryable is not None and body['error']['retryable'] is not case.retryable:
                return ['RETRYABLE']
        elif body.get('mode') != 'mock':
            return ['MOCK_MODE']
        return []
    except package.ContractValidationError as error:
        return sorted({issue.rule for issue in error.issues})
    except (ValueError, TypeError, KeyError, UnicodeError):
        return ['INVALID_BODY']


def completion_issues(cases, processes):
    expected = registry()
    issues = []
    if [c.get('id') for c in cases] != [c.id for c in expected]:
        issues.append('CASE_COVERAGE')
    if len(cases) == len(expected) and any((row.get('service'), row.get('profile')) != (spec.service, spec.profile)
                                          for row, spec in zip(cases, expected)):
        issues.append('CASE_IDENTITY')
    if any(c.blocked for c in expected):
        issues.append('PENDING_OWNER_CAPABILITIES')
    if any(c.get('outcome') != 'passed' or c.get('provenance') != 'service-http' for c in cases):
        issues.append('INCOMPLETE_CASES')
    if Counter((p.get('service'), p.get('profile')) for p in processes) != Counter(PROFILES):
        issues.append('PROCESS_COVERAGE')
    if any(type(p.get('pid')) is not int or p['pid'] <= 0 or type(p.get('port')) is not int or not 0 < p['port'] < 65536 or
           any(p.get(key) is not True for key in ('exited', 'port_closed', 'contained')) for p in processes):
        issues.append('PROCESS_CLEANUP')
    return issues


def environment(run, service, profile, token=None):
    env = os.environ.copy()
    for name in list(env):
        if name.upper().startswith(('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC', 'AWS_', 'NOTELENS_', 'PYTEST_')) or name.upper().endswith('_API_KEY') or name.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NODE_OPTIONS'):
            env.pop(name)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'scripts/project/scaffold_guard'),
               NOTELENS_MODE='mock', NOTELENS_RAG_MODE='mock', NOTELENS_CLASSIFIER_MODE='mock',
               NOTELENS_CLASSIFIER_MOCK_SCENARIO='supported',
               NOTELENS_RAG_MOCK_SCENARIO=profile.removeprefix('failure-') if profile.startswith('failure-') else 'sufficient',
               NOTELENS_REVIEW_NETWORK_LOG=str(run / 'network-blocks.jsonl'),
               NEXT_TELEMETRY_DISABLED='1', ANONYMIZED_TELEMETRY='False', OTEL_SDK_DISABLED='true',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               TMP=str(run / 'tmp'), TEMP=str(run / 'tmp'), TMPDIR=str(run / 'tmp'))
    if token:
        env[{'rag': 'NOTELENS_RAG_SERVICE_TOKEN', 'classifier': 'NOTELENS_CLASSIFIER_SERVICE_TOKEN',
             'extraction': 'NOTELENS_SERVICE_TOKEN'}[service]] = token
    return env


class Capture:
    """Drain unsafe service output in memory; retain flags, never persist its contents."""
    def __init__(self, stream, markers):
        self.traceback = self.leak = False
        def drain():
            tail = b''
            while chunk := stream.read(4096):
                tail = (tail + chunk)[-65536:]
                self.traceback |= b'Traceback' in tail
                self.leak |= any(marker and marker.encode() in tail for marker in markers)
        self.thread = threading.Thread(target=drain, daemon=True)
        self.thread.start()


@contextmanager
def owned_server(command, cwd, env, markers=()):
    process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    capture = Capture(process.stdout, markers)
    try:
        yield process, capture
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        capture.thread.join(timeout=2)
        if not capture.thread.is_alive():
            process.stdout.close()


def reachable(port):
    with socket.socket() as client:
        client.settimeout(.2)
        return client.connect_ex(('127.0.0.1', port)) == 0


def closed_port(port):
    deadline = time.monotonic() + 3
    while reachable(port):
        if time.monotonic() >= deadline:
            return False
        time.sleep(.02)
    return True


def request_data(case, token, marker):
    headers = list(IDS[case.request_id]) + [('X-NoteLens-Probe', marker)]
    valid = [('Authorization', 'Bearer ' + token)] if token else []
    wrong = [('Authorization', 'Bearer wrong-probe-token')]
    headers += {'valid': valid, 'missing': [], 'wrong': wrong,
                'valid-first': valid + wrong, 'invalid-first': wrong + valid}[case.auth]
    if case.method == 'GET':
        return headers, None, None
    document = json.loads((ROOT / 'contracts/v1/fixtures/documents.json').read_text())[
        'procedure' if case.service == 'extraction' else 'offset']
    if case.service == 'rag':
        value = {'schema_version': '1.0.0', 'question': 'What is the synthetic demo topic?'}
    else:
        value = {'schema_version': '1.0.0', 'document': document}
        if case.path == '/v1/document-answer':
            value['question'] = 'Which procedure is mentioned?'
    if case.body == 'invalid':
        if case.service == 'rag':
            value.pop('question')
        else:
            value['document']['text_sha256'] = '0' * 64
    body = b'{' if case.body == 'malformed' else json.dumps(value).encode('utf-8')
    return headers, body, document if case.service != 'rag' else None


def wire(port, case, headers, body):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        connection.putrequest(case.method, case.path, skip_accept_encoding=True)
        for key, value in headers:
            connection.putheader(key, value)
        if body is not None:
            connection.putheader('Content-Type', 'application/json')
            connection.putheader('Content-Length', str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        return response.status, response.getheaders(), response.read()
    finally:
        connection.close()


def check_runtime_origin(service, prefix, origin, metadata_directory, source, editable):
    expected = ROOT / 'services' / service / '.venv'
    generated = ROOT / 'contracts/generated/python'
    if Path(prefix).resolve() != expected.resolve() or not Path(metadata_directory).resolve().is_relative_to(expected.resolve()):
        raise ValueError('Installed environment origin')
    if source.rstrip('/') != generated.resolve().as_uri():
        raise ValueError('Installed contract source')
    if editable:
        if Path(origin).resolve() != (generated / 'src/notelens_contracts').resolve():
            raise ValueError('Editable contract origin')
    elif not Path(origin).resolve().is_relative_to(expected.resolve()):
        raise ValueError('Wheel contract origin')


def installed_runtime(service):
    origin = Path(importlib.util.find_spec('notelens_contracts').origin).parent
    distribution = importlib.metadata.distribution('notelens-contracts')
    direct = json.loads(distribution.read_text('direct_url.json'))
    source, editable = direct['url'], direct.get('dir_info', {}).get('editable') is True
    check_runtime_origin(service, sys.prefix, origin, distribution.locate_file(''), source, editable)
    if sha((origin / 'schema.json').read_bytes()) != sha((ROOT / 'contracts/v1/schema.json').read_bytes()):
        raise ValueError('Installed contract schema')
    return {'prefix': sys.prefix, 'python': sys.version.split()[0], 'contract_origin': str(origin),
            'contract_source': source, 'editable': editable, 'uvicorn': importlib.metadata.version('uvicorn')}


def worker(service, profile, target, nonce):
    if (service, profile) not in PROFILES:
        raise ValueError('Unknown profile')
    target = Path(target).resolve()
    if target.parent.parent != CACHE.resolve() or not target.parent.name.startswith('run-') or target.name != f'{service}-{profile}.json':
        raise ValueError('Report scope')
    run = target.parent
    selected = [c for c in registry() if (c.service, c.profile) == (service, profile)]
    rows, runtime = [], None
    token = 'probe-' + uuid4().hex if profile == 'token' else None
    marker = 'probe-marker-' + uuid4().hex
    process = capture = None
    record = {'service': service, 'profile': profile, 'pid': None, 'port': None,
              'exited': False, 'port_closed': False, 'contained': False}
    try:
        runtime = installed_runtime(service)  # Inspect the service install before loading client source.
        package = contracts()
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        module = {'rag': 'notelens_rag', 'classifier': 'notelens_classifier', 'extraction': 'notelens_extraction'}[service]
        command = [sys.executable, '-B', '-m', 'uvicorn', module + '.main:app', '--host', '127.0.0.1',
                   '--port', str(port), '--no-proxy-headers', '--no-access-log', '--log-level', 'error']
        with owned_server(command, ROOT, environment(run, service, profile, token), (token, marker)) as (process, capture):
            record.update(pid=process.pid, port=port)
            target.with_suffix('.process.json').write_text(json.dumps(record), encoding='utf-8')
            deadline = time.monotonic() + 20
            while not reachable(port):
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise ValueError('Service startup')
                time.sleep(.03)
            seen_health_ids = set()
            for case in selected:
                problems, status = [], None
                try:
                    headers, body, document = request_data(case, token, marker)
                    status, outgoing, raw = wire(port, case, headers, body)
                    problems = response_issues(case, status, outgoing, raw, headers, package, (token, marker), document)
                    if not problems and case.method == 'GET':
                        ids = headers_named(outgoing, 'X-Request-ID')
                        if ids and ids[0] in seen_health_ids:
                            problems.append('HEALTH_ID_REPEATED')
                        seen_health_ids.update(ids)
                except package.ContractValidationError as error:
                    problems = sorted({issue.rule for issue in error.issues})
                except Exception:
                    problems = ['TRANSPORT_OR_VALIDATION_FAILURE']
                rows.append({'id': case.id, 'service': service, 'profile': profile,
                             'provenance': 'service-http', 'outcome': 'failed' if problems else 'passed',
                             'http_status': status, 'issues': problems})
    except Exception:
        pass  # Missing prerequisites/startup are recorded below without unsafe exception text.
    finally:
        if process:
            record['exited'] = process.poll() is not None
            record['port_closed'] = closed_port(record['port'])
        if capture and (capture.leak or capture.traceback or capture.thread.is_alive()):
            for row in rows:
                row.update(outcome='failed', issues=sorted(set(row['issues'] + ['UNSAFE_SERVICE_LOG'])))
        observed = {row['id'] for row in rows}
        rows += [{'id': c.id, 'service': service, 'profile': profile, 'provenance': 'service-http',
                  'outcome': 'failed', 'http_status': None, 'issues': ['WORKER_PREREQUISITE_OR_STARTUP']}
                 for c in selected if c.id not in observed]
        target.write_text(json.dumps({'format': 'notelens-f011-worker-v1', 'run_id': nonce,
                          'runtime': runtime, 'process': record, 'cases': rows}, indent=2) + '\n', encoding='utf-8')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['mock'], default='mock')
    parser.parse_args(argv)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / 'latest.json').unlink(missing_ok=True)
    if inventory_issues(ROOT):
        raise ValueError('Current source inventory')
    contracts()
    source = source_fingerprint(ROOT)
    run = Path(tempfile.mkdtemp(prefix='run-', dir=CACHE))
    (run / 'tmp').mkdir()
    nonce = str(uuid4())
    specs, observed, processes = registry(), {}, []
    for service, profile in PROFILES:
        target = run / f'{service}-{profile}.json'
        python = ROOT / 'services' / service / '.venv/Scripts/python.exe'
        command = [str(python), '-B', str(Path(__file__).resolve()), '__worker__', service, profile, str(target), nonce]
        contained = False
        try:
            with (run / f'{service}-{profile}.log').open('w', encoding='utf-8') as output:
                result = run_owned(command, cwd=run, env=environment(run, service, profile), stdout=output, timeout=90)
            contained = True
            data = json.loads(target.read_text(encoding='utf-8'))
            selected = [c for c in specs if (c.service, c.profile) == (service, profile)]
            if result.returncode or data['format'] != 'notelens-f011-worker-v1' or data['run_id'] != nonce or \
                    [c['id'] for c in data['cases']] != [c.id for c in selected]:
                raise ValueError('Worker evidence')
            record = data['process']
            if (record['service'], record['profile']) != (service, profile):
                raise ValueError('Worker process identity')
            record['contained'] = True  # Only the coordinator can attest its completed job cleanup.
            if record.get('port'):
                record['port_closed'] = record['port_closed'] and closed_port(record['port'])
            processes.append(record)
            observed.update((row['id'], row) for row in data['cases'])
        except Exception:
            # Job containment stops descendants on exceptions/timeouts. No PID scan/kill.
            record = {'service': service, 'profile': profile, 'pid': None, 'port': None,
                      'exited': False, 'port_closed': False, 'contained': contained}
            processes.append(record)
    cases = []
    for case in specs:
        cases.append(observed.get(case.id, {'id': case.id, 'service': case.service, 'profile': case.profile,
                     'provenance': 'pending-owner' if case.blocked else 'service-http',
                     'outcome': 'blocked' if case.blocked else 'failed', 'http_status': None,
                     'issues': [case.blocked or 'WORKER_EVIDENCE_MISSING']}))
    problems = completion_issues(cases, processes)
    if inventory_issues(ROOT) or source_fingerprint(ROOT) != source:
        problems.append('SOURCE_DRIFT')
    network = run / 'network-blocks.jsonl'
    if network.exists() and network.read_text().strip():
        problems.append('EXTERNAL_NETWORK_ATTEMPT')
    report = {'format': 'notelens-f011-run-v1', 'scope': 'all-three-services', 'mode': 'mock',
              'run_id': nonce, 'passed': not problems, 'complete': not problems,
              'python_validation': 'generated-source', 'source_fingerprint': source,
              'case_count': len(cases), 'counts': dict(Counter(row['outcome'] for row in cases)),
              'cases': cases, 'processes': processes, 'issues': problems,
              'artifacts': {p.name: sha(p.read_bytes()) for p in run.iterdir() if p.is_file()}}
    path = run / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (CACHE / 'latest.json').write_text(json.dumps({'report': str(path.relative_to(ROOT)),
           'sha256': sha(path.read_bytes()), 'passed': report['passed'], 'complete': report['complete']}, indent=2) + '\n', encoding='utf-8')
    print(('PASS' if report['passed'] else 'INCOMPLETE') + ': F-011 ' + json.dumps(report['counts'], sort_keys=True))
    print('Evidence: ' + str(path.relative_to(ROOT)))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    try:
        if len(sys.argv) == 6 and sys.argv[1] == '__worker__':
            sys.exit(worker(*sys.argv[2:]))
        sys.exit(main())
    except Exception as error:
        print('FAIL: F-011 ' + type(error).__name__ + '; inspect owned metadata logs')
        sys.exit(1)
