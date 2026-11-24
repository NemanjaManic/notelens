"""Cross-module development evidence and leakage checks."""

import json

import pytest

from notelens_eval.qa_development import DEFAULT_MANIFEST, ROOT, SOURCE_PATHS, build_inventory


@pytest.fixture
def inputs():
    keys = ("document_fixture", "literature_proposal", "literature_source_review", "corpus_manifest")
    return (json.loads(DEFAULT_MANIFEST.read_bytes()),
            *(json.loads((ROOT / SOURCE_PATHS[key]).read_bytes()) for key in keys))


def test_inventory_keeps_source_specific_gaps_and_counts_duplicates_once(inputs):
    report = build_inventory(*inputs)
    assert report["cases"] == 66
    assert report["by_scope_and_state"]["mixed"] == {"sufficient": 6, "partial": 3, "insufficient": 1}
    assert report["duplicate_document_questions"] == [{
        "retained_id": "D-DOC/negation-01/absent", "excluded_id": "D-DOC/limited-04/absent",
    }]
    cases = report["case_references"]
    assert (cases["D-MIX-03"]["document"]["state"], cases["D-MIX-03"]["literature"]["state"]) == (
        "sufficient", "partial",
    )
    assert (cases["D-MIX-05"]["document"]["state"], cases["D-MIX-05"]["literature"]["state"]) == (
        "insufficient", "sufficient",
    )
    assert cases["D-MIX-06"]["literature"]["passage_ids"] == []


def test_groups_are_transitive_across_document_hashes_and_shared_citations(inputs):
    groups = build_inventory(*inputs)["source_groups"]
    assert len(groups) == 22
    assert {"A-QA-05", "A-QA-07", "D-MIX-07", "D-DOC/confirmed-04/supported"} <= set(groups["A-QA-05"])
    assert {"D-MIX-04", "D-MIX-05", "D-DOC/negation-01/supported", "D-DOC/limited-04/supported"} <= set(groups["A-QA-01"])
    assert {"D-MIX-06", "D-DOC/limited-01/absent-clinical"} <= set(groups["A-QA-03"])
    assert sum(map(len, groups.values())) == len({case_id for group in groups.values() for case_id in group}) == 66


@pytest.mark.parametrize(("key", "value", "message"), [
    ("expected_state", "insufficient", "differs from the selected"),
    ("literature_parts", [2], "unique, existing literature parts"),
])
def test_mixed_rows_fail_when_the_declared_evidence_cannot_support_them(inputs, key, value, message):
    inputs[0]["mixed_cases"][0][key] = value
    with pytest.raises(ValueError, match=message):
        build_inventory(*inputs)
