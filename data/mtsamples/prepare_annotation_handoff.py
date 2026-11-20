"""Prepare D-002's approved validation metadata without exporting benchmark text."""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import COLUMNS, TARGETS
from draft_splits import SOURCE
from freeze_splits import FOUNDATION_COMMIT, VERSION, json_bytes
from prepare_transcription import CANONICALIZATION_VERSION, prepare_transcription


HANDOFF_VERSION = "c002-d002-development-v1"


def read_partition(frozen_dir, summary, split):
    filename = f"{split}.json"
    payload = (frozen_dir / filename).read_bytes()
    partition = json.loads(payload)
    if (partition["split"] != split or partition["manifest_version"] != VERSION
            or partition["source_sha256"] != summary["source_sha256"]
            or sha256(payload).hexdigest() != summary["split_checksums"][filename]):
        raise ValueError("Split bytes do not match the frozen manifest.")
    return partition["groups"]


def read_group_changes(frozen_dir, summary):
    review_dir = frozen_dir.parent
    signoff_bytes = (review_dir / "review-signoff.json").read_bytes()
    preview_bytes = (review_dir / "split-preview-signed-off.json").read_bytes()
    if (sha256(signoff_bytes).hexdigest() != summary["review_signoff_sha256"]
            or sha256(preview_bytes).hexdigest() != json.loads(signoff_bytes)["sha256"]["signed_off_preview"]):
        raise ValueError("Group changes do not match the signed-off review.")
    training = {group["group_id"]: group for group in read_partition(frozen_dir, summary, "train")}
    changes = []
    for change in json.loads(preview_bytes).get("group_changes", []):
        group_id = change["new_group_id"]
        old_ids = {doc_id for group in change["previous_groups"] for doc_id in group["document_ids"]}
        new_ids = {doc["document_id"] for doc in training[group_id]["documents"]}
        if old_ids != new_ids or not change["development_only"]:
            raise ValueError("A group change does not match its frozen development membership.")
        changes.append({**change, "proposed_split": "train"})
    return changes


def candidate_metadata(source, source_digest, candidates):
    payload = source.read_bytes()
    if sha256(payload).hexdigest() != source_digest:
        raise ValueError("The source differs from the frozen version.")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("The source columns differ from the audited schema.")
    selected = {}
    digest_groups = {}
    for row in reader:
        doc_id = f"mtsamples-{source_digest[:16]}-{row['']}"
        if doc_id not in candidates:
            continue
        group_id, specialty = candidates[doc_id]
        if doc_id in selected or row["medical_specialty"].strip() != specialty:
            raise ValueError("A matched source document differs from the frozen membership.")
        prepared = prepare_transcription(row["transcription"])
        if digest_groups.setdefault(prepared.text_sha256, group_id) != group_id:
            raise ValueError("A canonical digest occurs under different validation groups.")
        selected[doc_id] = {
            "doc_id": doc_id, "group_id": group_id, "specialty": specialty, "split": "validation",
            "text_sha256": prepared.text_sha256, "permitted_for_annotation": True,
        }
    if selected.keys() != candidates.keys():
        raise ValueError("Some approved validation documents could not be prepared.")
    return [selected[doc_id] for doc_id in sorted(selected)]


def prepare(frozen_dir):
    summary_bytes = (frozen_dir / "manifest.json").read_bytes()
    summary = json.loads(summary_bytes)
    if (summary["manifest_version"] != VERSION or summary["foundation_commit"] != FOUNDATION_COMMIT
            or summary["status"] != "frozen local split membership"):
        raise ValueError("Use the signed-off local split version.")
    validation = read_partition(frozen_dir, summary, "validation")
    candidates = {doc["document_id"]: (group["group_id"], doc["specialty"])
                  for group in validation for doc in group["documents"]}
    if (len(candidates) != summary["documents_per_split"]["validation"]
            or len(candidates) != sum(len(group["documents"]) for group in validation)
            or {label for _, label in candidates.values()} != set(TARGETS)):
        raise ValueError("Validation membership does not reconcile with the frozen manifest.")
    group_changes = read_group_changes(frozen_dir, summary)
    output_dir = frozen_dir.parent / HANDOFF_VERSION
    if output_dir.exists():
        raise ValueError("This handoff version already exists.")

    # The preparation record stays local and precedes the first source access.
    started = datetime.now(timezone.utc)
    access_file = f"{HANDOFF_VERSION}-access-{started:%Y%m%dT%H%M%S%fZ}.json"
    with (frozen_dir.parent / access_file).open("xb") as audit:
        audit.write(json_bytes({
            "actor": "Codex, for Sara (C)",
            "started_at": started.isoformat(),
            "scope": "Local validation-only canonical SHA-256 preparation for D-002",
            "split_manifest_version": VERSION,
            "documents": [{"doc_id": doc_id, "group_id": candidates[doc_id][0]} for doc_id in sorted(candidates)],
        }))
    documents = candidate_metadata(SOURCE, summary["source_sha256"], candidates)
    result = json_bytes({
        "kind": "permitted_benchmark",
        "source_version": HANDOFF_VERSION,
        "split_manifest_version": VERSION,
        "split_manifest_sha256": sha256(summary_bytes).hexdigest(),
        "canonicalization_version": CANONICALIZATION_VERSION,
        "scope": "Development annotation only. Candidates are from the frozen validation split.",
        "access": "D coordinates selection and adjudication. Annotators and reviewers receive assigned rows only. Use only the approved source access.",
        "redistribution": "Restricted to the approved team handoff. No report text or source-row mapping is included.",
        "attribution": "Tara Boyle, Medical Transcriptions (Kaggle). Source reports from MTSamples.com.",
        "quarantine": {"unresolved_pairs": summary["review_outcomes"].get("unresolved", 0), "included": False},
        "group_changes": group_changes,
        "documents": documents,
    })
    checksum = sha256(result).hexdigest()
    with TemporaryDirectory(dir=frozen_dir.parent) as staging:
        pending = Path(staging) / HANDOFF_VERSION
        pending.mkdir()
        (pending / "manifest.json").write_bytes(result)
        (pending / "manifest.sha256").write_text(f"{checksum}  manifest.json\n", encoding="ascii", newline="\n")
        pending.rename(output_dir)
    return len(documents), checksum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-dir", type=Path, required=True)
    parser.add_argument("--approved-development-annotation", action="store_true", required=True)
    args = parser.parse_args()
    frozen_dir = args.frozen_dir.resolve()
    if frozen_dir.name != VERSION or not frozen_dir.is_relative_to(SOURCE.parent.resolve()):
        parser.error("Use the frozen split directory inside Git-ignored local storage.")
    try:
        count, checksum = prepare(frozen_dir)
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as error:
        parser.exit(1, f"Annotation handoff preparation failed ({type(error).__name__}). Check the local inputs.\n")
    print(json.dumps({"version": HANDOFF_VERSION, "candidates": count, "manifest_sha256": checksum}))


if __name__ == "__main__":
    main()
