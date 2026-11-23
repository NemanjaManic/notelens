"""Bridge pinned, independently reviewed answers to risk without fabricating ratings."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from .answer_review import DIMENSIONS, inspect
from .answer_risk import evaluate_answer_risk

PROTOCOL = "d011-semantic-review-protocol-v1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def outcome(case):
    response = case["response"]
    if response is None:
        return "operational_error"
    return ("partial_answer" if response["evidence_state"] == "partial" else "answer") if response["claims"] else "abstain"


def score_reviewed_packet(packet, reviews, decision):
    if packet.get("version") != "d011-semantic-review-packet-v1" or decision.get("version") != PROTOCOL:
        raise ValueError("Unsupported semantic review protocol.")
    if reviews.get("packet_sha256") != digest(packet):
        raise ValueError("Reviews target another immutable packet.")
    cases = {c["id"]: c for c in packet["cases"]}
    records = reviews["reviews"]
    if not cases or len(cases) != len(packet["cases"]) or len(records) != len(cases):
        raise ValueError("Every pinned case requires exactly one review record.")
    if {r["case_id"] for r in records} != set(cases):
        raise ValueError("Review case IDs differ from the packet.")
    references, predictions, pending = [], [], []
    critical = false_abstentions = 0
    for record in records:
        case = cases[record["case_id"]]
        source = case["request"]["document"]
        if hashlib.sha256(source["text"].encode()).hexdigest() != source["text_sha256"]:
            raise ValueError("Packet canonical source hash changed.")
        if (record["doc_id"], record["text_sha256"], record["response_sha256"]) != (
                source["doc_id"], source["text_sha256"], digest(case["response"])):
            raise ValueError("Review source/response hashes differ from the pinned packet.")
        response = case["response"]
        if record.get("response_id") != case["id"]:
            raise ValueError("Review response ID differs from the pinned case alias.")
        if response is not None and (
                record.get("mode"), record.get("extractor_or_answer_version"), record.get("prompt_version")) != (
                response["mode"], response["answer_version"], response["prompt_version"]):
            raise ValueError("Review mode or version differs from the saved response.")
        action = outcome(case)
        if record.get("response_action") not in (None, action):
            raise ValueError("Review cannot relabel an answer, abstention or technical failure.")
        state = inspect(record, require_current_form=True)
        if action == "operational_error":
            if state != "operational_error" or record.get("answerable_from_document") not in ("yes", "partly", "no"):
                pending.append(case["id"])
                continue
            references.append({"id": case["id"], "answerable": record["answerable_from_document"] in ("yes", "partly"),
                               "answer_correct": None})
            predictions.append({"id": case["id"], "outcome": "technical_error", "confidence": None})
            continue
        eligible = (state == "completed_declared_human_review"
                    and record.get("preparation_involvement") is False
                    and isinstance(record.get("ai_assistance_disclosure"), str)
                    and bool(record["ai_assistance_disclosure"].strip())
                    and isinstance(record.get("reviewer_alias"), str) and bool(record["reviewer_alias"].strip())
                    and record["answerable_from_document"] != "unclear"
                    and not record["needs_adjudication"]
                    and all(record["dimensions"][k] != "U" for k in DIMENSIONS))
        if not eligible:
            pending.append(case["id"])
            continue
        can_answer = record["answerable_from_document"] in ("yes", "partly")
        correct = all(record["dimensions"][k] == 2 for k in DIMENSIONS) and not record["critical_error"]
        critical += int(record["critical_error"])
        false_abstentions += int(action == "abstain" and can_answer)
        references.append({"id": case["id"], "answerable": can_answer,
                           "answer_correct": correct if action in ("answer", "partial_answer") else None})
        predictions.append({"id": case["id"], "outcome": "answered" if action in ("answer", "partial_answer") else "abstained",
                            "confidence": None})
    approved = (decision.get("approved") is True
                and all(isinstance(decision.get(k), str) and decision[k].strip() for k in ("approved_by", "decision_record")))
    if pending or not approved:
        return {"protocol": PROTOCOL, "status": "review_pending" if pending else "protocol_approval_pending",
                "cases": len(cases), "pending_case_ids": pending, "risk": None,
                "human_authorship_independently_verified": False}
    report = evaluate_answer_risk({"version": PROTOCOL, "cases": references},
                                  {"version": packet["version"], "cases": predictions})
    n, errors = report["overall"]["answered"], report["overall"]["incorrect_answers"]
    report.update(protocol=PROTOCOL, status="reviewed", packet_sha256=digest(packet),
                  risk=report["overall"]["risk"],
                  critical_errors=critical, false_abstentions=false_abstentions,
                  human_authorship_independently_verified=False,
                  zero_error_one_sided_95_upper=(1 - math.pow(0.05, 1 / n)) if n and errors == 0 else None,
                  confidence_note="A point risk below 0.05 on a small sample does not establish a 95% risk upper bound below 0.05.")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_bytes())
    result = score_reviewed_packet(load(args.packet), load(args.reviews), load(args.decision))
    args.output.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(json.dumps({"status": result["status"], "risk": result["risk"]}))
    return 0 if result["status"] == "reviewed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
