"""Record authorized pair-review metadata in a new local copy."""

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sys

from prepare_split_review import CACHE, DRAFT, build_review
from preview_reviewed_split import human_exposure, is_text, preview, review_date, review_timestamp, reviewed_pairs


DECISIONS = ("duplicate", "non_duplicate", "unresolved")


def pair_at(queue, original_queue, number):
    if not 1 <= number <= len(original_queue["pairs"]):
        raise ValueError("The pair number is outside the generated queue.")
    original = original_queue["pairs"][number - 1]
    return next(row for row in queue["pairs"] if row["groups"] == original["groups"])


def reserve_pair(queue, ledger, original_queue, number, reviewer, reviewed_on, purpose, *,
                 split_version=None, reserved_at=None):
    if not is_text(reviewer) or not is_text(purpose):
        raise ValueError("An exposure reservation requires a reviewer and purpose.")
    reviewed_on = review_date(reviewed_on)
    pair = pair_at(queue, original_queue, number)
    updated = deepcopy(ledger)
    entries = updated.setdefault("reviews", [])
    for group in pair["groups"]:
        reservation = {
            "group_id": group["group_id"], "document_ids": list(group["document_ids"]),
            "reviewer": reviewer, "review_date": reviewed_on, "purpose": purpose,
        }
        if reserved_at is not None:
            reservation.update(split_version=split_version, reserved_at=review_timestamp(reserved_at).isoformat())
        if reservation not in entries:
            entries.append(reservation)
    return updated


def record_access(queue, ledger, original_queue, number, reviewer, occurred_at, document_ids, scope, split_version):
    if (not is_text(reviewer) or not is_text(scope) or not document_ids
            or len(set(document_ids)) != len(document_ids)):
        raise ValueError("Access requires a reviewer, distinct document IDs and review scope.")
    pair = pair_at(queue, original_queue, number)
    timestamp = review_timestamp(occurred_at).isoformat()
    selected = set(document_ids)
    pair_documents = {doc_id for group in pair["groups"] for doc_id in group["document_ids"]}
    if not selected <= pair_documents:
        raise ValueError("An accessed document is outside the selected pair.")
    updated = deepcopy(ledger)
    entries = updated.setdefault("accesses", [])
    for group in pair["groups"]:
        matched = sorted(selected.intersection(group["document_ids"]))
        if matched:
            access = {"group_id": group["group_id"], "document_ids": matched, "reviewer": reviewer,
                      "split_version": split_version, "accessed_at": timestamp, "reviewed": scope}
            if access not in entries:
                entries.append(access)
    return updated


def record_decision(draft, queue, ledger, original_queue, number, reviewer, reviewed_on, decision, reason):
    if decision not in DECISIONS or not is_text(reviewer) or not is_text(reason):
        raise ValueError("A decision requires its reviewer and reason.")
    updated = deepcopy(queue)
    pair = pair_at(updated, original_queue, number)
    pair.update(status="reviewed", reviewer=reviewer, review_date=review_date(reviewed_on),
                decision=decision, reason=reason)
    groups = {group["group_id"]: group for group in draft["groups"]}
    _, exposures = human_exposure(ledger, groups, draft.get("allocation", {}).get("seed"))
    key = tuple(group["group_id"] for group in pair["groups"])
    if dict(reviewed_pairs(updated, original_queue, exposures))[key] != decision:
        raise ValueError("Both groups need recorded exposure by this decision date.")
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development-receipt", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--exposure", type=Path, required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    reserve = actions.add_parser("reserve", help="Record development exposure before opening a reviewed pair.")
    access = actions.add_parser("access", help="Record which reserved documents the reviewer actually opened.")
    decide = actions.add_parser("decide", help="Record a review decision after exposure is documented.")
    for action in (reserve, access, decide):
        action.add_argument("--pair", type=int, required=True, help="One-based row number in the generated queue.")
        action.add_argument("--reviewer", required=True)
        action.add_argument("--output", type=Path, required=True)
    for action in (reserve, decide):
        action.add_argument("--date", required=True, help="Review date in YYYY-MM-DD format.")
    reserve.add_argument("--purpose", required=True)
    reserve.add_argument("--at", help="Reservation time with timezone. Defaults to the current local time.")
    access.add_argument("--at", required=True, help="Actual access time with timezone.")
    access.add_argument("--document-id", action="append", required=True, help="Repeat for each document opened.")
    access.add_argument("--reviewed", required=True, help="What was reviewed, without excerpts or personal details.")
    decide.add_argument("--decision", choices=DECISIONS, required=True)
    decide.add_argument("--reason", required=True, help="Brief reason without text excerpts or personal details.")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(CACHE.resolve()) or not output.parent.is_dir():
        parser.error("Choose a new JSON output path in the ignored repository cache.")
    try:
        draft_bytes, receipt_bytes = DRAFT.read_bytes(), args.development_receipt.read_bytes()
        draft = json.loads(draft_bytes)
        queue, ledger = json.loads(args.queue.read_bytes()), json.loads(args.exposure.read_bytes())
        expected_queue, expected_ledger = build_review(
            draft, json.loads(receipt_bytes), sha256(draft_bytes).hexdigest(), sha256(receipt_bytes).hexdigest()
        )
        preview(draft, queue, ledger, expected_queue, expected_ledger)
        if args.action == "reserve":
            reserved_at = args.at or datetime.now().astimezone().isoformat(timespec="seconds")
            ledger = reserve_pair(queue, ledger, expected_queue, args.pair, args.reviewer, args.date, args.purpose,
                                  split_version=draft["allocation"]["seed"], reserved_at=reserved_at)
            payload = ledger
        elif args.action == "access":
            ledger = record_access(queue, ledger, expected_queue, args.pair, args.reviewer, args.at,
                                   args.document_id, args.reviewed, draft["allocation"]["seed"])
            payload = ledger
        else:
            queue = record_decision(draft, queue, ledger, expected_queue, args.pair, args.reviewer,
                                    args.date, args.decision, args.reason)
            payload = queue
        report = preview(draft, queue, ledger, expected_queue, expected_ledger)
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2) + "\n")
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        print("Review record failed. Check the pair, prior exposure records, inputs and new output path.",
              file=sys.stderr)
        return 1
    print(json.dumps({"action": args.action, "pair": args.pair, "status": report["status"],
                      "pair_status_counts": report["pair_status_counts"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
