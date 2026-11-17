"""Finite CI guard tests; advisories are fixtures, never counted as online scans."""

import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import check_ci as ci
import check_scope as scope
from test_scope import Repository


class CiChecks(unittest.TestCase):
    def setUp(self):
        self.workflow = scope.loads((ci.ROOT / ci.WORKFLOW).read_bytes())

    def test_actual_workflow_satisfies_the_supported_policy(self):
        self.assertEqual([], ci.workflow_issues(self.workflow))
        self.assertEqual('read', self.workflow['permissions']['contents'])

    def test_writable_tokens_and_privileged_events_are_rejected(self):
        for key, value in [('permissions', {'contents': 'write'}),
                           ('on', {'pull_request_target': {}}), ('on', {'workflow_run': {}})]:
            changed = deepcopy(self.workflow)
            changed[key] = value
            self.assertTrue(ci.workflow_issues(changed))

    def test_mutable_action_refs_and_credential_persistence_are_rejected(self):
        for key, value in [('uses', 'actions/checkout@v6'), ('with', {'persist-credentials': True})]:
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions']['steps'][0][key] = value
            self.assertTrue(ci.workflow_issues(changed))

    def test_secret_inputs_and_automatic_health_activation_are_rejected(self):
        changed = deepcopy(self.workflow)
        changed['on']['workflow_dispatch']['inputs']['api_key'] = {'default': '${{ secrets.KEY }}'}
        self.assertTrue(ci.workflow_issues(changed))
        for value in (True, '${{ true }}', "github.event_name == 'pull_request'"):
            changed = deepcopy(self.workflow)
            changed['jobs']['health']['if'] = value
            self.assertIn('HEALTH_OPT_IN', ci.workflow_issues(changed))

    def test_untrusted_pr_text_is_never_shell_source_or_secret_environment(self):
        for addition in ({'run': '${{ github.event.pull_request.title }}'},
                         {'env': {'TOKEN': '${{ secrets.TOKEN }}'}}):
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions']['steps'][5].update(addition)
            self.assertTrue(ci.workflow_issues(changed))

    def test_cache_and_arbitrary_action_inputs_are_rejected(self):
        for extra in ({'cache': 'npm'}, {'token': '${{ secrets.KEY }}'}):
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions']['steps'][3]['with'].update(extra)
            self.assertTrue(ci.workflow_issues(changed))

    def test_early_candidate_execution_and_guard_skips_are_rejected(self):
        changed = deepcopy(self.workflow)
        changed['jobs']['regressions']['steps'].insert(0, {'name': 'Untrusted early step', 'shell': 'pwsh', 'run': 'python candidate/code.py'})
        self.assertIn('STEP_ORDER_OR_COVERAGE', ci.workflow_issues(changed))
        changed = deepcopy(self.workflow)
        changed['jobs']['regressions']['steps'][5]['if'] = 'false'
        self.assertTrue(ci.workflow_issues(changed))

    def test_selftests_or_hidden_success_cannot_replace_the_trusted_scope_guard(self):
        for changed_run in ('python trusted/scripts/project/check_scope.py --self-test',
                            self.workflow['jobs']['regressions']['steps'][5]['run'].replace('--event $env:EVENT_PATH', '--self-test')):
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions']['steps'][5]['run'] = changed_run
            self.assertIn('RUN_POLICY', ci.workflow_issues(changed))

    def test_missing_checks_and_unbounded_or_other_runner_fail(self):
        for key, value in [('runs-on', 'self-hosted'), ('timeout-minutes', 0), ('timeout-minutes', True)]:
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions'][key] = value
            self.assertTrue(ci.workflow_issues(changed))
        changed = deepcopy(self.workflow)
        changed['jobs']['regressions']['steps'].pop(-2)
        self.assertTrue(ci.workflow_issues(changed))

    def test_health_failures_cannot_be_masked_or_replaced_with_counts(self):
        for change in ({'continue-on-error': True}, {'run': 'echo 148 passed; exit 0'},
                       {'run': self.workflow['jobs']['health']['steps'][-1]['run'].replace("throw 'F-011 remains incomplete or failed.'", 'Write-Output incomplete')}):
            changed = deepcopy(self.workflow)
            changed['jobs']['health']['steps'][-1].update(change)
            self.assertTrue(ci.workflow_issues(changed))

    def test_job_level_permission_or_skip_override_is_rejected(self):
        for key, value in [('permissions', {'contents': 'write'}), ('continue-on-error', True), ('if', 'false')]:
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions'][key] = value
            self.assertTrue(ci.workflow_issues(changed))

    def test_wrong_base_checkout_and_incomplete_history_fail(self):
        for field, value in [('ref', '${{ github.event.pull_request.head.sha }}'), ('fetch-depth', 1)]:
            changed = deepcopy(self.workflow)
            changed['jobs']['regressions']['steps'][0]['with'][field] = value
            self.assertTrue(ci.workflow_issues(changed))

    def test_forbidden_secret_names_and_allowed_example_content(self):
        for path in ('.env', '.env.production', 'services/rag/private.pem', '.aws/credentials', 'credentials.json'):
            self.assertTrue(ci.secret_issues(path, b'public-looking-text'))
        self.assertEqual([], ci.secret_issues('.env.example', b'NOTELENS_MODE=mock'))
        self.assertTrue(ci.secret_issues('.env.example', ('sk-' + 'a' * 32).encode()))

    def test_secret_diagnostics_never_include_the_matched_value(self):
        values = [('sk-' + 'a' * 32).encode(), ('ghp_' + 'b' * 36).encode(), ('AIza' + 'z' * 35).encode(),
                  ('AKIA' + 'C' * 16).encode(), ('-----BEGIN ' + 'PRIVATE KEY-----').encode()]
        for raw in values:
            result = ci.secret_issues('docs/team/fixture.md', raw)
            self.assertTrue(result)
            self.assertNotIn(raw.decode(), json.dumps(result))

    def test_removed_secret_in_an_intermediate_commit_is_still_detected(self):
        repo = Repository()
        self.addCleanup(repo.close)
        initial = repo.base
        path = 'docs/team/leak.md'
        repo.write(path, 'sk-' + 'a' * 32)
        repo.base = repo.snapshot()
        (repo.root / path).unlink()
        end = repo.snapshot()
        self.assertTrue(ci.scan_secrets(repo.root, head=None)['passed'])
        result = ci.scan_secrets(repo.root, initial, end)
        self.assertFalse(result['passed'])
        self.assertIn({'rule': 'PROVIDER_TOKEN', 'path': path}, result['issues'])

    def test_staged_secret_scan_preserves_untracked_drafts_and_index(self):
        repo = Repository()
        self.addCleanup(repo.close)
        repo.write('docs/team/draft.md', 'sk-' + 'a' * 32)
        before = (repo.root / '.git/index').read_bytes()
        self.assertTrue(ci.scan_secrets(repo.root, staged=True)['passed'])
        self.assertEqual(before, (repo.root / '.git/index').read_bytes())
        repo.git('add', 'docs/team/draft.md')
        self.assertFalse(ci.scan_secrets(repo.root, staged=True)['passed'])

    def test_environment_scrubs_provider_registry_and_preload_credentials(self):
        examples = {'OPENAI_API_KEY': 'synthetic', 'NPM_TOKEN': 'synthetic', 'NPM_CONFIG_REGISTRY': 'private',
                    'PIP_INDEX_URL': 'synthetic', 'UV_INDEX_URL': 'synthetic', 'NODE_OPTIONS': 'synthetic',
                    'NOTELENS_RAG_CORPUS_MANIFEST': 'synthetic', 'ACTIONS_RUNTIME_TOKEN': 'synthetic'}
        with patch.dict(os.environ, examples):
            env = ci.clean_environment()
        for name in examples:
            self.assertNotIn(name, env)

    def python_report(self, **extra):
        return {'dependencies': [{'name': 'fixture-package', 'version': '1.0', 'vulns': [], **extra}], 'fixes': []}

    def test_python_audit_requires_exact_complete_inventory(self):
        expected = {'fixture-package': '1.0'}
        self.assertEqual([], ci.python_audit_issues(self.python_report(), expected, 0))
        for changed in ({'dependencies': []}, self.python_report(version='2.0'),
                        self.python_report(skip_reason='not on public index'),
                        {'dependencies': self.python_report()['dependencies'] * 2}):
            self.assertTrue(ci.python_audit_issues(changed, expected, 0))

    def test_python_findings_and_advisory_outage_fail_even_with_zero_exit(self):
        expected = {'fixture-package': '1.0'}
        self.assertEqual(['DEPENDENCY_VULNERABILITY'], ci.python_audit_issues(self.python_report(vulns=[{'id': 'SYNTHETIC'}]), expected, 0))
        self.assertEqual(['ADVISORY_QUERY_FAILED'], ci.python_audit_issues(self.python_report(), expected, 1))
        self.assertTrue(ci.python_audit_issues({'error': 'synthetic'}, expected, 1))

    def npm_report(self):
        return {'auditReportVersion': 2, 'vulnerabilities': {}, 'metadata': {
            'vulnerabilities': {k: 0 for k in ('info', 'low', 'moderate', 'high', 'critical', 'total')},
            'dependencies': {'total': 3}}}

    def test_npm_coverage_empty_malformed_and_outage_results_fail(self):
        value = self.npm_report()
        self.assertEqual([], ci.npm_audit_issues(value, 0))
        self.assertEqual(['ADVISORY_QUERY_FAILED'], ci.npm_audit_issues(value, 1))
        for invalid in ({}, {'error': 'synthetic'}, {**value, 'metadata': {}},
                        {**value, 'metadata': {**value['metadata'], 'dependencies': {'total': 0}}}):
            self.assertTrue(ci.npm_audit_issues(invalid, 0))

    def test_npm_advisories_and_invalid_count_types_never_become_green(self):
        for count in (1, -1, True):
            value = self.npm_report()
            value['metadata']['vulnerabilities'].update(high=count, total=count)
            self.assertTrue(ci.npm_audit_issues(value, 0))
        value = self.npm_report()
        value['vulnerabilities']['fixture'] = {'severity': 'high'}
        self.assertEqual(['DEPENDENCY_VULNERABILITY'], ci.npm_audit_issues(value, 0))

    def test_duplicate_and_nonfinite_audit_json_is_rejected(self):
        for raw in ('{"dependencies":[],"dependencies":[]}', '{"total":NaN}'):
            with self.assertRaises(scope.Invalid):
                scope.loads(raw)

    def test_borrowed_interpreter_prefix_and_empty_inventory_fail(self):
        with patch('subprocess.check_output', return_value=b'{"prefix":"outside","packages":[]}'):
            with self.assertRaises(scope.Invalid):
                ci.environment_inventory(Path('fake/.venv/Scripts/python.exe'), ci.ROOT)

    def local_service(self):
        repo = Repository()
        self.addCleanup(repo.close)
        project = repo.root / 'services/rag'
        source = project / 'src/notelens_rag/__init__.py'
        source.parent.mkdir(parents=True)
        source.write_text('"""Synthetic local service."""\n', encoding='utf-8')
        prefix = project / '.venv'
        value = {'name': 'notelens-rag', 'version': '0.1.0', 'prefix': str(prefix),
                 'metadata': str(prefix / 'Lib/site-packages'), 'origin': str(source),
                 'direct': {'url': project.as_uri(), 'dir_info': {'editable': True}}}
        return project, prefix, value

    def test_local_service_requires_exact_declared_editable_origin(self):
        project, prefix, value = self.local_service()
        ci.validate_service_origin(project, prefix, value, '0.1.0')
        for key, wrong in [('prefix', str(project)), ('metadata', str(project)),
                           ('origin', str(project / 'other/__init__.py')), ('version', '0.2.0')]:
            changed = deepcopy(value)
            changed[key] = wrong
            with self.subTest(key=key), self.assertRaises(scope.Invalid):
                ci.validate_service_origin(project, prefix, changed, '0.1.0')

    def test_local_service_wrong_url_is_not_a_public_audit_exemption(self):
        project, prefix, value = self.local_service()
        value['direct']['url'] = project.parent.as_uri()
        with self.assertRaises(scope.Invalid):
            ci.validate_service_origin(project, prefix, value, '0.1.0')

    def test_local_service_wheel_modules_must_match_owner_source(self):
        project, prefix, value = self.local_service()
        installed = prefix / 'Lib/site-packages/notelens_rag/__init__.py'
        installed.parent.mkdir(parents=True)
        installed.write_bytes(Path(value['origin']).read_bytes())
        value['origin'] = str(installed)
        value['direct']['dir_info']['editable'] = False
        ci.validate_service_origin(project, prefix, value, '0.1.0')
        installed.write_text('altered', encoding='utf-8')
        with self.assertRaisesRegex(scope.Invalid, 'LOCAL_SERVICE_SOURCE_DRIFT'):
            ci.validate_service_origin(project, prefix, value, '0.1.0')

    def test_local_service_unexpected_extra_wheel_module_fails(self):
        project, prefix, value = self.local_service()
        installed = prefix / 'Lib/site-packages/notelens_rag/__init__.py'
        installed.parent.mkdir(parents=True)
        installed.write_bytes(Path(value['origin']).read_bytes())
        installed.with_name('extra.py').write_text('unexpected', encoding='utf-8')
        value['origin'] = str(installed)
        value['direct']['dir_info']['editable'] = False
        with self.assertRaises(scope.Invalid):
            ci.validate_service_origin(project, prefix, value, '0.1.0')

    def test_runtime_failure_is_safe_and_cannot_reuse_an_old_success_report(self):
        repo = Repository()
        self.addCleanup(repo.close)
        scope.save(repo.root, 'dependencies.json', {'passed': True})
        with patch.object(ci, 'dependencies', side_effect=OSError('synthetic-sensitive-marker')):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = ci.main(['--repo', str(repo.root), '--dependencies'])
        self.assertEqual(1, code)
        report = (repo.root / '.cache/review/f010/dependencies.json').read_text()
        self.assertNotIn('synthetic-sensitive-marker', report + output.getvalue())
        self.assertFalse(json.loads(report)['passed'])

    def test_live_mode_is_not_a_supported_cli_input(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            ci.main(['--dependencies', '--mode', 'live'])
        self.assertEqual(2, error.exception.code)
