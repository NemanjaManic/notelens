"""Replay the recorded BM25 candidates and validate their canonical evidence spans."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unicodedata import unidata_version

from notelens_rag.hybrid import BM25_B, BM25_K1, BM25Passages
from notelens_rag.ingestion import load_corpus


def ranking_settings():
    return {
        "algorithm": "bm25-passage-words-v1",
        "k1": BM25_K1,
        "b": BM25_B,
        "top_k": 5,
        "unicode_data_version": unidata_version,
    }


def verify(root):
    path = root / "docs/rag/evaluation/evidence-gap-proposals.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    corpus = load_corpus(repository_root=root, expected_corpus_version=record["corpus_version"])
    settings = ranking_settings()
    if record["ranking"] != settings:
        raise ValueError("The BM25 settings differ from the recorded proposal settings.")

    ranker = BM25Passages(corpus.passages)
    coverage_counts = Counter()
    distinct_passages = set()
    ranked_positions = evidence_spans = 0
    for case in record["cases"]:
        case_id = case["id"]
        ranked_ids = ranker.rank(case["question"])[:settings["top_k"]]
        if list(ranked_ids) != case["ranked_passage_ids"] or len(ranked_ids) != settings["top_k"]:
            raise ValueError(f"{case_id} candidate order differs from the reviewed order.")
        if corpus.by_id[ranked_ids[0]].topic_id != case["target_topic_id"]:
            raise ValueError(f"{case_id} target topic is missing at rank one.")
        distinct_passages.update(ranked_ids)
        ranked_positions += len(ranked_ids)

        supported = 0
        for part in case["parts"]:
            evidence = part["evidence"]
            if part["status"] != ("supported" if evidence else "missing_in_top_five"):
                raise ValueError(f"{case_id} part status and evidence disagree.")
            supported += bool(evidence)
            for span in evidence:
                passage_id = span["passage_id"]
                start, end = span["start"], span["end"]
                if passage_id not in ranked_ids:
                    raise ValueError(f"{case_id} evidence is outside the reviewed candidates.")
                passage = corpus.by_id[passage_id]
                if not 0 <= start < end <= len(passage.text):
                    raise ValueError(f"{case_id} evidence offsets are outside the passage.")
                digest = sha256(passage.text[start:end].encode("utf-8")).hexdigest()
                if digest != span["quote_sha256"]:
                    raise ValueError(f"{case_id} canonical quote digest differs.")
                evidence_spans += 1

        coverage = "none"
        if supported:
            coverage = "full" if supported == len(case["parts"]) else "partial"
        if not case["parts"] or case["expected_coverage"] != coverage:
            raise ValueError(f"{case_id} case coverage and part labels disagree.")
        coverage_counts[coverage] += 1

    return {
        "cases": len(record["cases"]),
        "ranked_positions": ranked_positions,
        "distinct_passages": len(distinct_passages),
        "evidence_spans": evidence_spans,
        "expected_coverage": dict(coverage_counts),
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parents[3]), indent=2))
