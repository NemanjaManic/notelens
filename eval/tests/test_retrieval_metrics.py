"""FR-019 ranking, evidence, grouping and CLI regressions."""

import json

import pytest

from notelens_eval.retrieval_metrics import evaluate_retrieval, score_case
from notelens_eval.run import main


def passage(passage_id, topic_id):
    return {"passage_id": passage_id, "topic_id": topic_id}


SINGLE = {"id": "single", "source_scope": "single", "required_topic_ids": ["target"],
          "required_passage_groups": [["target-support", "target-alternative"]]}
MULTI = {"id": "multi", "source_scope": "multi", "required_topic_ids": list("abcdef"),
         "required_passage_groups": [["a-support"], ["f-support"]]}


def test_relevance_is_separate_from_evidence_at_five():
    row = score_case(SINGLE, [
        passage("other-1", "other"), passage("other-2", "other"),
        passage("target-unreviewed", "target"), passage("extra-1", "extra"),
        passage("extra-2", "extra"), passage("target-support", "target"),
    ])
    assert row["topic_recall_at_5"] == 1
    assert row["topic_reciprocal_rank_at_5"] == 0.5
    assert row["all_required_topics_at_5"]
    assert row["passage_evidence_coverage_at_5"] == 0


def test_grouped_report_and_larger_than_five_reference(tmp_path, monkeypatch):
    references = {"version": "reference-v1", "cases": [SINGLE, MULTI]}
    predictions = {"version": "mock-ranking-v1", "cases": [
        {"id": "single", "ranked_passages": [passage("target-alternative", "target")]},
        {"id": "multi", "ranked_passages": [passage(f"{topic}-support", topic) for topic in "abcdef"]},
    ]}
    paths = [tmp_path / name for name in ("reference.json", "ranking.json")]
    for path, value in zip(paths, (references, predictions)):
        path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["notelens_eval.run", "--profile", "retrieval",
                                    "--references", str(paths[0]), "--predictions", str(paths[1]),
                                    "--output", str(tmp_path)])
    assert main() == 0
    report = json.loads((tmp_path / "retrieval-results.json").read_text(encoding="utf-8"))
    assert report["reference_version"] == "reference-v1"
    assert report["by_source_scope"]["single"]["all_required_evidence_rate_at_5"] == 1
    multi = report["by_source_scope"]["multi"]
    assert multi["topic_recall_at_5"] == 5 / 6
    assert multi["all_required_topics_rate_at_5"] == 0
    assert multi["passage_evidence_coverage_at_5"] == 0.5
    assert multi["more_than_five_required_topics"] == 1


def test_missing_predictions_are_not_treated_as_empty_rankings():
    with pytest.raises(ValueError, match="same case IDs"):
        evaluate_retrieval({"cases": [SINGLE, MULTI]}, {"cases": [{"id": "single"}]})
    assert score_case(SINGLE, [])["topic_recall_at_5"] == 0
