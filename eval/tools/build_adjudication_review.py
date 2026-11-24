"""Render a private, offline adjudication packet without publishing source text."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(packet: dict) -> None:
    documents = packet["documents"]
    expected = packet["expected_assignment_ids"]
    if len(expected) != len(set(expected)) or set(documents) != set(expected):
        raise ValueError("The packet must account for every expected assignment exactly once.")
    items = packet["items"]
    ids = [row["item_id"] for row in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate adjudication item ID.")
    covered = set(packet["previously_resolved_item_ids"])
    for row in items:
        if row["assignment_id"] not in documents:
            raise ValueError("Item has no document.")
        if covered.intersection(row["covers"]):
            raise ValueError("An earlier decision or another item already covers this ID.")
        covered.update(row["covers"])
    if covered != set(packet["required_coverage_ids"]):
        raise ValueError("The review omits or invents a required adjudication ID.")
    for aid, document in documents.items():
        if document["assignment_id"] != aid:
            raise ValueError("Document identity mismatch.")
        source = document["canonical_text"]
        if source is None:
            continue
        if digest(source.encode("utf-8")) != document["text_sha256"]:
            raise ValueError("Canonical text hash mismatch.")
        for entity in document["entities"]:
            for span in [entity["mention"], *entity["evidence"]]:
                if not 0 <= span["start"] < span["end"] <= len(source) or source[span["start"]:span["end"]] != span["quote"]:
                    raise ValueError("Candidate span does not match canonical text.")
        for row in (r for r in items if r["assignment_id"] == aid):
            for span in row["source_anchors"]:
                if not 0 <= span["start"] < span["end"] <= len(source) or source[span["start"]:span["end"]] != span["quote"]:
                    raise ValueError("Question anchor does not match canonical text.")


def build(packet_path: Path, output: Path) -> dict:
    raw = packet_path.read_bytes()
    packet = json.loads(raw)
    validate(packet)
    output.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).with_name("adjudication-review.html").read_text(encoding="utf-8")
    script = Path(__file__).with_name("adjudication-review.js").read_text(encoding="utf-8")
    payload = json.dumps(packet, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = template.replace("/* REVIEW_SCRIPT */", script).replace("PACKET_SHA256", digest(raw)).replace("PACKET_DATA", payload)
    (output / "review.html").write_text(page, encoding="utf-8")
    (output / "packet.json").write_bytes(raw)
    return {"version": "d013-complete-adjudication-preparation-v1", "date": "2026-11-23",
            "packet_sha256": digest(raw), "review_html_sha256": digest((output / "review.html").read_bytes()),
            "assignments_accounted_for": len(packet["documents"]), "pending_decision_items": len(packet["items"]),
            "item_categories": {kind: sum(r["category"] == kind for r in packet["items"]) for kind in sorted({r["category"] for r in packet["items"]})},
            "canonical_sources_verified": sum(d["canonical_text"] is not None for d in packet["documents"].values()),
            "canonical_sources_still_required": [aid for aid, d in packet["documents"].items() if d["canonical_text"] is None],
            "coverage_ids_accounted_for": len(packet["required_coverage_ids"]),
            "previously_decided_ids_preserved": len(packet["previously_resolved_item_ids"]),
            "all_known_pending_decisions_accounted_for": True,
            "human_decisions_generated": 0, "original_submissions_modified": False,
            "provider_calls": 0, "unseen_final_qa_sources_accessed": False, "full_d013_closed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args.packet, args.output)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
