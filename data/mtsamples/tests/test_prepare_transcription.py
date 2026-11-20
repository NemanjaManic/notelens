"""Synthetic unit tests and B's published F-012 preparation vectors."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_transcription import MAX_DOCUMENT_CODE_POINTS, PreparationError, prepare_transcription


ROOT = Path(__file__).resolve().parents[3]
F012_BASE = "1ac8bfe9cf3ea9853c417ffe3f86ed7a1a15b6f8"
F012_VECTORS = "apps/web/tests/fixtures/unicode-vectors.json"


class CanonicalPreparationTests(unittest.TestCase):
    def test_f012_preparation_vectors_from_published_base(self):
        try:
            fixture = subprocess.run(
                ["git", "show", f"{F012_BASE}:{F012_VECTORS}"], cwd=ROOT, capture_output=True, check=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.skipTest("The published F-012 vector commit is unavailable in this checkout.")
        vectors = json.loads(fixture.stdout)
        self.assertEqual(vectors["format"], "notelens-f012-vectors-v1")
        self.assertTrue(vectors["preparation"])
        for vector in vectors["preparation"]:
            with self.subTest(case=vector["id"]):
                result = prepare_transcription(vector["raw"])
                self.assertEqual(result.text, vector["canonical"])
                self.assertEqual(result.text_sha256, vector["sha256"])
                self.assertEqual(len(result.text), vector["code_points"])
                self.assertEqual(len(result.text.encode("utf-16-le")) // 2, vector["utf16_units"])
                self.assertEqual(result.canonicalization_version, "nfc-lf-v1")

    def test_preserves_spacing_and_bom_in_nonempty_transcription(self):
        canonical = " \ufeffCaf\u00e9\n\t\ufeff🩺\n  "
        result = prepare_transcription(" \ufeffCafe\u0301\r\n\t\ufeff🩺\r  ")
        self.assertEqual(result.text, canonical)
        self.assertEqual(result.text_sha256, sha256(canonical.encode("utf-8")).hexdigest())

    def test_invalid_input_and_surrogates_use_safe_codes(self):
        for value, code in ((b"decoded input required", "invalid-text"), (None, "invalid-text"),
                            ("prefix\ud800", "invalid-unicode"), ("\udc00suffix", "invalid-unicode")):
            with self.subTest(code=code), self.assertRaises(PreparationError) as caught:
                prepare_transcription(value)
            self.assertEqual(caught.exception.code, code)

    def test_blank_check_matches_javascript_without_stripping_accepted_text(self):
        with self.assertRaises(PreparationError) as caught:
            prepare_transcription("\ufeff\u00a0\r\n\t")
        self.assertEqual(caught.exception.code, "empty-text")
        self.assertEqual(prepare_transcription("\u0085").text, "\u0085")

    def test_code_point_limit_before_and_after_normalization(self):
        maximum = MAX_DOCUMENT_CODE_POINTS
        self.assertEqual(len(prepare_transcription("🩺" * maximum).text), maximum)
        for text in ("🩺" * (maximum + 1), "\u0344" * (maximum // 2 + 1)):
            with self.assertRaises(PreparationError) as caught:
                prepare_transcription(text)
            self.assertEqual(caught.exception.code, "text-too-large")
