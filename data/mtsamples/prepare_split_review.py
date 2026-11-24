"""Prepare a local duplicate review queue and exposure ledger from metadata only."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit import ROOT


CACHE = ROOT.parents[1] / ".cache"
DRAFT = ROOT / "raw/c002-provisional.json"


def build_review(draft, metrics, draft_sha256, receipt_sha256):
    if (not draft["status"].startswith("DRAFT") or metrics["test_scored"] is not False
            or metrics["split_sha256"] != draft_sha256 or metrics["source_sha256"] != draft["source_sha256"]):
        raise ValueError("The executed development receipt does not match the provisional split.")
    groups = {}
    documents = set()
    exposed = {"train": [], "validation": []}
    for group in draft["groups"]:
        group_id, split = group["group_id"], group["draft_split"]
        document_ids = sorted(row["document_id"] for row in group["documents"])
        if (group_id in groups or not document_ids or len(set(document_ids)) != len(document_ids)
                or documents.intersection(document_ids) or (group["flags"] and split is not None)
                or split not in (None, "train", "validation", "test")):
            raise ValueError("The provisional group inventory is inconsistent.")
        groups[group_id] = group
        documents.update(document_ids)
        if split in exposed:
            exposed[split].append({"group_id": group_id, "document_ids": document_ids})

    for name, entries in exposed.items():
        if len(entries) != metrics[f"{name}_groups"] or sum(len(row["document_ids"]) for row in entries) != metrics[f"{name}_rows"]:
            raise ValueError("Development group counts do not match the executed receipt.")
        entries.sort(key=lambda row: row["group_id"])

    pairs = []
    seen = set()
    for pair in draft["near_candidates"]:
        left, right = pair["group_a"], pair["group_b"]
        key = tuple(sorted((left, right)))
        overlap, size_a, size_b = pair["intersection"], pair["shingles_a"], pair["shingles_b"]
        if (left == right or key in seen or pair["decision"] != "unresolved"
                or not 0 < overlap <= min(size_a, size_b)):
            raise ValueError("The duplicate candidate inventory is inconsistent.")
        seen.add(key)
        parties = []
        for group_id in (left, right):
            group = groups[group_id]
            if group["draft_split"] is not None or "unresolved_near_candidate" not in group["flags"]:
                raise ValueError("A pending duplicate group is not quarantined.")
            parties.append({
                "group_id": group_id,
                "labels": group["labels"],
                "document_ids": sorted(row["document_id"] for row in group["documents"]),
                "review_exposure": "not_recorded",
            })
        pairs.append({
            "groups": parties,
            "intersection": overlap,
            "shingle_counts": [size_a, size_b],
            "jaccard": overlap / (size_a + size_b - overlap),
            "containment": overlap / min(size_a, size_b),
            "status": "pending_review",
            "reviewer": None,
            "review_date": None,
            "decision": None,
            "reason": None,
        })
    metadata = {"source_sha256": draft["source_sha256"], "draft_sha256": draft_sha256}
    return (
        {**metadata, "status": "provisional review queue", "pairs": pairs},
        {**metadata, "status": "development exposure from recorded model use",
         "development_receipt_sha256": receipt_sha256, "training": exposed["train"],
         "validation": exposed["validation"], "test_scored_by_receipt": False},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(CACHE.resolve()) or not output.parent.is_dir():
        parser.error("Choose a new output directory in the ignored repository cache.")
    try:
        draft_bytes, receipt_bytes = DRAFT.read_bytes(), args.development_receipt.read_bytes()
        queue, exposure = build_review(
            json.loads(draft_bytes), json.loads(receipt_bytes),
            sha256(draft_bytes).hexdigest(), sha256(receipt_bytes).hexdigest(),
        )
        output.mkdir(exist_ok=False)
        for filename, data in (("duplicate-review-queue.json", queue), ("development-exposure.json", exposure)):
            (output / filename).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError):
        print("Split review preparation failed. Verify the draft, executed receipt and output path.", file=sys.stderr)
        return 1
    print(json.dumps({"pending_pairs": len(queue["pairs"]), "training_groups": len(exposure["training"]),
                      "validation_groups": len(exposure["validation"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
