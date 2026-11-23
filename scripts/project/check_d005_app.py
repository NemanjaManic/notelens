"""Check the built app and Milica's pinned D-005 mock over authenticated loopback HTTP."""

import argparse
from contextlib import closing
from hashlib import sha256
from http.client import HTTPConnection, HTTPException
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit, urlunsplit
from uuid import UUID, uuid4

from smoke_mock import DemoPage, ask, prepare_example, require, verify_shutdown
from start_mock import MockStartupError, ROOT, get, start_stack


HANDOFF = 'e61140d3541e4b8b82a8cbd5e3d70e5b78ad0374'
ANSWER_VERSION = 'd-mock-answer-v2'
DOCUMENT_QUESTION = 'What does the document say about chest pain?'
PARTIAL_QUESTION = "What does the document say about chest pain and the patient's age?"
INSUFFICIENT_QUESTION = "What is the patient's age?"
OUT_OF_SCOPE_QUESTION = 'Can NoteLens recommend a treatment?'
AGE_GAP = 'The document does not provide the requested age.'
NO_ANSWER = 'The available sources do not support an answer.'
EVIDENCE_OFFSETS = [(7, 21), (47, 61)]


class ReportPage(DemoPage):
    def __init__(self, body):
        self.document_parts = []
        self.in_document = False
        self.mark_start = None
        self.mark_end = None
        self.citations = {}
        super().__init__(body)

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        fields = dict(attrs)
        if tag == 'div' and fields.get('id') == 'document-passage':
            self.in_document = True
        elif tag == 'mark' and self.in_document:
            self.mark_start = sum(map(len, self.document_parts))
        elif tag == 'a' and fields.get('href'):
            href = fields['href']
            location = urlsplit(href)
            key = parse_qs(location.query).get('evidence', [])
            if location.fragment == 'document-passage' and len(key) == 1:
                require(key[0] not in self.citations, 'each rendered citation has a distinct evidence key')
                self.citations[key[0]] = href

    def handle_endtag(self, tag):
        if self.in_document and tag == 'mark':
            self.mark_end = sum(map(len, self.document_parts))
        if self.in_document and tag == 'div':
            self.in_document = False
        super().handle_endtag(tag)

    def handle_data(self, data):
        if self.in_document and self.ignored_tag is None:
            self.document_parts.append(data)
        super().handle_data(data)


def verify_handoff(root):
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True,
                              capture_output=True, text=True, timeout=10).stdout.strip()

    require(git('rev-parse', 'HEAD') == HANDOFF, 'D-005 uses Milica’s exact handoff commit')
    require(not git('status', '--porcelain=v1', '--untracked-files=all', '--',
                    'services/extraction', 'contracts/generated/python', 'contracts/v1'),
            'pinned extraction source and contracts are clean')
    python = root / 'services/extraction/.venv/Scripts/python.exe'
    require(python.is_file(), 'pinned D-005 has its locked extraction environment')


def read_report(stack, href, cookie=None):
    location = urlsplit(href)
    require(not location.scheme and not location.netloc and location.path == '/demo', 'local report URL')
    request = urlunsplit(('', '', location.path, location.query, ''))
    status, body = get(stack.web_port, request, {'Cookie': cookie} if cookie else None)
    require(status == 200, 'report HTTP 200')
    return ReportPage(body)


def service_request(stack, path, payload):
    request_id = str(uuid4())
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {stack.service_token}',
               'X-Request-ID': request_id}
    with closing(HTTPConnection('127.0.0.1', stack.ports['extraction'], timeout=8)) as connection:
        connection.request('POST', path, json.dumps(payload).encode('utf-8'), headers)
        response = connection.getresponse()
        require(response.status == 200 and response.getheader('X-Request-ID') == request_id,
                'authenticated extraction HTTP 200 and request-ID correlation')
        require(response.getheader('Cache-Control') == 'no-store', 'extraction response is no-store')
        record = json.loads(response.read())
    require(record['schema_version'] == '1.0.0' and record['mode'] == 'mock',
            'D-005 returns the frozen mock contract')
    return record


def verify_identity(record, document):
    require((record['doc_id'], record['text_sha256']) == (document['doc_id'], document['text_sha256']),
            'wire record binds the app-issued document ID and canonical digest')


def verify_span(document, span):
    start, end = span['start'], span['end']
    text = document['text']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text),
            'citation has valid Unicode code-point bounds')
    require(span['quote'] == text[start:end], 'citation quote matches its exact canonical span')
    return start, end


def verify_claims(record, document, expected_offsets):
    sources = record['sources']
    require(len(sources) == len(record['claims']) == len(expected_offsets),
            'one claim and citation for each supported occurrence')
    for claim, source in zip(record['claims'], sources, strict=True):
        verify_identity(source, document)
        require(source['kind'] == 'document' and claim['source_ids'] == [source['source_id']],
                'claim links to its corresponding document source')
        require(claim['text'] == source['evidence']['quote'], 'literal mock claim matches source quote')
    require([verify_span(document, source['evidence']) for source in sources] == expected_offsets,
            'claim citations preserve the intended distinct occurrences')


def verify_rendered_citations(stack, href, cookie, page, document, expected):
    require(page.citations.keys() == expected.keys(), 'rendered citation keys match expected sources')
    turn = parse_qs(urlsplit(href).query).get('turn')
    for key, (start, end) in expected.items():
        citation_url = page.citations[key]
        params = parse_qs(urlsplit(citation_url).query)
        require(params.get('document') == [document['doc_id']] and params.get('turn') == turn,
                'citation points to the same document and selected answer')
        cited = read_report(stack, citation_url, cookie)
        require(''.join(cited.document_parts) == document['text'], 'citation preserves canonical document text')
        require((cited.mark_start, cited.mark_end) == (start, end) and
                ''.join(cited.highlights) == document['text'][start:end] and
                cited.contains(f'code points [{start}, {end})'),
                'rendered highlight marks the exact Unicode occurrence')


def exercise(stack):
    landing = read_report(stack, '/demo')
    url, cookie = prepare_example(stack, landing.example_action)
    document_id, = parse_qs(urlsplit(url).query)['document']
    fixture = json.loads((ROOT / 'contracts/v1/fixtures/documents.json').read_text(encoding='utf-8'))['offset']
    require(str(UUID(document_id)) == document_id and document_id != fixture['doc_id'],
            'web preparation issues a new canonical UUID')
    canonical = fixture['text']
    document = dict(fixture, doc_id=document_id, text_sha256=sha256(canonical.encode('utf-8')).hexdigest())
    require(document['text_sha256'] == fixture['text_sha256'], 'canonical text matches the frozen synthetic fixture digest')
    request = {'schema_version': '1.0.0', 'document': document}
    extraction = service_request(stack, '/v1/extract', request)
    verify_identity(extraction, document)
    require(extraction['extraction_status'] == 'completed' and extraction['summary']['status'] == 'completed',
            'pinned extraction and independent summary complete')
    items = extraction['items']
    require(len(items) == 2 and all(i['type'] == 'symptom' and i['assertion'] == 'negated' for i in items),
            'both repeated negated findings are present')
    require([verify_span(document, item['mention']) for item in items] == [(10, 20), (50, 60)],
            'mention locations distinguish both occurrences')
    require(all(len(item['evidence']) == 1 for item in items), 'one evidence span per repeated finding')
    require([verify_span(document, item['evidence'][0]) for item in items] == EVIDENCE_OFFSETS,
            'finding evidence matches exact code-point intervals')
    summary = extraction['summary']['result']
    require(summary['evidence_state'] == 'sufficient', 'summary has sufficient document evidence')
    verify_claims(summary, document, EVIDENCE_OFFSETS)

    report = read_report(stack, url, cookie)
    require(report.contains('Extraction: completed') and report.contains('Evidence: sufficient') and
            report.contains('Document-supported claim'), 'web report renders findings and summary')
    report_citations = {f'finding-{i}-0': bounds for i, bounds in enumerate(EVIDENCE_OFFSETS)}
    report_citations.update({f'summary-{i}': bounds for i, bounds in enumerate(EVIDENCE_OFFSETS)})
    verify_rendered_citations(stack, url, cookie, report, document, report_citations)

    cases = (
        (DOCUMENT_QUESTION, 'document', 'document', 'sufficient', None),
        (PARTIAL_QUESTION, 'partial-document', 'document', 'partial', AGE_GAP),
        (INSUFFICIENT_QUESTION, 'insufficient', 'none', 'insufficient', AGE_GAP),
        (OUT_OF_SCOPE_QUESTION, 'out-of-scope', 'none', 'insufficient', None),
    )
    for question, preset, route, state, gap in cases:
        answer = service_request(stack, '/v1/document-answer', {**request, 'question': question})
        require(answer['answer_version'] == ANSWER_VERSION and
                (answer['route'], answer['evidence_state']) == (route, state),
                'pinned document-answer route and evidence state')
        offsets = EVIDENCE_OFFSETS if route == 'document' else []
        verify_claims(answer, document, offsets)
        if not offsets:
            require(answer['text'] == NO_ANSWER and answer['prompt_version'] is None,
                    'unsupported or insufficient wire answer abstains without claims')
        if gap:
            require(gap in answer['warnings'], 'wire answer preserves the age gap')

        turn = ask(stack, cookie, url, preset=preset)
        page = read_report(stack, turn, cookie)
        web_state = 'unsupported' if preset == 'out-of-scope' else state
        require(page.answer == (route, web_state), 'rendered answer distinguishes each evidence state')
        if gap:
            require(page.contains(gap), 'rendered answer displays the explicit age gap')
        if web_state == 'insufficient':
            require(page.contains(NO_ANSWER), 'rendered insufficient answer abstains')
        if web_state == 'unsupported':
            require(page.contains('Question outside demo scope'), 'rendered out-of-scope question is unsupported')
        report_keys = {**report_citations,
                       **{f'answer-document-{i}': bounds for i, bounds in enumerate(offsets)}}
        verify_rendered_citations(stack, turn, cookie, page, document, report_keys)

    denied = read_report(stack, url)
    require(denied.contains('The document is unavailable') and not denied.document_parts and not denied.citations,
            'an unauthenticated browser cannot read the prepared document or its citations')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('handoff_checkout', type=Path, help='Separate checkout of the pinned D-005 handoff')
    root = parser.parse_args().handoff_checkout.resolve()
    stack = None
    exit_code = 0
    try:
        verify_handoff(root)
        with start_stack(extraction_root=root) as stack:
            exercise(stack)
    except MockStartupError as exc:
        print(str(exc), file=sys.stderr)
        exit_code = 1
    except (OSError, HTTPException, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        print('D-005 app HTTP check failed while reading the pinned checkout or an HTTP response.', file=sys.stderr)
        exit_code = 1
    finally:
        if stack:
            try:
                verify_shutdown(stack)
            except (MockStartupError, OSError):
                print('D-005 app HTTP check could not verify listener shutdown.', file=sys.stderr)
                exit_code = 1
    if exit_code == 0:
        print('PASS: pinned D-005 mock extraction and summary, document identity and exact Unicode citations, '
              'sufficient/partial/insufficient/unsupported outcomes, owner isolation and loopback shutdown.')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
