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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passages", type=Path, help="Optional pinned A passage JSONL artifact.")
    args = parser.parse_args()
    proposal = json.loads((ROOT / "docs/rag/qa-proposals.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data/knowledge/manifests/passages.json").read_text(encoding="utf-8"))
    passages = None
    if args.passages:
        raw = args.passages.read_bytes()
        if digest(raw) != manifest["artifact"]["sha256"]:
            parser.error("Passage artifact differs from A's pinned SHA-256.")
        rows = [json.loads(line) for line in raw.decode("utf-8").split("\n") if line]
        passages = {row["passage_id"]: row for row in rows}
        if len(rows) != len(passages):
            parser.error("Duplicate passage artifact IDs.")
    print(json.dumps(inventory(proposal, manifest, passages), indent=2))


if __name__ == "__main__":
    main()
