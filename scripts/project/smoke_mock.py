"""Follow the rendered demo controls against the local stack and verify shutdown."""

from html.parser import HTMLParser
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


def read_page(stack, href):
    path, _ = urldefrag(href)
    require(path.startswith('/demo') and not path.startswith('//'), 'local demo navigation')
    status, body = get(stack.web_port, path)
    require(status == 200, 'web response')
    return DemoPage(body)


def exercise(stack, scenario):
    landing = read_page(stack, '/demo')
    require(landing.contains('Mock mode') and landing.contains('does not replace a doctor')
            and landing.contains('Do not upload real personal medical reports'), 'English demo notices')
    report = read_page(stack, landing.links['Chest pain report'])
    require(report.contains('Cardiovascular / Pulmonary') and report.contains('Extraction: completed')
            and report.contains('Document-supported claim') and report.contains('No chest pain.'), 'report results')
    require(report.answer is None, 'answers only after a question is selected')

    mixed = 'What does the report say about chest pain, and what is the synthetic demo topic?'
    if scenario == 'insufficient':
        partial = read_page(stack, report.links[mixed])
        require(partial.answer == ('document', 'partial') and 'View document evidence' in partial.links
                and 'Literature source URL' not in partial.links
                and partial.contains('The available sources do not support an answer.'), 'partial mixed answer')
        return

    questions = (
        ('What does the document say about chest pain?', 'document', 'sufficient', True, False),
        ('What is the synthetic demo topic?', 'literature', 'sufficient', False, True),
        (mixed, 'mixed', 'sufficient', True, True),
        ("What is the patient's age?", 'none', 'insufficient', False, False),
    )
    for label, route, state, document, literature in questions:
        answer = read_page(stack, report.links[label])
        require(answer.answer == (route, state), f'{route} answer state')
        require(('View document evidence' in answer.links) == document, f'{route} document citation')
        require(('Literature source URL' in answer.links) == literature, f'{route} literature citation')
        if document:
            evidence = read_page(stack, answer.links['View document evidence'])
            require(evidence.answer == (route, state) and len(evidence.highlights) == 1
                    and 'chest pain' in evidence.highlights[0].lower()
                    and evidence.contains('code points ['), 'document citation highlight')
        if literature:
            require(answer.contains('Synthetic NoteLens Literature Example')
                    and answer.links['Literature source URL'] == 'https://example.invalid/notelens/synthetic',
                    'literature source attribution')


def smoke(scenario):
    stack = None
    try:
        with start_stack(rag_scenario=scenario) as stack:
            exercise(stack, scenario)
    finally:
        if stack:
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


def main():
    try:
        smoke('sufficient')
        smoke('insufficient')
    except (MockStartupError, OSError, KeyError, RuntimeError) as exc:
        print(str(exc) if isinstance(exc, MockStartupError) else 'Mock smoke could not complete.', file=sys.stderr)
        return 1
    print('PASS: mock report, four answer routes, citations, partial mixed answer and shutdown of both stacks.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
