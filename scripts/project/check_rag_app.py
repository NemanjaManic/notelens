"""Verify rendered app answers against the pinned key-free indexed RAG service."""

from contextlib import ExitStack
import http.client
import socket
import subprocess
import sys
import time
from urllib.parse import urldefrag

from smoke_mock import DemoPage, ask, prepare_example, read_page, require
from start_mock import ROOT, MockStartupError, get, start_stack


RAG_PIN = 'd2f85fbe97ec451ac3eda52a7b48ff101fc99dc4'
PINNED_PATHS = ('docs/rag', 'services/rag', 'contracts')
PARTIAL_QUESTION = 'What is the synthetic demo topic, and when did it begin?'
MISSING_QUESTION = 'When did the synthetic demo topic begin?'
DOCUMENT_QUESTION = 'What does the document say about chest pain?'
TOPIC_CLAIM = 'The synthetic demo topic is a placeholder used to demonstrate cited answers.'
LITERATURE_URL = 'https://example.invalid/notelens/indexed-demo-topic'
START_DATE_GAP = 'The retrieved sources do not support the requested information: Start date of the synthetic demo topic'
INSUFFICIENT = 'The available sources do not support an answer.'
UNAVAILABLE = 'Literature answer unavailable. Try again.'
DOCUMENT_QUOTE = 'No chest pain.'
DOCUMENT_SPANS = ((7, 21), (47, 61))


class RagPage(DemoPage):
    """Collect answer claims and repeated links without collapsing their labels."""

    def __init__(self, body):
        self.answer_depth = 0
        self.branch = None
        self.in_claims = False
        self.claim_text = None
        self.claims = {'Document': [], 'Literature': []}
        self.document_links = []
        self.in_passage = False
        self.passage_text = ''
        self.mark_start = None
        self.mark_span = None
        super().__init__(body)

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        fields = dict(attrs)
        if tag == 'section' and (self.answer_depth or 'data-answer-route' in fields):
            self.answer_depth += 1
            if self.answer_depth == 2:
                self.branch = fields.get('aria-label')
        if tag == 'ul' and self.answer_depth == 2 and fields.get('class') == 'claims':
            self.in_claims = True
        if self.in_claims and tag == 'p':
            self.claim_text = []
        if self.in_claims and tag == 'a' and self.branch == 'Document':
            self.document_links.append(fields.get('href', ''))
        if tag == 'div' and fields.get('id') == 'document-passage':
            self.in_passage = True
        if tag == 'mark' and self.in_passage:
            self.mark_start = len(self.passage_text)

    def handle_data(self, data):
        super().handle_data(data)
        if self.claim_text is not None:
            self.claim_text.append(data)
        if self.in_passage:
            self.passage_text += data

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag == 'p' and self.claim_text is not None:
            self.claims[self.branch].append(''.join(self.claim_text))
            self.claim_text = None
        if tag == 'ul' and self.in_claims:
            self.in_claims = False
        if tag == 'section' and self.answer_depth:
            if self.answer_depth == 2:
                self.branch = None
            self.answer_depth -= 1
        if tag == 'mark' and self.in_passage:
            self.mark_span = (self.mark_start, len(self.passage_text))
        if tag == 'div' and self.in_passage:
            self.in_passage = False


def verify_rag_pin():
    tracked = subprocess.run(
        ['git', 'diff', '--quiet', '--no-ext-diff', RAG_PIN, '--', *PINNED_PATHS],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    extra = subprocess.run(
        ['git', 'ls-files', '--others', '--exclude-standard', '-z', '--', *PINNED_PATHS],
        cwd=ROOT, capture_output=True, check=False,
    )
    require(tracked.returncode == extra.returncode == 0 and not extra.stdout,
            f'indexed RAG and contract source trees match {RAG_PIN}')


def rendered_answer(stack, href, cookie, expected):
    path, _ = urldefrag(href)
    require(path.startswith('/demo?document='), 'answer stays on the local report')
    status, body = get(stack.web_port, path, {'Cookie': cookie})
    require(status == 200, 'rendered answer HTTP 200')
    page = RagPage(body)
    require(page.answer == expected, f'rendered answer is {expected[0]}/{expected[1]}')
    return page


def check_document_citations(stack, turn, cookie, page):
    require(page.claims['Document'] == [DOCUMENT_QUOTE, DOCUMENT_QUOTE], 'both supported document claims survive')
    require(len(page.document_links) == len(DOCUMENT_SPANS), 'two distinct document source links')
    for index, (href, span) in enumerate(zip(page.document_links, DOCUMENT_SPANS, strict=True)):
        require(href == f'{turn}&evidence=answer-document-{index}#document-passage',
                'citation keeps the document and saved answer identities')
        highlighted = rendered_answer(stack, href, cookie, page.answer)
        start, end = span
        require(highlighted.passage_text == page.passage_text and highlighted.mark_span == span
                and highlighted.passage_text[start:end] == DOCUMENT_QUOTE
                and highlighted.contains(f'code points [{start}, {end})'),
                f'citation {index + 1} highlights the exact canonical occurrence')


def check_mixed_case(stack, path, cookie, notice, other_notice):
    turn = ask(stack, cookie, path, scope='both',
               documentQuestion=DOCUMENT_QUESTION, literatureQuestion=MISSING_QUESTION)
    page = rendered_answer(stack, turn, cookie, ('document', 'partial'))
    require(page.contains(notice) and not page.contains(other_notice), 'mixed answer distinguishes the literature outcome')
    require(not page.claims['Literature'] and 'Literature source URL' not in page.links,
            'mixed answer shows no unsupported literature claim or source')
    check_document_citations(stack, turn, cookie, page)
    return turn


def wait_for_closed_port(name, port):
    deadline = time.monotonic() + 5
    while True:
        remaining = deadline - time.monotonic()
        require(remaining > 0, f'{name} loopback port refused connections')
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=min(3.5, remaining)):
                pass
        except ConnectionRefusedError:
            return
        except TimeoutError:
            pass
        time.sleep(0.05)


def run():
    verify_rag_pin()
    stack = None
    try:
        with ExitStack() as rag_job, start_stack(indexed_rag_job=rag_job) as stack:
            require(get(stack.ports['rag'], '/health/ready')[0] == 401, 'indexed RAG enforces the service token')
            landing = read_page(stack, '/demo')
            path, cookie = prepare_example(stack, landing.example_action)

            baseline_turn = ask(stack, cookie, path, scope='document', documentQuestion=DOCUMENT_QUESTION)
            baseline = rendered_answer(stack, baseline_turn, cookie, ('document', 'sufficient'))
            check_document_citations(stack, baseline_turn, cookie, baseline)

            partial_turn = ask(stack, cookie, path, scope='literature', literatureQuestion=PARTIAL_QUESTION)
            partial = rendered_answer(stack, partial_turn, cookie, ('literature', 'partial'))
            require(partial.claims['Literature'] == [TOPIC_CLAIM] and not partial.claims['Document'],
                    'partial answer renders only the supported literature definition')
            require(partial.links.get('Literature source URL') == LITERATURE_URL
                    and partial.contains('Synthetic demo topic') and partial.contains(START_DATE_GAP),
                    'partial answer renders the indexed literature citation and explicit start-date gap')

            insufficient_turn = check_mixed_case(stack, path, cookie, INSUFFICIENT, UNAVAILABLE)
            rag_job.close()
            require(stack.processes['rag'].poll() is not None, 'owned indexed RAG job stopped')
            wait_for_closed_port('indexed RAG', stack.ports['rag'])
            require(stack.processes['web'].poll() is None and stack.processes['extraction'].poll() is None,
                    'web and document-answer processes stayed up')
            stopped_turn = check_mixed_case(stack, path, cookie, UNAVAILABLE, INSUFFICIENT)
            require(stopped_turn != insufficient_turn, 'outage produces a fresh saved answer')
    finally:
        if stack is not None:
            require(all(process.poll() is not None for process in stack.processes.values()), 'all app check processes stopped')
            for name, port in stack.ports.items():
                wait_for_closed_port(name, port)

    print(f'PASS: indexed RAG pin {RAG_PIN}.')
    print('PASS: partial literature question returned HTTP 200 with the indexed citation and the missing start-date gap.')
    print('PASS: insufficient and stopped RAG kept both document claims and exact citations at [7, 21) and [47, 61).')
    print('PASS: outcomes had distinct notices and all loopback listeners stopped.')


def main():
    try:
        run()
    except MockStartupError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, KeyError, ValueError, http.client.HTTPException, RuntimeError):
        print('Key-free RAG app check could not complete. Check the locked setup and production build.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
