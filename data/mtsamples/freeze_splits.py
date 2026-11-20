"""Freeze signed-off split membership from local metadata without reading transcriptions."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from draft_splits import SPLITS, group_id_for_documents
from prepare_split_review import DRAFT, build_review
from preview_reviewed_split import group_components, human_exposure, preview, reviewed_pairs


VERSION = "c002-split-v1"
FOUNDATION_COMMIT = "7eb12e56f33240a428f916ba583b9e00077712df"
DEVELOPMENT_SPLITS = ("train", "validation")


def json_bytes(record):
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def freeze(draft, queue, ledger, reconciled, original_queue):
    """Preserve assigned groups and allocate cleared components inside development."""
    if set(reconciled["pair_status_counts"]) - {"duplicate", "non_duplicate", "unresolved"}:
        raise ValueError("Every pair needs a recorded decision before freeze.")
    if any(reconciled["flagged_components_by_reason"].get(reason)
           for reason in ("heldout_component_exposed", "cross_partition_component")):
        raise ValueError("Resolve held-out exposure and cross-partition groups before freeze.")

    groups = {row["group_id"]: row for row in draft["groups"]}
    seed, weights = draft["allocation"]["seed"], draft["allocation"]["weights"]
    reserved, accessed = human_exposure(ledger, groups, seed)
    outcomes = reviewed_pairs(queue, original_queue, accessed)
    components = group_components(groups, outcomes)
    eligible = {tuple(sorted(row["group_ids"])) for row in reconciled["eligible_needing_assignment"]
                if row["development_only"]}
    unsafe_groups = {group_id for row in reconciled["components_needing_review"]
                     for group_id in row["group_ids"]}
    partitions = {split: [] for split in SPLITS}
    counts = Counter()
    new_development_groups = []

    for component in components:
        group_ids = tuple(sorted(component))
        members = [groups[group_id] for group_id in group_ids]
        docs = [{"document_id": doc["document_id"], "specialty": doc["category"]}
                for group in members for doc in group["documents"]]
        group = {"group_id": group_id_for_documents(doc["document_id"] for doc in docs),
                 "documents": sorted(docs, key=lambda doc: doc["document_id"])}
        assigned = {row["draft_split"] for row in members} - {None}
        if assigned:
            split, = assigned
            if unsafe_groups.intersection(group_ids) or any(row["flags"] for row in members):
                raise ValueError("An existing assignment contains a flagged group.")
            partitions[split].append(group)
            counts[split, docs[0]["specialty"]] += len(docs)
        elif group_ids in eligible:
            new_development_groups.append(group)

    # Use the original allocator's order and per-specialty deficit, with test locked.
    totals = Counter()
    for (_, label), amount in counts.items():
        totals[label] += amount
    for group in new_development_groups:
        totals[group["documents"][0]["specialty"]] += len(group["documents"])
    for group in sorted(new_development_groups,
                        key=lambda row: (-len(row["documents"]), sha256((seed + row["group_id"]).encode()).hexdigest())):
        docs = group["documents"]
        label = docs[0]["specialty"]
        split = max(DEVELOPMENT_SPLITS, key=lambda name: totals[label] * weights[name] - counts[name, label] * 100)
        partitions[split].append(group)
        counts[split, label] += len(docs)

    test_ids = {doc["document_id"] for group in partitions["test"] for doc in group["documents"]}
    prior_test_ids = {doc["document_id"] for group in groups.values() if group["draft_split"] == "test"
                      for doc in group["documents"]}
    exposed_ids = {doc["document_id"] for group_id in reserved for doc in groups[group_id]["documents"]}
    assigned_ids = [doc["document_id"] for part in partitions.values() for group in part for doc in group["documents"]]
    if test_ids != prior_test_ids or test_ids & exposed_ids or len(assigned_ids) != len(set(assigned_ids)):
        raise ValueError("Freeze would change test membership or assign a document more than once.")
    return partitions, counts, len(new_development_groups)


def build_files(draft_path, receipt_path, review_dir):
    draft_bytes, receipt_bytes = draft_path.read_bytes(), receipt_path.read_bytes()
    draft, receipt = json.loads(draft_bytes), json.loads(receipt_bytes)
    inputs = {name: (review_dir / filename).read_bytes() for name, filename in (
        ("development_exposure", "development-exposure.json"),
        ("signed_off_queue", "duplicate-review-queue-signed-off.json"),
        ("signed_off_preview", "split-preview-signed-off.json"),
    )}
    signoff_bytes = (review_dir / "review-signoff.json").read_bytes()
    signoff = json.loads(signoff_bytes)
    digests = {name: sha256(payload).hexdigest() for name, payload in inputs.items()}
    if (signoff["status"] != "pair decisions signed off by Sara" or signoff["confirmed_by"] != "Sara"
            or signoff["foundation_commit"] != FOUNDATION_COMMIT or signoff["sha256"] != digests):
        raise ValueError("The review artifacts do not match the local confirmation.")

    queue, ledger = json.loads(inputs["signed_off_queue"]), json.loads(inputs["development_exposure"])
    original_queue, original_ledger = build_review(
        draft, receipt, sha256(draft_bytes).hexdigest(), sha256(receipt_bytes).hexdigest(),
    )
    reconciled = preview(draft, queue, ledger, original_queue, original_ledger)
    if reconciled != json.loads(inputs["signed_off_preview"]):
        raise ValueError("The signed-off split preview cannot be reproduced.")
    partitions, counts, allocated = freeze(draft, queue, ledger, reconciled, original_queue)
    common = {"manifest_version": VERSION, "foundation_commit": FOUNDATION_COMMIT,
              "source_sha256": draft["source_sha256"], "seed": draft["allocation"]["seed"]}
    files = {f"{split}.json": json_bytes({
        **common, "split": split, "groups": sorted(groups, key=lambda group: group["group_id"]),
    }) for split, groups in partitions.items()}
    summary = {
        **common, "status": "frozen local split membership",
        "allocation": {"preferred_weights": draft["allocation"]["weights"],
                       "new_reviewed_components": "development only by per-specialty target deficit"},
        "review_outcomes": reconciled["pair_status_counts"],
        "review_signoff_sha256": sha256(signoff_bytes).hexdigest(),
        "draft_sha256": sha256(draft_bytes).hexdigest(),
        "documents_per_split": {split: sum(n for (name, _), n in counts.items() if name == split) for split in SPLITS},
        "specialty_support": {split: {label: n for (name, label), n in counts.items() if name == split} for split in SPLITS},
        "excluded_documents": sum(len(group["documents"]) for group in draft["groups"]) - sum(counts.values()),
        "new_development_groups": allocated,
        "split_checksums": {name: sha256(payload).hexdigest() for name, payload in files.items()},
    }
    files["manifest.json"] = json_bytes(summary)
    return files, summary


def verify_frozen(output_dir, manifest_checksum):
    """Verify the signed-off bytes using a pinned digest without source-row mappings."""
    manifest_bytes = (output_dir / "manifest.json").read_bytes()
    if sha256(manifest_bytes).hexdigest() != manifest_checksum:
        raise ValueError("The frozen summary differs from its pinned SHA-256.")
    summary = json.loads(manifest_bytes)
    if (summary["manifest_version"] != VERSION or summary["foundation_commit"] != FOUNDATION_COMMIT
            or summary["status"] != "frozen local split membership"):
        raise ValueError("Expected a C-002 frozen split summary.")
    for split in SPLITS:
        filename = f"{split}.json"
        payload = (output_dir / filename).read_bytes()
        if sha256(payload).hexdigest() != summary["split_checksums"][filename]:
            raise ValueError("A frozen partition differs from its recorded SHA-256.")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-receipt", type=Path)
    parser.add_argument("--review-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Reproduce the freeze from its original review inputs.")
    mode.add_argument("--verify-frozen", metavar="SHA256", help="Verify the frozen manifests without the review mapping.")
    args = parser.parse_args()
    if args.verify_frozen is None and args.development_receipt is None:
        parser.error("--development-receipt is required to build or reproduce a freeze.")
    raw = DRAFT.parent.resolve()
    review_dir = args.review_dir.resolve()
    if not review_dir.is_relative_to(raw) or review_dir == raw:
        parser.error("Use a review directory inside the Git-ignored local raw directory.")
    output_dir = review_dir / VERSION
    try:
        if args.verify_frozen is not None:
            summary = verify_frozen(output_dir, args.verify_frozen.lower())
        elif args.check:
            files, summary = build_files(DRAFT, args.development_receipt, review_dir)
            if any((output_dir / name).read_bytes() != data for name, data in files.items()):
                raise ValueError("Frozen manifests differ from the reproducible result.")
        else:
            if output_dir.exists():
                raise ValueError("The version already exists. Use --verify-frozen to verify it.")
            files, summary = build_files(DRAFT, args.development_receipt, review_dir)
            with TemporaryDirectory(dir=review_dir) as staging:
                pending = Path(staging) / VERSION
                pending.mkdir()
                for name, data in files.items():
                    (pending / name).write_bytes(data)
                pending.rename(output_dir)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(1, f"Split freeze failed ({type(error).__name__}). Verify the local inputs and output version.\n")
    print(json.dumps({key: summary[key] for key in
                      ("manifest_version", "documents_per_split", "excluded_documents", "new_development_groups")}))


if __name__ == "__main__":
    main()
