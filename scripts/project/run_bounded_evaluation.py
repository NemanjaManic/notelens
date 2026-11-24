"""Execute a pinned, runtime-only workload through the bounded web app."""

import argparse
from contextlib import ExitStack, closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from http.client import HTTPConnection, HTTPException
from io import BytesIO
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
from threading import Timer
import time
import unicodedata
from uuid import UUID
from zipfile import BadZipFile, ZipFile

from scaffold_process import owned_job
from smoke_mock import verify_shutdown
from start_bounded_evaluation import Endpoint, TOKEN_ENV, claim_approved_run, start_bounded_web
from start_mock import MockStack, MockStartupError, ROOT, child_environment


ROUTES = {'document_only', 'literature_only', 'mixed', 'out_of_scope'}
RUNTIME_FIELDS = {'case_id', 'case_version', 'question', 'document_file'}
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}')
DOC_PATH = re.compile(r'documents/[A-Za-z0-9][A-Za-z0-9_.-]*\.txt')
CAPTURE = 'X-NoteLens-Evaluation-Output'
SESSION_DOCUMENT_CAP = 3


class RunError(Exception):
    """A source-free failure reason suitable for the run receipt."""


def require(condition, reason):
    if not condition:
        raise RunError(reason)


def digest(data):
    return sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


@dataclass(frozen=True)
class Workload:
    manifest_sha256: str
    bundle_sha256: str
    cases: list
    sources: dict

    def required_calls(self):
        return {
            'extract': len(self.sources),
            'document-answer': sum(row['route'] in ('document_only', 'mixed') for row in self.cases),
            'literature-answer': sum(row['route'] in ('literature_only', 'mixed') for row in self.cases),
        }

    def reviewed_literature_hashes(self):
        return {scope: [digest(case['question'].encode('utf-8')) for case in self.cases if case['route'] == route]
                for scope, route in (('literature', 'literature_only'), ('both', 'mixed'))}


def load_workload(manifest_path, expected_manifest_hash, bundle_path):
    manifest_bytes = manifest_path.read_bytes()
    require(digest(manifest_bytes) == expected_manifest_hash, 'manifest_hash_mismatch')
    manifest = json.loads(manifest_bytes)
    bundle = bundle_path.read_bytes()
    bundle_hash = digest(bundle)
    require(bundle_hash == manifest['candidate_archives']['runtime']['sha256'], 'runtime_bundle_hash_mismatch')
    require(manifest.get('replacements_pending_review', 0) == 0, 'replacement_reviews_pending')
    rows = {row['case_id']: row for row in manifest['cases']}
    require(len(rows) == len(manifest['cases']) == manifest['case_count'] and rows, 'manifest_case_inventory_mismatch')
    cases, sources, documents = [], {}, set()
    with ZipFile(BytesIO(bundle)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'duplicate_runtime_archive_member')
        entries = json.loads(archive.read('runtime-cases.json'))
        require(len(entries) == len(rows) and {entry['case_id'] for entry in entries} == set(rows),
                'runtime_case_inventory_mismatch')
        for item in entries:
            require(set(item) == RUNTIME_FIELDS, 'unexpected_runtime_fields')
            cid, version, question = item['case_id'], item['case_version'], item['question']
            row = rows[cid]
            require(NAME.fullmatch(cid) and NAME.fullmatch(version), 'invalid_case_identity')
            require(version == row['case_version'], 'case_version_mismatch')
            require(digest(encoded(item)) == row['runtime_entry_sha256'], 'runtime_entry_hash_mismatch')
            require(isinstance(question, str) and bool(question) and question == question.strip()
                    and '\r' not in question and unicodedata.is_normalized('NFC', question), 'noncanonical_question')
            route, document_file = row['requested_route'], item['document_file']
            require(route in ROUTES, 'invalid_requested_route')
            require((document_file is not None) == (route in ('document_only', 'mixed')), 'case_document_binding_mismatch')
            source = None
            if document_file is not None:
                require(DOC_PATH.fullmatch(document_file), 'invalid_document_member')
                raw = archive.read(document_file)
                source = digest(raw)
                require(source == row['canonical_text_sha256'], 'canonical_document_hash_mismatch')
                text = raw.decode('utf-8')
                require(0 < len(text) <= 100_000 and '\r' not in text and unicodedata.is_normalized('NFC', text),
                        'noncanonical_document')
                sources.setdefault(source, raw)
                documents.add(document_file)
            else:
                require(row['canonical_text_sha256'] is None, 'unexpected_canonical_document_hash')
            cases.append({**item, 'route': route, 'source_sha256': source, 'runtime_entry_sha256': row['runtime_entry_sha256']})
        require(set(names) <= documents | {'README.txt', 'SHA256SUMS.txt', 'runtime-cases.json'},
                'archive_contains_non_runtime_content')
    require(len(documents) == manifest['runtime_document_count'] and bool(sources), 'runtime_document_inventory_mismatch')
    return Workload(expected_manifest_hash, bundle_hash, cases, sources)


class Web:
    def __init__(self, stack, deadline):
        self.stack = stack
        self.deadline = deadline

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        require(remaining > 0, 'deadline_exceeded')
        return remaining

    def request(self, path, expected, *, body=None, content_type=None, cookie=None, scope=None):
        headers = {'Origin': self.stack.web_origin, CAPTURE: '1'}
        if cookie:
            headers['Cookie'] = cookie
        if content_type:
            headers['Content-Type'] = content_type
        if scope:
            headers['X-NoteLens-Input-Scope'] = scope
        with closing(HTTPConnection('127.0.0.1', self.stack.web_port, timeout=self.remaining())) as conn:
            try:
                conn.connect()
                sock = conn.sock

                def interrupt():
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass

                with cancel_at(self.remaining(), interrupt):
                    conn.request('POST', path, body=body, headers=headers)
                    response = conn.getresponse()
                    data = response.read()
                    self.remaining()
            except (HTTPException, OSError):
                self.remaining()
                raise RunError('web_transport_failed') from None
        require(response.status == expected, f'unexpected_http_{response.status}')
        require(response.getheader('Cache-Control') == 'no-store', 'response_cache_policy_mismatch')
        return json.loads(data) if data else None, response.getheader('Set-Cookie')


@contextmanager
def cancel_at(seconds, interrupt):
    timer = Timer(seconds, interrupt)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


def save(output, name, value):
    with (output / name).open('xb') as file:
        file.write(encoded(value))


def create_output(output):
    require(not output.resolve().is_relative_to(ROOT.resolve()), 'choose_restricted_output_outside_checkout')
    output.mkdir()


def finish_output(output, receipt):
    receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
    save(output, 'run-receipt.json', receipt)
    checksums = ''.join(f'{digest(file.read_bytes())}  {file.name}\n' for file in sorted(output.iterdir()))
    with (output / 'SHA256SUMS.txt').open('x', encoding='ascii', newline='\n') as file:
        file.write(checksums)
    return receipt


def canonical_uuid(value):
    return isinstance(value, str) and str(UUID(value)) == value


def question_payload(case, doc_id):
    question, route = case['question'], case['route']
    scope, field = {
        'document_only': ('document', 'documentQuestion'), 'literature_only': ('literature', 'literatureQuestion'),
        'mixed': ('both', 'question'), 'out_of_scope': ('out-of-scope', 'question'),
    }[route]
    return {'document': doc_id, 'scope': scope, field: question}


def execute_workload(workload, output, stack_context, *, run_id, app_sha, deadline_seconds,
                     scope, profile, service_pins=None, approval_sha256=None):
    require(type(deadline_seconds) is int and 0 < deadline_seconds <= 3600, 'invalid_deadline')
    require(scope in ('synthetic', 'public'), 'invalid_document_scope')
    create_output(output)
    watchdog = {'enabled': False, 'triggered': False, 'job_drained': False, 'listeners_closed': []}
    receipt = {
        'format': 'notelens-bounded-web-output-v1', 'run_id': run_id, 'app_sha': app_sha,
        'approval_sha256': approval_sha256, 'profile': profile, 'service_pins': service_pins,
        'runtime_manifest_sha256': workload.manifest_sha256, 'runtime_bundle_sha256': workload.bundle_sha256,
        'deadline_seconds': deadline_seconds, 'required_http_operations': workload.required_calls(),
        'expected_cases': len(workload.cases), 'saved_cases': 0, 'saved_sources': 0,
        'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'failed', 'web_shutdown_verified': False,
        'whole_stack_watchdog': watchdog,
    }
    stage, case, source = 'startup', None, None
    stack = None
    deadline = time.monotonic() + deadline_seconds
    deadline_unix_ms = time.time_ns() // 1_000_000 + deadline_seconds * 1000
    try:
        with stack_context(deadline, deadline_unix_ms, watchdog) as stack:
            receipt['web_ready_utc'] = datetime.now(timezone.utc).isoformat()
            web = Web(stack, deadline)
            registered, captured, anchors, question_counts, cookie = {}, set(), [], {}, None
            for index, (source, text) in enumerate(workload.sources.items()):
                stage = 'session'
                if index % SESSION_DOCUMENT_CAP == 0:
                    _, header = web.request('/api/session', 204)
                    require(isinstance(header, str), 'session_cookie_missing')
                    cookie = header.split(';', 1)[0]
                    question_counts[cookie] = 0
                stage = 'submit'
                result, _ = web.request('/api/documents/submit', 201, body=text, content_type='text/plain; charset=utf-8',
                                        scope=scope, cookie=cookie)
                doc_id = result['document']
                require(canonical_uuid(doc_id), 'invalid_app_document_id')
                require(result['canonical_sha256'] == source, 'app_prepared_document_hash_mismatch')
                registered[source] = (doc_id, cookie)
                if index % SESSION_DOCUMENT_CAP == 0:
                    anchors.append((doc_id, cookie))
            for case in workload.cases:
                source = case['source_sha256']
                doc_id, cookie = registered[source] if source else min(anchors, key=lambda a: question_counts[a[1]])
                if source and source not in captured:
                    stage = 'source_output'
                    result, _ = web.request('/api/evaluation/source?document=' + doc_id, 200, cookie=cookie)
                    require(result['document'] == doc_id and result['canonical_sha256'] == source, 'source_output_identity_mismatch')
                    save(output, 'source-' + source + '.json', result)
                    receipt['saved_sources'] += 1
                    require(result['extraction']['state'] == result['classification']['state'] == 'ready'
                            and result['extraction']['record']['extraction_status'] in ('partial', 'completed'),
                            'source_analysis_unavailable')
                    captured.add(source)
                stage = 'answer_output'
                result, _ = web.request('/api/questions', 200, body=encoded(question_payload(case, doc_id)),
                                        content_type='application/json', cookie=cookie)
                question_counts[cookie] += 1
                turn = result.get('turn', {}) if result['kind'] == 'transient' else result
                answer = turn['answer']
                require(canonical_uuid(turn['id']), 'invalid_turn_id')
                save(output, f"case-{receipt['saved_cases'] + 1:03}.json", {
                    'case_id': case['case_id'], 'case_version': case['case_version'], 'requested_route': case['route'],
                    'runtime_entry_sha256': case['runtime_entry_sha256'], 'canonical_sha256': source,
                    'app_document_id': doc_id if source else None, 'turn_id': turn['id'], 'answer': answer,
                })
                receipt['saved_cases'] += 1
                expected = {'document_only': ['document'], 'literature_only': ['literature'],
                            'mixed': ['document', 'literature'], 'out_of_scope': []}[case['route']]
                require([branch['origin'] for branch in answer['branches']] == expected, 'answer_branch_mismatch')
                require(all(branch['result']['kind'] == 'accepted' for branch in answer['branches'])
                        and (expected or answer['state'] == 'unsupported'), 'answer_service_unavailable')
            stage = 'shutdown'
        require(not watchdog['triggered'], 'deadline_exceeded')
        receipt['status'] = 'completed'
    except (RunError, MockStartupError, HTTPException, OSError, KeyError, AttributeError, TypeError,
            ValueError, RuntimeError, KeyboardInterrupt) as error:
        reason = str(error) if isinstance(error, RunError) else type(error).__name__
        if isinstance(error, TimeoutError):
            reason = 'deadline_exceeded' if time.monotonic() >= deadline else 'startup_transport_timeout'
        if isinstance(error, KeyboardInterrupt):
            reason = 'interrupted'
        if watchdog['triggered'] and not watchdog.get('termination_failed'):
            reason = 'deadline_exceeded'
        save(output, 'failures.json', [{'stage': stage, 'reason': reason,
                                      'case_id': case['case_id'] if case else None, 'canonical_sha256': source}])
        receipt['failure_stage'] = stage
    if watchdog['enabled']:
        receipt['web_shutdown_verified'] = 'web' in watchdog['listeners_closed']
    elif stack:
        try:
            verify_shutdown(stack)
            receipt['web_shutdown_verified'] = True
        except (MockStartupError, OSError):
            receipt['status'] = 'failed'
            receipt['shutdown_failure'] = 'web_shutdown_unverified'
    return finish_output(output, receipt)


def save_preflight_failure(output, reason):
    try:
        create_output(output)
    except (RunError, OSError):
        return False
    save(output, 'failures.json', [{'stage': 'preflight', 'reason': reason}])
    finish_output(output, {'format': 'notelens-bounded-web-output-v1', 'status': 'failed',
                           'failure_stage': 'preflight', 'saved_cases': 0, 'saved_sources': 0})
    return True


@contextmanager
def start_managed_stack(endpoints, launches, limits, *, deadline, deadline_unix_ms, watchdog, profile, http_timeout_ms,
                        reviewed_literature_hashes=None):
    require(set(endpoints) == set(launches) == set(TOKEN_ENV), 'missing_managed_service_launch')
    watchdog['enabled'] = True
    job, stack = None, None
    try:
        with ExitStack() as reservations:
            for endpoint in endpoints.values():
                listener = reservations.enter_context(socket.socket())
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                listener.bind(('127.0.0.1', endpoint.port))
        with owned_job(deadline) as job:
            children = {name: job.start(command, cwd=cwd, env=env, stdout=subprocess.DEVNULL)
                        for name, (command, cwd, env) in launches.items()}
            with start_bounded_web(endpoints, limits, profile=profile, http_timeout_ms=http_timeout_ms,
                                   deadline_unix_ms=deadline_unix_ms, owner=job,
                                   reviewed_literature_hashes=reviewed_literature_hashes) as web:
                stack = MockStack(web.web_port, {**children, **web.processes},
                                  {**{name: endpoint.port for name, endpoint in endpoints.items()}, **web.ports})
                yield stack
    finally:
        if job is not None:
            watchdog.update(triggered=job.expired, job_drained=job.drained)
            if job.stop_error is not None or not job.drained:
                watchdog['termination_failed'] = True
        if stack is not None:
            verify_shutdown(stack)
            watchdog['listeners_closed'] = sorted(stack.ports)


def service_launches(config, endpoints):
    declared = config['service_launch']
    require(set(declared) == set(TOKEN_ENV), 'missing_managed_service_launch')
    launches = {}
    for name, token_key in TOKEN_ENV.items():
        command, cwd, inherit = (declared[name][key] for key in ('argv', 'cwd', 'inherit_env'))
        require(isinstance(command, list) and bool(command) and all(isinstance(arg, str) and arg for arg in command),
                'invalid_managed_service_command')
        executable, cwd = Path(command[0]), Path(cwd)
        require(executable.is_absolute() and executable.suffix.lower() == '.exe' and executable.is_file()
                and cwd.is_absolute() and cwd.is_dir(), 'invalid_managed_service_path')
        require(isinstance(inherit, list) and all(isinstance(key, str) and re.fullmatch(r'[A-Z][A-Z0-9_]*', key)
                and key not in TOKEN_ENV.values() for key in inherit), 'invalid_managed_service_environment')
        env = {**child_environment(), **{key: os.environ[key] for key in inherit}, token_key: endpoints[name].token}
        launches[name] = (command, cwd, env)
    return launches


@contextmanager
def approved_stack(config_path, config, config_bytes, workload, deadline, deadline_unix_ms, watchdog):
    endpoints = {name: Endpoint(**config['services'][name], token=os.environ[key]) for name, key in TOKEN_ENV.items()}
    launches = service_launches(config, endpoints)
    claim_approved_run(config_path, config['run_id'], config_bytes)
    with start_managed_stack(endpoints, launches, config['http_limits'], profile='provider-backed',
                             http_timeout_ms=config['http_timeout_ms'], deadline=deadline,
                             deadline_unix_ms=deadline_unix_ms, watchdog=watchdog,
                             reviewed_literature_hashes=workload.reviewed_literature_hashes()) as stack:
        yield stack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-config', type=Path, required=True)
    parser.add_argument('--approval-sha256', required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--runtime-zip', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = args.approved_config.read_bytes()
        require(digest(raw) == args.approval_sha256, 'approval_hash_mismatch')
        config = json.loads(raw)
        require(config['approved'] is True and all(isinstance(config[key], str) and config[key].strip()
                for key in ('operator', 'approved_by')), 'approved_operator_and_freeze_required')
        app_sha = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        require(app_sha == config['app_sha'] and not subprocess.check_output(
            ['git', '-C', str(ROOT), 'status', '--porcelain'], text=True).strip(), 'app_checkout_mismatch')
        workload = load_workload(args.manifest, config['runtime_manifest_sha256'], args.runtime_zip)
        require(workload.required_calls() == config['http_limits'], 'approved_http_limits_do_not_match_inventory')
        require(set(config['service_pins']) == set(TOKEN_ENV) and all(
            isinstance(pin, str) and pin.strip() for pin in config['service_pins'].values()), 'missing_service_pins')
        receipt = execute_workload(workload, args.output,
                                   lambda *timing: approved_stack(args.approved_config, config, raw, workload, *timing),
                                   run_id=config['run_id'], app_sha=app_sha, deadline_seconds=config['deadline_seconds'],
                                   scope=config['document_scope'], profile='provider-backed', service_pins=config['service_pins'],
                                   approval_sha256=args.approval_sha256)
        print(f"Evaluation run {receipt['status']}. Receipt and checksums written.")
        return 0 if receipt['status'] == 'completed' else 1
    except (RunError, KeyError, AttributeError, TypeError, ValueError, OSError, BadZipFile, subprocess.SubprocessError) as error:
        reason = str(error) if isinstance(error, RunError) else type(error).__name__
        print(f'Evaluation stopped: {reason}.', file=sys.stderr)
        try:
            if save_preflight_failure(args.output, reason):
                print('Preflight failure receipt and checksums written.', file=sys.stderr)
        except OSError:
            print('The preflight failure receipt could not be written.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
