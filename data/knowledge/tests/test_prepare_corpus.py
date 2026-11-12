"""Offline extraction checks using synthetic MedlinePlus-shaped source records."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_corpus.py"
SPEC = importlib.util.spec_from_file_location("prepare_corpus", SCRIPT)
corpus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(corpus)

SUMMARY = '<p>Demo 🩺 &amp; context.</p>\n<p>No chest pain.</p><p>No chest pain.</p>'


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="notelens-extraction-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.snapshot = self.root / "data/knowledge/manifests/snapshot.json"
        self.archive = self.root / "data/knowledge/raw/source.zip"
        self.output = self.root / "data/knowledge/.cache/corpus/selected-topics.jsonl"
        self.report = self.snapshot.with_name("prepared-corpus.json")
        self.tree = ET.Element("health-topics", {"total": "3"})
        for topic_id, language in (("20", "English"), ("3", "English"), ("8", "Spanish")):
            topic = ET.SubElement(self.tree, "health-topic", {
                "id": topic_id, "title": f"Demo topic {topic_id}", "language": language,
                "url": f"https://medlineplus.gov/demo{topic_id}.html",
                "date-created": "01/02/2020",
            })
            ET.SubElement(topic, "full-summary").text = SUMMARY
            if topic_id == "20":
                ET.SubElement(topic, "also-called").text = "Demo synonym"
                ET.SubElement(topic, "also-called").text = "Non-BMP 🩺 term"
            ET.SubElement(topic, "group", {
                "id": "11", "url": "https://medlineplus.gov/kidneysandurinarysystem.html",
            }).text = "Kidneys and Urinary System"
            ET.SubElement(topic, "site", {"url": "https://example.org/licensed"}).text = "DO NOT INGEST LINKED CONTENT"
            ET.SubElement(topic, "evaluation-answer").text = "DO NOT INGEST EVALUATION QA"
        self.save_source()

    def save_source(self, payload=None):
        if payload is None:
            self.tree.set("total", str(len(self.tree.findall("health-topic"))))
            payload = ET.tostring(self.tree, encoding="utf-8", xml_declaration=True)
        self.archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("topics.xml", payload)
        self.manifest = {
            "source": {"name": "MedlinePlus Health Topic XML", "release_date": "2026-11-10",
                       "attribution": "Source: MedlinePlus, National Library of Medicine."},
            "archive": {"local_path": "data/knowledge/raw/source.zip",
                        "size_bytes": self.archive.stat().st_size,
                        "sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                        "download_url": "https://medlineplus.gov/xml/demo.zip",
                        "members": [{"name": "topics.xml", "size_bytes": len(payload),
                                     "sha256": hashlib.sha256(payload).hexdigest()}]},
            "selection": {"status": "approved_initial_selection", "selection_rule_version": "demo-v1",
                          "selected_topic_ids": ["20", "3"]},
            "counts": {"selected_unique_topics": 2, "source_topics": len(self.tree.findall("health-topic"))},
        }
        self.save_manifest()

    def save_manifest(self):
        self.snapshot.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot.write_text(json.dumps(self.manifest), encoding="utf-8")

    def extract(self, **kwargs):
        return corpus.extract_corpus(self.root, **kwargs)

    def assert_rejected(self, message):
        with self.assertRaisesRegex(corpus.CorpusPreparationError, message):
            self.extract()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_exact_selection_preserves_summary_unicode_metadata_and_excludes_other_content(self):
        before = self.snapshot.read_bytes()
        with mock.patch("socket.socket", side_effect=AssertionError("Network access is forbidden")):
            report = self.extract()
        rows = [json.loads(line) for line in self.output.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["topic_id"] for row in rows], ["3", "20"])
        for row in rows:
            self.assertEqual(row["full_summary"], SUMMARY)
            self.assertEqual(row["summary_format"], "source_html")
            self.assertEqual(row["language"], "English")
            self.assertEqual(row["date_created"], "01/02/2020")
            self.assertEqual(row["source"]["snapshot_date"], "2026-11-10")
            self.assertEqual(row["source"]["archive_sha256"], self.manifest["archive"]["sha256"])
            self.assertEqual(row["source"]["xml_sha256"], self.manifest["archive"]["members"][0]["sha256"])
            self.assertTrue(row["source"]["attribution"])
            self.assertEqual(row["groups"][0]["id"], "11")
        self.assertEqual(rows[0]["synonyms"], [])
        self.assertEqual(rows[1]["synonyms"], ["Demo synonym", "Non-BMP 🩺 term"])
        self.assertNotIn("DO NOT INGEST", self.output.read_text(encoding="utf-8"))
        self.assertEqual(before, self.snapshot.read_bytes())
        self.assertEqual(report["counts"]["extracted_topics"], 2)
        self.assertEqual(report["counts"]["topics_with_synonyms"], 1)
        self.assertIsNone(report["counts"]["cleaned_topics"])
        self.assertIsNone(report["counts"]["passages"])
        self.assertEqual(report["artifact"]["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(report["stage"], "extraction_only")

    def test_repeated_extraction_is_byte_identical_for_same_source(self):
        self.extract()
        original = self.output.read_bytes()
        other = self.extract(output="data/knowledge/.cache/corpus/second.jsonl",
                             output_manifest="data/knowledge/manifests/second.json")
        self.assertEqual(original, (self.root / other["artifact"]["local_path"]).read_bytes())

    def test_changed_archive_is_rejected(self):
        with self.archive.open("ab") as source:
            source.write(b"changed")
        self.assert_rejected("archive.*(size|checksum)")

    def test_changed_member_checksum_is_rejected(self):
        self.manifest["archive"]["members"][0]["sha256"] = "0" * 64
        self.save_manifest()
        self.assert_rejected("XML.*checksum")

    def test_unapproved_selection_is_rejected(self):
        self.manifest["selection"]["status"] = "pending_review_and_approval"
        self.save_manifest()
        self.assert_rejected("approved")

    def test_duplicate_selected_ids_are_rejected(self):
        self.manifest["selection"]["selected_topic_ids"] = ["20", "20"]
        self.save_manifest()
        self.assert_rejected("duplicate")

    def test_missing_selected_id_is_rejected(self):
        self.manifest["selection"]["selected_topic_ids"] = ["3", "99"]
        self.save_manifest()
        self.assert_rejected("missing")

    def test_non_english_selected_topic_is_rejected(self):
        self.manifest["selection"]["selected_topic_ids"] = ["3", "8"]
        self.save_manifest()
        self.assert_rejected("English")

    def test_duplicate_source_id_is_rejected(self):
        self.tree.append(ET.fromstring(ET.tostring(self.tree[0])))
        self.save_source()
        self.assert_rejected("duplicate")

    def test_blank_or_missing_summary_is_rejected(self):
        topic = self.tree[0]
        for value in ("   ", None):
            with self.subTest(value=value):
                topic.find("full-summary").text = value
                self.save_source()
                self.assert_rejected("summary")
        topic.remove(topic.find("full-summary"))
        self.save_source()
        self.assert_rejected("summary")

    def test_missing_required_metadata_is_rejected(self):
        for field in ("title", "url"):
            with self.subTest(field=field):
                old = self.tree[0].attrib.pop(field)
                self.save_source()
                self.assert_rejected("metadata")
                self.tree[0].set(field, old)

    def test_nested_summary_markup_is_rejected_instead_of_silently_lost(self):
        ET.SubElement(self.tree[0].find("full-summary"), "p").text = "Unexpected XML child"
        self.save_source()
        self.assert_rejected("summary.*structure")

    def test_entity_declarations_are_rejected(self):
        payload = b'<!DOCTYPE health-topics [<!ENTITY demo "unexpected">]><health-topics total="0"/>'
        self.save_source(payload)
        self.assert_rejected("entity")

    def test_external_dtd_is_not_fetched(self):
        payload = b'<!DOCTYPE health-topics SYSTEM "https://example.invalid/no-network.dtd">' + ET.tostring(self.tree)
        self.save_source(payload)
        with mock.patch("socket.socket", side_effect=AssertionError("Network access is forbidden")):
            self.assertEqual(self.extract()["counts"]["extracted_topics"], 2)

    def test_wrong_selection_count_is_rejected(self):
        self.manifest["counts"]["selected_unique_topics"] = 9
        self.save_manifest()
        self.assert_rejected("selection count")

    def test_existing_artifact_is_not_overwritten(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b"existing output")
        with self.assertRaises(FileExistsError):
            self.extract()
        self.assertEqual(self.output.read_bytes(), b"existing output")
        self.assertFalse(self.report.exists())

    def test_existing_manifest_is_not_overwritten_or_leave_an_artifact(self):
        self.report.write_bytes(b"existing report")
        with self.assertRaises(FileExistsError):
            self.extract()
        self.assertEqual(self.report.read_bytes(), b"existing report")
        self.assertFalse(self.output.exists())

    def test_outputs_and_source_archive_cannot_escape_owned_paths(self):
        for kwargs in ({"output": "other.jsonl"}, {"output_manifest": "other.json"}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(corpus.CorpusPreparationError, "path"):
                self.extract(**kwargs)
        self.manifest["archive"]["local_path"] = "../outside.zip"
        self.save_manifest()
        self.assert_rejected("path")

    def test_cli_help_is_available_without_reading_corpus(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "extract", "--help"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--snapshot-manifest", result.stdout)


class SummaryCleaningTests(unittest.TestCase):
    def test_paragraphs_headings_links_entities_and_repeated_unicode_text(self):
        text, stats = corpus.clean_summary(
            '<h3>Demo &amp; context</h3><p>No <strong>pain</strong> \U0001fa7a.</p>'
            '<p>No pain \U0001fa7a.</p><p>Read <a href="https://example.invalid/never-fetch">this page</a>.</p>')
        self.assertEqual(text, 'Demo & context\n\nNo pain \U0001fa7a.\n\nNo pain \U0001fa7a.\n\nRead this page.')
        self.assertEqual(stats, {"tables": 0, "omitted_images": 0, "omitted_comments": 0})

    def test_lists_and_line_breaks_keep_separate_items(self):
        text, _ = corpus.clean_summary('<p>Options:</p><ul><li>First</li><li>Second<br/>continued</li></ul><p>End.</p>')
        self.assertEqual(text, 'Options:\n\n- First\n- Second\ncontinued\n\nEnd.')

    def test_inline_markup_does_not_split_words_or_change_negation_numbers(self):
        text, _ = corpus.clean_summary('<p>non<strong>cancerous</strong>; not 1.5 &lt; 2; A&nbsp; B.</p>')
        self.assertEqual(text, 'noncancerous; not 1.5 < 2; A B.')

    def test_entities_are_decoded_once_without_reparsing_literal_markup(self):
        text, _ = corpus.clean_summary('<p>&lt;p&gt; &amp;lt;b&amp;gt;</p>')
        self.assertEqual(text, '<p> &lt;b&gt;')

    def test_tables_preserve_empty_cells_row_order_headers_and_comparators(self):
        text, stats = corpus.clean_summary(
            '<h3>Ranges</h3><table><thead><tr><th>Category</th><th>Value</th><th></th></tr></thead>'
            '<tbody><tr><td>Low</td><td>Less than 80</td><td><strong>and</strong></td></tr>'
            '<tr><td>High</td><td>80 or higher</td><td>or</td></tr></tbody></table><p>After.</p>')
        self.assertEqual(text, 'Ranges\n\nCategory | Value | \nLow | Less than 80 | and\nHigh | 80 or higher | or\n\nAfter.')
        self.assertEqual(stats['tables'], 1)

    def test_images_comments_and_attributes_are_not_added_to_text(self):
        text, stats = corpus.clean_summary(
            '<p>Before<img src="https://example.invalid/no-download" alt="DO NOT INVENT IMAGE CONTENT"/> after.</p>'
            '<!-- NOT SUMMARY TEXT -->')
        self.assertEqual(text, 'Before after.')
        self.assertEqual(stats['omitted_images'], 1)
        self.assertEqual(stats['omitted_comments'], 1)

    def test_lists_inside_table_cells_stay_in_their_cell(self):
        text, stats = corpus.clean_summary(
            '<table><tr><th>Type</th><th>Symptoms</th></tr><tr><td>Motor</td>'
            '<td><ul><li>Weak muscles</li><li>No pain</li></ul>Other text.</td></tr></table>')
        self.assertEqual(text, 'Type | Symptoms\nMotor | - Weak muscles - No pain Other text.')
        self.assertEqual(stats['tables'], 1)

    def test_unsupported_or_ambiguous_structures_fail_instead_of_silently_losing_text(self):
        for html in ('<script>bad()</script>', '<style>p{}</style>', '<iframe>content</iframe>',
                     '<table><tr><td colspan="2">Merged</td></tr></table>',
                     '<table><tr><td>Unclosed', '<table>orphan text</table>',
                     '<!DOCTYPE html><p>Text</p>', '<p> </p>', '<img src="no-download"/>',
                     '<table><tr><td></td><td> </td></tr></table>'):
            with self.subTest(html=html), self.assertRaises(corpus.CorpusPreparationError):
                corpus.clean_summary(html)


class CorpusCleaningTests(unittest.TestCase):
    def setUp(self):
        fixture = ExtractionTests(methodName='test_cli_help_is_available_without_reading_corpus')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.extracted_report = fixture.extract()
        self.root = fixture.root
        self.output = self.root / corpus.CLEAN_OUTPUT
        self.report = self.root / corpus.CLEAN_REPORT

    def clean(self, **kwargs):
        return corpus.clean_corpus(self.root, **kwargs)

    def test_cleaning_preserves_original_records_provenance_and_inputs_without_network(self):
        originals = {path: path.read_bytes() for path in (
            self.fixture.snapshot, self.fixture.archive, self.fixture.output, self.fixture.report)}
        with mock.patch('socket.socket', side_effect=AssertionError('Network access is forbidden')):
            report = self.clean()
        before = [json.loads(line) for line in self.fixture.output.read_text(encoding='utf-8').splitlines()]
        after = [json.loads(line) for line in self.output.read_text(encoding='utf-8').splitlines()]
        for original, cleaned in zip(before, after, strict=True):
            for key, value in original.items():
                self.assertEqual(cleaned[key], value)
            self.assertEqual(cleaned['cleaned_summary'], 'Demo \U0001fa7a & context.\n\nNo chest pain.\n\nNo chest pain.')
            self.assertEqual(cleaned['cleaning']['text_sha256'], hashlib.sha256(cleaned['cleaned_summary'].encode('utf-8')).hexdigest())
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertEqual(report['counts']['cleaned_topics'], 2)
        self.assertIsNone(report['counts']['passages'])
        self.assertEqual(report['input']['extraction_manifest_sha256'], hashlib.sha256(self.fixture.report.read_bytes()).hexdigest())
        self.assertEqual(report['artifact']['sha256'], hashlib.sha256(self.output.read_bytes()).hexdigest())

    def test_same_inputs_produce_byte_identical_cleaned_artifacts(self):
        self.clean()
        other = self.clean(output='data/knowledge/.cache/corpus/cleaned-second.jsonl',
                           output_manifest='data/knowledge/manifests/cleaned-second.json')
        self.assertEqual(self.output.read_bytes(), (self.root / other['artifact']['local_path']).read_bytes())

    def rewrite_extracted_rows(self, rows):
        payload = ''.join(json.dumps(row) + '\n' for row in rows).encode('utf-8')
        self.fixture.output.write_bytes(payload)
        manifest = dict(self.extracted_report)
        manifest['artifact'] = dict(manifest['artifact'], size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        self.fixture.report.write_text(json.dumps(manifest), encoding='utf-8')

    def test_manifest_records_image_omissions_and_table_topic_ids(self):
        rows = [json.loads(line) for line in self.fixture.output.read_text(encoding='utf-8').splitlines()]
        rows[0]['full_summary'] = '<p>Text<img src="never-fetch"/><img src="also-never-fetch"/></p><!-- ignored -->'
        rows[1]['full_summary'] = '<table><tr><td>One</td><td>Two</td></tr></table>'
        self.rewrite_extracted_rows(rows)
        report = self.clean()
        self.assertEqual(report['counts']['omitted_images'], 2)
        self.assertEqual(report['counts']['tables'], 1)
        self.assertEqual(report['counts']['omitted_comments'], 1)
        self.assertEqual(report['affected_topic_ids'], {'tables': ['20'], 'omitted_images': ['3'], 'omitted_comments': ['3']})

    def test_invalid_later_summary_does_not_leave_partial_outputs(self):
        rows = [json.loads(line) for line in self.fixture.output.read_text(encoding='utf-8').splitlines()]
        rows[-1]['full_summary'] = '<script>NOT SUMMARY TEXT</script>'
        self.rewrite_extracted_rows(rows)
        with self.assertRaisesRegex(corpus.CorpusPreparationError, 'Topic 20: Unsupported'):
            self.clean()
        self.assertFalse(self.output.exists())
        self.assertFalse(self.report.exists())

    def test_changed_input_artifact_or_snapshot_is_rejected_before_outputs(self):
        for path in (self.fixture.output, self.fixture.snapshot):
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(path=path.name), self.assertRaisesRegex(corpus.CorpusPreparationError, 'checksum|size'):
                self.clean()
            self.assertFalse(self.output.exists())
            self.assertFalse(self.report.exists())
            path.write_bytes(original)

    def test_altered_selected_ids_or_provenance_are_rejected(self):
        original = self.fixture.output.read_bytes()
        for change in ('duplicate', 'extra', 'provenance', 'language', 'foreign_field'):
            rows = [json.loads(line) for line in original.decode('utf-8').splitlines()]
            if change == 'duplicate': rows.append(rows[0])
            elif change == 'extra': rows[0]['topic_id'] = '999'
            elif change == 'provenance': rows[0]['source']['snapshot_date'] = '1999-01-01'
            elif change == 'language': rows[0]['language'] = 'Spanish'
            else: rows[0]['evaluation_answer'] = 'DO NOT INGEST'
            payload = ''.join(json.dumps(row) + '\n' for row in rows).encode('utf-8')
            self.fixture.output.write_bytes(payload)
            manifest = dict(self.extracted_report)
            manifest['artifact'] = dict(manifest['artifact'], size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            self.fixture.report.write_text(json.dumps(manifest), encoding='utf-8')
            with self.subTest(change=change), self.assertRaises(corpus.CorpusPreparationError):
                self.clean()
            self.assertFalse(self.output.exists())

    def test_existing_outputs_and_out_of_scope_paths_are_protected(self):
        for path in (self.output, self.report):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'existing')
            with self.assertRaises(FileExistsError): self.clean()
            self.assertEqual(path.read_bytes(), b'existing')
            path.unlink()
        for kwargs in ({'output': '../outside.jsonl'}, {'output_manifest': 'other.json'},
                       {'extraction_manifest': '../outside.json'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(corpus.CorpusPreparationError):
                self.clean(**kwargs)

    def test_cli_clean_help_is_available(self):
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'clean', '--help'],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--extraction-manifest', result.stdout)


if __name__ == "__main__":
    unittest.main()
