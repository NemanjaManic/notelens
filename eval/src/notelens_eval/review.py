"""Compare two independent annotation drafts without adjudicating either one."""

import argparse
import json
import sys
from pathlib import Path

from notelens_extraction.evidence import validate_span, validate_text

ATTRIBUTES = ("assertion", "temporality", "subject")


def compare_submissions(document: dict, primary: dict, secondary: dict) -> dict:
    validate_text(document.get("text"), document.get("text_sha256"))
    if primary.get("role") != "primary" or secondary.get("role") != "secondary":
        raise ValueError("Comparison requires one primary and one secondary submission.")
    if primary.get("annotator") == secondary.get("annotator"):
        raise ValueError("Independent submissions must have different annotators.")
    if not primary.get("submission_id") or not secondary.get("submission_id") or primary["submission_id"] == secondary["submission_id"]:
        raise ValueError("Independent submissions require distinct submission IDs.")
    if not primary.get("assignment_id") or primary.get("assignment_id") != secondary.get("assignment_id"):
        raise ValueError("Submissions must belong to the same explicit assignment.")
    for submission in (primary, secondary):
        if (submission.get("doc_id"), submission.get("text_sha256")) != (
                document.get("doc_id"), document.get("text_sha256")):
            raise ValueError("Submission document identity does not match the canonical document.")

    def index(submission):
        rows, duplicates = {}, []
        entities = submission.get("entities")
        if not isinstance(entities, list):
            raise ValueError("Submission entities must be a reviewed list, including an explicit empty list.")
        for i, entity in enumerate(entities):
            if not isinstance(entity, dict) or entity.get("type") not in {"diagnosis", "symptom", "procedure"}:
                raise ValueError("Submission contains an invalid entity record.")
            mention = entity.get("mention")
            validate_span(document["text"], mention)
            evidence = entity.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise ValueError("Every compared mention needs evidence spans.")
            for evidence_span in evidence:
                validate_span(document["text"], evidence_span)
            key = (entity["type"], mention["start"], mention["end"])
            if key in rows:
                duplicates.append(i)
            rows[key] = {"index": i, "entity": entity}
        if duplicates:
            raise ValueError("Submission contains duplicate mention occurrences.")
        return rows

    p_rows, s_rows = index(primary), index(secondary)
    p_keys, s_keys = set(p_rows), set(s_rows)
    shared = sorted(p_keys & s_keys, key=lambda x: (x[1], x[2], x[0]))
    agreements, denominators, disagreements = {a: 0 for a in ATTRIBUTES}, {a: 0 for a in ATTRIBUTES}, []
    evidence_equal = evidence_compared = 0
    for key in shared:
        p_entity, s_entity = p_rows[key]["entity"], s_rows[key]["entity"]
        differences = {}
        for attribute in ATTRIBUTES:
            p_value, s_value = p_entity.get(attribute), s_entity.get(attribute)
            if p_value is None or s_value is None:
                continue
            denominators[attribute] += 1
            agreements[attribute] += int(p_value == s_value)
            if p_value != s_value:
                differences[attribute] = {"primary": p_value, "secondary": s_value}
        p_evidence = {(e.get("start"), e.get("end")) for e in p_entity.get("evidence", [])}
        s_evidence = {(e.get("start"), e.get("end")) for e in s_entity.get("evidence", [])}
        if p_evidence and s_evidence:
            evidence_compared += 1
            evidence_equal += int(p_evidence == s_evidence)
        if differences or p_evidence != s_evidence:
            disagreements.append({"mention_start": key[1], "mention_end": key[2], "entity_type": key[0],
                                  "attribute_differences": differences,
                                  "evidence_spans_equal": p_evidence == s_evidence})
    return {
        "kind": "independent_annotation_comparison",
        "status": "comparison_only_pending_human_adjudication",
        "doc_id": document["doc_id"], "text_sha256": document["text_sha256"],
        "annotators": {"primary": primary["annotator"], "secondary": secondary["annotator"]},
        "mention_matching": "exact type and half-open code-point offsets; no fuzzy matching or adjudication",
        "counts": {"primary_mentions": len(p_rows), "secondary_mentions": len(s_rows),
                   "exact_matched_mentions": len(shared), "missing_from_secondary": len(p_keys - s_keys),
                   "extra_in_secondary": len(s_keys - p_keys)},
        "attribute_agreement": {a: {"agree": agreements[a], "compared": denominators[a],
                                      "rate": agreements[a] / denominators[a] if denominators[a] else None}
                                for a in ATTRIBUTES},
        "evidence_span_agreement": {"equal": evidence_equal, "compared": evidence_compared,
                                    "rate": evidence_equal / evidence_compared if evidence_compared else None},
        "disagreements": disagreements,
        "human_reviewed": False,
        "limitations": ["Exact mention boundaries must match to compare attributes; disagreements in boundaries are counted as missing/extra mentions.",
                        "Agreement is descriptive on this document; it is not adjudication, clinical correctness, corpus-level reliability or a calibrated kappa statistic."]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare primary and independent secondary annotations; never adjudicates")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    if bundle.get("kind") not in {"synthetic_review_comparison", "permitted_review_comparison"}:
        parser.error("Bundle must be explicitly synthetic or permitted for review.")
    report = compare_submissions(bundle["document"], bundle["primary"], bundle["secondary"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError):
        print("Annotation comparison input is invalid or inaccessible; no adjudication was produced.", file=sys.stderr)
        raise SystemExit(1)
