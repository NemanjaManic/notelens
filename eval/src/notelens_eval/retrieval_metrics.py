"""Offline FR-019 scoring for ranked passages and independent relevance judgments."""

from statistics import mean


def indexed_cases(cases: list[dict]) -> dict:
    indexed = {case["id"]: case for case in cases}
    if not cases or len(indexed) != len(cases):
        raise ValueError("Evaluation case IDs must be nonempty and unique.")
    if any(not isinstance(case_id, str) or not case_id.strip() for case_id in indexed):
        raise ValueError("Evaluation case IDs must be nonempty strings.")
    return indexed


def identifiers(values: list[str]) -> set[str]:
    if not isinstance(values, list) or not values or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ValueError("Expected nonempty relevance identifiers.")
    unique = set(values)
    if len(unique) != len(values):
        raise ValueError("Duplicate relevance identifier.")
    return unique


def score_case(reference: dict, ranked: list[dict]) -> dict:
    expected_status = reference.get("expected_status", "supported")
    if expected_status not in {"supported", "insufficient"}:
        raise ValueError("Expected supported or insufficient retrieval references.")
    if expected_status == "insufficient":
        if reference["required_topic_ids"] != [] or reference["required_passage_groups"] != []:
            raise ValueError("Insufficient references cannot declare required topics or passages.")
        topics, groups = set(), []
    else:
        topics = identifiers(reference["required_topic_ids"])
        raw_groups = reference["required_passage_groups"]
        if not isinstance(raw_groups, list) or not raw_groups:
            raise ValueError("At least one reviewed evidence group is required.")
        groups = [identifiers(group) for group in raw_groups]
    scope = reference["source_scope"]
    if scope not in ("single", "multi"):
        raise ValueError("Expected single or multi source scope.")
    if len({frozenset(group) for group in groups}) != len(groups):
        raise ValueError("Duplicate evidence group.")
    if not isinstance(ranked, list):
        raise ValueError("Ranked passages must be a list.")
    passage_topics = {}
    for passage in ranked:
        passage_id, topic_id = passage["passage_id"], passage["topic_id"]
        identifiers([passage_id])
        identifiers([topic_id])
        if passage_topics.setdefault(passage_id, topic_id) != topic_id:
            raise ValueError("A ranked passage has conflicting topics.")
    top_five = ranked[:5]
    unique_topics = list(dict.fromkeys(row["topic_id"] for row in top_five))
    positions = [rank for rank, topic in enumerate(unique_topics, 1) if topic in topics]
    retrieved_passages = {row["passage_id"] for row in top_five}
    covered = sum(bool(group & retrieved_passages) for group in groups)
    return {
        "id": reference["id"], "source_scope": scope,
        "topic_recall_at_5": len(positions) / len(topics) if topics else None,
        "topic_reciprocal_rank_at_5": (1 / positions[0] if positions else 0.0) if topics else None,
        "all_required_topics_at_5": len(positions) == len(topics) if topics else None,
        "more_than_five_required_topics": len(topics) > 5,
        "passage_evidence_coverage_at_5": covered / len(groups) if groups else None,
        "all_required_evidence_at_5": covered == len(groups) if groups else None,
    }


def summarize(rows: list[dict]) -> dict:
    def average(key: str):
        values = [row[key] for row in rows if row[key] is not None]
        return mean(values) if values else None

    return {
        "cases": len(rows),
        "topic_metric_denominator": sum(row["topic_recall_at_5"] is not None for row in rows),
        "evidence_metric_denominator": sum(row["passage_evidence_coverage_at_5"] is not None for row in rows),
        "topic_recall_at_5": average("topic_recall_at_5"),
        "topic_mrr_at_5": average("topic_reciprocal_rank_at_5"),
        "all_required_topics_rate_at_5": average("all_required_topics_at_5"),
        "passage_evidence_coverage_at_5": average("passage_evidence_coverage_at_5"),
        "all_required_evidence_rate_at_5": average("all_required_evidence_at_5"),
        "more_than_five_required_topics": sum(row["more_than_five_required_topics"] for row in rows),
    }


def evaluate_retrieval(references: dict, predictions: dict) -> dict:
    expected = indexed_cases(references["cases"])
    actual = indexed_cases(predictions["cases"])
    if expected.keys() != actual.keys():
        raise ValueError("Retrieval references and predictions must have the same case IDs.")
    rows = [
        score_case(reference, actual[case_id]["ranked_passages"])
        for case_id, reference in expected.items()
    ]
    return {
        "label": "offline retrieval relevance scoring",
        "reference_version": references["version"],
        "prediction_version": predictions["version"],
        "overall": summarize(rows),
        "by_source_scope": {
            scope: summarize([row for row in rows if row["source_scope"] == scope])
            for scope in ("single", "multi")
        },
        "cases": rows,
    }
