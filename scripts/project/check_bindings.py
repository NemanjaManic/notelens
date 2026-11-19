"""Run shared payload cases against the independently installed generated Python package."""
from pathlib import Path
import json
import sys

from notelens_contracts.v1 import PreparedDocument, ClassificationRequest, ClassificationResult, ErrorDetail, ErrorEnvelope, LivenessResult, HealthResult
from notelens_contracts.v1 import validate_record, validate_json, validate_exchange, ContractValidationError

ROOT = Path(__file__).resolve().parents[2]
directory = ROOT / 'contracts/v1/fixtures'
read = lambda name: json.loads((directory / name).read_text(encoding='utf-8'))
cases, payloads, documents, references = read('manifest.json')['cases'], read('payloads.json'), read('documents.json'), read('references.json')
total = 0
for case in cases:
    if case['kind'] != 'payload':
        continue
    context = {}
    if 'document' in case: context['document'] = documents[case['document']]
    if 'reference' in case: context['reference'] = references[case['reference']]
    try:
        validate_record(case['definition'], payloads[case['id']], **context)
        actual = []
    except ContractValidationError as error:
        actual = [{'rule': item.rule, 'path': item.path} for item in error.issues]
    if actual != case['expected']:
        print('FAIL:', case['id'], actual, case['expected']); sys.exit(1)
    total += 1
for fixture in ['classification-supported', 'classification-probability']:
    for number in [float('nan'), float('inf'), float('-inf')]:
        value = json.loads(json.dumps(payloads[fixture])); value['scores'][0]['score'] = number
        try: validate_record('ClassificationResult', value)
        except ContractValidationError as error:
            assert error.issues[0].rule == 'NUMBER_FINITE'
        else: raise AssertionError('Non-finite native score accepted')
for text in ['{"a":1,"a":2}', '{"score":NaN}', '{"score":1e999}']:
    try: validate_json('ClassificationScore', text)
    except ContractValidationError as error: assert error.issues[0].rule == 'JSON_INPUT'
    else: raise AssertionError('Invalid JSON input accepted')
for fixture,numbers in [('classification-supported',[-1e300,0.0,1e300]),('classification-probability',[0.0,1.0])]:
    for number in numbers:
        value=json.loads(json.dumps(payloads[fixture]));value['scores'][0]['score']=number
        validate_record('ClassificationResult',value)
transport=read('transport-cases.json')['cases']
for case in transport:
    assert validate_exchange(case)==case['expected'],case['id']
from typing import get_type_hints,is_typeddict
import notelens_contracts.v1 as models
schema=__import__('notelens_contracts.runtime',fromlist=['VALIDATOR']).VALIDATOR.schema
for name in schema['$defs']:
    binding=getattr(models,name)
    if is_typeddict(binding): get_type_hints(binding)
    definition=schema['$defs'][name]
    if definition.get('type')=='object':
        required=set(definition.get('required',[]))
        assert binding.__required_keys__==required,name
        assert binding.__optional_keys__==set(definition['properties'])-required,name
print(f'PASS: installed Python package, {total}/{total} shared payload outcomes and {len(transport)}/{len(transport)} correlation outcomes; all 29 type exports resolve; native-number/JSON negatives')
