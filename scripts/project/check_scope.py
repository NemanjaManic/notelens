"""Read-only declared-scope checks; a valid declaration is not reviewer approval."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
POLICY = '.github/scope-policy.json'
MATRIX = 'docs/team/allowed-paths.md'
ROOT_FILES = ('README.md', 'AGENTS.md', 'package.json', 'package-lock.json',
              '.env.example', '.gitignore', '.gitattributes')
SHA = re.compile(r'[0-9a-f]{40}\Z')


class Invalid(ValueError):
    """Only safe rule identifiers, never raw input, belong in diagnostics."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def loads(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(Invalid('JSON_CONSTANT')))


def git(repo, *args):
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'}
    # Respect an explicit temporary index in local staged reviews, never write it.
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env,
                                   stderr=subprocess.DEVNULL, timeout=30)


def commit(repo, value):
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise Invalid('COMMIT_ID')
    if git(repo, 'rev-parse', '--verify', value + '^{commit}').decode().strip() != value:
        raise Invalid('COMMIT_ID')
    return value


def safe_path(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise Invalid('PATH')
    if '\\' in value or ':' in value or any(c in value for c in '*?[]<>"|') or value.startswith('/'):
        raise Invalid('PATH')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) or p.lower() == '.git' for p in value.split('/')):
        raise Invalid('PATH')
    if str(PurePosixPath(value)) != value:
        raise Invalid('PATH')
    if any(p.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *('COM' + str(i) for i in range(1, 10)),
                                      *('LPT' + str(i) for i in range(1, 10))} for p in value.split('/')):
        raise Invalid('PATH')
    return value


def matrix_rules(raw):
    rules = []
    for line in raw.decode('utf-8').splitlines():
        cells = [cell.strip() for cell in line.split('|')]
        if len(cells) < 4 or not re.match(r'^[ABCD](?:,|$)', cells[2]):
            continue
        member = cells[2][0]
        patterns = ROOT_FILES if cells[1].startswith('Root README/AGENTS') else re.findall(r'`([^`]+)`', cells[1])
        for pattern in patterns:
            safe_path(pattern[:-3] if pattern.endswith('/**') else pattern)
            rules.append({'pattern': pattern, 'member': member})
    if {r['member'] for r in rules} != set('ABCD') or len(rules) != 37:
        raise Invalid('MATRIX_COVERAGE')
    return rules


def validate_policy(policy, matrix):
    if not isinstance(policy, dict) or set(policy) != {'format', 'source', 'source_sha256', 'rules'} or \
            policy['format'] != 'notelens-scope-policy-v1' or policy['source'] != MATRIX:
        raise Invalid('POLICY_FORMAT')
    if policy['source_sha256'] != digest(matrix) or policy['rules'] != matrix_rules(matrix):
        raise Invalid('POLICY_MATRIX_DRIFT')
    return policy


def owner(policy, path):
    safe_path(path)
    matches = []
    for rule in policy['rules']:
        pattern = rule['pattern']
        if pattern == path or (pattern.endswith('/**') and path.startswith(pattern[:-2])):
            matches.append((len(pattern.removesuffix('/**')), rule['member']))
    return max(matches)[1] if matches else None


def policy_for(repo, base, local=False):
    if local:
        raw = (repo / POLICY).read_bytes()
        matrix = (repo / MATRIX).read_bytes()
    else:
        try:
            raw = git(repo, 'show', base + ':' + POLICY)
            matrix = git(repo, 'show', base + ':' + MATRIX)
        except subprocess.CalledProcessError as error:
            raise Invalid('BOOTSTRAP_REVIEW_REQUIRED') from error
    return validate_policy(loads(raw), matrix)


def declaration(raw, member=None):
    value = loads(raw)
    if not isinstance(value, dict) or set(value) != {'format', 'member', 'task', 'paths'} or \
            value['format'] != 'notelens-scope-v1' or value['member'] not in tuple('ABCD') or \
            (member is not None and member != value['member']):
        raise Invalid('DECLARATION')
    if not isinstance(value['task'], str) or not re.fullmatch(r'(?:F|[ABCD])-\d{3}', value['task']):
        raise Invalid('TASK_ALIAS')
    paths = value['paths']
    if not isinstance(paths, list) or not paths or len(paths) != len(set(safe_path(p) for p in paths)):
        raise Invalid('DECLARED_PATHS')
    return value


def event_declaration(raw):
    value = loads(raw)
    pr = value['pull_request']
    blocks = re.findall(r'^```notelens-scope\s*\n(.*?)^```\s*$', pr.get('body') or '', re.M | re.S)
    if len(blocks) != 1:
        raise Invalid('PR_DECLARATION')
    return declaration(blocks[0]), pr['base']['sha'], pr['head']['sha']


def parse_diff(raw):
    parts, changes, index = raw.split(b'\0'), [], 0
    while index < len(parts) and parts[index]:
        header = parts[index].decode('ascii').split()
        if len(header) != 5 or not re.fullmatch(r':[0-7]{6}', header[0]) or \
                not re.fullmatch(r'[0-7]{6}', header[1]) or \
                not all(SHA.fullmatch(h) for h in header[2:4]):
            raise Invalid('DIFF_RECORD')
        status = header[4]
        if not re.fullmatch(r'(?:[AMDT]|[RC]\d{1,3})', status):
            raise Invalid('DIFF_STATUS')
        old = safe_path(parts[index + 1].decode('utf-8'))
        new = safe_path(parts[index + 2].decode('utf-8')) if status[0] in 'RC' else old
        changes.append({'status': status, 'old_path': old, 'path': new,
                        'old_mode': header[0][1:], 'mode': header[1],
                        'old_oid': header[2], 'oid': header[3]})
        index += 3 if status[0] in 'RC' else 2
    if index != len(parts) - 1 or (parts and parts[-1] != b''):
        raise Invalid('DIFF_RECORD')
    return changes


def changes_for(repo, base=None, head=None, staged=False):
    if staged:
        anchor = git(repo, 'rev-parse', 'HEAD').decode().strip()
        commit(repo, anchor)
        tail = ['--cached', anchor]
    else:
        commit(repo, base)
        commit(repo, head)
        anchor = git(repo, 'merge-base', base, head).decode().strip()
        tail = [anchor, head]
    raw = git(repo, 'diff', '--raw', '-z', '--abbrev=40', '--no-ext-diff', '--no-textconv',
              '--find-renames', '--find-copies', '--find-copies-harder', *tail, '--')
    return anchor, parse_diff(raw)


def changed_paths(changes):
    return sorted({p for c in changes for p in (c['old_path'], c['path'])})


def scope_issues(policy, declared, changes):
    problems = []
    paths = changed_paths(changes)
    if not changes:
        problems.append({'rule': 'NO_CHANGES'})
    if set(paths) != set(declared['paths']):
        problems.append({'rule': 'DECLARATION_COVERAGE'})
    if len({p.casefold() for p in paths}) != len(paths):
        problems.append({'rule': 'PATH_CASE_COLLISION'})
    for change in changes:
        if any(mode not in ('000000', '100644', '100755') for mode in (change['old_mode'], change['mode'])):
            problems.append({'rule': 'FILE_MODE', 'path': change['path']})
        for path in set((change['old_path'], change['path'])):
            member = owner(policy, path)
            if member is None:
                problems.append({'rule': 'UNMAPPED_PATH', 'path': path})
            elif member != declared['member']:
                problems.append({'rule': 'OWNER_REVIEW_REQUIRED', 'path': path, 'owner': member})
            if path.startswith(('contracts/v1/', 'contracts/generated/')) or path == 'prompts/NoteLens_Codex_SpecKit_prompt_00.md':
                problems.append({'rule': 'FROZEN_OR_EXPLICIT_APPROVAL', 'path': path})
    return problems


def report(repo, declared, base=None, head=None, staged=False, local=False):
    anchor, changes = changes_for(repo, base, head, staged)
    policy = policy_for(repo, base if not staged else anchor, local)
    problems = scope_issues(policy, declared, changes)
    tree_paths = git(repo, 'ls-files', '--cached', '-z') if staged else git(repo, 'ls-tree', '-r', '--name-only', '-z', head)
    names = [safe_path(p.decode('utf-8')) for p in tree_paths.split(b'\0') if p]
    if len({p.casefold() for p in names}) != len(names):
        problems.append({'rule': 'TREE_CASE_COLLISION'})
    if not local and any(p in (POLICY, MATRIX) for p in changed_paths(changes)):
        problems.append({'rule': 'POLICY_CHANGE_REVIEW_REQUIRED'})
    if changes_for(repo, base, head, staged) != (anchor, changes):
        problems.append({'rule': 'SCOPE_SOURCE_DRIFT'})
    return {'format': 'notelens-scope-report-v1', 'passed': not problems,
            'trust': 'local-policy-not-approval' if local else 'target-base-policy',
            'member': declared['member'], 'task': declared['task'], 'base': base or anchor,
            'merge_base': anchor, 'head': head, 'staged': staged,
            'policy_sha256': digest(json.dumps(policy, sort_keys=True).encode()),
            'changes_sha256': digest(json.dumps(changes, sort_keys=True).encode()),
            'paths': changed_paths(changes), 'issues': problems,
            'identity_verified': False, 'reviewer_approval_verified': False}


def save(repo, name, value):
    folder = repo / '.cache/review/f010'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8', newline='\n')


def self_test(pattern):
    sys.path.insert(0, str(ROOT / 'scripts/project/tests'))
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'scripts/project/tests'), pattern=pattern)
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--member', choices=list('ABCD'))
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--base')
    parser.add_argument('--head')
    parser.add_argument('--declaration', type=Path)
    parser.add_argument('--event', type=Path)
    parser.add_argument('--local-policy', action='store_true', help='Explicit local review; never reviewer approval')
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test('test_scope.py')
    repo = args.repo.resolve()
    nonce = str(uuid4())
    save(repo, 'scope-report.json', {'passed': False, 'run_id': nonce, 'issues': [{'rule': 'IN_PROGRESS'}]})
    try:
        if args.event:
            if args.declaration or args.staged or args.base or args.head or args.local_policy:
                parser.error('--event cannot be combined with local/range inputs')
            declared, base, head = event_declaration(args.event.read_bytes())
            if args.member and args.member != declared['member']:
                raise Invalid('DECLARATION')
        else:
            if not args.declaration or (args.staged and (args.base or args.head)) or \
                    (not args.staged and not (args.base and args.head)):
                parser.error('provide a declaration and either --staged or --base/--head')
            declared = declaration(args.declaration.read_bytes(), args.member)
            base, head = args.base, args.head
        result = report(repo, declared, base, head, args.staged, args.local_policy)
    except Invalid as error:
        result = {'format': 'notelens-scope-report-v1', 'passed': False, 'issues': [{'rule': str(error)}]}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError):
        result = {'format': 'notelens-scope-report-v1', 'passed': False, 'issues': [{'rule': 'SCOPE_INPUT_OR_HISTORY'}]}
    result['run_id'] = nonce
    save(repo, 'scope-report.json', result)
    print(('PASS' if result['passed'] else 'FAIL') + ': declared scope; identity/review approval unverified')
    for issue in result['issues']:
        print(json.dumps(issue, ensure_ascii=True))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
