"""Synthetic checks for schema, cleaning and preservation of source text."""

import csv
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "audit.py"
SPEC = importlib.util.spec_from_file_location("mtsamples_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "synthetic.csv"

    def write(self, rows, columns=MODULE.COLUMNS):
        with self.source.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(rows)

    def row(self, identifier, label, text):
        return (identifier, "metadata must not be a predictor", label, "title", text, "label keyword")

    def test_exact_mapping_empty_exclusions_and_unicode_preservation(self):
        text = "  Synthetic \U0001f9ea report\r\nRepeated. Repeated. e\u0301  "
        self.write([self.row("0", " Neurology", text),
                    self.row("1", " Neurology", " \n\t"),
                    self.row("2", " Surgery", "Synthetic surgical report"),
                    self.row("3", " Neurosurgery", "Synthetic report")])
        result, cleaned = MODULE.audit(self.source)
        self.assertEqual(result["counts"]["source_rows"], 4)
        self.assertEqual(result["counts"]["target_empty_transcriptions"], 1)
        self.assertEqual(result["counts"]["non_target_rows"], 2)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["category"], "Neurology")
        self.assertEqual(cleaned[0]["transcription"], text)
        roundtrip = list(csv.DictReader(io.StringIO(MODULE.render_cleaned(cleaned), newline="")))
        self.assertEqual(roundtrip, cleaned)
        self.assertNotIn(text, MODULE.render_json(result))
        self.assertNotIn("metadata must not", MODULE.render_cleaned(cleaned))

    def test_exact_conflicts_are_reported_without_claiming_clean_benchmark(self):
        self.write([self.row("0", " Urology", "Synthetic duplicate"),
                    self.row("1", " Neurology", "Synthetic duplicate")])
        result, rows = MODULE.audit(self.source)
        self.assertEqual(result["preliminary_exact_text_inventory"]["conflicting_target_label_groups"], 1)
        self.assertEqual(len(rows), 2)

    def test_duplicate_source_ids_fail(self):
        self.write([self.row("0", " Urology", "One"), self.row("0", " Neurology", "Two")])
        with self.assertRaises(ValueError):
            MODULE.audit(self.source)

    def test_missing_columns_fail(self):
        self.write([], columns=("medical_specialty", "transcription"))
        with self.assertRaises(ValueError):
            MODULE.audit(self.source)

    def test_malformed_rows_fail(self):
        self.write([("0", "Only two fields")])
        with self.assertRaises(ValueError):
            MODULE.audit(self.source)

    def test_invalid_utf8_fails_without_replacement(self):
        self.source.write_bytes(b"\xff")
        with self.assertRaises(UnicodeError):
            MODULE.audit(self.source)

    def test_reproducible_cli_and_stale_output_detection(self):
        self.write([self.row("0", " Urology", "Synthetic private marker")])
        manifest = self.source.parent / "source.json"
        cleaned = self.source.parent / "cleaned.csv"
        command = [sys.executable, "-B", str(SCRIPT), "--source", str(self.source),
                   "--manifest", str(manifest), "--cleaned", str(cleaned)]
        for flags in ([], ["--check"]):
            process = subprocess.run(command + flags, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertNotIn("Synthetic private marker", process.stdout + process.stderr)
        cleaned.write_text("stale", encoding="utf-8")
        self.assertEqual(subprocess.run(command + ["--check"], capture_output=True).returncode, 1)

    def test_source_cannot_be_overwritten(self):
        self.write([self.row("0", " Urology", "Synthetic source")])
        original = self.source.read_bytes()
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), "--source", str(self.source),
                                  "--manifest", str(self.source)], capture_output=True)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(self.source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
