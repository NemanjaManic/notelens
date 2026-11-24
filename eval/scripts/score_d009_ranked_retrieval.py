"""Score real ranked IDs from a private A receipt with the existing evaluator."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from notelens_eval.retrieval_metrics import evaluate_retrieval


def score(run_dir, a_receipt, runtime_zip, refs_path, out_path):
    operator_raw = (run_dir / 'run-receipt.json').read_bytes()
    operator = json.loads(operator_raw)
    a_raw = a_receipt.read_bytes()
    ledger = json.loads(a_raw)
    if (operator['run_id'], operator['app_sha']) != (ledger['run_id'], ledger['app_sha']):
        raise ValueError('Operator and A receipt identity mismatch.')
    if hashlib.sha256(runtime_zip.read_bytes()).hexdigest() != operator['runtime_bundle_sha256']:
        raise ValueError('Runtime archive checksum mismatch.')
    with zipfile.ZipFile(runtime_zip) as archive:
        runtime = json.loads(archive.read('runtime-cases.json'))
    eligible = [row for row in runtime if row['case_id'].startswith(('F-LIT-', 'F-MIX-'))]
    requests = ledger['requests']
    if len(requests) > len(eligible) or (operator['status'] == 'completed' and len(requests) != len(eligible)):
        raise ValueError('Unexpected A request inventory.')
    predictions, missing, attempted = [], [], set()
    for index, row in enumerate(eligible):
        ranked = []
        if index < len(requests):
            request = requests[index]
            if hashlib.sha256(row['question'].encode('utf-8')).hexdigest() != request['question_sha256']:
                raise ValueError('A question order/hash mismatch.')
            if 'retrieval' in request:
                attempted.add(row['case_id'])
                ranked = request['retrieval']['ranked']
                if request['retrieval']['top_k'] != 5 or len(ranked) > 5:
                    raise ValueError('Unexpected retrieval configuration.')
            else:
                missing.append({'id':row['case_id'], 'status':request['status']})
        else:
            missing.append({'id':row['case_id'], 'status':'not_executed'})
        predictions.append({'id':row['case_id'], 'ranked_passages':ranked})
    refs_raw = refs_path.read_bytes()
    report = evaluate_retrieval(json.loads(refs_raw),
        {'version':'d009-ranked-from-live-receipt-v1','cases':predictions})
    if attempted:
        conditional = evaluate_retrieval(
            dict(json.loads(refs_raw), cases=[row for row in json.loads(refs_raw)['cases'] if row['id'] in attempted]),
            {'version':'d009-ranked-attempted-only-v1','cases':[row for row in predictions if row['id'] in attempted]})
        report['secondary_attempted_retrieval_only'] = conditional['overall']
    report.update(run_id=operator['run_id'], app_sha=operator['app_sha'],
        run_receipt_sha256=hashlib.sha256(operator_raw).hexdigest(),
        A_receipt_sha256=hashlib.sha256(a_raw).hexdigest(),
        retrieval_references_sha256=hashlib.sha256(refs_raw).hexdigest(),
        missing_rank_records=missing,
        metric_scope='Actual top-five candidates; abstentions/missing ranks remain empty on the full reference denominator.')
    out_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['overall'],indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run_dir','a_receipt','runtime_zip','references','output'):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    score(args.run_dir,args.a_receipt,args.runtime_zip,args.references,args.output)
