"""Provisional C-manifest adapter, pending templates and explicit adjudication.

This does not create C's production splits or anyone's completed annotations.
"""

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

from notelens_extraction.evidence import validate_span, validate_text

SPECIALTIES = ["Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology", "Neurology", "Urology"]
MEMBERS = ["member-a", "member-b", "member-c", "member-d"]


def select(manifest: dict, *, count: int, reviews: int, seed: int) -> dict:
    if count < 4 or count % 4 or not 0 <= reviews <= count:
        raise ValueError("Selection count must be divisible by four; review count must fit it.")
    if not manifest.get("source_version") or manifest.get("kind") not in {"synthetic", "permitted_benchmark"}:
        raise ValueError("An explicit permitted source/version is required.")
    documents = manifest["documents"]
    groups, ids, hash_splits = {}, set(), {}
    for doc in documents:
        if doc["doc_id"] in ids:
            raise ValueError("Duplicate source document ID.")
        ids.add(doc["doc_id"])
        if doc["specialty"] not in SPECIALTIES or doc["split"] not in {"validation", "test"}:
            raise ValueError("Expected target specialties and validation/test portions.")
        if not doc.get("permitted_for_annotation") or not re.fullmatch(r"[0-9a-f]{64}", doc["text_sha256"]):
            raise ValueError("Source access/permission and canonical hashes are required.")
        if "canonical_text" in doc:
            validate_text(doc["canonical_text"], doc["text_sha256"])
        if doc["text_sha256"] in hash_splits and hash_splits[doc["text_sha256"]] != doc["split"]:
            raise ValueError("An identical canonical hash crosses development/final portions.")
        hash_splits[doc["text_sha256"]] = doc["split"]
        group = doc["group_id"]
        if group in groups and groups[group]["split"] != doc["split"]:
            raise ValueError("A duplicate group crosses development/final portions.")
        if group in groups and groups[group]["specialty"] != doc["specialty"]:
            raise ValueError("A duplicate group has conflicting specialty labels.")
        if group not in groups or doc["doc_id"] < groups[group]["doc_id"]:
            groups[group] = doc
    candidates = sorted(groups.values(), key=lambda d: d["doc_id"])
    if len(candidates) < count:
        raise ValueError("Insufficient unique groups for the requested selection.")
    random.Random(seed).shuffle(candidates)
    chosen, totals = [], Counter()

    def take(pool, number, member=None):
        for _ in range(number):
            available = [d for d in candidates if d not in chosen and pool(d)]
            if not available:
                raise ValueError("No feasible development-only allocation for C or insufficient source groups.")
            # Prefer the least represented specialty; seeded input order breaks ties.
            doc = min(available, key=lambda d: totals[d["specialty"]])
            chosen.append(doc)
            totals[doc["specialty"]] += 1

    quota = count // 4
    take(lambda d: d["split"] == "validation", quota, "member-c")
    take(lambda d: True, count - quota)
    allocation = ["member-c"] * quota + [m for m in ("member-a", "member-b", "member-d") for _ in range(quota)]
    assignments = []
    for index, (doc, primary) in enumerate(zip(chosen, allocation)):
        assignments.append({"assignment_id": f"assignment-{index:03d}",
                            **{key: doc[key] for key in ("doc_id", "group_id", "split", "specialty", "text_sha256")},
                            "portion": "development" if doc["split"] == "validation" else "final",
                            "primary": primary, "reviewer": None, "review_state": "pending",
                            "access_state": "pending_team_policy"})
    for index, assignment in enumerate(assignments[:reviews]):
        allowed = [m for m in MEMBERS if m != assignment["primary"] and
                   (m != "member-c" or assignment["portion"] == "development")]
        assignment["reviewer"] = allowed[index % len(allowed)]
    portion_counts = dict(Counter(a["portion"] for a in assignments))
    return {"kind": manifest["kind"], "source_version": manifest["source_version"],
            "version": "assignment-proposal-v1", "seed": seed, "status": "proposal_pending_team_review",
            "human_reviewed": False, "specialty_counts": dict(totals),
            "portion_counts": portion_counts, "portion_proportions": {k: v / count for k, v in portion_counts.items()},
            "assignments": assignments}


def templates(manifest: dict) -> list[dict]:
    result = []
    for assignment in manifest["assignments"]:
        for role, member in (("primary", assignment["primary"]), ("secondary", assignment["reviewer"])):
            if member is None:
                continue
            result.append({"assignment_id": assignment["assignment_id"], "role": role,
                           "assignment_version": manifest["version"], "source_version": manifest["source_version"],
                           "group_id": assignment["group_id"], "portion": assignment["portion"],
                           "annotator": member, "doc_id": assignment["doc_id"],
                           "text_sha256": assignment["text_sha256"], "guide_version": "draft-2026-11-11",
                           "review_state": "pending", "human_reviewed": False, "entities": None,
                           "questions": [], "complete_document_review": False})
    return result


def merge(assignment: dict, document: dict, submissions: list[dict], decision: dict | None,
          *, synthetic: bool) -> dict:
    """Never infer human review. Resolve only an explicitly recorded decision.

    Primary/secondary submissions stay unchanged. A synthetic decision can exercise
    the path but can never become a human-reviewed reference.
    """
    validate_text(document["text"], document["text_sha256"])
    if (assignment["doc_id"], assignment["text_sha256"]) != (document["doc_id"], document["text_sha256"]):
        raise ValueError("Assignment/document mismatch.")
    by_id = {}
    for submission in submissions:
        role = submission["role"]
        expected = assignment["primary"] if role == "primary" else assignment["reviewer"] if role == "secondary" else None
        if not expected or submission.get("assignment_id") != assignment["assignment_id"] or submission["annotator"] != expected or submission["doc_id"] != document["doc_id"] or submission["text_sha256"] != document["text_sha256"]:
            raise ValueError("Submission identity, role or assignment mismatch.")
        if not submission.get("complete_document_review") or not isinstance(submission.get("entities"), list):
            raise ValueError("An incomplete template cannot become a reference.")
        identifier = submission["submission_id"]
        if identifier in by_id:
            raise ValueError("Duplicate submission ID.")
        for entity in submission["entities"]:
            if entity.get("type") not in {"diagnosis", "symptom", "procedure"} or entity.get("assertion") not in {"confirmed", "suspected", "negated"}:
                raise ValueError("Unresolved entity labels cannot become a canonical reference.")
            if entity.get("temporality") not in {"current", "historical", "unknown"} or entity.get("subject") not in {"patient", "family", "other", "unknown"}:
                raise ValueError("Invalid reference context labels.")
            validate_span(document["text"], entity["mention"])
            if not entity.get("evidence"):
                raise ValueError("Reference evidence is required.")
            for span in entity["evidence"]:
                validate_span(document["text"], span)
        by_id[identifier] = submission
    provenance = {key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                  for key, value in by_id.items()}
    base = {"doc_id": document["doc_id"], "text_sha256": document["text_sha256"],
            "submission_sha256": provenance, "human_reviewed": False}
    if decision is None:
        return {**base, "review_state": "pending_adjudication", "entities": None}
    if not decision.get("adjudicator") or not decision.get("rationale") or decision.get("selected_submission_id") not in by_id:
        raise ValueError("Adjudication needs an explicit reviewer, rationale and source submission.")
    required = {"primary", "secondary"} if assignment["reviewer"] else {"primary"}
    if {s["role"] for s in submissions} != required or len(submissions) != len(required):
        raise ValueError("Required independent submissions are missing.")
    if not synthetic and not (decision.get("human_reviewed") is True and all(s.get("human_reviewed") is True for s in submissions)):
        raise ValueError("Human review must be explicitly attested, not generated by the merger.")
    selected = by_id[decision["selected_submission_id"]]
    return {**base, "human_reviewed": not synthetic,
            "review_state": "synthetic_adjudication" if synthetic else "human_reviewed",
            "entities": selected["entities"], "decision": decision}


def main() -> int:
    parser = argparse.ArgumentParser(description="D-owned draft annotation tooling; no completed labels are generated")
    commands = parser.add_subparsers(dest="command", required=True)
    selection = commands.add_parser("select")
    selection.add_argument("manifest", type=Path)
    selection.add_argument("--count", type=int, default=40)
    selection.add_argument("--reviews", type=int, default=10)
    selection.add_argument("--seed", type=int, required=True)
    selection.add_argument("--output", type=Path, required=True)
    adjudication = commands.add_parser("merge")
    adjudication.add_argument("bundle", type=Path, help="Permitted assignment, document, submissions and explicit decision")
    adjudication.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "select":
        source = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = select(source, count=args.count, reviews=args.reviews, seed=args.seed)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "assignments.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (args.output / "blank-templates.json").write_text(json.dumps(templates(result), indent=2) + "\n", encoding="utf-8")
        print(f"Prepared {len(result['assignments'])} proposal assignments and pending templates; no human annotations generated.")
    else:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        if bundle.get("kind") not in {"synthetic", "permitted_benchmark"}:
            parser.error("Only permitted benchmark or synthetic bundles may be merged.")
        result = merge(bundle["assignment"], bundle["document"], bundle["submissions"],
                       bundle.get("decision"), synthetic=bundle["kind"] == "synthetic")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Prepared reference state: {result['review_state']}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError):
        print("Annotation input is invalid, inaccessible or infeasible; no completed reference was generated.", file=sys.stderr)
        raise SystemExit(1)
