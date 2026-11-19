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

    def steps(self, workflow):
        return workflow['jobs']['bootstrap-guard']['steps']

    def test_actual_workflow_satisfies_the_supported_policy(self):
        self.assertEqual([], ci.workflow_issues(self.workflow))
        self.assertEqual({'pull_request': {}}, self.workflow['on'])
        self.assertEqual({'contents': 'read'}, self.workflow['permissions'])
        self.assertEqual({'bootstrap-guard'}, set(self.workflow['jobs']))
        self.assertEqual(['Checkout trusted base', 'Checkout candidate', 'Setup Python',
                          'Bootstrap gate', 'Trusted guard'],
                         [step['name'] for step in self.steps(self.workflow)])

    def test_writable_tokens_and_privileged_events_are_rejected(self):
        for key, value, issue in (
                ('permissions', {'contents': 'write'}, 'TOKEN_PERMISSIONS'),
                ('permissions', {'contents': 'read', 'id-token': 'write'}, 'TOKEN_PERMISSIONS'),
                ('on', {'pull_request_target': {}}, 'WORKFLOW_EVENTS'),
                ('on', {'workflow_run': {}}, 'WORKFLOW_EVENTS')):
            with self.subTest(key=key, value=value):
                changed = deepcopy(self.workflow)
                changed[key] = value
                self.assertIn(issue, ci.workflow_issues(changed))

    def test_mutable_action_refs_and_credential_persistence_are_rejected(self):
        for index, action in enumerate(('checkout', 'checkout', 'setup-python')):
            with self.subTest(index=index):
                changed = deepcopy(self.workflow)
                self.steps(changed)[index]['uses'] = 'actions/' + action + '@v6'
                self.assertIn('ACTION_PIN', ci.workflow_issues(changed))
        changed = deepcopy(self.workflow)
        self.steps(changed)[0]['with']['persist-credentials'] = True
        self.assertIn('CHECKOUT_CREDENTIALS_OR_HISTORY', ci.workflow_issues(changed))

    def test_dispatch_health_and_other_jobs_are_excluded(self):
        changed = deepcopy(self.workflow)
        changed['on']['workflow_dispatch'] = {}
        self.assertIn('WORKFLOW_EVENTS', ci.workflow_issues(changed))
        for name in ('health', 'regressions', 'advisories'):
            with self.subTest(name=name):
                changed = deepcopy(self.workflow)
                changed['jobs'][name] = {'steps': []}
                self.assertIn('JOB_COVERAGE', ci.workflow_issues(changed))

    def test_pr_text_and_secrets_cannot_become_shell_source_or_environment(self):
        for addition, issue in (
                ({'run': '${{ github.event.pull_request.title }}'}, 'RUN_POLICY'),
                ({'env': {'TOKEN': '${{ secrets.TOKEN }}'}}, 'STEP_ENV'),
                ({'env': {'EVENT_PATH': '${{ github.event.pull_request.body }}'}}, 'STEP_ENV'),
                ({'env': {}}, 'STEP_ENV')):
            with self.subTest(addition=addition):
                changed = deepcopy(self.workflow)
                self.steps(changed)[4].update(addition)
                self.assertIn(issue, ci.workflow_issues(changed))

    def test_cache_and_arbitrary_action_inputs_are_rejected(self):
        for index, issue in ((0, 'CHECKOUT_TRUST'), (2, 'PYTHON_SETUP')):
            for extra in ({'cache': 'npm'}, {'token': '${{ secrets.KEY }}'}):
                with self.subTest(index=index, extra=extra):
                    changed = deepcopy(self.workflow)
                    self.steps(changed)[index]['with'].update(extra)
                    self.assertIn(issue, ci.workflow_issues(changed))

    def test_early_candidate_execution_installation_and_guard_reordering_are_rejected(self):
        for step in (
                {'name': 'Run candidate', 'shell': 'pwsh', 'run': 'python candidate/code.py'},
                {'name': 'Install', 'shell': 'pwsh', 'run': 'npm ci'}):
            with self.subTest(step=step):
                changed = deepcopy(self.workflow)
                self.steps(changed).insert(0, step)
                self.assertIn('STEP_ORDER_OR_COVERAGE', ci.workflow_issues(changed))
        changed = deepcopy(self.workflow)
        steps = self.steps(changed)
        steps[3], steps[4] = steps[4], steps[3]
        self.assertIn('STEP_ORDER_OR_COVERAGE', ci.workflow_issues(changed))

    def test_each_guard_command_and_failure_check_is_required(self):
        run = self.steps(self.workflow)[4]['run']
        required = [line for line in run.splitlines()
                    if line.startswith(('if ($null', '& python ', 'if ($LASTEXITCODE'))]
        self.assertEqual(7, len(required))
        for line in required:
            with self.subTest(line=line):
                changed = deepcopy(self.workflow)
                self.steps(changed)[4]['run'] = run.replace(line, '', 1)
                self.assertIn('RUN_POLICY', ci.workflow_issues(changed))

    def test_guards_cannot_be_replaced_or_masked(self):
        for index, change, issue in (
                (3, {'run': 'exit 0'}, 'RUN_POLICY'),
                (4, {'run': 'python trusted/scripts/project/check_scope.py --self-test'}, 'RUN_POLICY'),
                (4, {'run': self.steps(self.workflow)[4]['run'] + '\nexit 0'}, 'RUN_POLICY'),
                (4, {'continue-on-error': True}, 'RUN_SHAPE'),
                (4, {'if': 'false'}, 'RUN_SHAPE')):
            with self.subTest(index=index, change=change):
                changed = deepcopy(self.workflow)
                self.steps(changed)[index].update(change)
                self.assertIn(issue, ci.workflow_issues(changed))

    def test_runner_deadline_and_concurrency_are_exact(self):
        for key, value in [('runs-on', 'self-hosted'), ('timeout-minutes', 46),
                           ('timeout-minutes', 45.0), ('timeout-minutes', True)]:
            with self.subTest(key=key, value=value):
                changed = deepcopy(self.workflow)
                changed['jobs']['bootstrap-guard'][key] = value
                self.assertIn('RUNNER_OR_DEADLINE', ci.workflow_issues(changed))
        changed = deepcopy(self.workflow)
        changed['concurrency']['cancel-in-progress'] = 1
        self.assertIn('CONCURRENCY', ci.workflow_issues(changed))

    def test_job_level_permission_or_skip_override_is_rejected(self):
        for key, value in [('permissions', {'contents': 'write'}),
                           ('continue-on-error', True), ('if', 'false')]:
            with self.subTest(key=key):
                changed = deepcopy(self.workflow)
                changed['jobs']['bootstrap-guard'][key] = value
                self.assertIn('JOB_SHAPE', ci.workflow_issues(changed))

    def test_wrong_checkout_refs_and_incomplete_history_fail(self):
        for index, field, value, issue in (
                (0, 'ref', '${{ github.event.pull_request.head.sha }}', 'CHECKOUT_TRUST'),
                (1, 'ref', '${{ github.event.pull_request.head.sha || github.sha }}', 'CHECKOUT_TRUST'),
                (1, 'path', 'trusted', 'CHECKOUT_TRUST'),
                (0, 'fetch-depth', 1, 'CHECKOUT_CREDENTIALS_OR_HISTORY'),
                (1, 'fetch-depth', False, 'CHECKOUT_CREDENTIALS_OR_HISTORY')):
            with self.subTest(index=index, field=field, value=value):
                changed = deepcopy(self.workflow)
                self.steps(changed)[index]['with'][field] = value
                self.assertIn(issue, ci.workflow_issues(changed))

    def test_malformed_or_missing_steps_fail_closed(self):
        for steps, issue in (([], 'STEP_ORDER_OR_COVERAGE'), ([None], 'STEP_SHAPE'),
                             ({}, 'STEP_SHAPE'), (self.steps(self.workflow)[:-1], 'STEP_ORDER_OR_COVERAGE')):
            with self.subTest(issue=issue, steps=len(steps)):
                changed = deepcopy(self.workflow)
                changed['jobs']['bootstrap-guard']['steps'] = steps
                self.assertIn(issue, ci.workflow_issues(changed))

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
