"""Check the built app over HTTP with a loopback fitted-classifier response double."""

from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from threading import Thread
from uuid import UUID, uuid4

from smoke_mock import prepare_example, prepare_submitted_text, read_page, require
from start_mock import FittedClassifier, MockStartupError, ROOT, start_stack


def main():
    payloads = json.loads((ROOT / 'contracts/v1/fixtures/payloads.json').read_text(encoding='utf-8'))
    token = uuid4().hex
    model_version = 'report-check-response-double-v1'
    scenario = 'supported'
    calls = []

    class ClassifierDouble(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            request_id = self.headers.get('X-Request-ID', '')
            try:
                if self.path != '/v1/classify' or self.headers.get('Authorization') != f'Bearer {token}':
                    self.send_error(401)
                    return
                if self.headers.get_content_type() != 'application/json' or str(UUID(request_id)) != request_id:
                    self.send_error(400)
                    return
                request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                document = request['document']
                digest = sha256(document['text'].encode('utf-8')).hexdigest()
                if request['schema_version'] != '1.0.0' or document['text_sha256'] != digest:
                    self.send_error(422)
                    return
                calls.append((document['doc_id'], digest, request_id))
                if scenario == 'unavailable':
                    status = 503
                    payload = {'schema_version': '1.0.0', 'request_id': request_id, 'error': {
                        'code': 'configuration_required', 'retryable': False, 'message': 'Classifier unavailable.',
                    }}
                else:
                    status = 200
                    state = 'supported' if scenario == 'invalid' else scenario
                    payload = {**payloads[f'classification-{state}'], 'mode': 'live',
                               'doc_id': document['doc_id'], 'text_sha256': digest, 'model_version': model_version,
                               'confidence_note': 'Synthetic classifier response for the report check.'}
                    if state == 'supported':
                        payload['category'] = 'Orthopedic'
                        payload['scores'] = [
                            {**score, 'score': 2 if score['category'] == 'Orthopedic' else 0}
                            for score in payload['scores']
                        ]
                    if scenario == 'invalid':
                        payload['text_sha256'] = '0' * 64
                body = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('X-Request-ID', request_id)
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)
            except (KeyError, TypeError, ValueError):
                self.send_error(400)

    try:
        with ThreadingHTTPServer(('127.0.0.1', 0), ClassifierDouble) as service:
            thread = Thread(target=service.serve_forever, kwargs={'poll_interval': 0.05})
            thread.start()
            try:
                target = FittedClassifier(service.server_port, model_version, token)
                with start_stack(fitted_classifier=target) as stack:
                    landing = read_page(stack, '/demo')
                    require(landing.contains('Local classifier profile'), 'explicit classifier profile')
                    _, cookie = prepare_example(stack, landing.example_action)
                    path = prepare_submitted_text(stack, cookie)
                    require(not read_page(stack, path).contains('Classification used a fitted local model.'),
                            'non-owner cannot see the classification')
                    require(not calls, 'non-owner cannot invoke the classifier')

                    for scenario, label in (
                        ('supported', 'Orthopedic'),
                        ('uncertain', 'Specialty uncertain'),
                        ('unavailable', 'The specialty result is unavailable.'),
                        ('invalid', 'The specialty result could not be validated.'),
                    ):
                        view = read_page(stack, path, cookie)
                        require(view.contains(label), f'{scenario} classifier report')
                        require(view.contains('Findings, summaries and answers are mocked'), 'mock provenance')
                        require(not view.contains(token), 'classifier token keeps server-side')
                        if scenario in ('supported', 'uncertain'):
                            require(view.contains('Classification used a fitted local model.'), 'classifier provenance')
                            require(view.contains(model_version), 'classifier version visible')
                        else:
                            require(not view.contains(model_version), 'failed classification is withheld')
                    require(len(calls) == 4 and all(call[0] == path.split('=', 1)[1] for call in calls),
                            'authenticated classifier calls use the owned document')
                    require(len({call[2] for call in calls}) == 4, 'fresh request IDs')
            finally:
                service.shutdown()
                thread.join()
    except (MockStartupError, OSError, RuntimeError) as error:
        print(f'Classifier report check failed: {error}', file=sys.stderr)
        return 1
    print('PASS: report HTTP 200 for supported, uncertain, unavailable and invalid classifier responses. '
          'Classifier responses came from a loopback test double.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
