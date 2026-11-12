"""Audit a locally supplied MTSamples CSV without logging document contents.

Standard library only. This is C-001 data inspection, not a split/training pipeline.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
TARGETS = (
    "Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology",
    "Neurology", "Urology",
)
COLUMNS = ("", "description", "medical_specialty", "sample_name", "transcription", "keywords")


def audit(source):
    """Return aggregate metadata and nonempty target rows; never alter source text."""
    payload = Path(source).read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("Unexpected CSV schema; expected the six MTSamples columns.")
    rows = list(reader)
    source_ids = set()
    raw_counts = Counter()
    nonempty_counts = Counter()
    empty_counts = Counter()
    cleaned = []
    text_groups = defaultdict(list)
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed CSV record: field count does not match the header.")
        source_id = row[""]
        if not source_id or source_id in source_ids:
            raise ValueError("Source row IDs must be present and unique.")
        source_ids.add(source_id)
        raw_label = row["medical_specialty"]
        label = raw_label.strip()
        raw_counts[raw_label] += 1
        text = row["transcription"]
        if not text.strip():
            empty_counts[label] += 1
            continue
        nonempty_counts[label] += 1
        if label not in TARGETS:
            continue
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        text_groups[text_hash].append(label)
        cleaned.append({
            "document_id": f"mtsamples-{digest[:16]}-{source_id}",
            "source_row_id": source_id,
            "category": label,
            "transcription": text,
        })
    duplicates = [labels for labels in text_groups.values() if len(labels) > 1]
    conflicts = [labels for labels in duplicates if len(set(labels)) > 1]
    target_before = {label: sum(count for raw, count in raw_counts.items() if raw.strip() == label)
                     for label in TARGETS}
    result = {
        "audit_version": "mtsamples-audit-v1",
        "source": {
            "filename": Path(source).name,
            "sha256": digest,
            "bytes": len(payload),
            "encoding": "utf-8-sig (strict)",
            "upstream_release_version": None,
            "release_identity": "Local bytes identified by SHA-256; remote release equivalence not verified.",
            "provenance_review": "docs/ml/data-audit.md",
        },
        "schema": {"columns": list(COLUMNS), "source_id_column": "", "predictor_column": "transcription"},
        "cleaning": {
            "label_rule": "Strip surrounding label whitespace; exact five-target membership only.",
            "empty_rule": "Exclude transcription when str.strip() is empty.",
            "text_rule": "Preserve every character of retained transcription; no normalization or truncation.",
            "metadata_rule": "Description, sample_name, keywords and row IDs are not predictors.",
        },
        "counts": {
            "source_rows": len(rows),
            "source_categories": len(raw_counts),
            "all_empty_transcriptions": sum(empty_counts.values()),
            "all_nonempty_transcriptions": sum(nonempty_counts.values()),
            "target_rows_before_empty_removal": sum(target_before.values()),
            "target_empty_transcriptions": sum(empty_counts[label] for label in TARGETS),
            "target_nonempty_rows": len(cleaned),
            "non_target_rows": len(rows) - sum(target_before.values()),
        },
        "source_label_counts": dict(sorted(raw_counts.items())),
        "empty_transcriptions_by_label": dict(sorted(empty_counts.items())),
        "label_mapping": [
            {"source_label": raw, "target_label": raw.strip()}
            for raw in sorted(raw_counts) if raw.strip() in TARGETS
        ],
        "target_counts": {
            label: {"before": target_before[label], "empty_removed": empty_counts[label],
                    "after_empty_removal": nonempty_counts[label]}
            for label in TARGETS
        },
        "preliminary_exact_text_inventory": {
            "method": "SHA-256 of unchanged UTF-8 transcription, nonempty targets only.",
            "duplicate_groups": len(duplicates),
            "rows_in_duplicate_groups": sum(map(len, duplicates)),
            "conflicting_target_label_groups": len(conflicts),
            "rows_in_conflicting_groups": sum(map(len, conflicts)),
            "status": "Inspection only; near duplicates and conflict exclusions belong to C-002. No benchmark is frozen.",
        },
        "split_status": "Not created; C-002 prerequisites remain pending.",
        "language_review": "Not performed; source labels and nonempty text do not establish English compliance.",
    }
    return result, cleaned


def render_json(result):
    return json.dumps(result, indent=2, ensure_ascii=True) + "\n"


def render_cleaned(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=("document_id", "source_row_id", "category", "transcription"),
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "raw/mtsamples.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifests/source.json")
    parser.add_argument("--cleaned", type=Path, default=ROOT / "raw/targets-nonempty.csv")
    parser.add_argument("--check", action="store_true", help="Verify existing outputs without writing them.")
    args = parser.parse_args()
    try:
        paths = [p.resolve() for p in (args.source, args.manifest, args.cleaned)]
        if len(set(paths)) != 3:
            raise ValueError("Source, manifest and cleaned output paths must be distinct.")
        result, rows = audit(args.source)
        outputs = ((args.manifest, render_json(result)), (args.cleaned, render_cleaned(rows)))
        for path, content in outputs:
            expected = content.encode("utf-8")
            if args.check:
                if not path.exists() or path.read_bytes() != expected:
                    raise ValueError("Audit output missing or stale; regenerate and review it.")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(expected)
    except (OSError, UnicodeError, csv.Error, ValueError):
        # Parser/OS exceptions can contain source contents or local paths.
        print("Audit failed: check input/schema/unique IDs, distinct paths and output freshness.", file=sys.stderr)
        return 1
    print(json.dumps({"status": "verified" if args.check else "written", "counts": result["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
