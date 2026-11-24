"""Unavailable saved answers must remain technical failures, not evidence gaps."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class BranchOutcomeTests(unittest.TestCase):
    def score(self, kind=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'run-receipt.json').write_text('{}')
            refs = {'cases': [{'id': 'case-1', 'case_version': 'v1',
                               'expected_answer_route': 'none', 'expected_evidence_state': 'insufficient'}]}
            (root / 'refs.json').write_text(json.dumps(refs))
            (root / 'retr.json').write_text('{"cases": []}')
            if kind is not None:
                answer = {'route': 'none', 'state': 'unavailable' if kind == 'unavailable' else 'insufficient',
                          'branches': [{'origin': 'literature', 'result': {'kind': kind}}]}
                (root / 'case-001.json').write_text(json.dumps(
                    {'case_id': 'case-1', 'case_version': 'v1', 'answer': answer}))
            script = Path(__file__).resolve().parents[1] / 'scripts/score_d009_branches.py'
            subprocess.run([sys.executable, '-B', str(script), str(root), str(root / 'refs.json'),
                            str(root / 'retr.json'), str(root / 'out.json')], check=True, capture_output=True)
            return json.loads((root / 'out.json').read_text())['totals']

    def test_saved_unavailable_is_technical_failure(self):
        result = self.score('unavailable')
        self.assertEqual((result['technical_errors'], result['unavailable_branches'],
                          result['unsupported_branches'], result['completed_cases']), (1, 1, 0, 0))

    def test_explicit_unsupported_is_completed_gap(self):
        result = self.score('unsupported')
        self.assertEqual((result['technical_errors'], result['unavailable_branches'],
                          result['unsupported_branches'], result['completed_cases']), (0, 0, 1, 1))

    def test_unexecuted_is_technical_failure(self):
        result = self.score()
        self.assertEqual((result['executed'], result['technical_errors'], result['completed_cases']), (0, 1, 0))
