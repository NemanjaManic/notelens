"""D-007 public candidate inventory checks."""

import copy
import json

import pytest

from notelens_eval.qa_inventory import ROOT, digest, inventory


def load_inputs():
    return tuple(json.loads((ROOT / name).read_text(encoding="utf-8")) for name in (
        "docs/rag/qa-proposals.json", "data/knowledge/manifests/passages.json",
    ))


def test_public_candidates_remain_development_only():
    report = inventory(*load_inputs())
    assert report["cases"] == 9
    assert report["by_answerability"] == {"full": 7, "partial": 1, "none": 1}
    assert report["shared_passage_case_pairs"] == [("A-QA-05", "A-QA-07")]
    assert report["verified_passage_slices"] == 0
    assert not report["independent_semantic_review_completed"]


def test_tampered_topic_bounds_fail_inventory():
    proposals, manifest = load_inputs()
    proposals["cases"][0]["parts"][0]["evidence"][0]["topic_end"] += 1
    with pytest.raises(ValueError, match="Invalid evidence reference"):
        inventory(proposals, manifest)


def test_optional_artifact_checks_code_points_and_hash():
    proposals, manifest = load_inputs()
    case = copy.deepcopy(proposals["cases"][0])
    ref = case["parts"][0]["evidence"][0]
    passage = {key: ref[key] for key in ("topic_id", "title", "url")}
    passage.update(start=8, text="\U0001f9ea ABC")
    ref.update(passage_start=2, passage_end=5, topic_start=10, topic_end=13,
               quote_sha256=digest(b"ABC"))
    proposals["cases"] = [case]
    proposals["counts"].update(total=1, by_answerability={"full": 1},
                              by_source_shape={"single_topic": 1})
    passages = {ref["passage_id"]: passage}
    assert inventory(proposals, manifest, passages)["verified_passage_slices"] == 1
    passage["text"] = "\U0001f9ea DEF"
    with pytest.raises(ValueError, match="slice mismatch"):
        inventory(proposals, manifest, passages)
