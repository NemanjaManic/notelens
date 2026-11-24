"""Exercise the bounded production web profile with counted synthetic loopback services."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager, closing
from copy import deepcopy
from hashlib import sha256
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from uuid import UUID, uuid4

from check_d005_app import read_report
from smoke_mock import prepare_example, question_request, read_page, require
from start_bounded_evaluation import Endpoint, claim_approved_run, start_bounded_web
from start_mock import MockStartupError, ROOT


OPERATIONS = {
    'classifier': {'/v1/classify': 'classification-supported'},
    'extraction': {'/v1/extract': 'extraction-valid', '/v1/document-answer': 'answer-document'},
    'rag': {'/v1/literature-answer': 'answer-literature-insufficient-no-generation'},
}
DOCUMENT_QUESTION = 'What does the document say about chest pain?'
LITERATURE_QUESTION = 'What is the synthetic demo topic?'


def bind(value, document):
    if isinstance(value, list):
        for item in value:
            bind(item, document)
    elif isinstance(value, dict):
        for key, original in value.items():
            if key == 'doc_id' and document:
                value[key] = document['doc_id']
            elif key == 'text_sha256' and document:
                value[key] = document['text_sha256']
            elif key == 'mode' and original == 'mock':
                value[key] = 'live'
            else:
                bind(original, document)


@contextmanager
def service_double(name, fixtures, calls, fail, *, port=0, token=None, stall=None, observed_questions=None,
                   unsupported_literature=False):
    token = token or uuid4().hex
    model = f'bounded-offline-{name}-v1'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, record, identifier):
            payload = json.dumps(record).encode()
            self.send_response(status)
            for key, value in [('Content-Type', 'application/json'), ('Content-Length', str(len(payload))),
                               ('Cache-Control', 'no-store'), ('X-Request-ID', identifier)]:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)

        def authorized(self):
            return self.headers.get('Authorization') == f'Bearer {token}'

        def do_GET(self):
            if not self.authorized() or self.path != '/health/ready':
                self.send_error(401)
                return
            self.reply(200, {'schema_version': '1.0.0', 'service': name, 'status': 'ok', 'mode': 'live',
                             'version': '0.1.0', 'model_version': model, 'reason': None}, str(uuid4()))

        def do_POST(self):
            if not self.authorized() or self.path not in OPERATIONS[name]:
                self.send_error(401)
                return
            identifier = self.headers.get('X-Request-ID', '')
            try:
                assert str(UUID(identifier)) == identifier
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                assert data['schema_version'] == '1.0.0'
            except (AssertionError, KeyError, ValueError):
                self.send_error(422)
                return
            document = data.get('document')
            calls.append((self.path, document['text_sha256'] if document else None))
            if observed_questions is not None and self.path in observed_questions:
                observed_questions[self.path].append(sha256(data['question'].encode('utf-8')).hexdigest())
            if stall is not None:
                stall(self.path)
            if unsupported_literature and self.path == '/v1/literature-answer':
                self.reply(422, {'schema_version': '1.0.0', 'request_id': identifier, 'error': {
                    'code': 'validation_failure', 'message': 'Synthetic unsupported literature request.', 'retryable': False,
                }}, identifier)
                return
            if self.path == fail:
                self.reply(503, {'schema_version': '1.0.0', 'request_id': identifier, 'error': {
                    'code': 'configuration_required', 'message': 'Synthetic service failure.', 'retryable': True,
                }}, identifier)
                return
            record = deepcopy(fixtures[OPERATIONS[name][self.path]])
            bind(record, document)
            if name == 'classifier':
                record['model_version'] = model
            self.reply(200, record, identifier)

    with ThreadingHTTPServer(('127.0.0.1', port), Handler) as server:
        port = server.server_port
        thread = Thread(target=server.serve_forever, kwargs={'poll_interval': 0.05})
        thread.start()
        try:
            yield Endpoint(port, model, token)
        finally:
            server.shutdown()
            thread.join()
    with closing(socket.socket()) as probe:
        require(probe.connect_ex(('127.0.0.1', port)) != 0, f'{name} offline listener stopped')


@contextmanager
def exercise_profile(fixtures, limits, *, fail='', deadline_unix_ms=None, reviewed_question_hashes=None,
                     observed_questions=None, unsupported_literature=False):
    calls = []
    with ExitStack() as services:
        endpoints = {name: services.enter_context(service_double(name, fixtures, calls, fail,
                     observed_questions=observed_questions,
                     unsupported_literature=unsupported_literature)) for name in OPERATIONS}
        with start_bounded_web(endpoints, limits, profile='offline', http_timeout_ms=5_000,
                               deadline_unix_ms=deadline_unix_ms,
                               reviewed_question_hashes=reviewed_question_hashes) as stack:
            require(read_page(stack, '/demo').contains('Bounded evaluation dry run'), 'offline provenance label')
            yield stack, calls


def open_example(stack):
    return prepare_example(stack, read_page(stack, '/demo').example_action)


def submit(stack, text, cookie):
    with closing(HTTPConnection('localhost', stack.web_port, timeout=8)) as connection:
        connection.request('POST', '/api/documents/submit', body=text.encode('utf-8'), headers={
            'Origin': stack.web_origin, 'Cookie': cookie, 'Content-Type': 'text/plain; charset=utf-8',
            'X-NoteLens-Input-Scope': 'synthetic',
        })
        response = connection.getresponse()
        require(response.status == 201, 'synthetic text admitted')
        return '/demo?document=' + json.loads(response.read())['document']


def ask(stack, path, cookie, scope):
    payload = {'document': path.split('=', 1)[1], 'scope': scope}
    if scope != 'literature':
        payload['documentQuestion'] = DOCUMENT_QUESTION
    if scope != 'document':
        payload['literatureQuestion'] = LITERATURE_QUESTION
    status, body, _ = question_request(stack, cookie, payload=payload)
    require(status == 200 and body['kind'] == 'saved', 'question turn saved')
    return path + '&turn=' + body['id']


def billable_paths(calls):
    return [path for path, _ in calls if path != '/v1/classify']


def verify_normal_flow(fixtures, extra_text):
    limits = {'extract': 2, 'document-answer': 1, 'literature-answer': 2}
    with exercise_profile(fixtures, limits) as (stack, calls):
        path, cookie = open_example(stack)
        with ThreadPoolExecutor(max_workers=4) as pool:
            pages = list(pool.map(lambda _: read_report(stack, path, cookie), range(4)))
        require(all(page.contains('Extraction: completed') for page in pages), 'concurrent owner reports render extraction')
        require(pages[0].contains('Classification used a fitted local model.'), 'classifier result rendered')
        require(billable_paths(calls) == ['/v1/extract'], 'concurrent report extraction is single-flight')

        duplicate, duplicate_cookie = open_example(stack)
        require(path != duplicate, 'duplicate submission has a new app UUID')
        require(read_report(stack, duplicate, duplicate_cookie).contains('The findings and summary are unavailable.'),
                'duplicate source never borrows another session’s cached result')
        require(billable_paths(calls) == ['/v1/extract'], 'duplicate canonical source spends no extraction')
        require(not read_report(stack, path, duplicate_cookie).contains('Extraction: completed'), 'session isolation')

        second = submit(stack, extra_text, cookie)
        require(read_report(stack, second, cookie).contains('Extraction: completed'), 'next source is extracted')
        turn = ask(stack, path, cookie, 'both')
        page = read_report(stack, turn, cookie)
        require(page.answer == ('document', 'partial'), 'live-shaped literature insufficiency preserves document evidence')
        link = page.citations['answer-document-0']
        marked = read_report(stack, link, cookie)
        require(bool(marked.highlights) and marked.mark_start is not None, 'saved answer citation renders exact highlight')
        require(not page.contains('Saved-response replay'), 'bounded profile has its own provenance')
        require(read_report(stack, path, cookie).contains('Extraction: completed'), 'same-owner result stays bound to report')
        expected = ['/v1/extract', '/v1/extract', '/v1/document-answer', '/v1/literature-answer']
        require(billable_paths(calls) == expected, 'reopens and citation navigation spend no calls')
        require(len({digest for path, digest in calls if path == '/v1/extract'}) == 2, 'one extraction for each of two digests')

        overflow = ask(stack, path, cookie, 'document')
        require(read_report(stack, overflow, cookie).answer == ('none', 'unavailable'), 'document answer over limit is denied')
        ask(stack, path, cookie, 'literature')
        require(billable_paths(calls) == expected, 'over-limit request stops remaining work')


def verify_other_limits(fixtures, extra_text):
    for capped in ('extract', 'literature-answer'):
        limits = dict.fromkeys(('extract', 'document-answer', 'literature-answer'), 2)
        limits[capped] = 1
        with exercise_profile(fixtures, limits) as (stack, calls):
            path, cookie = open_example(stack)
            if capped == 'extract':
                read_report(stack, path, cookie)
                second = submit(stack, extra_text, cookie)
                require(read_report(stack, second, cookie).contains('The findings and summary are unavailable.'),
                        'second extraction is denied at the ceiling')
            else:
                require(read_report(stack, ask(stack, path, cookie, 'literature'), cookie).answer == ('none', 'insufficient'),
                        'live-shaped literature insufficiency is accepted')
                require(read_report(stack, ask(stack, path, cookie, 'literature'), cookie).answer == ('none', 'unavailable'),
                        'second literature call is denied at the ceiling')
                # Loading the first saved turn also extracts its report once.
            ask(stack, path, cookie, 'document')
            expected = Counter({'/v1/' + capped: 1})
            if capped == 'literature-answer':
                expected['/v1/extract'] = 1
            require(Counter(billable_paths(calls)) == expected, f'{capped} ceiling and stop enforced')


def verify_first_error(fixtures):
    limits = dict.fromkeys(('extract', 'document-answer', 'literature-answer'), 2)
    with exercise_profile(fixtures, limits, fail='/v1/document-answer') as (stack, calls):
        path, cookie = open_example(stack)
        turn = ask(stack, path, cookie, 'both')
        require(read_report(stack, turn, cookie).answer == ('none', 'unavailable'), 'failed mixed run reports unavailable')
        ask(stack, path, cookie, 'document')
        require(billable_paths(calls) == ['/v1/document-answer'], 'retryable HTTP 503 stops queued and subsequent dispatch')


def verify_receipt_claim():
    with TemporaryDirectory() as folder:
        config = Path(folder) / 'approval.json'
        path = claim_approved_run(config, 'offline-synthetic-run', b'{}')
        initial = path.read_bytes()
        try:
            claim_approved_run(config, 'offline-synthetic-run', b'{}')
        except FileExistsError:
            require(path.read_bytes() == initial, 'startup receipt remains immutable')
        else:
            require(False, 'a second claim of the run must fail')


def verify_unsupported_gap_continues(fixtures, extra_text):
    limits = {'extract': 2, 'document-answer': 1, 'literature-answer': 1}
    with exercise_profile(fixtures, limits, unsupported_literature=True) as (stack, calls):
        path, cookie = open_example(stack)
        require(read_report(stack, path, cookie).contains('Extraction: completed'), 'first source extraction')
        turn = ask(stack, path, cookie, 'literature')
        require(read_report(stack, turn, cookie).answer == ('none', 'unsupported'), 'unsupported state preserved')
        new_path = submit(stack, extra_text, cookie)
        require(read_report(stack, new_path, cookie).contains('Extraction: completed'),
                'unsupported literature must not poison the next source extraction')
        require(billable_paths(calls) == ['/v1/extract', '/v1/literature-answer', '/v1/extract'],
                'gap is counted once and the next unique extraction is dispatched')


def main():
    fixtures = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_bytes())
    source = json.loads((ROOT / 'contracts/v1/fixtures/documents.json').read_bytes())['offset']['text']
    try:
        verify_normal_flow(fixtures, source + '\nThe care team scheduled an English follow-up appointment.')
        print('PASS: two unique sources, one extraction each across concurrent renders, citation visits and duplicate submission.')
        verify_other_limits(fixtures, source + '\nThe care team scheduled an English follow-up appointment.')
        print('PASS: all three HTTP ceilings stop further dispatch before an over-limit call.')
        verify_first_error(fixtures)
        print('PASS: zero retries and no second mixed branch after a retryable HTTP 503. All listeners stopped.')
        verify_receipt_claim()
        print('PASS: a second startup claim is rejected and the first receipt is preserved.')
        verify_unsupported_gap_continues(fixtures, source + '\nThe care team scheduled an English follow-up appointment.')
        print('PASS: an unsupported literature gap remains explicit and the next unique source is extracted.')
    except (AssertionError, KeyError, ValueError, OSError, RuntimeError, MockStartupError) as exc:
        print(f'FAIL: bounded offline evaluation: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
