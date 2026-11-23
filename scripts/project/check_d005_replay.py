"""Verify the production app against Milica's private saved D-005 replay."""

import argparse
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from http.client import HTTPConnection, HTTPException
import json
import subprocess
import sys
from uuid import UUID, uuid4
from zipfile import ZipFile

from check_d005_app import read_report, verify_rendered_citations
from d005_replay import D005Replay, OUTPUTS, ReplaySetupError, bind_document_id
from smoke_mock import ask, require, verify_shutdown
from start_mock import MockStartupError, child_environment, start_stack


def pinned_sample(replay):
    python = replay.checkout / 'services/extraction/.venv/Scripts/python.exe'
    command = (
        "import json, sys; "
        "sys.path.insert(0, 'services/extraction/src'); "
        "from notelens_extraction.demo import request; "
        "from notelens_extraction.openai_trial import DEMO_QUESTION; "
        "print(json.dumps(request(DEMO_QUESTION)))"
    )
    return json.loads(subprocess.check_output([str(python), '-B', '-c', command], cwd=replay.checkout,
                                             env=child_environment(), text=True, timeout=15))


def submit(stack, text):
    payload = text.encode('utf-8')
    headers = {'Origin': stack.web_origin, 'Content-Type': 'text/plain; charset=utf-8',
               'X-NoteLens-Input-Scope': 'synthetic'}
    with closing(HTTPConnection('localhost', stack.web_port, timeout=8)) as connection:
        connection.request('POST', '/api/documents/submit', payload, headers)
        reply = connection.getresponse()
        require(reply.status == 201 and reply.getheader('Cache-Control') == 'no-store', 'replay document admission')
        doc_id = json.loads(reply.read())['document']
        cookie = reply.getheader('Set-Cookie', '').split(';', 1)[0]
        require(str(UUID(doc_id)) == doc_id and cookie.startswith('__Host-notelens-session='), 'app document and owner')
    return doc_id, cookie


def request_service(stack, operation, payload, expected_status=200):
    path = '/v1/extract' if operation == 'extract' else '/v1/document-answer'
    request_id = str(uuid4())
    headers = {'Content-Type': 'application/json', 'X-Request-ID': request_id,
               'Authorization': f'Bearer {stack.service_token}'}
    with closing(HTTPConnection('127.0.0.1', stack.ports['extraction'], timeout=8)) as connection:
        connection.request('POST', path, json.dumps(payload).encode('utf-8'), headers)
        reply = connection.getresponse()
        require(reply.status == expected_status and reply.getheader('X-Request-ID') == request_id,
                f'{operation} HTTP {expected_status} with request ID correlation')
        require(reply.getheader('Cache-Control') == 'no-store', 'private service response')
        if expected_status == 200:
            require(reply.getheader('X-Generation-Attempts') == '1', f'{operation} single saved replay')
        return json.loads(reply.read())


def exercise(stack, sample, outputs):
    document = sample['document']
    text = document['text']
    require(sha256(text.encode('utf-8')).hexdigest() == document['text_sha256'], 'reviewed canonical document digest')
    require(read_report(stack, '/demo').contains('D-005 saved-response replay'), 'explicit replay profile label')
    for operation, result in outputs.items():
        request = sample if operation == 'answer' else {k: sample[k] for k in ('schema_version', 'document')}
        require(request_service(stack, operation, request) == result, f'original {operation} result unchanged')
    doc_id, cookie = submit(stack, text)
    require(doc_id != document['doc_id'], 'new app-issued document ID')
    href = f'/demo?document={doc_id}'
    app_document = {**document, 'doc_id': doc_id}
    denied = read_report(stack, href)
    require(not denied.document_parts and denied.contains('The document is unavailable'), 'non-owner receives no report')
    report = read_report(stack, href, cookie)
    require(report.contains('Extraction: completed') and report.contains('Evidence: sufficient'),
            'reviewed findings and summary are rendered')
    extraction = outputs['extract']
    expected = {f'finding-{i}-{n}': (span['start'], span['end'])
                for i, item in enumerate(extraction['items']) for n, span in enumerate(item['evidence'])}
    expected.update({f'summary-{i}': (source['evidence']['start'], source['evidence']['end'])
                     for i, source in enumerate(extraction['summary']['result']['sources'])})
    verify_rendered_citations(stack, href, cookie, report, app_document, expected)

    turn = ask(stack, cookie, href, scope='document', documentQuestion=sample['question'])
    page = read_report(stack, turn, cookie)
    require(page.answer == ('document', 'sufficient') and page.contains('Saved-response replay'),
            'reviewed question accepted and sufficient answer shown')
    answer_sources = {f'answer-document-{i}': (source['evidence']['start'], source['evidence']['end'])
                      for i, source in enumerate(outputs['answer']['sources'])}
    verify_rendered_citations(stack, turn, cookie, page, app_document, {**expected, **answer_sources})

    app_request = {**sample, 'document': app_document}
    review_answer = deepcopy(outputs['answer'])
    bind_document_id(review_answer, document['doc_id'], doc_id)
    require(request_service(stack, 'answer', app_request) == review_answer,
            'answer keeps recorded claims, offsets, and canonical digest with app identity')
    refusal = request_service(stack, 'answer', {**app_request, 'question': 'What is the patient age?'}, 503)
    require(refusal['error']['code'] == 'configuration_required', 'unrecorded question gets no saved answer')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', help='Clean reviewed D-005 checkout')
    parser.add_argument('bundle', help='Private reviewed D-005 v3 ZIP')
    args = parser.parse_args()
    stack = None
    try:
        replay = D005Replay.from_paths(args.checkout, args.bundle)
        sample = pinned_sample(replay)
        with ZipFile(replay.bundle) as archive:
            outputs = {op: json.loads(archive.read(name)) for op, (_, name) in OUTPUTS.items()}
        try:
            with start_stack(d005_replay=replay) as stack:
                exercise(stack, sample, outputs)
        finally:
            if stack:
                verify_shutdown(stack)
    except (MockStartupError, ReplaySetupError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, HTTPException, ValueError, KeyError, subprocess.SubprocessError):
        print('Could not verify the key-free D-005 replay.', file=sys.stderr)
        return 1
    print('PASS: authenticated saved responses, app document identity, findings and summary, '
          'cough admission and answer, exact citations, unmatched question refusal, and loopback shutdown.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
