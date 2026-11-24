"""Synthetic checks of the provisional C-002 duplicate and split analysis."""

import importlib.util
from pathlib import Path
import sys

import pytest


DATA = Path(__file__).resolve().parents[3] / "data/mtsamples"
sys.path.insert(0, str(DATA))
SPEC = importlib.util.spec_from_file_location("c002_draft", DATA / "draft_splits.py")
DRAFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRAFT)


def row(identifier, category, text):
    return {"document_id": "synthetic-" + identifier, "source_row_id": identifier,
            "category": category, "transcription": text}


def test_normalized_cross_label_conflicts_are_excluded():
    rows = [row("1", "Neurology", "Synthetic CAFE\u0301\r\nwith six ordered tokens here."),
            row("2", "Urology", "synthetic café with six ordered tokens here.")]
    groups, candidates = DRAFT.build(rows)
    assert len(groups) == 1 and not candidates
    assert groups[0]["labels"] == ["Neurology", "Urology"]
    assert "conflicting_target_labels" in groups[0]["flags"]
    assert groups[0]["draft_split"] is None


def test_contained_near_candidates_are_quarantined_not_automatically_accepted():
    text = " ".join("token" + str(i) for i in range(35))
    groups, candidates = DRAFT.build([row("1", "Neurology", text),
                                      row("2", "Neurology", text + " additional words here")])
    assert len(candidates) == 1 and candidates[0]["decision"] == "unresolved"
    assert all("unresolved_near_candidate" in group["flags"] for group in groups)
    assert all(group["draft_split"] is None for group in groups)


def test_short_nonidentical_texts_do_not_form_empty_shingle_match():
    groups, candidates = DRAFT.build([row("1", "Neurology", "one two"),
                                      row("2", "Urology", "three four")])
    assert not candidates
    assert all("short_text_unreviewed" in group["flags"] for group in groups)
    assert all(group["draft_split"] is None for group in groups)


def test_allocation_is_order_independent_and_groups_do_not_cross_splits():
    rows = [row(str(i), "Neurology", f"synthetic case number {i} has independent content marker{i}")
            for i in range(20)]
    rows.append(row("copy", "Neurology", rows[0]["transcription"]))
    first, first_candidates = DRAFT.build(rows)
    second, second_candidates = DRAFT.build(list(reversed(rows)))
    assert first == second and first_candidates == second_candidates
    assert {g["draft_split"] for g in first} == set(DRAFT.SPLITS)
    members = [d["document_id"] for group in first for d in group["documents"]]
    assert len(members) == len(set(members)) == len(rows)
    shared = next(g for g in first if len(g["documents"]) == 2)
    assert shared["draft_split"] in DRAFT.SPLITS
    assert "transcription" not in str(first)


def test_duplicate_document_identifiers_are_rejected():
    rows = [row("same", "Neurology", "one two three four five"),
            row("same", "Urology", "six seven eight nine ten")]
    with pytest.raises(ValueError, match="Duplicate document IDs"):
        DRAFT.build(rows)
