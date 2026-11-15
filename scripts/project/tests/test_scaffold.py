"""Prevent a partial checkout from being reported as a complete foundation."""

import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import unittest
import subprocess
from unittest.mock import patch
from check_scaffold import service_issues, web_issues
from scaffold_state import ROOT, STEPS, HTTP_CASES, HTTP_PROCESSES, sha, encoded, receipt_issues, inventory_issues, source_files, source_fingerprint
from scaffold_process import run_owned


class ScaffoldChecks(unittest.TestCase):
    def test_missing_owner_service_is_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn('missing', service_issues(Path(directory), 'rag')[0])

    def test_presence_alone_does_not_verify_a_service(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / 'services/rag'
            (base / 'src/notelens_rag').mkdir(parents=True)
            (base / 'src/notelens_rag/main.py').write_text('')
            (base / 'uv.lock').write_text('')
            (base / 'pyproject.toml').write_text('[project]\ndependencies=["notelens-contracts==1.0.0"]')
            self.assertIn('runtime verification', service_issues(root, 'rag')[0])

    def test_registry_substitution_and_wrong_workspace_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'apps/web').mkdir(parents=True)
            (root / 'package.json').write_text(json.dumps({'private': True, 'workspaces': ['apps/*']}))
            (root / 'apps/web/package.json').write_text(json.dumps({'dependencies': {'@notelens/contracts': '^1.0.0'}}))
            (root / 'package-lock.json').write_text(json.dumps({'packages': {'node_modules/@notelens/contracts': {'resolved': 'https://registry.example/contracts.tgz'}}}))
            issues = web_issues(root)
            for issue in ('ROOT_WORKSPACES', 'CONTRACT_DEPENDENCY', 'CONTRACT_LOCK_LINK', 'BUILD_NOT_VERIFIED'):
                self.assertIn(issue, issues)

    def test_absent_or_malformed_metadata_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIn('WORKSPACE_METADATA', web_issues(root))
            (root / 'package.json').write_text('[]')
            self.assertIn('WORKSPACE_METADATA', web_issues(root))


class SharedEvidenceChecks(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.cache/scaffold/test-fixtures'
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        cache = self.root / '.cache/scaffold'
        cache.mkdir(parents=True)
        self.facts = {'runtime': 'current candidate'}
        self.receipt = {'format': 'notelens-f004-run-v1', 'candidate': str(self.root.resolve()),
                        'source_fingerprint': 'current sources', 'runtime_fingerprint': sha(encoded(self.facts)),
                        'steps': [{'id': step, 'exit_code': 0} for step in STEPS], 'artifacts': []}
        for step in STEPS:
            self.artifact(f'.cache/scaffold/{step}.log', 'local command output')
        self.http = {'passed': True, 'cases': [{'id': case, 'passed': True} for case in HTTP_CASES],
                     'processes': [{'service': service, 'scenario': scenario, 'pid': index + 1,
                                    'stopped': True, 'port_closed': True}
                                   for index, (service, scenario) in enumerate(HTTP_PROCESSES)]}
        self.artifact('.cache/scaffold/http.json', json.dumps(self.http))
        for service, expected in [('rag', 319), ('classifier', 51), ('extraction', 59)]:
            self.artifact(f'.cache/scaffold/{service}.xml', f'<testsuites><testsuite tests="{expected}" failures="0" errors="0" skipped="0"/></testsuites>')

    def artifact(self, relative, content):
        target = self.root / relative
        target.write_text(content, encoding='utf-8')
        self.receipt['artifacts'] = [item for item in self.receipt['artifacts'] if item['path'] != relative]
        self.receipt['artifacts'].append({'path': relative, 'sha256': sha(target.read_bytes())})

    def issues(self, receipt=None, sources='current sources', facts=None):
        return receipt_issues(self.root, self.receipt if receipt is None else receipt, sources, self.facts if facts is None else facts)

    def test_complete_current_evidence_can_pass(self):
        self.assertEqual([], self.issues())

    def test_present_scaffolds_without_receipt_do_not_pass(self):
        self.assertIn('RECEIPT_INVALID', self.issues({}))

    def test_changed_sources_invalidate_receipt(self):
        self.assertIn('RECEIPT_SOURCE_STALE', self.issues(sources='modified sources'))

    def test_changed_or_borrowed_runtime_invalidates_receipt(self):
        self.assertIn('RECEIPT_RUNTIME_STALE', self.issues(facts={'runtime': 'different candidate'}))

    def test_failed_or_missing_command_cannot_pass(self):
        self.receipt['steps'][0]['exit_code'] = 1
        self.assertIn('RECEIPT_STEPS', self.issues())
        self.receipt['steps'].pop()
        self.assertIn('RECEIPT_STEPS', self.issues())

    def test_tampered_log_or_missing_artifact_cannot_pass(self):
        (self.root / '.cache/scaffold/contracts.log').write_text('replaced')
        self.assertIn('RECEIPT_ARTIFACT', self.issues())
        (self.root / '.cache/scaffold/contracts.log').unlink()
        self.assertIn('RECEIPT_INVALID', self.issues())

    def test_rehashed_incomplete_http_coverage_still_fails(self):
        self.http['cases'].pop()
        self.artifact('.cache/scaffold/http.json', json.dumps(self.http))
        self.assertIn('RECEIPT_HTTP_CASES', self.issues())

    def test_rehashed_skipped_tests_still_fail(self):
        self.artifact('.cache/scaffold/rag.xml', '<testsuites><testsuite tests="319" failures="0" errors="0" skipped="1"/></testsuites>')
        self.assertIn('RECEIPT_TEST_COVERAGE', self.issues())

    def test_unstopped_process_fails(self):
        self.http['processes'][0]['stopped'] = False
        self.artifact('.cache/scaffold/http.json', json.dumps(self.http))
        self.assertIn('RECEIPT_PROCESS_CLEANUP', self.issues())

    def test_rehashed_missing_duplicate_or_substituted_process_records_fail(self):
        original = self.http['processes']
        for records in (original[:1], original[:-1], original + original[:1], original[:-1] + original[:1]):
            with self.subTest(records=len(records)):
                self.http['processes'] = records
                self.artifact('.cache/scaffold/http.json', json.dumps(self.http))
                self.assertIn('RECEIPT_PROCESS_COVERAGE', self.issues())

    def test_process_records_require_positive_pid_and_boolean_cleanup(self):
        record = self.http['processes'][0]
        for key, value in [('pid', 0), ('pid', True), ('stopped', 'true'), ('port_closed', 1)]:
            with self.subTest(key=key, value=value):
                with patch.dict(record, {key: value}):
                    self.artifact('.cache/scaffold/http.json', json.dumps(self.http))
                    self.assertIn('RECEIPT_PROCESS_CLEANUP', self.issues())

    def test_other_candidate_cannot_reuse_receipt(self):
        self.receipt['candidate'] = str(self.root / 'another-candidate')
        self.assertIn('RECEIPT_CONTEXT', self.issues())

    def test_owner_frozen_and_unlisted_source_drift_is_rejected(self):
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.cache/\n')
        frozen = self.root / 'contracts/schema.json'
        frozen.parent.mkdir()
        frozen.write_text('frozen fixture bytes')
        owner = self.root / 'services/rag/main.py'
        owner.parent.mkdir(parents=True)
        owner.write_text('owner fixture bytes')
        manifest_path = self.root / 'scripts/project/scaffold_inputs.json'
        manifest_path.parent.mkdir(parents=True)
        manifest = {'base_files': {'.gitignore': sha((self.root / '.gitignore').read_bytes()), 'contracts/schema.json': sha(frozen.read_bytes())},
                    'imports': {'services/rag/main.py': {'sha256': sha(owner.read_bytes())}},
                    'b_input_files': {}, 'b_editable': [], 'b_additions': ['scripts/project/scaffold_inputs.json']}
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual([], inventory_issues(self.root))
        owner.write_text('altered owner code')
        frozen.write_text('altered frozen bytes')
        (owner.parent / 'unapproved.py').write_text('unexpected file')
        issues = inventory_issues(self.root)
        self.assertIn('OWNER_DRIFT:services/rag/main.py', issues)
        self.assertIn('BASE_DRIFT:contracts/schema.json', issues)
        self.assertIn('UNLISTED_SOURCE:services/rag/unapproved.py', issues)

    def test_generated_next_declaration_output_is_explicit_and_exact(self):
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.cache/\n')
        declaration = self.root / 'apps/web/next-env.d.ts'
        declaration.parent.mkdir(parents=True)
        original = b'import "./.next/dev/types/routes.d.ts";\n'
        declaration.write_bytes(b'import "./.next/types/routes.d.ts";\n')
        manifest_path = self.root / 'scripts/project/scaffold_inputs.json'
        manifest_path.parent.mkdir(parents=True)
        manifest = {'base_files': {'.gitignore': sha((self.root / '.gitignore').read_bytes())},
                    'imports': {}, 'b_input_files': {'apps/web/next-env.d.ts': sha(original)},
                    'b_generated_outputs': {'apps/web/next-env.d.ts': sha(declaration.read_bytes())},
                    'b_editable': [], 'b_additions': ['scripts/project/scaffold_inputs.json']}
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual([], inventory_issues(self.root))
        declaration.write_bytes(b'unexpected generated-file edit')
        self.assertIn('B_INPUT_DRIFT:apps/web/next-env.d.ts', inventory_issues(self.root))
        manifest['b_generated_outputs']['services/rag/main.py'] = 'unapproved'
        manifest_path.write_text(json.dumps(manifest))
        self.assertIn('GENERATED_OUTPUT_SCOPE', inventory_issues(self.root))

    def test_editable_checker_and_test_inputs_must_exist(self):
        actual = source_files(ROOT)
        for name in ('scripts/project/check_scaffold.py', 'scripts/project/tests/test_scaffold.py'):
            with self.subTest(name=name), patch('scaffold_state.source_files', return_value={p: h for p, h in actual.items() if p != name}):
                self.assertIn('MISSING_B_SOURCE:' + name, inventory_issues(ROOT))

    def test_extra_markdown_drafts_are_outside_scope_but_code_is_not(self):
        subprocess.run(['git', 'init', '--quiet', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.cache/\n')
        manifest_path = self.root / 'scripts/project/scaffold_inputs.json'
        manifest_path.parent.mkdir(parents=True)
        pinned = self.root / 'docs/platform/pinned.md'
        pinned.parent.mkdir(parents=True)
        pinned.write_text('approved documentation')
        manifest = {'base_files': {'.gitignore': sha((self.root / '.gitignore').read_bytes()),
                                    'docs/platform/pinned.md': sha(pinned.read_bytes())},
                    'imports': {}, 'b_input_files': {}, 'b_editable': [],
                    'b_additions': ['scripts/project/scaffold_inputs.json']}
        manifest_path.write_text(json.dumps(manifest))
        fingerprint = source_fingerprint(self.root)
        draft = pinned.parent / 'report-workspace-design.md'
        draft.write_text('user draft to preserve')
        self.assertEqual([], inventory_issues(self.root))
        self.assertEqual(fingerprint, source_fingerprint(self.root))
        draft.write_text('independently updated user draft')
        self.assertEqual(fingerprint, source_fingerprint(self.root))
        pinned.write_text('changed pinned documentation')
        self.assertIn('BASE_DRIFT:docs/platform/pinned.md', inventory_issues(self.root))
        extra = pinned.parent / 'unapproved.py'
        extra.write_text('unexpected runtime code')
        self.assertIn('UNLISTED_SOURCE:docs/platform/unapproved.py', inventory_issues(self.root))


@unittest.skipUnless(os.name == 'nt', 'Windows verification containment')
class OwnedProcessChecks(unittest.TestCase):
    def setUp(self):
        parent = ROOT / '.cache/scaffold/test-fixtures'
        parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ready = self.root / 'child.json'
        # A real inert descendant owns a loopback listener, never a service or report.
        child = ('import json,os,socket,time;from pathlib import Path;'
                 's=socket.socket();s.bind(("127.0.0.1",0));s.listen();'
                 f'Path({str(self.ready)!r}).write_text(json.dumps({{"pid":os.getpid(),"port":s.getsockname()[1]}}));'
                 'time.sleep(60)')
        self.parent_command = [sys.executable, '-B', '-c',
                               'import subprocess,sys,time;'
                               f'subprocess.Popen([sys.executable,"-B","-c",{child!r}]);time.sleep(60)']

    def assert_descendant_stopped(self):
        self.assertTrue(self.ready.is_file(), 'Inert descendant must have started for this regression')
        info = json.loads(self.ready.read_text())
        deadline = time.monotonic() + 5
        while True:
            with socket.socket() as client:
                client.settimeout(0.2)
                connected = client.connect_ex(('127.0.0.1', info['port'])) == 0
            if not connected:
                return
            if time.monotonic() >= deadline:
                self.fail('Owned descendant listener survived containment cleanup')
            time.sleep(0.02)

    def test_timeout_stops_descendant_and_preserves_unrelated_process(self):
        unrelated = subprocess.Popen([sys.executable, '-B', '-c', 'import time;time.sleep(60)'])
        try:
            with (self.root / 'timeout.log').open('w') as output:
                with self.assertRaises(subprocess.TimeoutExpired):
                    run_owned(self.parent_command, cwd=ROOT, env=os.environ.copy(), stdout=output, timeout=3)
            self.assert_descendant_stopped()
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.kill()
            unrelated.wait(timeout=5)

    def test_coordinator_termination_stops_its_descendant(self):
        supervisor_code = ('import os,sys;sys.path.insert(0,' + repr(str(ROOT / 'scripts/project')) + ');'
                           'from scaffold_process import run_owned;'
                           f'run_owned({self.parent_command!r},cwd={str(ROOT)!r},env=os.environ.copy(),stdout=sys.stdout,timeout=60)')
        with (self.root / 'interruption.log').open('w') as output:
            supervisor = subprocess.Popen([sys.executable, '-B', '-c', supervisor_code], stdout=output, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while not self.ready.is_file() and supervisor.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(self.ready.is_file(), 'Contained descendant did not start')
            finally:
                if supervisor.poll() is None:
                    supervisor.kill()
                supervisor.wait(timeout=5)
        self.assert_descendant_stopped()

    def test_success_and_failure_keep_the_actual_exit_status(self):
        for status in (0, 7):
            with self.subTest(status=status), (self.root / 'exit.log').open('w') as output:
                result = run_owned([sys.executable, '-B', '-c', f'raise SystemExit({status})'],
                                   cwd=ROOT, env=os.environ.copy(), stdout=output, timeout=10)
                self.assertEqual(status, result.returncode)
