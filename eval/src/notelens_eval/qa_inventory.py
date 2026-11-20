"""Inventory A's public QA proposals without approving or freezing them."""

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HASH = re.compile(r"[0-9a-f]{64}")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_span(start: int, end: int) -> None:
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError("Expected a nonempty Unicode code-point interval.")


def inventory(proposal: dict, manifest: dict, passages: dict | None = None) -> dict:
    if (proposal["partition"] != "development_candidate"
            or proposal["corpus_version"] != manifest["corpus_version"]):
        raise ValueError("Expected public development candidates for the pinned corpus.")
    cases = set()
    questions = set()
    coverage = Counter()
    scope = Counter()
    shared = defaultdict(set)
    evidence_count = 0
    for case in proposal["cases"]:
        case_id = case["id"]
        question = " ".join(case["question"].casefold().split())
        if not question or case_id in cases or question in questions or not case["parts"]:
            raise ValueError("Duplicate case or question, or an empty question or parts list.")
        cases.add(case_id)
        questions.add(question)
        topics = set()
        supported = 0
        for part in case["parts"]:
            citations = part["evidence"]
            if part["status"] == "missing_in_reviewed_scope" and not citations:
                continue
            if part["status"] != "supported" or not citations or not part["expected_fact"].strip():
                raise ValueError(f"Inconsistent part status in {case_id}.")
            supported += 1
            for ref in citations:
                topic = ref["topic_id"]
                passage_id = ref["passage_id"]
                start, end = ref["passage_start"], ref["passage_end"]
                topic_start, topic_end = ref["topic_start"], ref["topic_end"]
                check_span(start, end)
                check_span(topic_start, topic_end)
                if (topic not in manifest["counts"]["passages_by_topic_id"]
                        or end - start != topic_end - topic_start
                        or not re.fullmatch(rf"mplus-{re.escape(topic)}-[0-9a-f]{{64}}", passage_id)
                        or ref["field"] != "cleaned_summary"
                        or not HASH.fullmatch(ref["quote_sha256"])):
                    raise ValueError(f"Invalid evidence reference in {case_id}.")
                if passages is not None:
                    passage = passages.get(passage_id)
                    if (passage is None or any(ref[key] != passage[key] for key in ("topic_id", "title", "url"))
                            or end > len(passage["text"])
                            or (topic_start, topic_end) != (passage["start"] + start, passage["start"] + end)
                            or digest(passage["text"][start:end].encode("utf-8")) != ref["quote_sha256"]):
                        raise ValueError(f"Pinned passage slice mismatch in {case_id}.")
                topics.add(topic)
                shared[passage_id].add(case_id)
                evidence_count += 1
        answerability = "none" if not supported else "full" if supported == len(case["parts"]) else "partial"
        source_shape = "no_supported_topic" if not topics else "single_topic" if len(topics) == 1 else "multi_topic"
        required = case["proposed_required_topic_ids"]
        if (case["answerability"] != answerability or case["source_shape"] != source_shape
                or sorted(required) != sorted(topics) or case["requires_more_than_five_topics"] != (len(topics) > 5)):
            raise ValueError(f"Inconsistent proposed labels in {case_id}.")
        coverage[answerability] += 1
        scope[source_shape] += 1

    counts = proposal["counts"]
    if (not cases or counts["total"] != len(cases) or counts["by_answerability"] != coverage
            or counts["by_source_shape"] != scope):
        raise ValueError("Proposal inventory differs from its declared counts.")
    overlaps = sorted({pair for users in shared.values() for pair in combinations(sorted(users), 2)})
    return {
        "partition": "development_candidate", "corpus_version": proposal["corpus_version"],
        "cases": len(cases), "by_answerability": dict(coverage), "by_source_shape": dict(scope),
        "evidence_references": evidence_count, "shared_passage_case_pairs": overlaps,
        "verified_passage_slices": evidence_count if passages is not None else 0,
        "independent_semantic_review_completed": False,
    }


def validate_development_manifest(development: dict, proposal_raw: bytes, corpus_raw: bytes) -> None:
    proposal, corpus = json.loads(proposal_raw), json.loads(corpus_raw)
    report = inventory(proposal, corpus)
    inputs = development["inputs"]
    if (development["partition"], development["corpus_version"], inputs["proposal"]["sha256"],
        inputs["corpus_manifest"]["sha256"], inputs["pinned_passage_artifact_sha256"]) != (
        report["partition"], report["corpus_version"], digest(proposal_raw), digest(corpus_raw),
        corpus["artifact"]["sha256"],
    ):
        raise ValueError("Development manifest differs from the pinned proposal or corpus.")
    rows = {row["id"]: row for row in development["cases"]}
    if len(rows) != len(development["cases"]) or rows.keys() != {case["id"] for case in proposal["cases"]}:
        raise ValueError("Development manifest must cover each proposal exactly once.")
    overlap = report["shared_passage_case_pairs"]
    if (development["shared_passage_case_pairs"] != [list(pair) for pair in overlap]
            or any(rows[left]["split_group"] != rows[right]["split_group"] for left, right in overlap)
            or any(row["split_group"] not in rows for row in rows.values())):
        raise ValueError("Shared passages must stay in the same development split group.")
    packets = development["review_packets"]
    if not packets or any(not HASH.fullmatch(packet["sha256"]) for packet in packets.values()):
        raise ValueError("Review packets require SHA-256 values.")
    outcomes = Counter()
    verified_count = 0
    for case in proposal["cases"]:
        row = rows[case["id"]]
        for field in ("answerability", "source_shape", "required_topic_ids"):
            proposal_field = f"proposed_{field}" if field == "required_topic_ids" else field
            if row[f"proposed_{field}"] != case[proposal_field]:
                raise ValueError("Development manifest changed an owner proposal label.")
        if len(row["parts"]) != len(case["parts"]):
            raise ValueError("Each proposal part requires one review row.")
        for index, (part, review) in enumerate(zip(case["parts"], row["parts"], strict=True), 1):
            evidence = {number: ref["quote_sha256"] for number, ref in enumerate(part["evidence"], 1)}
            verified = review["verified_evidence"]
            seen = {ref["evidence_index"] for ref in verified}
            if review["part"] != index or len(seen) != len(verified) or not seen <= evidence.keys() or any(
                evidence.get(ref["evidence_index"]) != ref["quote_sha256"] or ref["packet"] not in packets
                for ref in verified
            ):
                raise ValueError("A reviewed excerpt differs from its proposed citation.")
            allowed = (("gap_in_supplied_top_five",) if not evidence else
                       ("supported_in_available_excerpt", "insufficient_in_available_excerpt")
                       if seen == evidence.keys() else ("pending_exact_excerpt",))
            outcome = review["outcome"]
            if outcome not in allowed or not review["note"].strip():
                raise ValueError("A development part has inconsistent review coverage.")
            outcomes[outcome] += 1
            verified_count += len(seen)
    if development["counts"] != {
        "cases": len(rows), "proposed_evidence_references": report["evidence_references"],
        "verified_excerpt_references": verified_count, "verified_from_full_passage_artifact": 0,
        "by_part_review_outcome": outcomes,
    }:
        raise ValueError("Development manifest counts differ from the review rows.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passages", type=Path, help="Optional pinned A passage JSONL artifact.")
    parser.add_argument("--development-manifest", type=Path, help="Check D's excerpt review against the proposal.")
    args = parser.parse_args()
    proposal_raw = (ROOT / "docs/rag/qa-proposals.json").read_bytes()
    corpus_raw = (ROOT / "data/knowledge/manifests/passages.json").read_bytes()
    proposal, manifest = json.loads(proposal_raw), json.loads(corpus_raw)
    development = None
    if args.development_manifest:
        try:
            development = json.loads(args.development_manifest.read_bytes())
            validate_development_manifest(development, proposal_raw, corpus_raw)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(str(exc))
    passages = None
    if args.passages:
        raw = args.passages.read_bytes()
        if digest(raw) != manifest["artifact"]["sha256"]:
            parser.error("Passage artifact differs from A's pinned SHA-256.")
        rows = [json.loads(line) for line in raw.decode("utf-8").split("\n") if line]
        passages = {row["passage_id"]: row for row in rows}
        if len(rows) != len(passages):
            parser.error("Duplicate passage artifact IDs.")
    report = inventory(proposal, manifest, passages)
    if development is not None:
        report["excerpt_review"] = development["counts"]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
