"""Rank evidence must retain repeated question hashes and missing-case penalties."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

script=Path(__file__).resolve().parents[1]/'scripts/score_d009_ranked_retrieval.py'
spec=importlib.util.spec_from_file_location('ranked_binding',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RankedBindingTests(unittest.TestCase):
    def run_fixture(self, *, mismatch=False, missing=False):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)
            question='What is condition A?'
            ids=['F-LIT-01','F-MIX-01']
            with zipfile.ZipFile(p/'runtime.zip','w') as archive:
                archive.writestr('runtime-cases.json',json.dumps([
                    {'case_id':key,'question':question} for key in ids]))
            operator={'run_id':'run-1','app_sha':'a'*40,'status':'completed',
                      'runtime_bundle_sha256':hashlib.sha256((p/'runtime.zip').read_bytes()).hexdigest()}
            (p/'run-receipt.json').write_text(json.dumps(operator))
            requests=[]
            refs=[]
            for i,key in enumerate(ids):
                row={'question_sha256':hashlib.sha256(question.encode()).hexdigest(),'status':'completed',
                     'retrieval':{'top_k':5,'ranked':[{'passage_id':f'p{i}','topic_id':f't{i}'}]}}
                if missing and i==1:
                    row.pop('retrieval');row['status']='completed_abstained'
                requests.append(row)
                refs.append({'id':key,'source_scope':'single','required_topic_ids':[f't{i}'],
                             'required_passage_groups':[[f'p{i}']]})
            (p/'a.json').write_text(json.dumps({'run_id':'wrong' if mismatch else 'run-1',
                                               'app_sha':'a'*40,'requests':requests}))
            (p/'refs.json').write_text(json.dumps({'version':'test-v1','cases':refs}))
            with contextlib.redirect_stdout(io.StringIO()):
                module.score(p,p/'a.json',p/'runtime.zip',p/'refs.json',p/'scores.json')
            return json.loads((p/'scores.json').read_text())

    def test_repeated_hashes_remain_distinct_ordered_case_records(self):
        result=self.run_fixture()
        self.assertEqual(result['overall']['topic_recall_at_5'],1.0)
        self.assertEqual(result['overall']['topic_metric_denominator'],2)

    def test_wrong_run_receipt_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'identity mismatch'):
            self.run_fixture(mismatch=True)

    def test_missing_ranking_keeps_full_denominator(self):
        result=self.run_fixture(missing=True)
        self.assertEqual(result['overall']['topic_recall_at_5'],0.5)
        self.assertEqual(result['overall']['topic_metric_denominator'],2)
        self.assertEqual(result['secondary_attempted_retrieval_only']['topic_recall_at_5'],1.0)
