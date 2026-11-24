"""Follow the rendered demo controls against the local stack and verify shutdown."""

import http.client
from html.parser import HTMLParser
import json
import socket
import sys
import time
from urllib.parse import urldefrag

from start_mock import MockStartupError, get, start_stack


class DemoPage(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.links = {}
        self.text = []
        self.highlights = []
        self.answer = None
        self.example_action = None
        self.current_link = None
        self.highlighted = False
        self.ignored_tag = None
        self.feed(body.decode('utf-8'))

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag in ('script', 'style'):
            self.ignored_tag = tag
        if tag == 'a':
            self.current_link = fields.get('href')
        if tag == 'button' and fields.get('id') == 'open-builtin-example' and fields.get('type') == 'button':
            self.example_action = fields.get('data-endpoint')
        if tag == 'mark':
            self.highlighted = True
        if 'data-answer-route' in fields:
            self.answer = (fields['data-answer-route'], fields.get('data-answer-state'))

    def handle_endtag(self, tag):
        if tag == self.ignored_tag:
            self.ignored_tag = None
        if tag == 'a':
            self.current_link = None
        if tag == 'mark':
            self.highlighted = False

    def handle_data(self, data):
        if self.ignored_tag is not None:
            return
        self.text.append(data)
        if self.current_link is not None:
            self.links[data] = self.current_link
        if self.highlighted:
            self.highlights.append(data)

    def contains(self, text):
        return text in ''.join(self.text)


def require(condition, label):
    if not condition:
        raise MockStartupError(f'Mock smoke check failed: {label}.')


def read_page(stack, href, cookie=None):
    path, _ = urldefrag(href)
    require(path.startswith('/demo') and not path.startswith('//'), 'local demo navigation')
    status, body = get(stack.web_port, path, {'Cookie': cookie} if cookie else None)
    require(status == 200, 'web response')
    return DemoPage(body)


def prepare_example(stack, action):
    require(action == '/api/documents/builtin', 'local example button endpoint')
    connection = http.client.HTTPConnection('localhost', stack.web_port, timeout=2)
    try:
        connection.request('POST', action, headers={'Origin': stack.web_origin})
        response = connection.getresponse()
        require(response.status == 303 and response.getheader('Cache-Control') == 'no-store', 'example preparation response')
        location = response.getheader('Location', '')
        cookie = response.getheader('Set-Cookie', '').split(';', 1)[0]
        require(location.startswith('/demo?document=') and cookie.startswith('__Host-notelens-session='), 'prepared report redirect')
        return location, cookie
    finally:
        connection.close()


def prepare_submitted_text(stack, cookie):
    connection = http.client.HTTPConnection('localhost', stack.web_port, timeout=2)
    try:
        body = 'This synthetic medical report describes a scheduled follow-up. No chest pain.'
        connection.request('POST', '/api/documents/submit', body=body, headers={
            'Origin': stack.web_origin, 'Cookie': cookie, 'Content-Type': 'text/plain; charset=utf-8',
            'X-NoteLens-Input-Scope': 'synthetic',
        })
        response = connection.getresponse()
        require(response.status == 201, 'synthetic text preparation')
        return '/demo?document=' + json.loads(response.read())['document']
    finally:
        connection.close()


def question_request(stack, cookie, method='POST', path='/api/questions', payload=None, origin=None):
    connection = http.client.HTTPConnection('localhost', stack.web_port, timeout=8)
    try:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode('utf-8') if payload else None
        headers = {'Origin': origin or stack.web_origin, 'Content-Type': 'application/json'}
        if cookie:
            headers['Cookie'] = cookie
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = response.read()
        require(response.getheader('Cache-Control') == 'no-store', 'question response is no-store')
        return response.status, json.loads(data) if data else None, response.getheader('Retry-After')
    finally:
        connection.close()


def ask(stack, cookie, path, **question):
    status, response, _ = question_request(stack, cookie, payload={'document': path.split('=', 1)[1], **question})
    require(status == 200 and response.get('kind') == 'saved', 'question response stored by opaque ID')
    return path + '&turn=' + response['id']


def exercise(stack, scenario):
    landing = read_page(stack, '/demo')
    require(landing.contains('Mock mode') and landing.contains('does not replace a doctor')
            and landing.contains('Do not upload real personal medical reports'), 'English demo notices')
    path, cookie = prepare_example(stack, landing.example_action)
    denied = read_page(stack, path)
    require(denied.contains('The document is unavailable') and not denied.contains('No chest pain.'), 'non-owner report denied')
    report = read_page(stack, path, cookie)
    require(report.contains('Cardiovascular / Pulmonary') and report.contains('Extraction: completed')
            and report.contains('Document-supported claim') and report.contains('No chest pain.'), 'report results')
    require(report.answer is None, 'answers only after a question is selected')

    doc_question = 'What does the document say about chest pain?'
    lit_question = 'What is the synthetic demo topic?'
    if scenario in ('insufficient', 'provider_unavailable'):
        partial = read_page(stack, ask(stack, cookie, path, scope='both',
                            documentQuestion=doc_question, literatureQuestion=lit_question), cookie)
        literature_gap = ('The available sources do not support an answer.' if scenario == 'insufficient'
                          else 'Literature answer unavailable.')
        require(partial.answer == ('document', 'partial') and 'View document evidence' in partial.links
                and 'Literature source URL' not in partial.links and partial.contains(literature_gap), 'partial mixed answer')
        return

    questions = (
        ({'scope': 'document', 'documentQuestion': doc_question}, 'document', 'sufficient', True, False),
        ({'scope': 'literature', 'literatureQuestion': lit_question}, 'literature', 'sufficient', False, True),
        ({'scope': 'both', 'documentQuestion': doc_question, 'literatureQuestion': lit_question},
         'mixed', 'sufficient', True, True),
        ({'preset': 'insufficient'}, 'none', 'insufficient', False, False),
    )
    saved = []
    for question, route, state, document, literature in questions:
        turn_path = ask(stack, cookie, path, **question)
        saved.append(turn_path)
        answer = read_page(stack, turn_path, cookie)
        require(answer.answer == (route, state), f'{route} answer state')
        require(('View document evidence' in answer.links) == document, f'{route} document citation')
        require(('Literature source URL' in answer.links) == literature, f'{route} literature citation')
        if document:
            evidence = read_page(stack, answer.links['View document evidence'], cookie)
            require(evidence.answer == (route, state) and len(evidence.highlights) == 1
                    and 'chest pain' in evidence.highlights[0].lower()
                    and evidence.contains('code points ['), 'document citation highlight')
        if literature:
            require(answer.contains('Synthetic NoteLens Literature Example')
                    and answer.links['Literature source URL'] == 'https://example.invalid/notelens/synthetic',
                    'literature source attribution')

    partial = read_page(stack, ask(stack, cookie, path, preset='partial-document'), cookie)
    require(partial.answer == ('document', 'partial') and 'View document evidence' in partial.links
            and partial.contains('The document does not provide the requested age.'), 'partial document citation and gap')
    unsupported = read_page(stack, ask(stack, cookie, path, preset='out-of-scope'), cookie)
    require(unsupported.answer == ('none', 'unsupported') and 'View document evidence' not in unsupported.links
            and 'Literature source URL' not in unsupported.links, 'out-of-scope question')

    evicted = read_page(stack, saved[0], cookie)
    require(evicted.answer is None and evicted.contains('no longer in the conversation history'), 'oldest turn evicted')
    unchanged = read_page(stack, path + '&question=mixed', cookie)
    require(unchanged.answer is None, 'legacy GET cannot ask a question')
    unsupported_text = ask(stack, cookie, path, scope='literature',
                           literatureQuestion='What does the published evidence say about this synthetic medical example?')
    answer = read_page(stack, unsupported_text, cookie)
    require(answer.answer == ('none', 'unsupported') and answer.contains('limited set of questions'),
            'honest free-text mock scope')

    submitted_path = prepare_submitted_text(stack, cookie)
    findings_path = ask(stack, cookie, submitted_path, preset='findings')
    findings = read_page(stack, findings_path, cookie)
    require(findings.answer == ('document', 'sufficient') and 'View document evidence' in findings.links
            and 'Literature source URL' not in findings.links, 'submitted document question')
    denied_answer = read_page(stack, findings_path)
    require(denied_answer.answer is None and not denied_answer.contains('No chest pain.'), 'submitted answer owner isolation')

    clear_path = '/api/questions?' + path.split('?', 1)[1]
    document = path.split('=', 1)[1]
    valid = {'document': document, 'scope': 'document', 'documentQuestion': doc_question}
    require(question_request(stack, None, payload=valid)[0] == 404, 'non-owner question denied')
    require(question_request(stack, cookie, payload=valid, origin='http://example.invalid')[0] == 403,
            'cross-origin question denied')
    require(question_request(stack, cookie, payload={**valid, 'documentQuestion': 'Age?'})[0] == 422,
            'inconclusive language asks for longer input')
    require(question_request(stack, cookie, payload={**valid, 'documentQuestion': '😀' * 1001})[0] == 413,
            'excess question rejected')
    require(question_request(stack, cookie, payload=b' ' * (16 * 1024 + 1))[0] == 413, 'excess body rejected')
    require(question_request(stack, cookie, method='DELETE', path=clear_path)[0] == 204, 'owner can clear history')
    require(read_page(stack, unsupported_text, cookie).answer is None and read_page(stack, findings_path, cookie).answer,
            'clear drops saved answer from the selected document only')
    ask(stack, cookie, path, preset='document')
    ask(stack, cookie, path, preset='document')
    status, _, retry = question_request(stack, cookie, payload=valid)
    require(status == 429 and int(retry) > 0, 'rolling session submission limit')


def verify_shutdown(stack):
    require(all(process.poll() is not None for process in stack.processes.values()), 'process shutdown')
    for name, port in stack.ports.items():
        deadline = time.monotonic() + 3
        while True:
            with socket.socket() as probe:
                probe.settimeout(0.25)
                if probe.connect_ex(('127.0.0.1', port)) != 0:
                    break
            require(time.monotonic() < deadline, f'{name} loopback port closed')
            time.sleep(0.05)


def smoke(scenario):
    stack = None
    try:
        with start_stack(rag_scenario=scenario) as stack:
            exercise(stack, scenario)
    finally:
        if stack:
            verify_shutdown(stack)


def main():
    try:
        smoke('sufficient')
        smoke('insufficient')
        smoke('provider_unavailable')
    except (MockStartupError, OSError, KeyError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, MockStartupError) else 'Mock smoke could not complete.', file=sys.stderr)
        return 1
    print('PASS: owner-only mock reports, free-text routing, citations, history, question limits and mock stack shutdown.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
