"""Review-candidate regression tests; no canonical promotion or live services."""

from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_candidate as build
import check_candidate as candidate
import check_contracts as p1


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts=candidate.CandidateContracts()
        cls.cases,cls.payloads,cls.documents,cls.references=p1.load_suite(cls.contracts)

    def test_regeneration_matches_reviewed_files(self):
        candidate.verify_candidate()
        for name,data in build.assets().items():
            self.assertEqual((build.CANDIDATE/name).read_bytes(),data,name)

    def test_candidate_suite_and_correlation_outcomes(self):
        self.assertEqual(p1.run_suite(self.contracts)[2],[])
        self.assertEqual(candidate.check_transport(self.contracts)[1],[])

    def test_p1_still_passes_unchanged(self):
        self.assertEqual(p1.run_suite(p1.Contracts())[2],[])
        manifest=p1.read_json(build.CANDIDATE/'candidate.json')
        for name,digest in manifest['p1_files'].items():
            self.assertEqual(hashlib.sha256((p1.ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_no_freeze_even_when_candidate_passes(self):
        output=io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(candidate.main(['--require-freeze']),1)
        self.assertIn('CANDIDATE_NOT_CANONICAL',output.getvalue())
        self.assertFalse((p1.ROOT/'contracts/v1/freeze.json').exists())

    def test_unknown_assertion_and_procedure_plan_are_separate(self):
        self.assertEqual(self.contracts.validate(self.payloads['extraction-unknown-assertion'],'ExtractionItem',self.documents['offset']),[])
        item=deepcopy(self.payloads['procedure-planned'])
        item['procedure_status']='performed'
        issues=self.contracts.validate(item,'ExtractionItem',self.documents['procedure'],self.references['planned-procedure'])
        self.assertEqual(issues,[p1.Issue('REFERENCE_ATTRIBUTE','/procedure_status')])

    def test_summary_failure_preserves_findings(self):
        result=self.payloads['analysis-summary-failed-findings-kept']
        self.assertTrue(result['items'])
        self.assertEqual(result['summary']['status'],'failed')
        self.assertEqual(self.contracts.validate(result,'ExtractionResult',self.documents['offset']),[])

    def test_empty_complete_is_not_failure_or_medical_absence(self):
        result=self.payloads['extraction-empty']
        self.assertEqual(result['extraction_status'],'completed')
        self.assertEqual(result['items'],[])
        self.assertEqual(result['summary']['result']['evidence_state'],'insufficient')
        self.assertEqual(self.contracts.validate(result,'ExtractionResult',self.documents['offset']),[])

    def test_skipped_pipeline_cannot_invent_executed_model(self):
        result=deepcopy(self.payloads['classification-unsupported'])
        self.assertIsNone(result['model_version'])
        self.assertIsNone(result['score_kind'])
        result['model_version']='configured-but-unused'
        self.assertIn(p1.Issue('STRUCTURE','/model_version'),self.contracts.validate(result,'ClassificationResult',self.documents['offset']))

    def test_no_live_scope_detector_is_implied_by_mock(self):
        result=deepcopy(self.payloads['classification-unsupported'])
        result['mode']='live'
        self.assertEqual(self.contracts.validate(result,'ClassificationResult',self.documents['offset']),[p1.Issue('SCOPE_POLICY_UNAPPROVED','/scope_policy_version')])

    def test_mixed_origins_and_text_graph_are_checked(self):
        result=deepcopy(self.payloads['answer-mixed-origins'])
        self.assertEqual(self.contracts.validate(result,'AnswerResult',self.documents['offset']),[])
        result['mode']='live'
        self.assertEqual(self.contracts.validate(result,'AnswerResult',self.documents['offset']),[p1.Issue('MODE_PROVENANCE','/mode')])
        result=deepcopy(self.payloads['answer-document'])
        result['text']+=' Unclaimed substantive text.'
        self.assertEqual(self.contracts.validate(result,'AnswerResult',self.documents['offset']),[p1.Issue('TEXT_CLAIMS','/text')])

    def test_local_id_collisions_are_preserved_with_prefixes(self):
        result=self.payloads['answer-prefixed-local-id-collisions']
        self.assertEqual({source['source_id'] for source in result['sources']},{'a:shared-source','d:shared-source'})
        self.assertEqual(self.contracts.validate(result,'AnswerResult',self.documents['offset']),[])
        crossed=self.payloads['answer-cross-component-citation']
        self.assertEqual(self.contracts.validate(crossed,'AnswerResult',self.documents['offset']),[p1.Issue('CLAIM_COMPONENT','/claims/0/component_id')])

    def test_root_prompt_and_component_prompt_cannot_disagree(self):
        result=deepcopy(self.payloads['answer-document'])
        result['prompt_version']='different-prompt'
        self.assertEqual(self.contracts.validate(result,'AnswerResult',self.documents['offset']),[p1.Issue('ROOT_VERSION','/prompt_version')])

    def test_inconclusive_language_is_not_admitted_as_english(self):
        document=deepcopy(self.documents['offset'])
        document['language_validation']=build.language('inconclusive')
        self.assertIn(p1.Issue('STRUCTURE','/language_validation/outcome'),self.contracts.validate(document,'PreparedDocument'))

    def test_correlation_fallback_is_failure_not_success(self):
        case=next(case for case in p1.read_json(build.CANDIDATE/'transport-cases.json')['cases'] if case['id']=='missing-id-fallback')
        self.assertEqual(case['disposition'],'failed_call')
        self.assertEqual(candidate.validate_exchange(case,self.contracts),[])
        case=deepcopy(case);case['status']=200
        self.assertEqual(candidate.validate_exchange(case,self.contracts),['INVALID_REQUEST_SUCCESS'])

    def test_candidate_drift_is_rejected(self):
        original=build.assets
        def altered():
            values=original();values['schema.json']+=b'\n';return values
        with patch.object(build,'assets',side_effect=altered):
            with self.assertRaisesRegex(p1.CheckError,'CANDIDATE_DRIFT'):
                candidate.verify_candidate()

    def test_validator_runs_outside_repository(self):
        result=subprocess.run([sys.executable,str(p1.ROOT/'scripts/project/check_candidate.py')],cwd=p1.ROOT/'.cache',capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertNotIn('Traceback',result.stderr)

    def test_python_and_javascript_agree_on_repeated_non_bmp_span(self):
        data={'text':self.documents['offset']['text'],'start':47,'end':61,'quote':'No chest pain.'}
        script="const fs=require('fs');const v=JSON.parse(fs.readFileSync(0,'utf8'));const chars=Array.from(v.text);const start=chars.slice(0,v.start).join('').length;const end=chars.slice(0,v.end).join('').length;if(start!==48||end!==62||v.text.slice(start,end)!==v.quote||v.text.slice(v.start,v.end)===v.quote)process.exit(1);process.stdout.write('PASS: code-point/UTF-16 conversion');"
        result=subprocess.run(['node','-e',script],input=json.dumps(data),capture_output=True,text=True,check=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('PASS',result.stdout)


if __name__=='__main__':
    unittest.main()
