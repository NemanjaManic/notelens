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


def read_source_manifest(path: Path, *, expected_sha256: str | None,
                         source_version: str | None) -> tuple[dict, str]:
    if (expected_sha256 is None) != (source_version is None):
        raise ValueError("Provide the expected manifest SHA-256 and source version together.")
    if expected_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("Expected SHA-256 must contain 64 hexadecimal characters.")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("Could not read the source manifest.") from exc
    checksum = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and checksum != expected_sha256.lower():
        raise ValueError("Source manifest SHA-256 differs from the expected checksum.")

    def unique_fields(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError("Source manifest contains duplicate JSON fields.")
            result[key] = value
        return result

    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_fields)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Source manifest must contain valid UTF-8 JSON.") from exc
    if not isinstance(manifest, dict):
        raise ValueError("The source manifest must be a JSON object.")
    if source_version is not None and manifest.get("source_version") != source_version:
        raise ValueError("Source manifest version differs from the expected version.")
    return manifest, checksum


def validate_selection_size(count: int, reviews: int) -> None:
    if count < 4 or count % 4 or not 0 <= reviews <= count:
        raise ValueError("Selection count must be divisible by four; review count must fit it.")


def candidate_groups(manifest: dict) -> list[dict]:
    if not isinstance(manifest, dict):
        raise ValueError("The source manifest must be a JSON object.")
    version = manifest.get("source_version")
    if (not isinstance(version, str) or not version.strip()
            or manifest.get("kind") not in ("synthetic", "permitted_benchmark")):
        raise ValueError("An explicit permitted source/version is required.")
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise ValueError("The manifest documents must be a JSON array.")
    groups, ids, documents_by_hash = {}, set(), {}
    for index, doc in enumerate(documents, start=1):
        if not isinstance(doc, dict):
            raise ValueError(f"Candidate row {index} must be a JSON object.")
        doc_id, group = doc.get("doc_id"), doc.get("group_id")
        if not all(isinstance(value, str) and value.strip() for value in (doc_id, group)):
            raise ValueError(f"Candidate row {index} requires document and group IDs.")
        if doc_id in ids:
            raise ValueError("Duplicate source document ID.")
        ids.add(doc_id)
        if doc.get("specialty") not in SPECIALTIES or doc.get("split") not in ("validation", "test"):
            raise ValueError("Expected target specialties and validation/test portions.")
        digest = doc.get("text_sha256")
        if (doc.get("permitted_for_annotation") is not True or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("Source access/permission and canonical hashes are required.")
        if "canonical_text" in doc:
            validate_text(doc["canonical_text"], digest)
        first = documents_by_hash.setdefault(digest, doc)
        if first["split"] != doc["split"]:
            raise ValueError("An identical canonical hash crosses development/final portions.")
        if first["group_id"] != group:
            raise ValueError("An identical canonical hash belongs to different duplicate groups.")
        if group in groups and groups[group]["split"] != doc["split"]:
            raise ValueError("A duplicate group crosses development/final portions.")
        if group in groups and groups[group]["specialty"] != doc["specialty"]:
            raise ValueError("A duplicate group has conflicting specialty labels.")
        if group not in groups or doc_id < groups[group]["doc_id"]:
            groups[group] = doc
    return sorted(groups.values(), key=lambda d: d["doc_id"])


def preflight(manifest: dict, *, count: int, reviews: int) -> dict:
    validate_selection_size(count, reviews)
    candidates = candidate_groups(manifest)
    group_counts = Counter(doc["split"] for doc in candidates)
    specialty_counts = Counter(doc["specialty"] for doc in candidates)
    development_groups = group_counts["validation"]
    quota = count // len(MEMBERS)
    issues = []
    if len(candidates) < count:
        issues.append("insufficient_unique_groups")
    if development_groups < quota:
        issues.append("insufficient_member_c_development_primary_groups")
    if reviews and development_groups <= quota:
        issues.append("member_c_development_review_unavailable")
    return {"kind": "annotation_manifest_preflight", "source_kind": manifest["kind"],
            "source_version": manifest["source_version"], "candidate_documents": len(manifest["documents"]),
            "candidate_groups": len(candidates), "requested_documents": count, "requested_reviews": reviews,
            "groups_by_split": {split: group_counts[split] for split in ("validation", "test")},
            "groups_by_specialty": {specialty: specialty_counts[specialty] for specialty in SPECIALTIES},
            "member_c_primary_quota": quota, "issues": issues,
            "status": "needs_review" if issues else "ready_for_selection_review"}


def select(manifest: dict, *, count: int, reviews: int, seed: int) -> dict:
    validate_selection_size(count, reviews)
    candidates = candidate_groups(manifest)
    if len(candidates) < count:
        raise ValueError("Insufficient unique groups for the requested selection.")
    random.Random(seed).shuffle(candidates)
    chosen, totals = [], Counter()

    def take(pool, number):
        for _ in range(number):
            available = [d for d in candidates if d not in chosen and pool(d)]
            if not available:
                raise ValueError("No feasible development-only allocation for C or insufficient source groups.")
            # Prefer the least represented specialty; seeded input order breaks ties.
            doc = min(available, key=lambda d: totals[d["specialty"]])
            chosen.append(doc)
            totals[doc["specialty"]] += 1

    quota = count // 4
    development_count = sum(d["split"] == "validation" for d in candidates)
    reserve_c_review = reviews > 0 and development_count > quota
    take(lambda d: d["split"] == "validation", quota + int(reserve_c_review))
    take(lambda d: True, count - len(chosen))
    allocation = ["member-c"] * quota + [m for m in ("member-a", "member-b", "member-d") for _ in range(quota)]
    assignments = []
    for index, (doc, primary) in enumerate(zip(chosen, allocation)):
        assignments.append({"assignment_id": f"assignment-{index:03d}",
                            **{key: doc[key] for key in ("doc_id", "group_id", "split", "specialty", "text_sha256")},
                            "portion": "development" if doc["split"] == "validation" else "final",
                            "primary": primary, "reviewer": None, "review_state": "pending",
                            "access_state": "pending_team_policy"})
    review_candidates = assignments
    if reserve_c_review:
        # The additional development group follows C's primary quota and is owned by A.
        assignments[quota]["reviewer"] = "member-c"
        review_candidates = assignments[:quota] + assignments[quota + 1:]
    for index, assignment in enumerate(review_candidates[:reviews - int(reserve_c_review)]):
        allowed = [m for m in MEMBERS if m != assignment["primary"] and
                   (m != "member-c" or assignment["portion"] == "development")]
        assignment["reviewer"] = allowed[index % len(allowed)]
    portion_counts = dict(Counter(a["portion"] for a in assignments))
    return {"kind": manifest["kind"], "source_version": manifest["source_version"],
            "version": "assignment-proposal-v1", "seed": seed, "status": "proposal_pending_team_review",
            "human_reviewed": False, "specialty_counts": dict(totals),
            "portion_counts": portion_counts, "portion_proportions": {k: v / count for k, v in portion_counts.items()},
            "review_warnings": ["member_c_development_review_unavailable"] if reviews and not reserve_c_review else [],
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
                           "unresolved_questions": [], "complete_document_review": False})
    return result


def lint_submission(assignment: dict, document: dict, submission: dict) -> dict:
    """Check an annotator draft before review; never certifies semantic completeness."""
    errors, questions = [], []

    def issue(code: str):
        errors.append(code)

    try:
        validate_text(document.get("text"), document.get("text_sha256"))
    except (ValueError, TypeError):
        issue("invalid_canonical_document")
    identity = (assignment.get("assignment_id"), assignment.get("doc_id"), assignment.get("text_sha256"))
    if not all(isinstance(value, str) and value for value in identity):
        issue("invalid_assignment_identity")
    if (document.get("doc_id"), document.get("text_sha256")) != identity[1:]:
        issue("assignment_document_mismatch")
    if (submission.get("assignment_id"), submission.get("doc_id"), submission.get("text_sha256")) != identity:
        issue("submission_identity_mismatch")
    role = submission.get("role")
    expected_annotator = assignment.get("primary") if role == "primary" else assignment.get("reviewer") if role == "secondary" else None
    if not expected_annotator or submission.get("annotator") != expected_annotator:
        issue("annotator_role_mismatch")
    if not isinstance(submission.get("submission_id"), str) or not submission["submission_id"].strip():
        issue("missing_submission_id")
    if submission.get("complete_document_review") is not True:
        issue("document_review_not_marked_complete")
    entities = submission.get("entities")
    if not isinstance(entities, list):
        issue("entities_must_be_explicit_list")
        entities = []
    unresolved = []
    for field in ("unresolved_questions", "questions"):
        entries = submission.get(field, [])
        if isinstance(entries, list):
            unresolved.extend(entries)
        else:
            issue(f"{field}_must_be_list")
    questions.extend(f"unresolved_question_{index + 1}" for index, value in enumerate(unresolved) if value)
    seen = set()
    text = document.get("text", "") if isinstance(document.get("text", ""), str) else ""
    for index, entity in enumerate(entities):
        prefix = f"entity_{index + 1}"
        if not isinstance(entity, dict):
            issue(prefix + "_must_be_object")
            continue
        kind = entity.get("type")
        valid_kind = kind in ("diagnosis", "symptom", "procedure")
        if not valid_kind:
            issue(prefix + "_invalid_type")
        mention = entity.get("mention")
        try:
            validate_span(text, mention)
        except ValueError:
            issue(prefix + "_invalid_mention_span")
            mention = None
        if mention is not None and valid_kind:
            occurrence = (kind, mention["start"], mention["end"])
            if occurrence in seen:
                issue(prefix + "_duplicate_occurrence")
            seen.add(occurrence)
        assertion = entity.get("assertion")
        if assertion not in ("confirmed", "suspected", "negated", "unknown"):
            if assertion is None or entity.get("assertion_unresolved"):
                questions.append(prefix + "_assertion_unresolved")
            else:
                issue(prefix + "_invalid_assertion")
        if entity.get("temporality") not in ("current", "historical", "unknown"):
            issue(prefix + "_invalid_temporality")
        if entity.get("subject") not in ("patient", "family", "other", "unknown"):
            issue(prefix + "_invalid_subject")
        evidence = entity.get("evidence")
        valid_evidence = []
        if not isinstance(evidence, list) or not evidence:
            issue(prefix + "_evidence_required")
        else:
            for span in evidence:
                try:
                    validate_span(text, span)
                    valid_evidence.append(span)
                except (ValueError, TypeError):
                    issue(prefix + "_invalid_evidence_span")
        if mention and valid_evidence and not any(span["start"] <= mention["start"] and span["end"] >= mention["end"] for span in valid_evidence):
            questions.append(prefix + "_mention_not_covered_by_evidence")
        status = entity.get("procedure_status")
        if kind == "procedure":
            if status not in ("planned", "ordered", "performed", "cancelled", "hypothetical", "unknown"):
                issue(prefix + "_invalid_procedure_status")
        elif status is not None:
            issue(prefix + "_nonprocedure_status")
        icd = entity.get("icd")
        if icd is not None:
            try:
                validate_span(text, icd["evidence"])
                if icd["code"] != icd["evidence"]["quote"]:
                    issue(prefix + "_icd_not_literal")
            except (ValueError, TypeError, KeyError):
                issue(prefix + "_invalid_icd_evidence")
    if errors:
        status = "needs_correction"
    elif questions:
        status = "needs_clarification"
    else:
        status = "ready_for_independent_review"
    return {"kind": "annotation_lint_report", "status": status,
            "assignment_id": assignment.get("assignment_id"), "doc_id": document.get("doc_id"),
            "submission_id": submission.get("submission_id"), "annotator": submission.get("annotator"),
            "entity_count": len(entities), "errors": errors, "questions": questions,
            "human_reviewed": False,
            "limitation": "Structural and workflow checks only; this does not certify annotation completeness, agreement, semantic support or clinical correctness."}


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
            if entity.get("type") not in {"diagnosis", "symptom", "procedure"} or entity.get("assertion") not in {"confirmed", "suspected", "negated", "unknown"}:
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
    preflight_parser = commands.add_parser("preflight", help="Verify a C-002 adapter manifest without assigning documents")
    preflight_parser.add_argument("manifest", type=Path)
    preflight_parser.add_argument("--count", type=int, default=40)
    preflight_parser.add_argument("--reviews", type=int, default=10)
    preflight_parser.add_argument("--expected-sha256", required=True)
    preflight_parser.add_argument("--source-version", required=True)
    selection = commands.add_parser("select")
    selection.add_argument("manifest", type=Path)
    selection.add_argument("--count", type=int, default=40)
    selection.add_argument("--reviews", type=int, default=10)
    selection.add_argument("--seed", type=int, required=True)
    selection.add_argument("--output", type=Path, required=True)
    selection.add_argument("--expected-sha256")
    selection.add_argument("--source-version")
    adjudication = commands.add_parser("merge")
    adjudication.add_argument("bundle", type=Path, help="Permitted assignment, document, submissions and explicit decision")
    adjudication.add_argument("--output", type=Path, required=True)
    lint = commands.add_parser("lint")
    lint.add_argument("bundle", type=Path, help="One assignment, canonical document and one draft submission")
    lint.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command in {"preflight", "select"}:
        try:
            source, checksum = read_source_manifest(args.manifest, expected_sha256=args.expected_sha256,
                                                    source_version=args.source_version)
            if args.command == "preflight":
                report = preflight(source, count=args.count, reviews=args.reviews)
        except (OSError, ValueError) as exc:
            print(f"Invalid annotation manifest: {exc}", file=sys.stderr)
            return 1
        if args.command == "preflight":
            print(json.dumps({**report, "manifest_sha256": checksum}, sort_keys=True))
            return int(bool(report["issues"]))
    if args.command == "select":
        result = select(source, count=args.count, reviews=args.reviews, seed=args.seed)
        result["source_manifest_sha256"] = checksum
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "assignments.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        (args.output / "blank-templates.json").write_text(json.dumps(templates(result), indent=2) + "\n", encoding="utf-8")
        if result["review_warnings"]:
            print("The proposal cannot give C an independent development review. Review capacity before freezing assignments.",
                  file=sys.stderr)
        print(f"Prepared {len(result['assignments'])} proposal assignments and pending templates; no human annotations generated.")
    elif args.command == "merge":
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        if bundle.get("kind") not in {"synthetic", "permitted_benchmark"}:
            parser.error("Only permitted benchmark or synthetic bundles may be merged.")
        result = merge(bundle["assignment"], bundle["document"], bundle["submissions"],
                       bundle.get("decision"), synthetic=bundle["kind"] == "synthetic")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Prepared reference state: {result['review_state']}.")
    else:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        if bundle.get("kind") not in {"synthetic", "permitted_benchmark"}:
            parser.error("Only explicitly synthetic or permitted benchmark bundles may be linted.")
        result = lint_submission(bundle["assignment"], bundle["document"], bundle["submission"])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Submission lint status: {result['status']} ({len(result['errors'])} structural issue(s), {len(result['questions'])} question(s)).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError):
        print("Annotation input is invalid, inaccessible or infeasible; no completed reference was generated.", file=sys.stderr)
        raise SystemExit(1)
