"""Reconcile duplicate decisions and exposure into a local, provisional split preview."""

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

from audit import TARGETS
from draft_splits import group_id_for_documents
from prepare_split_review import CACHE, DRAFT, build_review


REVIEW_FIELDS = {"status", "decision", "reviewer", "review_date", "reason"}
PARTITIONS = ("train", "validation", "test")


def review_date(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Review dates must use YYYY-MM-DD.")
    return value


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def review_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Review timestamps must be strings with a timezone.")
    event = datetime.fromisoformat(value)
    if event.utcoffset() is None:
        raise ValueError("Review timestamps must include a timezone.")
    return event


def exposure_documents(entry, groups):
    group = groups[entry["group_id"]]
    ids = entry["document_ids"]
    if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
            or not set(ids) <= {row["document_id"] for row in group["documents"]}
            or not is_text(entry["reviewer"])):
        raise ValueError("A review exposure entry does not match the provisional group.")
    return ids


def human_exposure(ledger, groups, split_version=None):
    development = set()
    reviewed = set()
    reservations = defaultdict(list)
    for entry in ledger.get("reviews", []):
        ids = exposure_documents(entry, groups)
        if not is_text(entry["purpose"]):
            raise ValueError("An exposure reservation requires a purpose.")
        group_id = entry["group_id"]
        recorded_date = review_date(entry["review_date"])
        development.add(group_id)
        if "reserved_at" in entry or "split_version" in entry:
            moment = review_timestamp(entry["reserved_at"])
            if not split_version or entry["split_version"] != split_version or moment.date().isoformat() != recorded_date:
                raise ValueError("The reserve timestamp or split version is inconsistent.")
            for doc_id in ids:
                reservations[group_id, doc_id, entry["reviewer"]].append(moment)
        else:
            # Preserve existing date-only review records.
            reviewed.add((group_id, recorded_date))

    for entry in ledger.get("accesses", []):
        ids = exposure_documents(entry, groups)
        group_id = entry["group_id"]
        if entry["split_version"] != split_version or not is_text(entry["reviewed"]):
            raise ValueError("An access record requires the current split version and review scope.")
        moment = review_timestamp(entry["accessed_at"])
        for doc_id in ids:
            if not any(when <= moment for when in reservations.get((group_id, doc_id, entry["reviewer"]), ())):
                raise ValueError("Document access must follow a reservation by the recorded reviewer.")
        reviewed.add((group_id, moment.date().isoformat()))
    return development, reviewed


def reviewed_pairs(queue, expected_queue, exposed):
    if ({key: value for key, value in queue.items() if key != "pairs"}
            != {key: value for key, value in expected_queue.items() if key != "pairs"}):
        raise ValueError("The review queue does not match the draft metadata.")
    earliest_exposure = {}
    for group, reviewed_on in sorted(exposed, key=lambda entry: entry[1]):
        earliest_exposure.setdefault(group, reviewed_on)
    expected_by_pair = {tuple(group["group_id"] for group in row["groups"]): row for row in expected_queue["pairs"]}
    outcomes = []
    for row in queue["pairs"]:
        groups = tuple(group["group_id"] for group in row["groups"])
        expected = expected_by_pair.pop(groups, None)
        if expected is None:
            raise ValueError("An unexpected or repeated pair was found in the review queue.")
        if ({key: value for key, value in row.items() if key not in REVIEW_FIELDS}
                != {key: value for key, value in expected.items() if key not in REVIEW_FIELDS}):
            raise ValueError("A review pair differs from the generated queue.")
        if row["status"] == "pending_review":
            if any(row[key] is not None for key in REVIEW_FIELDS - {"status"}):
                raise ValueError("Pending pairs may not contain adjudication fields.")
            outcomes.append((groups, "pending_review"))
            continue
        if (row["status"] != "reviewed" or row["decision"] not in ("duplicate", "non_duplicate", "unresolved")
                or not is_text(row["reviewer"]) or not is_text(row["reason"])):
            raise ValueError("A reviewed pair requires a supported decision, reviewer and reason.")
        decided_on = review_date(row["review_date"])
        if any(group not in earliest_exposure or earliest_exposure[group] > decided_on for group in groups):
            outcomes.append((groups, "missing_review_exposure"))
        else:
            outcomes.append((groups, row["decision"]))
    if expected_by_pair:
        raise ValueError("A generated pair is missing from the review queue.")
    return sorted(outcomes)


def group_components(group_ids, outcomes):
    parent = {group_id: group_id for group_id in group_ids}

    def representative(group_id):
        while parent[group_id] != group_id:
            parent[group_id] = parent[parent[group_id]]
            group_id = parent[group_id]
        return group_id

    for (left, right), status in outcomes:
        if status == "duplicate":
            first, second = sorted((representative(left), representative(right)))
            parent[second] = first

    components = defaultdict(list)
    for group_id in sorted(parent):
        components[representative(group_id)].append(group_id)
    for (left, right), status in outcomes:
        if status == "non_duplicate" and representative(left) == representative(right):
            raise ValueError("Duplicate decisions conflict with a transitive non-duplicate decision.")
    return components.values()


def preview(draft, queue, ledger, expected_queue, expected_ledger):
    if {key: value for key, value in ledger.items() if key not in ("reviews", "accesses")} != expected_ledger:
        raise ValueError("The model exposure ledger does not match the executed development receipt.")
    groups = {group["group_id"]: group for group in draft["groups"]}
    reserved_groups, reviewed = human_exposure(ledger, groups, draft.get("allocation", {}).get("seed"))
    outcomes = reviewed_pairs(queue, expected_queue, reviewed)
    development_ids = {entry["group_id"] for entry in ledger["training"] + ledger["validation"]}
    development_ids.update(reserved_groups)

    pending = defaultdict(set)
    for group_ids, status in outcomes:
        if status not in ("duplicate", "non_duplicate"):
            for group_id in group_ids:
                pending[group_id].add(status)

    retained = {name: Counter() for name in PARTITIONS}
    group_counts = {name: Counter() for name in PARTITIONS}
    unassigned, needs_review, group_changes = [], [], []
    unassigned_documents = unassigned_components = 0
    flags_count = Counter()
    components = group_components(groups, outcomes)
    for member_ids in components:
        members = [groups[group_id] for group_id in member_ids]
        flags = {flag for member in members for flag in member["flags"] if flag != "unresolved_near_candidate"}
        pending_reasons = {reason for group_id in member_ids for reason in pending.get(group_id, ())}
        flags.update(pending_reasons)
        labels = sorted({label for member in members for label in member["labels"]})
        if not set(labels) <= set(TARGETS):
            raise ValueError("A component carries a label outside the five target specialties.")
        documents = sum(len(member["documents"]) for member in members)
        existing = {member["draft_split"] for member in members if member["draft_split"] is not None}
        development_only = bool(development_ids.intersection(member_ids))
        if len(labels) != 1:
            flags.add("conflicting_target_labels")
        if "test" in existing and development_only:
            flags.add("heldout_component_exposed")
        if len(existing) > 1:
            flags.add("cross_partition_component")

        if len(members) > 1:
            previous_groups = [
                {"group_id": member["group_id"], "split": member["draft_split"],
                 "document_ids": sorted(row["document_id"] for row in member["documents"])}
                for member in members
            ]
            group_changes.append({
                "previous_groups": previous_groups,
                "new_group_id": group_id_for_documents(
                    doc_id for group in previous_groups for doc_id in group["document_ids"]
                ),
                "proposed_split": next(iter(existing)) if existing and not flags else None,
                "development_only": development_only,
                "reason": "Confirmed duplicate review",
            })

        if flags:
            flags_count.update(flags)
            # Keep the already-excluded routine audit groups out of the detailed review list.
            if development_only or pending_reasons:
                needs_review.append({"group_ids": member_ids, "flags": sorted(flags), "development_only": development_only})
        elif existing:
            partition, = existing
            retained[partition][labels[0]] += documents
            group_counts[partition][labels[0]] += 1
            continue
        else:
            unassigned.append({"group_ids": member_ids, "label": labels[0], "documents": documents,
                               "development_only": development_only})
        unassigned_documents += documents
        unassigned_components += 1

    partition_summary = {
        partition: {
            "documents": sum(retained[partition].values()),
            "groups": sum(group_counts[partition].values()),
            "documents_per_label": {label: retained[partition][label] for label in TARGETS},
            "groups_per_label": {label: group_counts[partition][label] for label in TARGETS},
        }
        for partition in PARTITIONS
    }
    if (sum(entry["documents"] for entry in partition_summary.values()) + unassigned_documents
            != draft["summary"]["target_rows"]):
        raise ValueError("Document totals do not reconcile with the provisional draft.")
    result = {
        "status": "provisional preview for review",
        "source_sha256": expected_queue["source_sha256"],
        "draft_sha256": expected_queue["draft_sha256"],
        "pair_status_counts": dict(sorted(Counter(status for _, status in outcomes).items())),
        "development_groups_recorded": len(development_ids),
        "retained_partitions": partition_summary,
        "unassigned_documents": unassigned_documents,
        "unassigned_components": unassigned_components,
        "flagged_components_by_reason": dict(sorted(flags_count.items())),
        "eligible_needing_assignment": unassigned,
        "components_needing_review": needs_review,
    }
    if group_changes:
        result["group_changes"] = group_changes
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-receipt", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--exposure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(CACHE.resolve()) or not output.parent.is_dir():
        parser.error("Choose a new JSON output path in the ignored repository cache.")
    try:
        draft_bytes, receipt_bytes = DRAFT.read_bytes(), args.development_receipt.read_bytes()
        draft = json.loads(draft_bytes)
        queue_bytes, exposure_bytes = args.queue.read_bytes(), args.exposure.read_bytes()
        expected_queue, expected_ledger = build_review(
            draft, json.loads(receipt_bytes), sha256(draft_bytes).hexdigest(), sha256(receipt_bytes).hexdigest()
        )
        report = preview(draft, json.loads(queue_bytes), json.loads(exposure_bytes), expected_queue, expected_ledger)
        report["input_sha256"] = {
            "queue": sha256(queue_bytes).hexdigest(),
            "exposure": sha256(exposure_bytes).hexdigest(),
            "development_receipt": sha256(receipt_bytes).hexdigest(),
        }
        payload = json.dumps(report, indent=2) + "\n"
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
    except (OSError, ValueError, KeyError, TypeError):
        print("Split preview failed. Verify the draft, review records and output path.", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": report["status"], "pair_status_counts": report["pair_status_counts"],
        "development_groups_recorded": report["development_groups_recorded"],
        "retained_documents": {key: value["documents"] for key, value in report["retained_partitions"].items()},
        "unassigned_documents": report["unassigned_documents"],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
