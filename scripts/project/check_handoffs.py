"""Verify the local backlog and member handoff references for F-006."""

from dataclasses import dataclass
from graphlib import CycleError, TopologicalSorter
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]
FOUNDATION = '000-foundation'
MEMBERS = {
    'a': ('001-rag', 'services/rag', 'RetrievalResult', 'answer-literature'),
    'b': ('002-platform', 'apps/web', 'PreparedDocument', 'offset'),
    'c': ('003-classification', 'services/classifier', 'ClassificationResult', 'classification-supported'),
    'd': ('004-extraction-evaluation', 'services/extraction', 'ExtractionResult', 'extraction-valid'),
}
RUNBOOK = 'docs/platform/f-005-mock-startup.md'
RESOLVER = '.specify/scripts/powershell/check-prerequisites.ps1'
MOCK_SCRIPTS = ('start_mock.py', 'smoke_mock.py')
TASK = re.compile(r'^- \[([ xX])\] (T\d{3})(?: \[[^\]\n]+\])* ([A-Z]-\d{3}):[^\n]+$', re.M)
TASK_LINE = re.compile(r'^- \[[^\n\]]*\] T[^\n]*$', re.M)
DEPENDENCY = re.compile(r'(\d{3}-[\w-]+)/(T\d{3}) \(([A-Z]-\d{3})\)')
DEPENDENCIES = re.compile(r'^  - \*\*Dependencies\*\*:\s*([^\n]+)', re.M)
LINK = re.compile(r'\]\(([^)]+)\)')
TABLE_TASK = re.compile(r'^\| ([A-Z]-\d{3}) \| (T\d{3}) \| [^|]+ \| [^|]+ \|$', re.M)
PROMPT_TASK = re.compile(r'^- ([A-Z]-\d{3}) \S', re.M)


class CheckError(ValueError):
    pass


def require(condition, location, message):
    if not condition:
        raise CheckError(f'{location}: {message}')


@dataclass(frozen=True)
class Task:
    alias: str
    done: bool
    dependencies: tuple[tuple[str, str, str], ...]


def load_backlogs(root):
    tasks = {}
    aliases = set()
    features = [(FOUNDATION, 'F'), *((entry[0], member.upper()) for member, entry in MEMBERS.items())]
    for feature, prefix in features:
        path = f'specs/{feature}/tasks.md'
        source = (root / path).read_text(encoding='utf-8')
        matches = list(TASK.finditer(source))
        require(len(matches) >= 5 and len(matches) == len(TASK_LINE.findall(source)),
                path, 'expected well-formed task entries with stable IDs and aliases')
        for index, match in enumerate(matches):
            marker, task_id, alias = match.groups()
            location = f'{path} {task_id}'
            require((feature, task_id) not in tasks, location, 'duplicate task ID')
            require(alias.startswith(prefix + '-') and alias not in aliases, location, 'invalid or duplicate alias')
            end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
            fields = DEPENDENCIES.findall(source[match.end():end])
            require(len(fields) == 1, location, 'expected one Dependencies field')
            dependencies = []
            field = fields[0].strip()
            if field != 'None' and not field.startswith('None;'):
                for item in field.split(';'):
                    ref = DEPENDENCY.fullmatch(item.strip())
                    require(ref is not None, location, 'malformed task dependency')
                    dependencies.append(ref.groups())
            tasks[feature, task_id] = Task(alias, marker.lower() == 'x', tuple(dependencies))
            aliases.add(alias)
    return tasks


def check_dependencies(tasks):
    graph = {}
    references = 0
    for key, task in tasks.items():
        targets = []
        for feature, task_id, alias in task.dependencies:
            target = (feature, task_id)
            require(target in tasks and tasks[target].alias == alias, task.alias,
                    f'unresolved dependency {feature}/{task_id} ({alias})')
            require(target not in targets, task.alias, f'duplicate dependency {alias}')
            targets.append(target)
            references += 1
        graph[key] = targets
    try:
        tuple(TopologicalSorter(graph).static_order())
    except CycleError as error:
        raise CheckError('specs: task dependencies contain a cycle') from error
    return references


def section(source, title, location):
    match = re.search(r'^#{2,3} ' + re.escape(title) + r'\s*\n(.*?)(?=^#{2,3} |\Z)', source, re.M | re.S)
    require(match and match[1].strip(), location, f'missing or empty {title} section')
    return match[1]


def local_target(root, path, target):
    local = urlsplit(target)
    require(not local.scheme and not local.netloc, path, f'expected a local target {target}')
    result = (path.parent / unquote(local.path)).resolve() if local.path else path
    require(result.is_relative_to(root) and result.exists(), path, f'missing or out-of-repo target {target}')
    return result


def check_fixture(root, path, source, fixture, member):
    match = re.search(r'Use `([^`]+)`[^\n]*\[Frozen fixture\]\(([^)]+)\)', source)
    require(match and match[1] == fixture, path, 'missing or wrong frozen fixture reference')
    catalog = local_target(root, path, match[2])
    expected = 'documents.json' if member == 'b' else 'payloads.json'
    require(catalog == root / 'contracts/v1/fixtures' / expected, path, 'fixture link must target the canonical catalog')
    entries = json.loads(catalog.read_text(encoding='utf-8'))
    require(isinstance(entries, dict), path, 'the fixture catalog must be an object')
    record = entries.get(fixture)
    require(isinstance(record, dict), path, 'the named fixture must be an object')
    if member == 'b':
        origin = record.get('source')
        valid = isinstance(origin, dict) and origin.get('kind') == 'synthetic_text'
    else:
        valid = record.get('mode') == 'mock'
    require(valid and record.get('schema_version') == '1.0.0', path, 'fixture is missing or has the wrong version or origin')


def check_member(root, member, config, tasks):
    feature, owned_project, record, fixture = config
    expected = [(task.alias, task_id) for (name, task_id), task in tasks.items() if name == feature][:5]
    handoff = root / f'docs/team/handoffs/member-{member}.md'
    prompt = root / f'docs/team/start-prompts/member-{member}.md'
    docs = {path: path.read_text(encoding='utf-8') for path in (handoff, prompt)}
    for path, source in docs.items():
        targets = {local_target(root, path, target) for target in LINK.findall(source)
                   if not target.startswith(('https://', 'http://'))}
        for line in (f"$env:SPECIFY_FEATURE_DIRECTORY = 'specs/{feature}'",
                     "$env:SPECIFY_FEATURE_NO_PERSIST = '1'", f'& ./{RESOLVER} -PathsOnly -Json'):
            require(line in source.splitlines(), path, 'missing or incorrect PowerShell feature selection')
        for script in MOCK_SCRIPTS:
            command = f'uv run --locked --offline --directory scripts/project python -B {script}'
            require(command in source.splitlines(), path, f'missing locked mock command for {script}')
        has_runbook = root / RUNBOOK in targets if path == handoff else f'`{RUNBOOK}`' in source
        require(has_runbook, path, 'missing mock runbook reference')
        require(owned_project + '/**' in source, path, 'missing owner scope')

    owned = section(docs[handoff], 'Ownership and contracts', handoff)
    require(f'`{record}`' in owned, handoff, 'missing frozen input/output record')
    check_fixture(root, handoff, owned, fixture, member)
    require(TABLE_TASK.findall(section(docs[handoff], 'First five tasks', handoff)) == expected,
            handoff, 'first-five table does not match the feature backlog')
    require('## BEGIN PROMPT' in docs[prompt] and '## END PROMPT' in docs[prompt],
            prompt, 'missing copyable prompt boundaries')
    require(PROMPT_TASK.findall(section(docs[prompt], 'Current tasks', prompt)) == [alias for alias, _ in expected],
            prompt, 'current tasks do not match the first five backlog aliases')

    checks = section(docs[handoff], 'Run the key-free mock', handoff)
    if member == 'b':
        command = 'node apps/web/scripts/check-contracts.mjs'
        require(command in checks.splitlines() and (root / command.removeprefix('node ')).is_file(),
                handoff, 'missing runnable focused web check')
    else:
        prefix = f'uv run --locked --offline --directory {owned_project} python -B -m pytest '
        targets = [target for line in checks.splitlines() if line.startswith(prefix)
                   for target in line.removeprefix(prefix).split()]
        require(targets and all(re.fullmatch(r'tests/test_[a-z0-9_]+\.py', target)
                                and (root / owned_project / target).is_file() for target in targets),
                handoff, 'missing runnable focused service check')


def check_handoffs(root):
    root = root.resolve()
    for path in (RUNBOOK, RESOLVER, *(f'scripts/project/{name}' for name in MOCK_SCRIPTS)):
        require((root / path).is_file(), path, 'required command or runbook is missing')
    tasks = load_backlogs(root)
    require({'F-010', 'F-006'} <= {task.alias for task in tasks.values()},
            FOUNDATION, 'missing F-010 or F-006 backlog entry')
    references = check_dependencies(tasks)
    for member, config in MEMBERS.items():
        check_member(root, member, config, tasks)
    return tasks, references


def main():
    try:
        tasks, references = check_handoffs(ROOT)
    except (OSError, ValueError) as error:
        print(f'FAIL: {error}')
        return 1
    print(f'PASS: five backlogs, {len(tasks)} tasks, {references} dependency references, four handoffs, four start prompts.')
    for alias in ('F-010', 'F-006'):
        task = next(task for task in tasks.values() if task.alias == alias)
        print(f'{alias} backlog status: {"checked" if task.done else "open"}.')
    print('Checked local documentation and references. Runtime evidence and approval are tracked in the backlog.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
