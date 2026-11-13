"""Generate frozen-schema Python/TypeScript types and runtime packages deterministically."""

from __future__ import annotations
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import textwrap

from check_contracts import ROOT, require_freeze, CheckError
from frozen_contracts import FrozenContracts


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, indent=2) + '\n').encode()


def source_node(path, name, method=None):
    source = path.read_text(encoding='utf-8')
    node = next(n for n in ast.parse(source).body if getattr(n, 'name', '') == name)
    if method:
        node = next(n for n in node.body if getattr(n, 'name', '') == method)
    return textwrap.dedent(ast.get_source_segment(source, node))


def python_runtime():
    base = ROOT / 'scripts/project/check_contracts.py'
    candidate = ROOT / 'scripts/project/check_candidate.py'
    helpers = '\n\n'.join(source_node(base, name) for name in ['pointer', 'at_pointer'])
    first = source_node(base, 'Contracts', 'validate').replace('def validate(', 'def _base_validate(', 1)
    second = source_node(candidate, 'CandidateContracts', 'validate').replace('super().validate(', 'self._base_validate(')
    header = '''# Generated from the canonical schema and shared Python semantic validator sources.
from __future__ import annotations
from contextlib import nullcontext
from dataclasses import dataclass
import hashlib, json, math, re, unicodedata
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

class CheckError(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Issue:
    rule: str
    path: str

offline = nullcontext
def deny_remote(uri):
    raise NoSuchResource(ref=uri)

def rendered(value, fallback):
    return "\\n\\n".join(claim['text'] for claim in value['claims']) if value['claims'] else fallback

'''
    import build_candidate as behavior
    header += 'builder = SimpleNamespace(LABELS=' + repr(behavior.LABELS) + ', NO_ANSWER=' + repr(behavior.NO_ANSWER) + ', NO_SUMMARY=' + repr(behavior.NO_SUMMARY) + ', rendered=rendered)\n\n'
    init = '''class RuntimeValidator:
    def __init__(self):
        self.schema = json.loads(Path(__file__).with_name('schema.json').read_text(encoding='utf-8'))
        self.schema_id = self.schema['$id']
        self.registry = Registry(retrieve=deny_remote).with_resource(self.schema_id, Resource.from_contents(self.schema))

'''
    footer = '''
VALIDATOR = RuntimeValidator()

class ContractValidationError(ValueError):
    def __init__(self, issues):
        self.issues = issues
        super().__init__('Contract validation failed: ' + ', '.join(item.rule + '@' + (item.path or '/') for item in issues))

def validate_record(definition, payload, *, document=None, reference=None):
    issues = VALIDATOR.validate(payload, definition, document, reference)
    if issues:
        raise ContractValidationError(issues)
    return payload

def validate_json(definition, text, *, document=None, reference=None):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('Nonstandard JSON number')
    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Non-finite JSON number')
        return result
    try:
        payload = json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite)
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ContractValidationError([Issue('JSON_INPUT', '')]) from None
    return validate_record(definition, payload, document=document, reference=reference)
'''
    transport = '\n\n' + source_node(candidate, 'request_id') + '\n\n' + source_node(candidate, 'validate_exchange').replace('case, contracts)', 'case, contracts=VALIDATOR)') + '\n'
    return (header + helpers + '\n\n' + init + textwrap.indent(first, '    ') + '\n\n' + textwrap.indent(second, '    ') + '\n' + footer + transport).encode()


def types(schema, language):
    definitions = deepcopy(schema['$defs'])
    inline = {}
    def expr(spec, hint):
        if '$ref' in spec:
            return spec['$ref'].split('/')[-1]
        if 'const' in spec:
            values = [spec['const']]
        elif 'enum' in spec:
            values = spec['enum']
        else:
            values = None
        if values is not None:
            if language == 'py':
                return 'Literal[' + ', '.join(repr(v) for v in values) + ']'
            return ' | '.join(json.dumps(v) for v in values)
        for union in ['anyOf', 'oneOf']:
            if union in spec:
                parts = [expr(child, hint + 'Case' + str(i)) for i, child in enumerate(spec[union], 1)]
                return ('Union[' + ', '.join(parts) + ']') if language == 'py' else '(' + ' | '.join(parts) + ')'
        kind = spec.get('type')
        if isinstance(kind, list):
            return expr({'anyOf': [{'type': k} for k in kind]}, hint)
        if kind == 'array':
            child = expr(spec['items'], hint + 'Item')
            return 'list[' + child + ']' if language == 'py' else '(' + child + ')[]'
        if kind == 'object':
            inline[hint] = spec
            return hint
        mapping = {'string': ('str', 'string'), 'number': ('float', 'number'), 'integer': ('int', 'number'), 'boolean': ('bool', 'boolean'), 'null': ('None', 'null')}
        if kind not in mapping:
            raise CheckError('GENERATOR_SCHEMA: unsupported static type shape')
        return mapping[kind][language == 'ts']
    rows = {}
    queue = list(definitions.items())
    done = set()
    while queue:
        name, spec = queue.pop(0)
        if name in done:
            continue
        done.add(name)
        if spec.get('type') == 'object':
            fields = []
            for key, value in spec['properties'].items():
                annotation = expr(value, name + ''.join(part.title() for part in key.split('_')))
                required = key in spec.get('required', [])
                if language == 'py':
                    fields.append('    ' + key + ': ' + (annotation if required else 'NotRequired[' + annotation + ']'))
                else:
                    fields.append('  ' + key + ('' if required else '?') + ': ' + annotation + ';')
            if language == 'py':
                keys = list(spec['properties'])
                required_fields = [field for key, field in zip(keys, fields) if key in spec.get('required', [])]
                optional_fields = [field for key, field in zip(keys, fields) if key not in spec.get('required', [])]
                if optional_fields:
                    # Class total flags preserve runtime key metadata with postponed annotations.
                    rows[name] = 'class ' + name + 'Required(TypedDict):\n' + '\n'.join(required_fields or ['    pass']) + '\n\nclass ' + name + '(' + name + 'Required, total=False):\n' + '\n'.join(optional_fields) + '\n'
                else:
                    rows[name] = 'class ' + name + '(TypedDict):\n' + '\n'.join(fields) + '\n'
            else:
                rows[name] = 'export interface ' + name + ' {\n' + '\n'.join(fields) + '\n}\n'
        else:
            annotation = expr(spec, name + 'Value')
            rows[name] = name + ': TypeAlias = ' + annotation + '\n' if language == 'py' else 'export type ' + name + ' = ' + annotation + ';\n'
        queue.extend((k, v) for k, v in inline.items() if k not in done)
    if language == 'py':
        objects = [rows[n] for n in rows if rows[n].startswith('class ')]
        aliases = [rows[n] for n in rows if not rows[n].startswith('class ')]
        # Alias unions may refer to aliases declared later; object fields are postponed.
        for i, value in enumerate(aliases):
            if 'Union[' in value:
                aliases[i] = re_forward_alias(value, definitions)
        output = '# Generated; do not edit. Runtime validation is required.\nfrom __future__ import annotations\nfrom typing import TypedDict, NotRequired, Literal, Union, TypeAlias\n\n' + '\n'.join(objects + aliases)
        output += '\nfrom .runtime import validate_record, validate_json, validate_exchange, ContractValidationError, Issue\n'
        return output.encode()
    output = '// Generated; do not edit. Runtime validation is required.\n\n' + '\n'.join(rows.values())
    output += '\nexport interface Records {\n' + '\n'.join('  ' + name + ': ' + name + ';' for name in definitions) + '\n}\n'
    output += '''export interface Issue { rule: string; path: string; }
export interface Context { document?: PreparedDocument; reference?: { attributes?: Record<string, unknown>; spans?: Record<string, unknown> }; }
export function validatePayload<K extends keyof Records>(definition: K, payload: unknown, context?: Context): Promise<Issue[]>;
export function validateRecord<K extends keyof Records>(definition: K, payload: unknown, context?: Context): Promise<Records[K]>;
export function validateJson<K extends keyof Records>(definition: K, text: string, context?: Context): Promise<Records[K]>;
export interface Exchange { request_headers: [string,string][]; response_headers: [string,string][]; status: number; body: unknown; path?: string; disposition: string; }
export function validateExchange(exchange: Exchange): Promise<string[]>;
export class ContractValidationError extends Error { issues: Issue[]; }
'''
    return output.encode()


def re_forward_alias(value, definitions):
    import re
    return re.sub(r'\b(' + '|'.join(definitions) + r')\b', lambda m: repr(m[0]) if m.start() > value.index('=') else m[0], value)


def assets():
    contracts = FrozenContracts()
    require_freeze(contracts)
    schema = contracts.schema
    prefix = 'contracts/generated/'
    py = prefix + 'python/'
    package = py + 'src/notelens_contracts/'
    ts = prefix + 'typescript/'
    outputs = {
        package + 'v1.py': types(schema, 'py'), package + 'runtime.py': python_runtime(),
        package + 'schema.json': (contracts.directory / 'schema.json').read_bytes(),
        package + '__init__.py': b'# Generated package.\nfrom .v1 import *\n', package + 'py.typed': b'',
        py + 'pyproject.toml': b'''# Generated; do not edit.
[build-system]
requires = ["hatchling==1.33.0"]
build-backend = "hatchling.build"
[project]
name = "notelens-contracts"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = ["jsonschema[format-nongpl]==4.26.0", "referencing==0.37.0"]
[tool.hatch.build.targets.wheel]
packages = ["src/notelens_contracts"]
''',
        ts + 'v1.d.ts': types(schema, 'ts'),
        ts + 'v1.mjs': (ROOT / 'contracts/runtime/typescript.mjs').read_bytes(),
        ts + 'schema.json': (contracts.directory / 'schema.json').read_bytes(),
        ts + 'package.json': encoded({'name': '@notelens/contracts', 'version': '1.0.0', 'private': True, 'type': 'module', 'exports': {'./v1': {'types': './v1.d.ts', 'import': './v1.mjs'}}, 'dependencies': {'ajv': '8.20.0', 'ajv-formats': '3.0.1'}, 'devDependencies': {'typescript': '7.0.2'}}),
    }
    inputs = ['scripts/project/generate_contracts.py', 'scripts/project/check_contracts.py', 'scripts/project/check_candidate.py', 'contracts/runtime/typescript.mjs']
    metadata = {'schema_version': '1.0.0', 'schema_sha256': hashlib.sha256(outputs[package + 'schema.json']).hexdigest(), 'freeze_sha256': hashlib.sha256((contracts.directory / 'freeze.json').read_bytes()).hexdigest(), 'inputs_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in inputs}, 'generated_files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(outputs.items())}}
    outputs[prefix + 'manifest.json'] = encoded(metadata)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        outputs = assets()
        for name, data in outputs.items():
            path = ROOT / name
            if args.check:
                if not path.is_file() or path.read_bytes() != data:
                    raise CheckError('GENERATION_DRIFT: ' + name)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        print('PASS: ' + ('reproducible generated bindings match' if args.check else 'generated frozen Python/TypeScript packages'))
        return 0
    except CheckError as error:
        print('FAIL: ' + str(error)); return 1


if __name__ == '__main__':
    sys.exit(main())
