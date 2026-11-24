"""Verify bounded operator capture using generated synthetic inputs and loopback doubles."""

from collections import Counter
from contextlib import ExitStack, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Thread
import time
from types import SimpleNamespace
from uuid import uuid4
from zipfile import ZipFile

from check_bounded_evaluation import DOCUMENT_QUESTION, LITERATURE_QUESTION, billable_paths, exercise_profile, service_double
from run_bounded_evaluation import RunError, Web, digest, encoded, execute_workload, load_workload, service_launches, start_managed_stack
from smoke_mock import require, verify_shutdown
from start_bounded_evaluation import Endpoint, TOKEN_ENV
from start_mock import ROOT


MIXED_QUESTION = ('Could you explain what the doctor wrote about the chest pain in the document '
                  'and tell me what the medical literature says about that symptom in general?')
OUT_OF_SCOPE_QUESTION = ('I need help writing a birthday invitation for my younger brother. Can you write a playful '
                         'invitation and remind everyone to bring a friend and something to share with the group?')


def make_bundle(directory, source, *, include_scoring=False, wrong_entry_hash=False, wrong_source_hash=False):
    documents = {'documents/a.txt': source.encode(), 'documents/a-copy.txt': source.encode(),
                 'documents/b.txt': (source + '\nThe care team scheduled an English follow-up appointment.').encode()}
    cases = [
        ('DOC-A', 'document_only', DOCUMENT_QUESTION, 'documents/a.txt'),
        ('MIX-A', 'mixed', MIXED_QUESTION, 'documents/a-copy.txt'),
        ('DOC-B', 'document_only', DOCUMENT_QUESTION, 'documents/b.txt'),
        ('LIT-A', 'literature_only', LITERATURE_QUESTION, None),
        ('OOS-A', 'out_of_scope', OUT_OF_SCOPE_QUESTION, None),
    ]
    return write_bundle(directory, cases, documents, include_scoring=include_scoring,
                        wrong_entry_hash=wrong_entry_hash, wrong_source_hash=wrong_source_hash)


def write_bundle(directory, cases, documents, *, include_scoring=False, wrong_entry_hash=False, wrong_source_hash=False):
    entries = [dict(case_id=key, case_version='v1', question=question, document_file=member)
               for key, _, question, member in cases]
    bundle = directory / 'runtime.zip'
    with ZipFile(bundle, 'w') as archive:
        archive.writestr('runtime-cases.json', encoded(entries))
        for member, body in documents.items():
            archive.writestr(member, body)
        if include_scoring:
            archive.writestr('scoring.json', b'[]')
    rows = [dict(case_id=key, case_version='v1', requested_route=route, runtime_entry_sha256=digest(encoded(entry)),
                 canonical_text_sha256=digest(documents[member]) if member else None)
            for (key, route, _, member), entry in zip(cases, entries, strict=True)]
    if wrong_entry_hash:
        rows[0]['runtime_entry_sha256'] = '0' * 64
    if wrong_source_hash:
        rows[0]['canonical_text_sha256'] = '0' * 64
    manifest = directory / 'manifest.json'
    raw = encoded(dict(case_count=len(rows), runtime_document_count=len(documents), cases=rows,
                       replacements_pending_review=0, candidate_archives={'runtime': {'sha256': digest(bundle.read_bytes())}}))
    manifest.write_bytes(raw)
    return manifest, digest(raw), bundle


def expect_error(action, reason):
    try:
        action()
    except RunError as error:
        require(str(error) == reason, f'expected {reason}, received {error}')
    else:
        require(False, f'expected {reason}')


def verify_checksums(output):
    rows = [line.split('  ', 1) for line in (output / 'SHA256SUMS.txt').read_text().splitlines()]
    require(len(rows) == len(list(output.iterdir())) - 1, 'one checksum for every saved file')
    require({name for _, name in rows} == {file.name for file in output.iterdir()} - {'SHA256SUMS.txt'}, 'checksum inventory')
    for checksum, name in rows:
        require(digest((output / name).read_bytes()) == checksum, f'{name} verifies against the checksum list')


def read(output, name):
    return json.loads((output / name).read_bytes())


def run_capture(fixtures, workload, output, *, fail='', deadline_seconds=20):
    calls = []

    @contextmanager
    def counted_stack(_deadline, deadline_unix_ms, _watchdog):
        with exercise_profile(fixtures, workload.required_calls(), fail=fail, deadline_unix_ms=deadline_unix_ms) as (stack, observed):
            try:
                yield stack
            finally:
                calls.extend(observed)

    app_sha = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    result = execute_workload(workload, output, counted_stack, run_id=output.name, app_sha=app_sha,
                              deadline_seconds=deadline_seconds, scope='synthetic', profile='offline')
    verify_checksums(output)
    require(read(output, 'run-receipt.json') == result and result['profile'] == 'offline', 'saved run receipt')
    require(result['web_shutdown_verified'], 'owned web shutdown verified')
    require(result['app_sha'] == app_sha and result['runtime_manifest_sha256'] == workload.manifest_sha256
            and result['runtime_bundle_sha256'] == workload.bundle_sha256, 'run pins recorded')
    return result, calls


def verify_capture(fixtures, workload, folder):
    output = folder / 'offline-success'
    receipt, calls = run_capture(fixtures, workload, output)
    if receipt['status'] != 'completed':
        raise AssertionError(f"Synthetic capture stopped: {read(output, 'failures.json')}")
    require((receipt['saved_cases'], receipt['saved_sources']) == (5, 2), 'full capture')
    require(Counter(billable_paths(calls)) == Counter({'/v1/extract': 2, '/v1/document-answer': 3, '/v1/literature-answer': 2}),
            'exact dispatch counts with no out-of-scope provider calls')
    require(len({source for path, source in calls if path == '/v1/extract'}) == 2, 'each canonical source extracted once')
    first, mixed, second, lit, outside = [read(output, f'case-{n:03}.json') for n in range(1, 6)]
    require(first['app_document_id'] == mixed['app_document_id'] != second['app_document_id'], 'one ID per canonical source')
    require(first['canonical_sha256'] == mixed['canonical_sha256'] != second['canonical_sha256'], 'output retains canonical identity')
    source_output = read(output, 'source-' + first['canonical_sha256'] + '.json')
    require(source_output['document'] == first['app_document_id'] and source_output['classification']['state'] == 'ready',
            'classification and extraction captured for the original ID')
    require([record['answer']['state'] for record in (first, mixed, second, lit, outside)] ==
            ['sufficient', 'partial', 'sufficient', 'insufficient', 'unsupported'], 'exact evidence states preserved')
    require(lit['app_document_id'] is None and outside['app_document_id'] is None, 'session anchors stay out of saved case outputs')
    require(not (output / 'failures.json').exists(), 'successful run has no failure record')


def verify_failure(fixtures, workload, folder):
    output = folder / 'offline-stopped'
    receipt, calls = run_capture(fixtures, workload, output, fail='/v1/literature-answer')
    require((receipt['status'], receipt['saved_cases'], receipt['saved_sources']) == ('failed', 2, 1), 'capture stops on first error')
    require(billable_paths(calls) == ['/v1/extract', '/v1/document-answer', '/v1/document-answer', '/v1/literature-answer'],
            'no retry or subsequent case after service error')
    require(read(output, 'case-001.json')['answer']['state'] == 'sufficient', 'the previous result was retained')
    require(read(output, 'case-002.json')['answer']['state'] == 'partial', 'the failed mixed case retains document support')
    require(read(output, 'failures.json')[0] == {'stage': 'answer_output', 'reason': 'answer_service_unavailable',
            'case_id': 'MIX-A', 'canonical_sha256': workload.cases[1]['source_sha256']}, 'source-free failure locates the exact step')


def verify_full_inventory(fixtures, folder, source):
    documents, cases = {}, []
    for index in range(16):
        member = f'documents/synthetic-{index + 1}.txt'
        documents[member] = (source + f'\nThe care team scheduled a follow-up visit for synthetic example {index + 1}.').encode()
        route, question = ('document_only', DOCUMENT_QUESTION) if index < 8 else ('mixed', MIXED_QUESTION)
        cases.append((f'SYN-{index + 1:02}', route, question, member))
    cases.extend((f'SYN-{index:02}', 'literature_only', LITERATURE_QUESTION, None) for index in range(17, 25))
    cases.extend((f'SYN-{index:02}', 'out_of_scope', OUT_OF_SCOPE_QUESTION, None) for index in (25, 26))
    workload = load_workload(*write_bundle(folder, cases, documents))
    output = folder / 'offline-full-inventory'
    receipt, calls = run_capture(fixtures, workload, output, deadline_seconds=45)
    if receipt['status'] != 'completed':
        raise AssertionError(f"Full synthetic inventory stopped: {read(output, 'failures.json')}")
    require((receipt['saved_cases'], receipt['saved_sources']) == (26, 16), 'full 26-case synthetic inventory captured')
    require(Counter(billable_paths(calls)) == Counter(dict.fromkeys(
        ('/v1/extract', '/v1/document-answer', '/v1/literature-answer'), 16)), 'the full inventory fits all three HTTP ceilings')
    require(len({source for path, source in calls if path == '/v1/extract'}) == 16, 'one extraction per source across sessions')


def verify_deadline():
    reached = Event()
    release = Event()

    class SlowHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            reached.set()
            release.wait(5)

    with ThreadingHTTPServer(('127.0.0.1', 0), SlowHandler) as server:
        thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05})
        thread.start()
        stack = SimpleNamespace(web_port=server.server_port, web_origin=f'http://localhost:{server.server_port}')
        try:
            start = time.monotonic()
            web = Web(stack, start + 0.35)
            expect_error(lambda: web.request('/api/questions', 200), 'deadline_exceeded')
            require(reached.is_set() and time.monotonic() - start < 1.5, 'deadline interrupts an in-flight HTTP wait')
            expect_error(lambda: web.request('/api/questions', 200), 'deadline_exceeded')
        finally:
            release.set()
            server.shutdown()
            thread.join()


def verify_preflight_failure(folder, manifest, bundle):
    config = folder / 'approval.json'
    config.write_bytes(b'{}')
    output = folder / 'offline-preflight'
    command = [sys.executable, '-B', str(ROOT / 'scripts/project/run_bounded_evaluation.py'), '--approved-config', str(config),
               '--approval-sha256', '0' * 64, '--manifest', str(manifest), '--runtime-zip', str(bundle), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, check=False)
    require(result.returncode == 1, 'preflight refuses unverified approval')
    require(read(output, 'failures.json') == [{'stage': 'preflight', 'reason': 'approval_hash_mismatch'}], 'preflight saved safely')
    verify_checksums(output)
    original = (output / 'SHA256SUMS.txt').read_bytes()
    require(subprocess.run(command, capture_output=True, check=False).returncode == 1, 'existing output is refused')
    require((output / 'SHA256SUMS.txt').read_bytes() == original, 'existing receipt preserved')


def serve_watchdog_double(name, port, marker):
    fixtures = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_bytes())

    def stall(path):
        if name == 'rag' and path == '/v1/literature-answer':
            marker.write_text('stalled\n', encoding='ascii')
            Event().wait(120)

    with service_double(name, fixtures, [], '', port=port, token=os.environ[TOKEN_ENV[name]], stall=stall):
        Event().wait()


def verify_whole_stack_watchdog(workload, folder):
    marker = folder / 'rag-stalled.txt'
    endpoints, service_commands = {}, {}
    with ExitStack() as reservations:
        for name in TOKEN_ENV:
            reservation = reservations.enter_context(socket.socket())
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
            endpoints[name] = Endpoint(port, f'bounded-offline-{name}-v1', uuid4().hex)
            service_commands[name] = {'argv': [sys.executable, '-B', str(Path(__file__).resolve()),
                                                '--service-double', name, str(port), str(marker)],
                                      'cwd': str(ROOT), 'inherit_env': []}
    launches = service_launches({'service_launch': service_commands}, endpoints)

    stopped_before_cleanup = False

    @contextmanager
    def stack_context(deadline, deadline_unix_ms, watchdog):
        nonlocal stopped_before_cleanup
        with start_managed_stack(endpoints, launches, workload.required_calls(), profile='offline',
                                 http_timeout_ms=30_000, deadline=deadline,
                                 deadline_unix_ms=deadline_unix_ms, watchdog=watchdog) as stack:
            try:
                yield stack
            finally:
                # Defer context cleanup so only the independent watchdog can stop the job.
                until = deadline + 3
                while any(child.poll() is None for child in stack.processes.values()) and time.monotonic() < until:
                    time.sleep(0.02)
                verify_shutdown(stack)
                stopped_before_cleanup = True

    output = folder / 'offline-global-timeout'
    start = time.monotonic()
    receipt = execute_workload(workload, output, stack_context, run_id=output.name, app_sha='offline-working-tree',
                              deadline_seconds=8, scope='synthetic', profile='offline')
    elapsed = time.monotonic() - start
    require(marker.is_file(), 'the owned RAG worker entered the deliberately stalled request')
    require(stopped_before_cleanup, 'the watchdog stopped all listeners before normal cleanup')
    require(7.8 <= elapsed < 13, 'the watchdog stopped at the accelerated absolute deadline')
    require(receipt['whole_stack_watchdog'] == {'enabled': True, 'triggered': True, 'job_drained': True,
            'listeners_closed': ['classifier', 'extraction', 'rag', 'web']}, 'all four process trees and listeners stopped')
    require((receipt['status'], receipt['saved_cases'], receipt['saved_sources']) == ('failed', 1, 1),
            'the completed answer and source survived timeout')
    require(read(output, 'case-001.json')['answer']['state'] == 'sufficient', 'prior answer retained')
    require(read(output, 'failures.json')[0] == {'stage': 'answer_output', 'reason': 'deadline_exceeded',
            'case_id': 'MIX-A', 'canonical_sha256': workload.cases[1]['source_sha256']}, 'the deadline receipt identifies the stalled case')
    require(read(output, 'run-receipt.json') == receipt, 'the watchdog receipt was preserved')
    verify_checksums(output)


def main():
    fixtures = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_bytes())
    source = json.loads((ROOT / 'contracts/v1/fixtures/documents.json').read_bytes())['offset']['text']
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        manifest, checksum, bundle = make_bundle(folder, source)
        workload = load_workload(manifest, checksum, bundle)
        expect_error(lambda: load_workload(manifest, '0' * 64, bundle), 'manifest_hash_mismatch')
        bundle.write_bytes(bundle.read_bytes() + b'tampered')
        expect_error(lambda: load_workload(manifest, checksum, bundle), 'runtime_bundle_hash_mismatch')
        expect_error(lambda: load_workload(*make_bundle(folder, source, wrong_entry_hash=True)), 'runtime_entry_hash_mismatch')
        expect_error(lambda: load_workload(*make_bundle(folder, source, wrong_source_hash=True)), 'canonical_document_hash_mismatch')
        expect_error(lambda: load_workload(*make_bundle(folder, source, include_scoring=True)), 'archive_contains_non_runtime_content')
        verify_preflight_failure(folder, manifest, bundle)
        print('PASS: manifest, ZIP, case and source tampering rejected; scoring inputs refused; preflight failure recorded.')
        verify_capture(fixtures, workload, folder)
        print('PASS: five synthetic cases, two canonical sources and two extractions; outputs and checksums verified.')
        verify_failure(fixtures, workload, folder)
        print('PASS: first HTTP 503 preserved prior and partial results, recorded the failure and stopped without retry.')
        verify_full_inventory(fixtures, folder, source)
        print('PASS: 26 synthetic cases across sessions; 16 extractions, 16 document answers and 16 literature answers.')
        verify_deadline()
        print('PASS: deadline interrupted a pending HTTP response and refused further dispatch.')
        verify_whole_stack_watchdog(workload, folder)
        print('PASS: whole-stack deadline stopped all four trees and listeners; prior outputs and checksummed receipt survived.')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--service-double':
        serve_watchdog_double(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]))
    else:
        main()
