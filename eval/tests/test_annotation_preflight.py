import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from notelens_eval.annotations import preflight, read_source_manifest


SOURCE = Path(__file__).resolve().parents[1] / "fixtures/annotation-source-synthetic.json"
VERSION = "synthetic-source-v1"


def run_annotations(*args):
    return subprocess.run([sys.executable, "-B", "-m", "notelens_eval.annotations", *args],
                          capture_output=True, text=True, timeout=30)


def test_preflight_cli_confirms_source_bytes_and_reports_aggregate_capacity(tmp_path):
    manifest = tmp_path / "restricted-source.json"
    raw = SOURCE.read_bytes()
    manifest.write_bytes(raw)
    checksum = hashlib.sha256(raw).hexdigest()

    result = run_annotations("preflight", str(manifest), "--count", "20",
                             "--expected-sha256", checksum.upper(), "--source-version", VERSION)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["manifest_sha256"] == checksum
    assert report["status"] == "ready_for_selection_review"
    assert report["groups_by_split"] == {"validation": 12, "test": 8}
    assert report["candidate_documents"] == report["candidate_groups"] == 20
    assert report["issues"] == []
    assert "synthetic-source-00" not in result.stdout
    assert "Synthetic annotation exercise" not in result.stdout
    assert set(tmp_path.iterdir()) == {manifest}
    assert manifest.read_bytes() == raw


def test_accepted_checksum_is_rechecked_before_select_creates_output(tmp_path):
    manifest = tmp_path / "changed-source.json"
    raw = SOURCE.read_bytes()
    manifest.write_bytes(raw + b"\n")
    output = tmp_path / "assignments"
    checksum = hashlib.sha256(raw).hexdigest()

    result = run_annotations("select", str(manifest), "--count", "20", "--seed", "1",
                             "--output", str(output), "--expected-sha256", checksum,
                             "--source-version", VERSION)

    assert result.returncode == 1
    assert "SHA-256 differs" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize(("content", "match"), [
    (b'{"source_version":"new"}', "version differs"),
    (b'{"source_version":"synthetic-source-v1","source_version":"other"}', "duplicate JSON fields"),
])
def test_manifest_rejects_ambiguous_or_unexpected_version(tmp_path, content, match):
    manifest = tmp_path / "source.json"
    manifest.write_bytes(content)
    with pytest.raises(ValueError, match=match):
        read_source_manifest(manifest, expected_sha256=hashlib.sha256(content).hexdigest(),
                             source_version=VERSION)


def test_preflight_reports_review_capacity_without_creating_assignments():
    manifest = json.loads(SOURCE.read_bytes())
    for document in manifest["documents"]:
        if document["split"] == "validation":
            document["split"] = "test"

    report = preflight(manifest, count=40, reviews=10)

    assert report["status"] == "needs_review"
    assert report["issues"] == ["insufficient_unique_groups", "insufficient_member_c_development_primary_groups",
                                 "member_c_development_review_unavailable"]
    assert report["member_c_primary_quota"] == 10
    assert "assignments" not in report
