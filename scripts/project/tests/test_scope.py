"""Adversarial scope checks using disposable synthetic Git repositories only."""

import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import check_scope as scope


class Repository:
    def __init__(self):
        folder = scope.ROOT / '.cache/review/f010-tests'
        folder.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=folder)
        self.root = Path(self.temporary.name)
        self.env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 'Synthetic NoteLens fixture', 'GIT_COMMITTER_NAME': 'Synthetic NoteLens fixture',
                    'GIT_AUTHOR_EMAIL': 'fixture@example.invalid', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
        self.git('init', '--quiet')
        self.git('config', 'core.autocrlf', 'false')
        self.write('.gitignore', '.cache/\n')
        self.write(scope.MATRIX, (scope.ROOT / scope.MATRIX).read_bytes())
        self.write(scope.POLICY, (scope.ROOT / scope.POLICY).read_bytes())
        self.base = self.snapshot()

    def git(self, *args, data=None):
        return subprocess.check_output(['git', '-C', str(self.root), *args], input=data,
                                       env=self.env, stderr=subprocess.DEVNULL)

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode('utf-8') if isinstance(data, str) else data)

    def snapshot(self):
        # Synthetic commit objects/refs live only in this disposable repository.
        self.git('add', '-A')
        tree = self.git('write-tree').decode().strip()
        parent = ['-p', self.base] if hasattr(self, 'base') else []
        value = self.git('commit-tree', tree, *parent, '-m', 'Synthetic fixture').decode().strip()
        self.git('update-ref', 'HEAD', value)
        return value

    def close(self):
        self.temporary.cleanup()


def declared(paths, member='B'):
    return scope.declaration(json.dumps({'format': 'notelens-scope-v1', 'member': member,
                                         'task': 'F-010', 'paths': paths}))


class ScopeChecks(unittest.TestCase):
    def setUp(self):
        self.repo = Repository()
        self.addCleanup(self.repo.close)
        self.policy = scope.loads((self.repo.root / scope.POLICY).read_bytes())

    def range(self, paths, member='B'):
        head = self.repo.snapshot()
        return scope.report(self.repo.root, declared(paths, member), self.repo.base, head)

    def test_all_owned_areas_and_annotation_exceptions(self):
        examples = {'services/rag/x.py': 'A', 'data/knowledge/x.json': 'A', 'docs/rag/x.md': 'A',
                    'specs/001-rag/x.md': 'A', 'services/classifier/x.py': 'C', 'data/mtsamples/x.json': 'C',
                    'docs/ml/x.md': 'C', 'specs/003-classification/x.md': 'C', 'services/extraction/x.py': 'D',
                    'docs/extraction-eval/x.md': 'D', 'specs/004-extraction-evaluation/x.md': 'D',
                    'eval/x.json': 'D', 'apps/web/x.ts': 'B', 'contracts/x.json': 'B', 'infra/x.yml': 'B',
                    '.github/x.json': 'B', 'scripts/project/x.py': 'B', 'docs/team/x.md': 'B',
                    'docs/platform/x.md': 'B', 'docs/decisions/x.md': 'B', 'specs/000-foundation/x.md': 'B',
                    'specs/002-platform/x.md': 'B', '.specify/x.json': 'B', '.agents/skills/x.md': 'B',
                    '.codex/shared.json': 'B', 'package-lock.json': 'B', '.env.example': 'B'}
        examples.update({'eval/annotations/member-' + m.lower() + '/review.json': m for m in 'ABCD'})
        for path, member in examples.items():
            with self.subTest(path=path):
                self.assertEqual(member, scope.owner(self.policy, path))

    def test_b_does_not_own_unlisted_root_or_unknown_member_directory(self):
        for path in ('new-root.json', 'docs/unknown/x.md', 'eval/annotations/member-bad/x.json'):
            self.assertNotEqual('B', scope.owner(self.policy, path))

    def test_policy_is_bound_to_the_actual_matrix(self):
        matrix = (self.repo.root / scope.MATRIX).read_bytes()
        for key in ('source_sha256', 'source', 'format'):
            changed = deepcopy(self.policy)
            changed[key] = 'altered'
            with self.subTest(key=key), self.assertRaises(scope.Invalid):
                scope.validate_policy(changed, matrix)
        changed = deepcopy(self.policy)
        changed['rules'][0]['member'] = 'D'
        with self.assertRaises(scope.Invalid):
            scope.validate_policy(changed, matrix)

    def test_single_owner_range_passes_without_claiming_approval(self):
        path = 'docs/team/fixture.md'
        self.repo.write(path, 'Synthetic.')
        result = self.range([path])
        self.assertTrue(result['passed'])
        self.assertFalse(result['identity_verified'])
        self.assertFalse(result['reviewer_approval_verified'])
        self.assertEqual('target-base-policy', result['trust'])

    def test_each_members_own_annotation_passes_other_member_fails(self):
        path = 'eval/annotations/member-a/primary.json'
        self.repo.write(path, '{}')
        head = self.repo.snapshot()
        self.assertTrue(scope.report(self.repo.root, declared([path], 'A'), self.repo.base, head)['passed'])
        for member in 'BCD':
            self.assertFalse(scope.report(self.repo.root, declared([path], member), self.repo.base, head)['passed'])

    def test_undeclared_and_stale_extra_paths_fail(self):
        self.repo.write('docs/team/one.md', 'One')
        self.repo.write('docs/team/two.md', 'Two')
        result = self.range(['docs/team/one.md', 'docs/team/stale.md'])
        self.assertIn({'rule': 'DECLARATION_COVERAGE'}, result['issues'])

    def test_mixed_owner_package_requires_review(self):
        paths = ['apps/web/fixture.ts', 'services/rag/fixture.py']
        for path in paths:
            self.repo.write(path, 'Synthetic')
        result = self.range(paths)
        self.assertFalse(result['passed'])
        self.assertIn({'rule': 'OWNER_REVIEW_REQUIRED', 'path': paths[1], 'owner': 'A'}, result['issues'])

    def test_frozen_files_and_source_prompt_require_separate_approval(self):
        for path in ('contracts/v1/fixture.json', 'contracts/generated/python/fixture.py',
                     'prompts/NoteLens_Codex_SpecKit_prompt_00.md'):
            with self.subTest(path=path):
                changes = [{'path': path, 'old_path': path, 'old_mode': '000000', 'mode': '100644'}]
                self.assertIn({'rule': 'FROZEN_OR_EXPLICIT_APPROVAL', 'path': path},
                              scope.scope_issues(self.policy, declared([path]), changes))

    def test_local_staged_scope_does_not_scan_untracked_drafts_or_modify_index(self):
        path = 'docs/team/fixture.md'
        self.repo.write(path, 'Synthetic')
        self.repo.git('add', '--', path)
        self.repo.write('docs/team/unrelated-draft.md', 'Preserve this draft.')
        index = (self.repo.root / '.git/index').read_bytes()
        result = scope.report(self.repo.root, declared([path]), staged=True, local=True)
        self.assertTrue(result['passed'])
        self.assertEqual([path], result['paths'])
        self.assertEqual(index, (self.repo.root / '.git/index').read_bytes())
        self.assertEqual('local-policy-not-approval', result['trust'])

    def test_empty_index_cannot_pass_as_a_real_scope(self):
        result = scope.report(self.repo.root, declared(['docs/team/fixture.md']), staged=True, local=True)
        self.assertIn({'rule': 'NO_CHANGES'}, result['issues'])

    def test_non_bmp_and_spaced_paths_survive_actual_git_wire(self):
        path = 'docs/team/synthetic \U0001f9ea example.md'
        self.repo.write(path, 'Synthetic')
        result = self.range([path])
        self.assertTrue(result['passed'])
        self.assertEqual([path], result['paths'])

    def test_invalid_and_windows_ambiguous_paths_fail(self):
        for path in ('/absolute', '../escape', 'a/../b', 'a//b', 'a\\b', 'C:/x', './a', 'a\x00b',
                     'a\nb', '.git/config', 'a/*', 'a.', 'a ', 'a/NUL.txt', 'a/COM1', 'a/<x>'):
            with self.subTest(path=repr(path)), self.assertRaises(scope.Invalid):
                scope.safe_path(path)

    def test_declaration_is_strict_and_rejects_self_approval(self):
        value = declared(['docs/team/a.md'])
        for changes in ({'member': 'X'}, {'paths': []}, {'paths': ['docs/team/a.md'] * 2},
                        {'task': 'arbitrary'}, {'approved': True}, {'paths': ['*']}):
            with self.subTest(changes=changes), self.assertRaises((scope.Invalid, TypeError)):
                scope.declaration(json.dumps({**value, **changes}))
        with self.assertRaises(scope.Invalid):
            scope.declaration(json.dumps(value), 'A')

    def test_duplicate_json_keys_and_nonfinite_values_fail(self):
        for raw in ('{"member":"A","member":"B"}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(scope.Invalid):
                scope.loads(raw)

    def test_pr_body_is_data_and_exactly_one_scope_block_is_required(self):
        value = declared(['docs/team/a.md'])
        body = 'Untrusted `$(command)` text.\n```notelens-scope\n' + json.dumps(value) + '\n```\n'
        event = {'pull_request': {'body': body, 'base': {'sha': self.repo.base}, 'head': {'sha': self.repo.base}}}
        self.assertEqual(value, scope.event_declaration(json.dumps(event))[0])
        for invalid in ('', body + body):
            event['pull_request']['body'] = invalid
            with self.assertRaises(scope.Invalid):
                scope.event_declaration(json.dumps(event))

    def test_full_commit_ids_and_history_are_required(self):
        for value in ('HEAD', '--help', self.repo.base[:7], 'f' * 40):
            with self.subTest(value=value), self.assertRaises((scope.Invalid, subprocess.CalledProcessError)):
                scope.commit(self.repo.root, value)

    def test_head_cannot_reassign_ownership_in_its_policy(self):
        changed = deepcopy(self.policy)
        changed['rules'][0]['member'] = 'A'
        self.repo.write(scope.POLICY, json.dumps(changed))
        self.repo.write('apps/web/fixture.ts', 'Synthetic')
        result = self.range([scope.POLICY, 'apps/web/fixture.ts'])
        self.assertFalse(result['passed'])
        self.assertIn({'rule': 'POLICY_CHANGE_REVIEW_REQUIRED'}, result['issues'])
        # It still evaluates B with the trusted base; A cannot grant itself web paths.
        self.assertFalse(scope.report(self.repo.root, declared(result['paths'], 'A'),
                                      self.repo.base, self.repo.snapshot())['passed'])

    def test_missing_base_policy_is_bootstrap_required(self):
        (self.repo.root / scope.POLICY).unlink()
        without_policy = self.repo.snapshot()
        with self.assertRaisesRegex(scope.Invalid, 'BOOTSTRAP_REVIEW_REQUIRED'):
            scope.policy_for(self.repo.root, without_policy)

    def test_rename_and_copy_check_the_source_owner(self):
        source, destination = 'services/rag/a.py', 'apps/web/a.py'
        self.repo.write(source, 'Synthetic source with enough content for detection.\n')
        self.repo.base = self.repo.snapshot()
        self.repo.write(destination, (self.repo.root / source).read_bytes())
        copy = self.range([source, destination])
        self.assertFalse(copy['passed'])
        (self.repo.root / source).unlink()
        rename = self.range([source, destination])
        self.assertFalse(rename['passed'])
        self.assertIn(source, rename['paths'])

    def test_deleted_file_retains_its_owner(self):
        path = 'services/classifier/fixture.py'
        self.repo.write(path, 'Synthetic')
        self.repo.base = self.repo.snapshot()
        (self.repo.root / path).unlink()
        self.assertFalse(self.range([path])['passed'])

    def test_mode_only_changes_are_evaluated(self):
        path = 'docs/team/executable.md'
        self.repo.write(path, 'Synthetic')
        self.repo.base = self.repo.snapshot()
        self.repo.git('update-index', '--chmod=+x', path)
        result = scope.report(self.repo.root, declared([path]), staged=True, local=True)
        self.assertTrue(result['passed'])

    def test_symlink_git_mode_is_rejected_without_following_it(self):
        oid = self.repo.git('hash-object', '-w', '--stdin', data=b'../../outside').decode().strip()
        path = 'docs/team/link'
        self.repo.git('update-index', '--add', '--cacheinfo', '120000,' + oid + ',' + path)
        result = scope.report(self.repo.root, declared([path]), staged=True, local=True)
        self.assertIn({'rule': 'FILE_MODE', 'path': path}, result['issues'])

    def test_submodules_and_case_collisions_fail(self):
        changes = [{'old_path': 'docs/team/A.md', 'path': 'docs/team/a.md',
                    'old_mode': '000000', 'mode': '160000'}]
        issues = scope.scope_issues(self.policy, declared(['docs/team/A.md', 'docs/team/a.md']), changes)
        self.assertIn({'rule': 'PATH_CASE_COLLISION'}, issues)
        self.assertIn({'rule': 'FILE_MODE', 'path': 'docs/team/a.md'}, issues)

    def test_malformed_diff_records_never_pass(self):
        for raw in (b'bad\0a\0', b':100644 100644 ' + b'0' * 40 + b' ' + b'1' * 40 + b' U\0a\0',
                    b':100644 100644 ' + b'0' * 40 + b' ' + b'1' * 40 + b' M\0\xff\0'):
            with self.assertRaises((scope.Invalid, UnicodeError)):
                scope.parse_diff(raw)

    def test_cli_emits_safe_failure_without_leaking_pr_text(self):
        event = self.repo.root / '.cache/event.json'
        event.parent.mkdir()
        event.write_text('{"pull_request":{"body":"synthetic-sensitive-marker"}}')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = scope.main(['--repo', str(self.repo.root), '--event', str(event)])
        self.assertEqual(1, code)
        self.assertNotIn('synthetic-sensitive-marker', output.getvalue())
        self.assertFalse(json.loads((event.parent / 'review/f010/scope-report.json').read_text())['passed'])
