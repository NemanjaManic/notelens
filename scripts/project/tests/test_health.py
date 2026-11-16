"""B checker regressions; fixture results never replace owner HTTP evidence."""

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import check_health as health


class HealthChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = health.contracts()
        cls.payloads = json.loads((health.ROOT / 'contracts/v1/fixtures/payloads.json').read_text())

    def check(self, case, body, headers=None, incoming=None, status=None, secrets=()):
        return health.response_issues(case, status if status is not None else case.status,
                    [('Content-Type', 'application/json')] + (headers or []),
                    json.dumps(body).encode(), incoming or [], self.package, secrets)

    def ready(self, status=200):
        return health.Case('fixture-ready', 'rag', 'open', '/health/ready', status, 'HealthResult')

    def error(self, case=None, incoming=None, headers=None, changes=None):
        case = case or health.Case('fixture-auth', 'rag', 'token', '/health/ready', 401,
                                   'ErrorEnvelope', code='unauthorized', retryable=False)
        diagnostic = '33333333-3333-4333-8333-333333333333'
        value = {'schema_version': '1.0.0', 'request_id': diagnostic,
                 'error': {'code': case.code, 'message': 'Synthetic failure.', 'retryable': False}}
        if changes:
            changes(value)
        return self.check(case, value, headers if headers is not None else [
                          ('X-Request-ID', diagnostic), ('WWW-Authenticate', 'Bearer')], incoming)

    def test_id_free_ready_and_liveness_are_valid(self):
        self.assertEqual([], self.check(self.ready(), self.payloads['health-valid']))
        case = replace(self.ready(), path='/health/live', definition='LivenessResult')
        self.assertEqual([], self.check(case, {**self.payloads['liveness-valid'], 'service': 'rag'}))

    def test_health_ignores_malformed_and_duplicate_incoming_ids(self):
        for incoming in health.IDS.values():
            with self.subTest(incoming=len(incoming)):
                self.assertEqual([], self.check(self.ready(), self.payloads['health-valid'], incoming=incoming))
                self.assertEqual([], self.error(incoming=incoming))

    def test_not_ready_uses_health_result_and_mock_mode(self):
        value = {**self.payloads['health-not-ready'], 'mode': 'mock'}
        self.assertEqual([], self.check(self.ready(503), value))
        self.assertEqual(['MOCK_MODE'], self.check(self.ready(503), self.payloads['health-not-ready']))

    def test_wrong_service_and_live_mode_are_rejected(self):
        self.assertEqual(['SERVICE_IDENTITY'], self.check(self.ready(), {**self.payloads['health-valid'], 'service': 'classifier'}))
        self.assertEqual(['MOCK_MODE'], self.check(self.ready(), {**self.payloads['health-valid'], 'mode': 'live'}))

    def test_wrong_status_or_missing_endpoint_cannot_pass(self):
        self.assertEqual(['HTTP_STATUS'], self.check(self.ready(), self.payloads['health-valid'], status=503))
        self.assertEqual(['MISSING_ENDPOINT'], self.check(self.ready(), {}, status=404))

    def test_health_status_body_mismatch_cannot_pass(self):
        self.assertEqual(['HEALTH_STATUS'], self.check(self.ready(), {**self.payloads['health-not-ready'], 'mode': 'mock'}))
        self.assertEqual(['HEALTH_STATUS'], self.check(self.ready(503), self.payloads['health-valid']))

    def test_success_id_is_optional_but_must_not_echo_or_duplicate(self):
        identity = health.IDS['canonical'][0][1]
        self.assertEqual(['HEALTH_ID_REUSED'], self.check(self.ready(), self.payloads['health-valid'],
            [('X-Request-ID', identity)], health.IDS['canonical']))
        self.assertEqual(['RESPONSE_ID'], self.check(self.ready(), self.payloads['health-valid'],
            [('X-Request-ID', identity), ('X-Request-ID', identity)]))

    def test_auth_error_requires_diagnostic_id_and_challenge(self):
        self.assertEqual(['RESPONSE_ID'], self.error(headers=[('WWW-Authenticate', 'Bearer')]))
        self.assertEqual(['AUTH_CHALLENGE'], self.error(headers=[('X-Request-ID', '33333333-3333-4333-8333-333333333333')]))

    def test_duplicate_challenge_and_reused_id_are_rejected(self):
        headers = [('X-Request-ID', '33333333-3333-4333-8333-333333333333'),
                   ('WWW-Authenticate', 'Bearer'), ('WWW-Authenticate', 'Bearer')]
        self.assertEqual(['AUTH_CHALLENGE'], self.error(headers=headers))
        incoming = [('X-Request-ID', '33333333-3333-4333-8333-333333333333')]
        self.assertEqual(['HEALTH_AUTH_ID_REUSED'], self.error(incoming=incoming))

    def test_auth_correlation_code_and_retryable_rules(self):
        self.assertEqual(['ERROR_CORRELATION'], self.error(changes=lambda v: v.update(request_id=health.IDS['canonical'][0][1])))
        self.assertEqual(['HEALTH_AUTH_ERROR'], self.error(changes=lambda v: v['error'].update(code='internal_error')))
        self.assertEqual(['HEALTH_AUTH_ERROR'], self.error(changes=lambda v: v['error'].update(retryable=True)))

    def test_malformed_json_and_wrong_response_type_are_rejected(self):
        issues = health.response_issues(self.ready(), 200, [('Content-Type', 'application/json')], b'{', [], self.package)
        self.assertEqual(['JSON_INPUT'], issues)
        self.assertTrue(self.check(self.ready(503), {'schema_version': '1.0.0', 'request_id': health.IDS['canonical'][0][1],
                         'error': {'code': 'provider_unavailable', 'message': 'Synthetic.', 'retryable': False}}))

    def test_wrong_content_type_is_rejected(self):
        self.assertEqual(['CONTENT_TYPE'], health.response_issues(self.ready(), 200, [('Content-Type', 'text/html')],
                         json.dumps(self.payloads['health-valid']).encode(), [], self.package))

    def test_sensitive_response_value_is_not_written_to_diagnostics(self):
        marker = 'synthetic-sensitive-marker'
        issues = self.check(self.ready(), {**self.payloads['health-valid'], 'version': marker}, secrets=[marker])
        self.assertEqual(['UNSAFE_ECHO'], issues)
        self.assertNotIn(marker, json.dumps(issues))

    def test_business_admission_and_health_rules_are_distinct(self):
        case = health.Case('business-fixture', 'rag', 'token', '/v1/retrieve', 400, 'ErrorEnvelope',
                           method='POST', code='validation_failure')
        self.assertEqual([], self.error(case=case, headers=[('X-Request-ID', '33333333-3333-4333-8333-333333333333')]))

    def test_owner_retryability_is_not_overridden(self):
        case = health.Case('business-fixture', 'extraction', 'open', '/v1/extract', 504, 'ErrorEnvelope',
                           method='POST', code='timeout', retryable=True)
        self.assertEqual([], self.error(case=case, incoming=health.IDS['canonical'],
             headers=health.IDS['canonical'], changes=lambda v: (v.update(request_id=health.IDS['canonical'][0][1]), v['error'].update(retryable=True))))

    def test_error_envelopes_do_not_require_the_rejected_document_context(self):
        case = health.Case('invalid-document', 'classifier', 'token', '/v1/classify', 422,
                           'ErrorEnvelope', method='POST', code='validation_failure')
        identity = health.IDS['canonical'][0][1]
        raw = json.dumps({'schema_version': '1.0.0', 'request_id': identity,
                          'error': {'code': 'validation_failure', 'message': 'Synthetic.', 'retryable': False}}).encode()
        self.assertEqual([], health.response_issues(case, 422,
            [('Content-Type', 'application/json')] + health.IDS['canonical'], raw,
            health.IDS['canonical'], self.package, document={'text_sha256': 'invalid'}))

    def test_matrix_has_unique_ids_and_explicit_owner_blockers(self):
        cases = health.registry()
        self.assertEqual(210, len(cases))
        self.assertEqual(len(cases), len({c.id for c in cases}))
        self.assertEqual(12, sum(bool(c.blocked) for c in cases))
        self.assertTrue(all(c.profile is None for c in cases if c.blocked))

    def sample_evidence(self):
        cases = [{'id': c.id, 'service': c.service, 'profile': c.profile,
                  'provenance': 'service-http', 'outcome': 'passed'} for c in health.registry()]
        processes = [{'service': service, 'profile': profile, 'pid': index + 1, 'port': 12345,
                      'exited': True, 'port_closed': True, 'contained': True}
                     for index, (service, profile) in enumerate(health.PROFILES)]
        return cases, processes

    def test_even_green_records_cannot_hide_pending_owner_capabilities(self):
        cases, processes = self.sample_evidence()
        self.assertIn('PENDING_OWNER_CAPABILITIES', health.completion_issues(cases, processes))

    def test_missing_duplicate_and_replaced_case_ids_fail(self):
        cases, processes = self.sample_evidence()
        for changed in (cases[:-1], cases + cases[:1], cases[:-1] + cases[:1]):
            self.assertIn('CASE_COVERAGE', health.completion_issues(changed, processes))

    def test_fixtures_and_failed_cases_cannot_be_runtime_passes(self):
        cases, processes = self.sample_evidence()
        cases[0]['provenance'] = 'checker-fixture'
        self.assertIn('INCOMPLETE_CASES', health.completion_issues(cases, processes))
        cases[0]['provenance'] = 'service-http'; cases[0]['outcome'] = 'failed'
        self.assertIn('INCOMPLETE_CASES', health.completion_issues(cases, processes))

    def test_wrong_case_identity_and_partial_process_records_fail(self):
        cases, processes = self.sample_evidence()
        cases[0]['service'] = 'wrong'
        self.assertIn('CASE_IDENTITY', health.completion_issues(cases, processes))
        self.assertIn('PROCESS_COVERAGE', health.completion_issues(cases, processes[:1]))

    def test_unstopped_process_or_invalid_pid_port_fails(self):
        cases, processes = self.sample_evidence()
        for key, value in [('exited', False), ('contained', False), ('port_closed', False), ('pid', True), ('port', None)]:
            with self.subTest(key=key), patch.dict(processes[0], {key: value}):
                self.assertIn('PROCESS_CLEANUP', health.completion_issues(cases, processes))

    def test_complete_supported_matrix_can_pass_aggregation(self):
        case = health.Case('minimal', 'rag', 'open', '/health/live', 200, 'LivenessResult')
        rows = [{'id': 'minimal', 'service': 'rag', 'profile': 'open', 'provenance': 'service-http', 'outcome': 'passed'}]
        process = {'service': 'rag', 'profile': 'open', 'pid': 1, 'port': 12345,
                   'exited': True, 'port_closed': True, 'contained': True}
        with patch.object(health, 'registry', return_value=[case]), patch.object(health, 'PROFILES', (('rag', 'open'),)):
            self.assertEqual([], health.completion_issues(rows, [process]))

    def test_request_headers_preserve_duplicates_without_credentials_in_case_ids(self):
        case = replace(self.ready(), auth='valid-first', request_id='duplicate')
        headers, body, context = health.request_data(case, 'synthetic-test-token', 'synthetic-marker')
        self.assertEqual(2, len(health.headers_named(headers, 'Authorization')))
        self.assertEqual(2, len(health.headers_named(headers, 'X-Request-ID')))
        self.assertIsNone(body)
        self.assertNotIn('synthetic-test-token', case.id)

    def test_environment_scrubs_external_configuration_and_preserves_only_test_profile(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic', 'NOTELENS_RAG_CORPUS_MANIFEST': 'external', 'NODE_OPTIONS': 'external'}):
            env = health.environment(health.CACHE, 'rag', 'open')
        self.assertNotIn('OPENAI_API_KEY', env)
        self.assertNotIn('NOTELENS_RAG_CORPUS_MANIFEST', env)
        self.assertNotIn('NODE_OPTIONS', env)
        self.assertEqual('mock', env['NOTELENS_RAG_MODE'])

    def test_declared_editable_contract_install_is_accepted(self):
        prefix = health.ROOT / 'services/rag/.venv'
        package = health.ROOT / 'contracts/generated/python/src/notelens_contracts'
        source = (health.ROOT / 'contracts/generated/python').resolve().as_uri()
        health.check_runtime_origin('rag', prefix, package, prefix / 'Lib/site-packages', source, True)

    def test_wheel_contract_install_is_accepted_in_its_own_environment(self):
        prefix = health.ROOT / 'services/classifier/.venv'
        source = (health.ROOT / 'contracts/generated/python').resolve().as_uri()
        health.check_runtime_origin('classifier', prefix, prefix / 'Lib/site-packages/notelens_contracts',
                                    prefix / 'Lib/site-packages', source, False)

    def test_borrowed_environment_or_metadata_is_rejected(self):
        prefix = health.ROOT / 'services/rag/.venv'
        package = health.ROOT / 'contracts/generated/python/src/notelens_contracts'
        source = (health.ROOT / 'contracts/generated/python').resolve().as_uri()
        with self.assertRaises(ValueError):
            health.check_runtime_origin('rag', health.ROOT / 'services/classifier/.venv', package,
                                        prefix / 'Lib/site-packages', source, True)
        with self.assertRaises(ValueError):
            health.check_runtime_origin('rag', prefix, package, health.ROOT / 'outside', source, True)

    def test_unreviewed_source_or_false_editable_origin_is_rejected(self):
        prefix = health.ROOT / 'services/rag/.venv'
        package = health.ROOT / 'contracts/generated/python/src/notelens_contracts'
        source = (health.ROOT / 'contracts/generated/python').resolve().as_uri()
        with self.assertRaises(ValueError):
            health.check_runtime_origin('rag', prefix, package, prefix / 'Lib/site-packages', 'https://invalid.example/package', True)
        with self.assertRaises(ValueError):
            health.check_runtime_origin('rag', prefix, health.ROOT / 'outside', prefix / 'Lib/site-packages', source, True)
        with self.assertRaises(ValueError):
            health.check_runtime_origin('rag', prefix, package, prefix / 'Lib/site-packages', source, False)

    def test_live_mode_is_rejected_before_any_worker(self):
        with patch.object(health, 'run_owned') as launch, patch('sys.stderr'):
            with self.assertRaises(SystemExit) as error:
                health.main(['--mode', 'live'])
        self.assertEqual(2, error.exception.code)
        launch.assert_not_called()

    @unittest.skipUnless(os.name == 'nt', 'Windows local process control')
    def test_owned_server_is_stopped_even_when_probe_raises(self):
        folder = health.CACHE / 'self-test-fixtures'
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            ready = Path(temporary) / 'port.txt'
            code = ('import socket,time;from pathlib import Path;'
                    's=socket.socket();s.bind(("127.0.0.1",0));s.listen();'
                    f'Path({str(ready)!r}).write_text(str(s.getsockname()[1]));time.sleep(60)')
            with self.assertRaisesRegex(RuntimeError, 'synthetic'):
                with health.owned_server([sys.executable, '-B', '-c', code], health.ROOT, os.environ.copy()) as (process, capture):
                    deadline = time.monotonic() + 5
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(.02)
                    self.assertTrue(ready.exists())
                    port = int(ready.read_text())
                    self.assertTrue(health.reachable(port))
                    raise RuntimeError('synthetic')
            self.assertIsNotNone(process.poll())
            self.assertTrue(health.closed_port(port))
            self.assertFalse(capture.thread.is_alive())
