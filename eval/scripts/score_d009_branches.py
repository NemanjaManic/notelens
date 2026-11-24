"""Branch-level structural scoring of a saved D-009 run against Sara's references.

Reuses the final_qa.py checks (schema, document code-point spans, literal literature
membership) per accepted branch record, plus web-level route/state agreement and a
cited-source retrieval proxy. Writes aggregate-only results (no case text).
"""
import hashlib
import json
import sys
from pathlib import Path

from notelens_extraction.contracts import validate_schema
from notelens_extraction.evidence import EvidenceError, validate_span, validate_text

run_dir, refs_path, retr_path, out_path = map(Path, sys.argv[1:5])
refs = json.loads(refs_path.read_text(encoding="utf-8"))
retr = {c["id"]: c for c in json.loads(retr_path.read_text(encoding="utf-8"))["cases"]}
saved = {}
for p in sorted(run_dir.glob("case-*.json")):
    record = json.loads(p.read_text(encoding="utf-8"))
    saved[record["case_id"]] = record

rows, totals = [], {"cases": 0, "executed": 0, "technical_errors": 0, "route_match": 0, "state_match": 0,
                    "branches": 0, "branches_schema_valid": 0, "branches_literal_valid": 0,
                    "branches_context_missing": 0, "unsupported_branches": 0,
                    "unavailable_branches": 0, "completed_cases": 0,
                    "saved_unavailable_cases": 0}
retrieval = {"cases": 0, "executed": 0, "topic_hit": 0, "topic_denominator": 0,
             "passage_group_coverage_sum": 0.0, "passage_denominator": 0}
for case in refs["cases"]:
    totals["cases"] += 1
    cid = case["id"]
    row = {"id": cid, "case_version": case["case_version"], "executed": cid in saved}
    document = case.get("document")
    passages = {p["passage_id"]: p for p in case.get("passages", [])}
    for p in passages.values():
        assert hashlib.sha256(p["text"].encode("utf-8")).hexdigest() == p["text_sha256"]
    if document is not None:
        validate_text(document["text"], document["text_sha256"])
    if cid not in saved:
        totals["technical_errors"] += 1
        row["error"] = "technical_error_not_executed"
    else:
        totals["executed"] += 1
        record = saved[cid]
        assert record["case_version"] == case["case_version"]
        answer = record["answer"]
        unavailable = answer.get("state") == "unavailable" or any(
            b["result"]["kind"] not in ("accepted", "unsupported") for b in answer["branches"])
        if unavailable:
            totals["saved_unavailable_cases"] += 1
            totals["technical_errors"] += 1
            row["error"] = "technical_error_saved_unavailable"
        else:
            totals["completed_cases"] += 1
        row["route_match"] = answer["route"] == case.get("expected_answer_route")
        row["state_match"] = answer["state"] == case.get("expected_evidence_state")
        totals["route_match"] += row["route_match"]
        totals["state_match"] += row["state_match"]
        branch_rows = []
        for branch in answer["branches"]:
            totals["branches"] += 1
            kind = branch["result"]["kind"]
            b = {"origin": branch["origin"], "kind": kind, "schema_valid": False, "literal_valid": False}
            if kind != "accepted":
                totals["unsupported_branches" if kind == "unsupported" else "unavailable_branches"] += 1
                branch_rows.append(b)
                continue
            result = branch["result"]["record"]
            try:
                assert result.get("mode") == "live"
                validate_schema(result, "AnswerResult", document=document if branch["origin"] == "document" else None)
                b["schema_valid"] = True
                totals["branches_schema_valid"] += 1
                missing = False
                for source in result["sources"]:
                    if source["kind"] == "document":
                        if document is None:
                            missing = True
                            continue
                        if (source["doc_id"], source["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
                            raise EvidenceError("foreign document")
                        validate_span(document["text"], source["evidence"])
                    else:
                        passage = passages.get(source["passage_id"])
                        if passage is None:
                            missing = True
                            continue
                        if source["text"] not in passage["text"]:
                            raise EvidenceError("excerpt absent")
                if missing:
                    totals["branches_context_missing"] += 1
                    b["error"] = "source_context_missing"
                else:
                    b["literal_valid"] = True
                    totals["branches_literal_valid"] += 1
            except (EvidenceError, ValueError, AssertionError, KeyError, TypeError) as exc:
                b["error"] = type(exc).__name__
            branch_rows.append(b)
        row["branches"] = branch_rows
    rows.append(row)
    if cid in retr:
        ref = retr[cid]
        retrieval["cases"] += 1
        cited = []
        if cid in saved:
            retrieval["executed"] += 1
            for branch in saved[cid]["answer"]["branches"]:
                if branch["origin"] == "literature" and branch["result"]["kind"] == "accepted":
                    cited += [s for s in branch["result"]["record"]["sources"] if s["kind"] == "literature"]
        topics = set(ref.get("required_topic_ids", []))
        groups = [set(g) for g in ref.get("required_passage_groups", [])]
        if topics:
            retrieval["topic_denominator"] += 1
            retrieval["topic_hit"] += bool(topics & {s["topic_id"] for s in cited})
        if groups:
            retrieval["passage_denominator"] += 1
            ids = {s["passage_id"] for s in cited}
            retrieval["passage_group_coverage_sum"] += sum(bool(g & ids) for g in groups) / len(groups)

summary = {
    "format": "notelens-d009-branch-structural-scoring-v1",
    "run_receipt_sha256": hashlib.sha256((run_dir / "run-receipt.json").read_bytes()).hexdigest(),
    "references_sha256": hashlib.sha256(refs_path.read_bytes()).hexdigest(),
    "retrieval_references_sha256": hashlib.sha256(retr_path.read_bytes()).hexdigest(),
    "totals": totals,
    "retrieval_cited_source_proxy": {
        **{k: v for k, v in retrieval.items() if k != "passage_group_coverage_sum"},
        "any_required_topic_cited_rate": retrieval["topic_hit"] / retrieval["topic_denominator"] if retrieval["topic_denominator"] else None,
        "passage_group_coverage_mean": (retrieval["passage_group_coverage_sum"] / retrieval["passage_denominator"]
                                        if retrieval["passage_denominator"] else None),
        "note": "Proxy from cited literature sources, not topic_recall@5. Actual ranked retrieval, when retained, is scored separately.",
    },
    "cases": rows,
}
out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "cases"}, indent=1))
