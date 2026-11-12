"""Regression checks for the validator, catalog, and recorded-freeze gate.

All temporary approvals are explicitly synthetic and exist only in ignored test copies.
"""

from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_contracts as checks


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = checks.Contracts()
        cls.cases, cls.payloads, cls.documents, cls.references = checks.load_suite(cls.contracts)
        cache = checks.ROOT / ".cache/contract-tests"
        cache.mkdir(parents=True, exist_ok=True)
        cls.cache = cache

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.cache)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(checks.ROOT / "contracts/v1", self.root / "contracts/v1")
        self.copy = checks.Contracts(self.root)

    def save(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")

    def catalog(self):
        return checks.read_json(self.root / "contracts/v1/fixtures/manifest.json")

    def test_complete_suite(self):
        total, positive, failures = checks.run_suite(self.contracts)
        self.assertGreater(total, positive)
        self.assertGreater(positive, 0)
        self.assertEqual(failures, [])

    def test_cli_runs_from_another_directory(self):
        result = subprocess.run([sys.executable, str(checks.ROOT / "scripts/project/check_contracts.py")],
                                cwd=self.root, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("fixture outcomes", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_named_definition_is_not_permissive_schema_root(self):
        self.assertEqual(self.contracts.validate({}, "PreparedDocument"), [checks.Issue("STRUCTURE", "")])

    def test_negative_rejected_for_wrong_reason_is_a_failure(self):
        catalog = self.catalog()
        case = next(case for case in catalog["cases"] if case["id"] == "document-wrong-digest")
        case["expected"] = [{"rule": "SPAN_QUOTE", "path": "/text_sha256"}]
        self.save("contracts/v1/fixtures/manifest.json", catalog)
        failures = checks.run_suite(self.copy)[2]
        self.assertEqual([case_id for case_id, _, _ in failures], ["document-wrong-digest"])

    def test_expected_invalid_cannot_be_declared_valid(self):
        catalog = self.catalog()
        case = next(case for case in catalog["cases"] if case["id"] == "document-wrong-digest")
        case["expected"] = []
        self.save("contracts/v1/fixtures/manifest.json", catalog)
        with self.assertRaisesRegex(checks.CheckError, "incomplete"):
            checks.run_suite(self.copy)

    def test_catalog_rejects_empty_cases(self):
        self.save("contracts/v1/fixtures/manifest.json", {"catalog_version": 1, "cases": []})
        with self.assertRaisesRegex(checks.CheckError, "CATALOG"):
            checks.run_suite(self.copy)

    def test_catalog_rejects_missing_definition_coverage(self):
        catalog = self.catalog()
        case = next(case for case in catalog["cases"] if case["id"] == "claim-valid")
        catalog["cases"].remove(case)
        payloads = checks.read_json(self.root / "contracts/v1/fixtures/payloads.json")
        del payloads["claim-valid"]
        self.save("contracts/v1/fixtures/manifest.json", catalog)
        self.save("contracts/v1/fixtures/payloads.json", payloads)
        with self.assertRaisesRegex(checks.CheckError, "coverage"):
            checks.run_suite(self.copy)

    def test_catalog_rejects_duplicate_case_id(self):
        catalog = self.catalog()
        catalog["cases"].append(deepcopy(catalog["cases"][0]))
        self.save("contracts/v1/fixtures/manifest.json", catalog)
        with self.assertRaisesRegex(checks.CheckError, "duplicate case"):
            checks.run_suite(self.copy)

    def test_catalog_rejects_orphaned_payload(self):
        payloads = checks.read_json(self.root / "contracts/v1/fixtures/payloads.json")
        payloads["orphaned"] = {}
        self.save("contracts/v1/fixtures/payloads.json", payloads)
        with self.assertRaisesRegex(checks.CheckError, "orphaned"):
            checks.run_suite(self.copy)

    def test_catalog_rejects_missing_context(self):
        catalog = self.catalog()
        catalog["cases"][0]["document"] = "missing"
        self.save("contracts/v1/fixtures/manifest.json", catalog)
        with self.assertRaisesRegex(checks.CheckError, "context"):
            checks.run_suite(self.copy)

    def test_json_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for data in ['{"a":1,"a":2}', '{"score":NaN}', '{"score":Infinity}', '{"score":1e999}', '{']:
            with self.subTest(data=data):
                path = self.root / "malformed.json"
                path.write_text(data, encoding="utf-8")
                with self.assertRaisesRegex(checks.CheckError, "JSON_INPUT"):
                    checks.read_json(path)

    def test_repeated_quote_is_valid_text_but_not_intended_occurrence(self):
        document = self.documents["offset"]
        payload = self.payloads["span-first-valid"]
        self.assertEqual(self.contracts.validate(payload, "EvidenceSpan", document), [])
        self.assertEqual(self.contracts.validate(payload, "EvidenceSpan", document,
                                               self.references["second-occurrence"]),
                         [checks.Issue("REFERENCE_SPAN", "")])

    def test_text_length_boundary_counts_code_points(self):
        document = deepcopy(self.documents["offset"])
        for length, expected in [(100_000, []), (100_001, [checks.Issue("STRUCTURE", "/text")])]:
            with self.subTest(length=length):
                document["text"] = "\U0001fa7a" * length
                document["text_sha256"] = hashlib.sha256(document["text"].encode("utf-8")).hexdigest()
                self.assertEqual(self.contracts.validate(document, "PreparedDocument"), expected)

    def test_embedded_invalid_digest_is_payload_failure(self):
        request = deepcopy(self.payloads["classification-request-valid"])
        request["document"]["text_sha256"] = "0" * 64
        self.assertEqual(self.contracts.validate(request, "ClassificationRequest"),
                         [checks.Issue("TEXT_DIGEST", "/document/text_sha256")])

    def test_icd_prefix_is_not_an_explicit_source_code(self):
        item = deepcopy(self.payloads["extraction-explicit-icd"])
        item["icd"]["code"] = "R07"
        self.assertEqual(self.contracts.validate(item, "ExtractionItem", self.documents["history"]),
                         [checks.Issue("ICD_SOURCE", "/icd/code")])

    def test_prepared_text_does_not_reveal_original_bom_count(self):
        document = deepcopy(self.documents["offset"])
        document["text"] = "\ufeffText."
        document["text_sha256"] = hashlib.sha256(document["text"].encode("utf-8")).hexdigest()
        self.assertEqual(self.contracts.validate(document, "PreparedDocument"), [])

    def test_reference_pointer_must_resolve(self):
        with self.assertRaisesRegex(checks.CheckError, "REFERENCE_POINTER"):
            self.contracts.validate(self.payloads["claim-valid"], "Claim",
                                    reference={"attributes": {"/missing": "value"}})

    def test_local_reference_resolves_and_external_reference_is_denied(self):
        self.contracts.check_refs({"$ref": "./schema.json#/$defs/PreparedDocument"},
                                  self.contracts.directory / "openapi.json")
        for ref in ["https://example.invalid/schema", "file:///C:/outside.json", "../outside.json", "#/$defs/Missing"]:
            with self.subTest(ref=ref), self.assertRaises(checks.CheckError):
                self.contracts.check_refs({"$ref": ref}, self.contracts.directory / "schema.json")

    def test_network_access_is_blocked(self):
        with checks.offline():
            with self.assertRaises(OSError):
                socket.create_connection(("example.invalid", 443))
            with self.assertRaises(OSError):
                socket.getaddrinfo("example.invalid", 443)
            self.assertEqual(checks.run_suite(self.contracts)[2], [])

    def test_openapi_rejects_wrong_but_resolving_request_definition(self):
        api = deepcopy(self.contracts.api)
        api["paths"]["/v1/classify"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"] = \
            "./schema.json#/$defs/ClassificationResult"
        with self.assertRaisesRegex(checks.CheckError, "OPENAPI_BINDING"):
            self.contracts.check_openapi(api)

    def test_openapi_rejects_missing_required_operation(self):
        api = deepcopy(self.contracts.api)
        del api["paths"]["/v1/extract"]
        with self.assertRaisesRegex(checks.CheckError, "OPENAPI_BINDING"):
            self.contracts.check_openapi(api)

    def test_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(checks.CheckError, "LOCAL_PATH"):
            checks.contained(self.root, "../outside.json")

    def synthetic_freeze(self):
        self.save("contracts/v1/freeze.json", {
            "schema_version": "1.0.0", **checks.freeze_digests(self.copy),
            "approvals": [{"member": member, "decision": "approved", "date": "2026-11-11",
                           "evidence": "docs/decisions/contract-freeze.md#member-" + member.lower()}
                          for member in "ABCD"],
        })
        evidence = self.root / "docs/decisions/contract-freeze.md"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("# Synthetic test data only\n\n" + "\n".join(
            "## Member " + member + "\nSynthetic consistency test; not an actual approval.\n" for member in "ABCD"),
            encoding="utf-8")

    def test_freeze_missing_or_malformed_fails(self):
        with self.assertRaisesRegex(checks.CheckError, "FREEZE_PENDING"):
            checks.require_freeze(self.copy)
        self.save("contracts/v1/freeze.json", {})
        with self.assertRaisesRegex(checks.CheckError, "FREEZE_RECORD"):
            checks.require_freeze(self.copy)

    def test_synthetic_freeze_record_consistency(self):
        self.synthetic_freeze()
        checks.require_freeze(self.copy)
        self.assertFalse((checks.ROOT / "contracts/v1/freeze.json").exists())

    def test_freeze_rejects_missing_duplicate_and_pending_owner(self):
        for mutation in ("missing", "duplicate", "pending", "date", "version"):
            with self.subTest(mutation=mutation):
                self.synthetic_freeze()
                record = checks.read_json(self.root / "contracts/v1/freeze.json")
                if mutation == "missing": record["approvals"].pop()
                if mutation == "duplicate": record["approvals"][0]["member"] = "B"
                if mutation == "pending": record["approvals"][0]["decision"] = "pending"
                if mutation == "date": record["approvals"][0]["date"] = "2026-02-30"
                if mutation == "version": record["schema_version"] = "0.0.0"
                self.save("contracts/v1/freeze.json", record)
                with self.assertRaises(checks.CheckError): checks.require_freeze(self.copy)

    def test_freeze_requires_resolving_owner_evidence(self):
        self.synthetic_freeze()
        path = self.root / "docs/decisions/contract-freeze.md"
        path.write_text("# No owner sections\n", encoding="utf-8")
        with self.assertRaisesRegex(checks.CheckError, "FREEZE_EVIDENCE"):
            checks.require_freeze(self.copy)
        path.unlink()
        with self.assertRaisesRegex(checks.CheckError, "FREEZE_EVIDENCE"):
            checks.require_freeze(self.copy)

    def test_freeze_detects_changed_schema_api_manifest_and_payload(self):
        for relative in ("schema.json", "openapi.json", "fixtures/manifest.json", "fixtures/payloads.json"):
            with self.subTest(relative=relative):
                self.synthetic_freeze()
                path = self.root / "contracts/v1" / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with self.assertRaisesRegex(checks.CheckError, "FREEZE_DIGEST"):
                    checks.require_freeze(self.copy)
                path.write_bytes(original)

    def test_guarded_cli_fails_without_leaking_payload(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = checks.main(["--require-freeze"])
        self.assertEqual(code, 1)
        self.assertIn("FREEZE_PENDING", output.getvalue())
        self.assertNotIn(self.documents["offset"]["text"], output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_failure_diagnostics_omit_third_party_exception_details(self):
        output = io.StringIO()
        with patch.object(checks, "Contracts", side_effect=RuntimeError("sensitive request body")), redirect_stdout(output):
            self.assertEqual(checks.main([]), 1)
        self.assertIn("CHECK_INFRASTRUCTURE", output.getvalue())
        self.assertNotIn("sensitive", output.getvalue())


if __name__ == "__main__":
    unittest.main()
