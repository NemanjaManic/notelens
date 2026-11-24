"""Create an ignored, provisional C-002 analysis; never output document bodies."""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

from audit import ROOT, TARGETS, audit

SOURCE = ROOT / "raw/mtsamples.csv"
AUDIT = ROOT / "manifests/source.json"
OUTPUT = ROOT / "raw/c002-provisional.json"
SEED = "c002-draft-v1"
SPLITS = ("train", "validation", "test")
WEIGHTS = (70, 15, 15)
TOKEN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def group_id_for_documents(document_ids):
    encoded = json.dumps(sorted(document_ids), ensure_ascii=True, separators=(",", ":"))
    return "group-" + digest(encoded)


def comparison(text):
    return " ".join(unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).casefold().split())


def shingles(text):
    words = TOKEN.findall(text)
    return {tuple(words[i:i + 5]) for i in range(len(words) - 4)}


def build(rows):
    """Inspect all target texts; output metadata only, never review labels as gold."""
    identifiers = [row["document_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate document IDs cannot be assigned safely.")
    grouped = defaultdict(list)
    for row in rows:
        grouped[comparison(row["transcription"])].append(row)
    groups = []
    for value, members in grouped.items():
        gid = group_id_for_documents(row["document_id"] for row in members)
        groups.append({"group_id": gid, "rows": sorted(members, key=lambda row: row["document_id"]),
                       "shingles": shingles(value)})
    groups.sort(key=lambda group: group["group_id"])
    # Count intersections exhaustively using an inverted index, with exact integer
    # comparisons. Thresholds are draft screening parameters, not reviewed decisions.
    index = defaultdict(list)
    for i, group in enumerate(groups):
        for shingle in group["shingles"]:
            index[shingle].append(i)
    intersections = Counter()
    for members in index.values():
        for offset, i in enumerate(members):
            for j in members[offset + 1:]:
                intersections[(i, j)] += 1
    candidates = []
    quarantined = set()
    for (i, j), common in sorted(intersections.items()):
        a, b = len(groups[i]["shingles"]), len(groups[j]["shingles"])
        union = a + b - common
        if common * 100 >= 80 * union or common * 100 >= 95 * min(a, b):
            quarantined.update((i, j))
            candidates.append({"group_a": groups[i]["group_id"], "group_b": groups[j]["group_id"],
                               "intersection": common, "shingles_a": a, "shingles_b": b,
                               "decision": "unresolved"})
    results = []
    for i, group in enumerate(groups):
        labels = sorted({row["category"] for row in group["rows"]})
        flags = []
        if len(labels) > 1:
            flags.append("conflicting_target_labels")
        if i in quarantined:
            flags.append("unresolved_near_candidate")
        if not group["shingles"]:
            flags.append("short_text_unreviewed")
        if any(len(unicodedata.normalize("NFC", r["transcription"].replace("\r\n", "\n").replace("\r", "\n"))) > 100000 for r in group["rows"]):
            flags.append("over_provisional_text_limit")
        records = [{"document_id": row["document_id"], "source_row_id": row["source_row_id"],
                    "category": row["category"], "source_text_sha256": digest(row["transcription"])}
                   for row in group["rows"]]
        results.append({"group_id": group["group_id"], "labels": labels, "flags": flags,
                        "documents": records, "draft_split": None})
    # Group-disjoint illustrative allocation, stratified by label. This is not a
    # final split, not annotation material and never selected by model performance.
    for label in TARGETS:
        eligible = [g for g in results if not g["flags"] and g["labels"] == [label]]
        eligible.sort(key=lambda g: (-len(g["documents"]), digest(SEED + g["group_id"])))
        total = sum(len(g["documents"]) for g in eligible)
        assigned = [0, 0, 0]
        for group in eligible:
            split = max(range(3), key=lambda x: (total * WEIGHTS[x] - assigned[x] * 100, -x))
            group["draft_split"] = SPLITS[split]
            assigned[split] += len(group["documents"])
    return results, candidates


def summary(groups, candidates):
    flags = Counter(flag for group in groups for flag in group["flags"])
    by_class = {label: {split: sum(len(g["documents"]) for g in groups if g["labels"] == [label] and g["draft_split"] == split)
                         for split in SPLITS} for label in TARGETS}
    return {"target_rows": sum(len(g["documents"]) for g in groups), "comparison_groups": len(groups),
            "conflicting_groups": flags["conflicting_target_labels"],
            "conflicting_rows": sum(len(g["documents"]) for g in groups if "conflicting_target_labels" in g["flags"]),
            "near_candidate_pairs": len(candidates), "unresolved_near_groups": flags["unresolved_near_candidate"],
            "short_groups": flags["short_text_unreviewed"], "over_limit_groups": flags["over_provisional_text_limit"],
            "excluded_or_quarantined_rows": sum(len(g["documents"]) for g in groups if g["flags"]),
            "draft_split_class_counts": by_class}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the existing draft without overwriting it.")
    args = parser.parse_args()
    source_meta = json.loads(AUDIT.read_text(encoding="utf-8"))
    measured, rows = audit(SOURCE)
    if measured["source"]["sha256"] != source_meta["source"]["sha256"]:
        raise ValueError("Source checksum differs from the audited source.")
    groups, candidates = build(rows)
    output = {"status": "DRAFT - NOT FROZEN OR APPROVED FOR TRAINING OR ANNOTATION",
              "source_sha256": measured["source"]["sha256"],
              "method": "NFC, LF, casefold, whitespace collapse; five-token shingle screening",
              "unicode_version": unicodedata.unidata_version,
              "python_version": sys.version.split()[0],
              "screening": "draft: Jaccard >= 0.80 or minimum-side containment >= 0.95; unresolved, not adjudicated",
              "allocation": {"seed": SEED, "weights": dict(zip(SPLITS, WEIGHTS)), "status": "illustrative only"},
              "summary": summary(groups, candidates), "groups": groups, "near_candidates": candidates}
    rendered = (json.dumps(output, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != rendered:
            raise ValueError("Draft is missing or stale; inspect the source and regenerate.")
    else:
        OUTPUT.write_bytes(rendered)
    print(json.dumps({"status": "verified" if args.check else "written",
                      "output": "data/mtsamples/raw/c002-provisional.json", "summary": output["summary"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError, KeyError, csv.Error):
        print("Draft analysis failed: check the audited input, unique IDs and draft freshness.", file=sys.stderr)
        sys.exit(1)
